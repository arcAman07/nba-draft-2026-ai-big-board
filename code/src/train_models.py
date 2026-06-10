"""Phase 3 training + validation.

Leave-one-draft-class-out (LODCO) CV: 22 folds grouped by draft year
(2000-2021). Every model is compared to the pick-slot-only baseline.

Outputs:
  models/metrics_regression.json
  models/metrics_tiers.json
  models/metrics_bust.json
  models/cv_oof_predictions.csv (out-of-fold preds for best models)
  figures/feature_importance.png
  figures/calibration_bust.png (bust model calibration, LODCO out-of-fold)

Run: python3 src/train_models.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LassoCV, LogisticRegression, RidgeCV
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_common import (
    PICK_FEATURES,
    SEED,
    SKILL_FEATURES,
    TIER_ORDER,
    TRANSFORMS,
    assign_bust,
    assign_tier,
    load_historical,
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(BASE, "models")
FIGURES = os.path.join(BASE, "figures")
os.makedirs(MODELS, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)

np.random.seed(SEED)

ALPHAS = np.logspace(-2, 3, 30)


def make_ridge():
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("m", RidgeCV(alphas=ALPHAS)),
        ]
    )


def make_lasso():
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("m", LassoCV(alphas=ALPHAS, cv=5, random_state=SEED, max_iter=20000)),
        ]
    )


def make_hgb():
    return HistGradientBoostingRegressor(
        max_iter=300,
        max_depth=3,
        learning_rate=0.05,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=SEED,
    )


def make_logit_multi():
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("m", LogisticRegression(max_iter=5000, C=0.3, random_state=SEED)),
        ]
    )


def make_hgb_clf():
    return HistGradientBoostingClassifier(
        max_iter=250,
        max_depth=3,
        learning_rate=0.05,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=SEED,
    )


def make_bust_logit():
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("m", LogisticRegression(max_iter=5000, C=0.3, random_state=SEED)),
        ]
    )


def lodco_regression(h, features, model_factory, tname, target="career_vorp"):
    """LODCO CV. Model is trained on transformed target; metrics on raw scale."""
    fwd, inv = TRANSFORMS[tname]
    oof = np.full(len(h), np.nan)
    years = sorted(h["year"].unique())
    for yr in years:
        tr, te = h["year"] != yr, h["year"] == yr
        m = model_factory()
        m.fit(h.loc[tr, features], fwd(h.loc[tr, target].values))
        oof[te.values] = inv(m.predict(h.loc[te, features]))
    y = h[target].values
    per_year_rho = [
        spearmanr(y[h.year == yr], oof[(h.year == yr).values]).statistic for yr in years
    ]
    return oof, {
        "mae": float(mean_absolute_error(y, oof)),
        "rmse": float(np.sqrt(mean_squared_error(y, oof))),
        "spearman_pooled": float(spearmanr(y, oof).statistic),
        "spearman_mean_within_year": float(np.nanmean(per_year_rho)),
    }


def lodco_pick_baseline(h, target="career_vorp"):
    """Isotonic (monotone decreasing) fit of outcome on pick slot only."""
    oof = np.full(len(h), np.nan)
    years = sorted(h["year"].unique())
    for yr in years:
        tr, te = h["year"] != yr, h["year"] == yr
        iso = IsotonicRegression(increasing=False, out_of_bounds="clip")
        iso.fit(h.loc[tr, "pick"], h.loc[tr, target])
        oof[te.values] = iso.predict(h.loc[te, "pick"])
    y = h[target].values
    per_year_rho = [
        spearmanr(y[h.year == yr], oof[(h.year == yr).values]).statistic for yr in years
    ]
    return oof, {
        "mae": float(mean_absolute_error(y, oof)),
        "rmse": float(np.sqrt(mean_squared_error(y, oof))),
        "spearman_pooled": float(spearmanr(y, oof).statistic),
        "spearman_mean_within_year": float(np.nanmean(per_year_rho)),
    }


def lodco_classifier(h, features, model_factory, ycol, classes):
    oof = np.empty(len(h), dtype=object)
    oof_proba = np.full((len(h), len(classes)), np.nan)
    for yr in sorted(h["year"].unique()):
        tr, te = h["year"] != yr, h["year"] == yr
        m = model_factory()
        m.fit(h.loc[tr, features], h.loc[tr, ycol])
        proba = m.predict_proba(h.loc[te, features])
        cls = list(m.classes_) if hasattr(m, "classes_") else list(m[-1].classes_)
        for j, c in enumerate(cls):
            oof_proba[te.values, classes.index(c)] = proba[:, j]
        oof[te.values] = [classes[i] for i in np.nanargmax(
            oof_proba[te.values], axis=1)]
    y = h[ycol].values
    return oof, oof_proba, {
        "accuracy": float(accuracy_score(y, oof)),
        "macro_f1": float(f1_score(y, oof, average="macro")),
        "confusion_matrix": confusion_matrix(y, oof, labels=classes).tolist(),
        "labels": classes,
    }


def lodco_binary(h, features, model_factory, ycol):
    oof = np.full(len(h), np.nan)
    for yr in sorted(h["year"].unique()):
        tr, te = h["year"] != yr, h["year"] == yr
        m = model_factory()
        m.fit(h.loc[tr, features], h.loc[tr, ycol])
        oof[te.values] = m.predict_proba(h.loc[te, features])[:, 1]
    y = h[ycol].values
    return oof, {
        "auc": float(roc_auc_score(y, oof)),
        "brier": float(brier_score_loss(y, oof)),
        "log_loss": float(log_loss(y, oof)),
        "accuracy_at_0.5": float(accuracy_score(y, oof >= 0.5)),
    }


def main():
    h = load_historical(os.path.join(BASE, "data/processed/historical_enriched.csv"))
    h["tier"] = h.apply(assign_tier, axis=1)
    h["bust"] = assign_bust(h)
    print(f"Loaded {len(h)} players, {h.year.nunique()} draft classes")
    print("Tier counts:", h.tier.value_counts().to_dict())
    print("Bust rate:", round(h.bust.mean(), 3))

    results = {}

    # ---------- 1. pick-slot baseline ----------
    oof_base, results["baseline_pick_isotonic"] = lodco_pick_baseline(h)
    print("baseline:", results["baseline_pick_isotonic"])

    # ---------- 2. transform selection (ridge + hgb on skill features) ----------
    transform_scan = {}
    for tname in TRANSFORMS:
        _, m_r = lodco_regression(h, SKILL_FEATURES, make_ridge, tname)
        _, m_g = lodco_regression(h, SKILL_FEATURES, make_hgb, tname)
        transform_scan[tname] = {"ridge": m_r, "hgb": m_g}
        print(f"transform={tname} ridge={m_r} hgb={m_g}")
    results["transform_scan"] = transform_scan
    # choose transform by mean of ridge+hgb pooled spearman, ties -> lower MAE
    best_t = max(
        TRANSFORMS,
        key=lambda t: (
            transform_scan[t]["ridge"]["spearman_pooled"]
            + transform_scan[t]["hgb"]["spearman_pooled"]
        ),
    )
    results["chosen_transform"] = best_t
    print("chosen transform:", best_t)

    # ---------- 3. main regression models ----------
    oof = {}
    oof["ridge_skill"], results["ridge_skill"] = lodco_regression(
        h, SKILL_FEATURES, make_ridge, best_t
    )
    oof["lasso_skill"], results["lasso_skill"] = lodco_regression(
        h, SKILL_FEATURES, make_lasso, best_t
    )
    oof["hgb_skill"], results["hgb_skill"] = lodco_regression(
        h, SKILL_FEATURES, make_hgb, best_t
    )
    oof["ridge_withpick"], results["ridge_withpick"] = lodco_regression(
        h, PICK_FEATURES, make_ridge, best_t
    )
    oof["hgb_withpick"], results["hgb_withpick"] = lodco_regression(
        h, PICK_FEATURES, make_hgb, best_t
    )
    for k in ["ridge_skill", "lasso_skill", "hgb_skill", "ridge_withpick", "hgb_withpick"]:
        print(k, results[k])

    # best skill model by pooled spearman
    skill_models = ["ridge_skill", "lasso_skill", "hgb_skill"]
    best_reg = max(skill_models, key=lambda k: results[k]["spearman_pooled"])
    results["best_skill_regression"] = best_reg
    print("best skill regression:", best_reg)

    # ---------- 4. standardized coefficients (full-data fit, interpretability) ----------
    rid = make_ridge().fit(h[SKILL_FEATURES], TRANSFORMS[best_t][0](h.career_vorp.values))
    las = make_lasso().fit(h[SKILL_FEATURES], TRANSFORMS[best_t][0](h.career_vorp.values))
    results["ridge_coefs_std"] = dict(
        zip(SKILL_FEATURES, np.round(rid[-1].coef_, 4).tolist())
    )
    results["lasso_coefs_std"] = dict(
        zip(SKILL_FEATURES, np.round(las[-1].coef_, 4).tolist())
    )
    results["ridge_alpha"] = float(rid[-1].alpha_)
    results["lasso_alpha"] = float(las[-1].alpha_)

    # ---------- 5. tier classifier ----------
    tier_res = {}
    # pick-only baseline classifier
    _, _, tier_res["baseline_pick_logit"] = lodco_classifier(
        h, ["pick"], make_logit_multi, "tier", TIER_ORDER
    )
    _, _, tier_res["logit_skill"] = lodco_classifier(
        h, SKILL_FEATURES, make_logit_multi, "tier", TIER_ORDER
    )
    oof_tier, oof_tier_proba, tier_res["hgb_skill"] = lodco_classifier(
        h, SKILL_FEATURES, make_hgb_clf, "tier", TIER_ORDER
    )
    for k, v in tier_res.items():
        print("tier", k, {x: v[x] for x in ["accuracy", "macro_f1"]})
    results_tiers = tier_res

    # ---------- 6. bust probability model ----------
    bust_res = {}
    oof_bust_base, bust_res["baseline_pick_logit"] = lodco_binary(
        h, ["pick"], make_bust_logit, "bust"
    )
    oof_bust, bust_res["logit_skill"] = lodco_binary(
        h, SKILL_FEATURES, make_bust_logit, "bust"
    )
    oof_bust_hgb, bust_res["hgb_skill"] = lodco_binary(
        h, SKILL_FEATURES, make_hgb_clf, "bust"
    )
    for k, v in bust_res.items():
        print("bust", k, v)
    best_bust = (
        "logit_skill"
        if bust_res["logit_skill"]["auc"] >= bust_res["hgb_skill"]["auc"]
        else "hgb_skill"
    )
    bust_res["best"] = best_bust
    oof_bust_best = oof_bust if best_bust == "logit_skill" else oof_bust_hgb

    # ---------- 7. calibration curve for bust model (LODCO out-of-fold) ----------
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frac_pos, mean_pred = calibration_curve(
        h.bust.values, oof_bust_best, n_bins=10, strategy="quantile"
    )
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect calibration")
    ax.plot(mean_pred, frac_pos, "o-", color="tab:red", label=f"{best_bust} (LODCO OOF)")
    ax.set_xlabel("Mean predicted bust probability (bin)")
    ax.set_ylabel("Observed bust fraction (bin)")
    ax.set_title(
        f"Bust model calibration, 2000-2021 LODCO out-of-fold\n"
        f"AUC={bust_res[best_bust]['auc']:.3f}, Brier={bust_res[best_bust]['brier']:.3f}"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "calibration_bust.png"), dpi=150)
    plt.close(fig)
    bust_res["calibration_bins"] = {
        "mean_pred": np.round(mean_pred, 4).tolist(),
        "frac_pos": np.round(frac_pos, 4).tolist(),
    }

    # ---------- 8. permutation importance (averaged over LODCO test folds) ----------
    fwd, inv = TRANSFORMS[best_t]
    factories = {"ridge_skill": make_ridge, "lasso_skill": make_lasso, "hgb_skill": make_hgb}
    imp_reg = np.zeros(len(SKILL_FEATURES))
    imp_bust = np.zeros(len(SKILL_FEATURES))
    years = sorted(h.year.unique())
    rng = np.random.RandomState(SEED)
    for yr in years:
        tr, te = h.year != yr, h.year == yr
        m = factories[best_reg]()
        m.fit(h.loc[tr, SKILL_FEATURES], fwd(h.loc[tr, "career_vorp"].values))
        pi = permutation_importance(
            m, h.loc[te, SKILL_FEATURES], fwd(h.loc[te, "career_vorp"].values),
            n_repeats=5, random_state=rng, scoring="neg_mean_absolute_error",
        )
        imp_reg += pi.importances_mean / len(years)
        mb = (make_bust_logit if best_bust == "logit_skill" else make_hgb_clf)()
        mb.fit(h.loc[tr, SKILL_FEATURES], h.loc[tr, "bust"])
        pib = permutation_importance(
            mb, h.loc[te, SKILL_FEATURES], h.loc[te, "bust"],
            n_repeats=5, random_state=rng, scoring="roc_auc",
        )
        imp_bust += pib.importances_mean / len(years)

    order = np.argsort(imp_reg)
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    axes[0].barh(
        [SKILL_FEATURES[i] for i in order], imp_reg[order], color="tab:blue"
    )
    axes[0].set_title(f"VORP model ({best_reg})\npermutation importance (MAE, LODCO folds)")
    orderb = np.argsort(imp_bust)
    axes[1].barh(
        [SKILL_FEATURES[i] for i in orderb], imp_bust[orderb], color="tab:red"
    )
    axes[1].set_title(f"Bust model ({best_bust})\npermutation importance (AUC, LODCO folds)")
    for ax in axes:
        ax.axvline(0, color="k", lw=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "feature_importance.png"), dpi=150)
    plt.close(fig)
    results["permutation_importance_vorp"] = dict(
        zip(SKILL_FEATURES, np.round(imp_reg, 5).tolist())
    )
    bust_res["permutation_importance"] = dict(
        zip(SKILL_FEATURES, np.round(imp_bust, 5).tolist())
    )

    # ---------- 9. first-round-only evaluation (2026 use case) ----------
    # Same LODCO OOF predictions, metrics restricted to picks 1-30.
    fr = (h.pick <= 30).values
    yfr = h.career_vorp.values[fr]

    def fr_metrics(pred):
        rho_y = [
            spearmanr(
                h.career_vorp.values[fr & (h.year == yr).values],
                pred[fr & (h.year == yr).values],
            ).statistic
            for yr in years
        ]
        return {
            "mae": float(mean_absolute_error(yfr, pred[fr])),
            "rmse": float(np.sqrt(mean_squared_error(yfr, pred[fr]))),
            "spearman_pooled": float(spearmanr(yfr, pred[fr]).statistic),
            "spearman_mean_within_year": float(np.nanmean(rho_y)),
        }

    results["first_round_eval"] = {"baseline_pick_isotonic": fr_metrics(oof_base)}
    for k, v in oof.items():
        results["first_round_eval"][k] = fr_metrics(v)
    print("first-round eval:")
    for k, v in results["first_round_eval"].items():
        print(" ", k, {x: round(v[x], 3) for x in v})
    bfr = h.bust.values[fr]
    bust_res["first_round_eval"] = {
        "baseline_pick_logit": {
            "auc": float(roc_auc_score(bfr, oof_bust_base[fr])),
            "brier": float(brier_score_loss(bfr, oof_bust_base[fr])),
        },
        best_bust: {
            "auc": float(roc_auc_score(bfr, oof_bust_best[fr])),
            "brier": float(brier_score_loss(bfr, oof_bust_best[fr])),
        },
    }
    print("first-round bust eval:", bust_res["first_round_eval"])

    # ---------- 10. save ----------
    oof_df = h[["year", "pick", "player", "career_vorp", "tier", "bust"]].copy()
    oof_df["oof_baseline_pick"] = oof_base
    for k, v in oof.items():
        oof_df[f"oof_{k}"] = v
    oof_df["oof_bust_prob"] = oof_bust_best
    for j, c in enumerate(TIER_ORDER):
        oof_df[f"oof_tierprob_{c}"] = oof_tier_proba[:, j]
    oof_df.to_csv(os.path.join(MODELS, "cv_oof_predictions.csv"), index=False)

    with open(os.path.join(MODELS, "metrics_regression.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(MODELS, "metrics_tiers.json"), "w") as f:
        json.dump(results_tiers, f, indent=2)
    with open(os.path.join(MODELS, "metrics_bust.json"), "w") as f:
        json.dump(bust_res, f, indent=2)
    print("saved metrics + figures")


if __name__ == "__main__":
    main()
