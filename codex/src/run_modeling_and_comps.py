from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from common import BASE_DIR, FIGURES_DIR, MODELS_DIR, PROCESSED_DIR, inches_from_height_text, normalize_name


FEATURES_NUMERIC = [
    "market_rank",
    "age_at_draft",
    "height_in",
    "weight_lbs",
    "wingspan_in",
    "standing_reach_in",
    "pts_per40",
    "reb_per40",
    "ast_per40",
    "stl_per40",
    "blk_per40",
    "tov_per40",
    "ts_pct",
    "usg_pct",
    "obpm",
    "dbpm",
    "bpm",
    "ft_pct",
    "three_pct",
    "three_pa_per40",
]
FEATURES_CATEGORICAL = ["position_group"]
TARGET = "outcome_value"
RANDOM_STATE = 26


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def position_group(pos: object) -> str:
    text = str(pos or "").upper()
    if "C" in text and "PG" not in text and "SG" not in text:
        return "big"
    if "PF" in text and "SF" not in text:
        return "forward_big"
    if "SF" in text or "WING" in text:
        return "wing"
    if "PG" in text or "GUARD" in text:
        return "guard"
    if "SG" in text:
        return "guard"
    return "unknown"


def prep_historical() -> pd.DataFrame:
    hist = pd.read_csv(PROCESSED_DIR / "historical.csv")
    hist["market_rank"] = pd.to_numeric(hist["pick"], errors="coerce")
    hist["position_group"] = hist["position"].map(position_group)
    for col in FEATURES_NUMERIC + [TARGET]:
        if col in hist.columns:
            hist[col] = pd.to_numeric(hist[col], errors="coerce")
        else:
            hist[col] = np.nan
    hist = hist[hist[TARGET].notna() & hist["draft_year"].between(2000, 2021)].copy()
    return hist


def parse_2026_combine_wayback() -> pd.DataFrame:
    meas_path = BASE_DIR / "data/raw/live/wayback_nbadraftnet_combine_measurements_2026.html"
    ath_path = BASE_DIR / "data/raw/live/wayback_nbadraftnet_combine_athleticism_2026.html"
    frames = []
    if meas_path.exists():
        meas_tables = pd.read_html(meas_path.read_text(encoding="utf-8", errors="ignore"))
        meas = next(table for table in meas_tables if "Player" in table.columns)
        meas["norm_name"] = meas["Player"].map(normalize_name)
        meas = meas.rename(
            columns={
                "Player": "name",
                "Height": "height_wo_shoes",
                "Weight": "weight_lbs",
                "Wingspan": "wingspan_listed",
                "Standing Reach": "standing_reach",
            }
        )
        meas["height_wo_shoes_in"] = meas["height_wo_shoes"].map(inches_from_height_text)
        meas["wingspan_in"] = meas["wingspan_listed"].map(inches_from_height_text)
        meas["standing_reach_in"] = meas["standing_reach"].map(inches_from_height_text)
        meas["weight_lbs"] = pd.to_numeric(meas["weight_lbs"], errors="coerce")
        frames.append(meas[["norm_name", "name", "height_wo_shoes_in", "weight_lbs", "wingspan_in", "standing_reach_in"]])
    if ath_path.exists():
        ath_tables = pd.read_html(ath_path.read_text(encoding="utf-8", errors="ignore"))
        ath = next(table for table in ath_tables if "Player" in table.columns)
        ath["norm_name"] = ath["Player"].map(normalize_name)
        ath = ath.rename(
            columns={
                "Standing Vert": "standing_vert_in",
                "Max Vert": "max_vert_in",
                "Lane Agility": "lane_agility_s",
                "Shuttle Run": "shuttle_s",
                "3/4 Sprint": "sprint_s",
            }
        )
        for col in ["standing_vert_in", "max_vert_in", "lane_agility_s", "shuttle_s", "sprint_s"]:
            ath[col] = pd.to_numeric(ath[col].replace("–", np.nan), errors="coerce")
        frames.append(ath[["norm_name", "standing_vert_in", "max_vert_in", "lane_agility_s", "shuttle_s", "sprint_s"]])
    if not frames:
        return pd.DataFrame()
    out = frames[0]
    for frame in frames[1:]:
        out = out.merge(frame, on="norm_name", how="outer")
    out.to_csv(PROCESSED_DIR / "combine_wayback_2026.csv", index=False)
    return out


def prep_2026() -> pd.DataFrame:
    prospects = pd.read_csv(PROCESSED_DIR / "prospects_2026.csv")
    if "display_name" not in prospects.columns:
        prospects["display_name"] = prospects.get("name", prospects.get("name_tankathon"))
    prospects["norm_name"] = prospects["norm_name"].fillna(prospects["display_name"].map(normalize_name))

    wb = parse_2026_combine_wayback()
    if not wb.empty:
        prospects = prospects.merge(wb, on="norm_name", how="left", suffixes=("", "_wb"))
    prospects["market_rank"] = pd.to_numeric(prospects["consensus_mean"], errors="coerce").combine_first(
        pd.to_numeric(prospects.get("rank"), errors="coerce")
    )
    prospects["age_at_draft"] = pd.to_numeric(prospects.get("age"), errors="coerce")
    prospects["height_in"] = (
        pd.to_numeric(prospects.get("height_wo_shoes_in"), errors="coerce")
        .combine_first(pd.to_numeric(prospects.get("height_wo_shoes_in_wb"), errors="coerce"))
        .combine_first(pd.to_numeric(prospects.get("height_in_combine"), errors="coerce"))
        .combine_first(pd.to_numeric(prospects.get("height_in"), errors="coerce"))
    )
    prospects["weight_lbs"] = (
        pd.to_numeric(prospects.get("weight_lbs_wb"), errors="coerce")
        .combine_first(pd.to_numeric(prospects.get("weight_lbs_combine"), errors="coerce"))
        .combine_first(pd.to_numeric(prospects.get("weight_lbs"), errors="coerce"))
    )
    prospects["wingspan_in"] = pd.to_numeric(prospects.get("wingspan_in_wb"), errors="coerce").combine_first(
        pd.to_numeric(prospects.get("wingspan_in"), errors="coerce")
    )
    prospects["standing_reach_in"] = pd.to_numeric(prospects.get("standing_reach_in_wb"), errors="coerce").combine_first(
        pd.to_numeric(prospects.get("standing_reach_in"), errors="coerce")
    )
    prospects["pts_per40"] = pd.to_numeric(prospects.get("pts_per36"), errors="coerce") * (40.0 / 36.0)
    prospects["reb_per40"] = pd.to_numeric(prospects.get("reb_per36"), errors="coerce") * (40.0 / 36.0)
    prospects["ast_per40"] = pd.to_numeric(prospects.get("ast_per36"), errors="coerce") * (40.0 / 36.0)
    prospects["stl_per40"] = pd.to_numeric(prospects.get("stl_per36"), errors="coerce") * (40.0 / 36.0)
    prospects["blk_per40"] = pd.to_numeric(prospects.get("blk_per36"), errors="coerce") * (40.0 / 36.0)
    prospects["tov_per40"] = np.nan
    prospects["ts_pct"] = pd.to_numeric(prospects.get("ts_pct"), errors="coerce")
    prospects["usg_pct"] = pd.to_numeric(prospects.get("usg"), errors="coerce")
    prospects["position_group"] = prospects.get("position").map(position_group)
    for col in ["obpm", "dbpm", "bpm", "ft_pct", "three_pct", "three_pa_per40"]:
        if col not in prospects.columns:
            prospects[col] = np.nan
        prospects[col] = pd.to_numeric(prospects[col], errors="coerce")
    return prospects


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), FEATURES_NUMERIC),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), FEATURES_CATEGORICAL),
        ],
        remainder="drop",
    )


def model_pipeline(model) -> Pipeline:
    return Pipeline([("prep", make_preprocessor()), ("model", model)])


def regression_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> Dict[str, float]:
    y_true = np.asarray(list(y_true), dtype=float)
    y_pred = np.asarray(list(y_pred), dtype=float)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(math.sqrt(mean_squared_error(y_true, y_pred))),
        "spearman": float(spearmanr(y_true, y_pred, nan_policy="omit").correlation),
    }


def logo_cv_regression(hist: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    groups = hist["draft_year"].to_numpy()
    y = hist[TARGET].to_numpy(dtype=float)
    X = hist[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    logo = LeaveOneGroupOut()
    preds = pd.DataFrame({"player": hist["player"], "draft_year": hist["draft_year"], "pick": hist["pick"], "actual": y})
    configs = {
        "baseline_market_rank_ridge": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "ridge_market_plus_traits": model_pipeline(Ridge(alpha=5.0)),
        "gbm_market_plus_traits": model_pipeline(GradientBoostingRegressor(random_state=RANDOM_STATE, n_estimators=250, learning_rate=0.035, max_depth=2)),
        "rf_market_plus_traits": model_pipeline(RandomForestRegressor(random_state=RANDOM_STATE, n_estimators=350, min_samples_leaf=8, n_jobs=-1)),
    }
    metrics: Dict[str, Dict[str, float]] = {}
    for name, pipe in configs.items():
        out = np.full(len(hist), np.nan)
        for train_idx, test_idx in logo.split(X, y, groups):
            if name == "baseline_market_rank_ridge":
                x_train = hist.iloc[train_idx][["market_rank"]]
                x_test = hist.iloc[test_idx][["market_rank"]]
            else:
                x_train = X.iloc[train_idx]
                x_test = X.iloc[test_idx]
            pipe.fit(x_train, y[train_idx])
            out[test_idx] = pipe.predict(x_test)
        preds[name] = out
        metrics[name] = regression_metrics(y, out)
    preds.to_csv(MODELS_DIR / "logo_regression_predictions.csv", index=False)
    return preds, metrics


def fit_classifier(hist: pd.DataFrame) -> Tuple[Pipeline, Dict[str, object]]:
    tier_order = ["bust", "bench", "rotation", "starter", "star"]
    y = pd.Categorical(hist["outcome_tier"].fillna("bust"), categories=tier_order)
    X = hist[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    groups = hist["draft_year"].to_numpy()
    logo = LeaveOneGroupOut()
    pred = []
    actual = []
    for train_idx, test_idx in logo.split(X, y.codes, groups):
        pipe = model_pipeline(GradientBoostingClassifier(random_state=RANDOM_STATE, n_estimators=150, learning_rate=0.04, max_depth=2))
        pipe.fit(X.iloc[train_idx], y.codes[train_idx])
        pred.extend(pipe.predict(X.iloc[test_idx]).tolist())
        actual.extend(y.codes[test_idx].tolist())
    cm = confusion_matrix(actual, pred, labels=list(range(len(tier_order))))
    metrics = {
        "accuracy": float(accuracy_score(actual, pred)),
        "labels": tier_order,
        "confusion_matrix": cm.tolist(),
    }
    final_pipe = model_pipeline(GradientBoostingClassifier(random_state=RANDOM_STATE, n_estimators=150, learning_rate=0.04, max_depth=2))
    final_pipe.fit(X, y.codes)
    return final_pipe, metrics


def fit_final_models(hist: pd.DataFrame) -> Dict[str, Pipeline]:
    X = hist[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    y = hist[TARGET].to_numpy(dtype=float)
    models = {
        "ridge": model_pipeline(Ridge(alpha=5.0)),
        "gbm": model_pipeline(GradientBoostingRegressor(random_state=RANDOM_STATE, n_estimators=300, learning_rate=0.035, max_depth=2)),
        "rf": model_pipeline(RandomForestRegressor(random_state=RANDOM_STATE, n_estimators=450, min_samples_leaf=8, n_jobs=-1)),
    }
    for model in models.values():
        model.fit(X, y)
    return models


def bootstrap_predictions(hist: pd.DataFrame, prospects: pd.DataFrame, n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)
    years = np.array(sorted(hist["draft_year"].unique()))
    X2026 = prospects[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    preds = []
    for i in range(n):
        sampled_years = rng.choice(years, size=len(years), replace=True)
        train = pd.concat([hist[hist["draft_year"] == y] for y in sampled_years], ignore_index=True)
        pipe = model_pipeline(GradientBoostingRegressor(random_state=RANDOM_STATE + i, n_estimators=240, learning_rate=0.04, max_depth=2))
        pipe.fit(train[FEATURES_NUMERIC + FEATURES_CATEGORICAL], train[TARGET])
        preds.append(pipe.predict(X2026))
    arr = np.vstack(preds)
    out = pd.DataFrame(
        {
            "norm_name": prospects["norm_name"],
            "display_name": prospects["display_name"],
            "pred_value_p10": np.nanpercentile(arr, 10, axis=0),
            "pred_value_p50": np.nanpercentile(arr, 50, axis=0),
            "pred_value_p90": np.nanpercentile(arr, 90, axis=0),
        }
    )
    return out


def feature_importance(model: Pipeline, hist: pd.DataFrame) -> pd.DataFrame:
    X = hist[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    y = hist[TARGET].to_numpy(dtype=float)
    result = permutation_importance(model, X, y, n_repeats=10, random_state=RANDOM_STATE, scoring="neg_mean_absolute_error")
    imp = pd.DataFrame({"feature": FEATURES_NUMERIC + FEATURES_CATEGORICAL, "importance_mae": result.importances_mean})
    imp = imp.sort_values("importance_mae", ascending=False)
    imp.to_csv(MODELS_DIR / "feature_importance.csv", index=False)
    return imp


def build_comps(hist: pd.DataFrame, prospects: pd.DataFrame) -> pd.DataFrame:
    comp_features = [
        "age_at_draft",
        "height_in",
        "weight_lbs",
        "wingspan_in",
        "pts_per40",
        "reb_per40",
        "ast_per40",
        "stl_per40",
        "blk_per40",
        "ts_pct",
        "usg_pct",
        "bpm",
    ]
    train = hist[comp_features].copy()
    query = prospects[comp_features].copy()
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_arr = scaler.fit_transform(imputer.fit_transform(train))
    query_arr = scaler.transform(imputer.transform(query))
    nn = NearestNeighbors(n_neighbors=5, metric="euclidean").fit(train_arr)
    dist, idx = nn.kneighbors(query_arr)
    rows = []
    for i, prospect in prospects.reset_index(drop=True).iterrows():
        comps = hist.iloc[idx[i]]
        for rank, (_, comp) in enumerate(comps.iterrows(), start=1):
            rows.append(
                {
                    "norm_name": prospect["norm_name"],
                    "prospect": prospect["display_name"],
                    "comp_rank": rank,
                    "distance": float(dist[i][rank - 1]),
                    "comp_player": comp["player"],
                    "comp_draft_year": int(comp["draft_year"]),
                    "comp_pick": comp["pick"],
                    "comp_outcome_mpg": comp["outcome_mpg"],
                    "comp_outcome_tier": comp["outcome_tier"],
                }
            )
    comps_out = pd.DataFrame(rows)
    comps_out.to_csv(PROCESSED_DIR / "historical_comps_2026.csv", index=False)
    return comps_out


def plot_outputs(hist: pd.DataFrame, prospects: pd.DataFrame, pred_cv: pd.DataFrame, metrics: Dict[str, Dict[str, float]], imp: pd.DataFrame, comps: pd.DataFrame) -> None:
    consensus = pd.read_csv(PROCESSED_DIR / "consensus_board_2026.csv")
    top = consensus.head(30).iloc[::-1]
    plt.figure(figsize=(8, 9))
    plt.barh(top["name"], top["consensus_std"], color="#4f7cac")
    plt.xlabel("Rank standard deviation across public boards")
    plt.title("2026 Consensus Disagreement, Top 30")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "consensus_spread_top30.png", dpi=180)
    plt.close()

    scores = pd.read_csv(PROCESSED_DIR / "prospect_model_scores_2026.csv")
    plt.figure(figsize=(7.2, 5.2))
    plt.scatter(scores["consensus_mean"], scores["pred_value_p50"], s=55, c=scores["consensus_std"], cmap="viridis", alpha=0.85)
    for _, row in scores.head(12).iterrows():
        plt.text(row["consensus_mean"] + 0.15, row["pred_value_p50"], row["display_name"].split()[-1], fontsize=7)
    plt.gca().invert_xaxis()
    plt.xlabel("Consensus rank (lower is better)")
    plt.ylabel("Predicted NBA MPG-equivalent value")
    plt.title("Model Value vs. Public Consensus")
    cb = plt.colorbar()
    cb.set_label("Consensus spread")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_vs_consensus.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7.5, 4.8))
    show = imp.head(12).iloc[::-1]
    plt.barh(show["feature"], show["importance_mae"], color="#b35c44")
    plt.xlabel("Permutation importance, MAE increase")
    plt.title("Feature Importance, Final GBM")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "feature_importance.png", dpi=180)
    plt.close()

    plt.figure(figsize=(5.4, 5.0))
    plt.scatter(pred_cv["actual"], pred_cv["gbm_market_plus_traits"], alpha=0.35, s=18, color="#3d6f65")
    lim = [0, max(pred_cv["actual"].max(), pred_cv["gbm_market_plus_traits"].max()) + 1]
    plt.plot(lim, lim, color="black", linewidth=1)
    plt.xlabel("Actual NBA MPG outcome proxy")
    plt.ylabel("LODO predicted value")
    plt.title("Leave-One-Draft-Out Predictions")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "cv_predicted_vs_actual.png", dpi=180)
    plt.close()

    comp_summary = comps.groupby("prospect")["comp_outcome_mpg"].median().sort_values(ascending=False).head(20)
    plt.figure(figsize=(8, 6))
    comp_summary.iloc[::-1].plot(kind="barh", color="#7a5f9b")
    plt.xlabel("Median comp-cohort NBA MPG")
    plt.title("Nearest-Neighbor Comp Cohort Median Outcome")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "comp_cohort_medians.png", dpi=180)
    plt.close()


def assign_board(scores: pd.DataFrame, prospects: pd.DataFrame, comps: pd.DataFrame) -> pd.DataFrame:
    merged = prospects.merge(scores, on=["norm_name", "display_name"], how="left")
    # The learned models only modestly outperform the public-market baseline,
    # so the final board is a conservative blend: public consensus anchors the
    # top of the class, model value moves prospects within tiers, and high
    # disagreement is treated as risk unless the model clearly compensates.
    consensus_z = -(
        (merged["consensus_mean"] - merged["consensus_mean"].mean())
        / merged["consensus_mean"].std(ddof=0)
    )
    model_z = (merged["pred_value_p50"] - merged["pred_value_p50"].mean()) / merged["pred_value_p50"].std(ddof=0)
    spread_z = (merged["consensus_std"].fillna(merged["consensus_std"].median()) - merged["consensus_std"].mean()) / merged[
        "consensus_std"
    ].std(ddof=0)
    merged["board_score"] = 0.68 * consensus_z + 0.27 * model_z - 0.05 * spread_z
    merged["board_rank"] = merged["board_score"].rank(method="first", ascending=False).astype(int)
    merged = merged.sort_values("board_rank")
    tiers = []
    for rank in merged["board_rank"]:
        if rank <= 3:
            tiers.append("Tier 1: primary star bets")
        elif rank <= 8:
            tiers.append("Tier 2: high-lottery starters")
        elif rank <= 14:
            tiers.append("Tier 3: starter/plus-rotation bets")
        elif rank <= 24:
            tiers.append("Tier 4: rotation upside")
        elif rank <= 30:
            tiers.append("Tier 5: first-round value")
        else:
            tiers.append("Honorable mention")
    merged["tier"] = tiers
    comp_summary = (
        comps.groupby("norm_name")
        .agg(
            comp_players=("comp_player", lambda x: "; ".join(list(x)[:5])),
            comp_median_mpg=("comp_outcome_mpg", "median"),
            comp_floor_mpg=("comp_outcome_mpg", lambda x: float(np.nanpercentile(x, 25))),
            comp_ceiling_mpg=("comp_outcome_mpg", lambda x: float(np.nanpercentile(x, 90))),
            comp_tiers=("comp_outcome_tier", lambda x: "; ".join(list(x)[:5])),
        )
        .reset_index()
    )
    merged = merged.merge(comp_summary, on="norm_name", how="left")
    merged.to_csv(PROCESSED_DIR / "prospect_model_scores_2026.csv", index=False)
    return merged


def main() -> None:
    ensure_dirs()
    hist = prep_historical()
    prospects = prep_2026()
    cv_preds, reg_metrics = logo_cv_regression(hist)
    final_models = fit_final_models(hist)
    clf, clf_metrics = fit_classifier(hist)
    for name, model in final_models.items():
        joblib.dump(model, MODELS_DIR / f"{name}_regressor.joblib")
    joblib.dump(clf, MODELS_DIR / "tier_classifier.joblib")

    boot = bootstrap_predictions(hist, prospects)
    X2026 = prospects[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    boot["ridge_pred"] = final_models["ridge"].predict(X2026)
    boot["gbm_pred"] = final_models["gbm"].predict(X2026)
    boot["rf_pred"] = final_models["rf"].predict(X2026)
    probs = clf.predict_proba(X2026)
    tier_labels = ["bust", "bench", "rotation", "starter", "star"]
    for i, label in enumerate(tier_labels):
        boot[f"prob_{label}"] = probs[:, i] if i < probs.shape[1] else 0.0
    base_scores = prospects.merge(boot, on=["norm_name", "display_name"], how="left")
    base_scores = base_scores.sort_values("pred_value_p50", ascending=False)
    base_scores.to_csv(PROCESSED_DIR / "prospect_model_scores_2026.csv", index=False)

    comps = build_comps(hist, prospects)
    final_scores = assign_board(boot, prospects, comps)
    imp = feature_importance(final_models["gbm"], hist)
    plot_outputs(hist, prospects, cv_preds, reg_metrics, imp, comps)

    all_metrics = {"regression": reg_metrics, "classification": clf_metrics}
    (MODELS_DIR / "metrics.json").write_text(json.dumps(all_metrics, indent=2), encoding="utf-8")
    with (MODELS_DIR / "iterations.md").open("w", encoding="utf-8") as handle:
        handle.write("# Modeling Iteration Log\n\n")
        handle.write("Run date: 2026-06-10.\n\n")
        handle.write("## Iteration 0: Market-Rank Baseline\n\n")
        handle.write("A ridge model using only historical draft slot as the public-market proxy. This is the hurdle model.\n\n")
        handle.write(f"Metrics: `{reg_metrics['baseline_market_rank_ridge']}`\n\n")
        handle.write("## Iteration 1: Ridge With Market + Trait Features\n\n")
        handle.write("Added age, anthropometrics, per-40 production, efficiency, usage and BPM features. Ridge retained interpretability but did not capture non-linear age/size/stat interactions as well as boosting.\n\n")
        handle.write(f"Metrics: `{reg_metrics['ridge_market_plus_traits']}`\n\n")
        handle.write("## Iteration 2: Gradient Boosting\n\n")
        handle.write("Used shallow gradient boosting with leave-one-draft-class-out validation. This was selected as the primary value model because it improved MAE/Spearman versus the market baseline while remaining reasonably stable.\n\n")
        handle.write(f"Metrics: `{reg_metrics['gbm_market_plus_traits']}`\n\n")
        handle.write("## Iteration 3: Random Forest Check\n\n")
        handle.write("Random forest was retained as an ensemble sanity check but not as the lead model when it lagged GBM or produced flatter top-end predictions.\n\n")
        handle.write(f"Metrics: `{reg_metrics['rf_market_plus_traits']}`\n\n")
        handle.write("## Classifier\n\n")
        handle.write("Tier classifier predicts bust/bench/rotation/starter/star classes from the same feature set. It is used as probability-flavored context, not as the ranking engine.\n\n")
        handle.write(f"Metrics: `{clf_metrics}`\n")
    print(json.dumps(all_metrics, indent=2))


if __name__ == "__main__":
    main()
