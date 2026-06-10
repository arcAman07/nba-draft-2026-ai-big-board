"""Apply Phase 3 models to the 2026 prospect pool (40 players).

Feature construction mirrors src/model_common.py historical conventions:
- height_in from listed height (matches BBR-listed convention in historical),
  wingspan/reach/weight preferred from combine measurements when present.
- NCAA rate stats mapped 1:1 from prospect_stats_2026.csv. STL%/BLK% are NOT
  published there (only per-game steals/blocks), so they are APPROXIMATED:
      stl_pct ~= 100 * spg * 40 / (mpg * 68.0)   (68 poss/40min, ~2025-26 D1 avg)
      blk_pct ~= 100 * bpg * 40 / (mpg * 35.0)   (~35 opponent 2PA/game)
  Same constants applied to all 40 prospects, so cross-prospect ordering is
  preserved; absolute levels are approximate. Documented choice.
- Internationals (Lopez, De Larrea, Suigo): usage/ast/tov/obpm/bpm are
  UNVERIFIED in the source -> treated as missing (miss_ncaa_adv=1) per the
  explicit missing-data policy; TS%, 3PA rate, FT%, stl/blk approximations
  come from their pro-league stats and are flagged (league strength differs
  from NCAA; the model has no league-quality adjustment -> wide uncertainty).

Uncertainty: 200 bootstrap reps resampling the 22 training draft classes with
replacement; ridge refit per rep; per-player predictive draws = rep prediction
+ residual sampled from LODCO out-of-fold residuals of picks 1-45 (asinh
scale), then inverse-transformed. Percentiles therefore reflect both model
uncertainty and irreducible outcome noise.

Run: python3 src/apply_2026.py  (requires train_models.py outputs)
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_common import (
    SEED,
    SKILL_FEATURES,
    TIER_ORDER,
    TRANSFORMS,
    assign_bust,
    assign_tier,
    load_historical,
    normalize_name,
)
from train_models import make_bust_logit, make_logit_multi, make_ridge

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(BASE, "models")
FIGURES = os.path.join(BASE, "figures")

N_BOOT = 200
D1_POSS_PER40 = 68.0
OPP_2PA_PER_GAME = 35.0


def parse_height(s):
    ft, inch = s.split("-")
    return int(ft) * 12 + int(inch)


def build_2026_features():
    p = pd.read_csv(os.path.join(BASE, "data/processed/prospect_stats_2026.csv"))
    c = pd.read_csv(os.path.join(BASE, "data/processed/combine_2026.csv"))
    b = pd.read_csv(os.path.join(BASE, "data/processed/consensus_board.csv"))
    for df in (p, c, b):
        df["key"] = df["player"].map(normalize_name)

    merge_log = []
    no_combine = set(p.key) - set(c.key)
    for k in no_combine:
        merge_log.append(f"NO COMBINE ROW: {k}")
    extra_board = set(b.key) - set(p.key)
    merge_log.append(
        "consensus-board players without prospect stats rows (not modeled): "
        + ", ".join(sorted(b.loc[b.key.isin(extra_board), "player"]))
    )

    m = p.merge(
        c[["key", "height_no_shoes_in", "wingspan_in", "standing_reach_in", "weight_lbs"]],
        on="key",
        how="left",
    ).merge(b[["key", "median_rank", "mean_rank", "spread"]], on="key", how="left")

    # UNVERIFIED strings -> NaN (3 internationals)
    adv_cols = ["usage_pct", "ast_pct", "tov_pct", "obpm", "bpm"]
    unverified = m[adv_cols].apply(lambda s: s.astype(str).str.contains("UNVERIFIED")).any(axis=1)
    for col in adv_cols:
        m[col] = pd.to_numeric(m[col], errors="coerce")

    X = pd.DataFrame(index=m.index)
    X["age_at_draft"] = m.age_at_draft
    X["height_in"] = m.height.map(parse_height).astype(float)
    X["weight_lbs"] = m.weight_lbs.fillna(m.weight)
    X["wingspan_in"] = m.wingspan_in
    X["standing_reach_in"] = m.standing_reach_in
    X["wing_minus_height"] = X.wingspan_in - X.height_in
    X["ncaa_ts_pct"] = m.ts_pct
    X["ncaa_usg_pct"] = m.usage_pct
    X["ncaa_ast_pct"] = m.ast_pct
    X["ncaa_tov_pct"] = m.tov_pct
    X["ncaa_stl_pct"] = 100.0 * m.spg * 40.0 / (m.mpg * D1_POSS_PER40)
    X["ncaa_blk_pct"] = 100.0 * m.bpg * 40.0 / (m.mpg * OPP_2PA_PER_GAME)
    X["ncaa_ft_pct"] = m.ft_pct
    X["ncaa_3pa_per40"] = m.three_pa_pg * 40.0 / m.mpg
    X["ncaa_obpm"] = m.obpm
    X["ncaa_bpm"] = m.bpm
    X["miss_age"] = X.age_at_draft.isna().astype(int)
    X["miss_anthro"] = X.height_in.isna().astype(int)
    X["miss_wingspan"] = X.wingspan_in.isna().astype(int)
    X["miss_ncaa_core"] = X.ncaa_ts_pct.isna().astype(int)
    X["miss_ncaa_adv"] = X.ncaa_obpm.isna().astype(int)

    intl = ~m.league.str.startswith("NCAA")
    flags = []
    for i in m.index:
        f = []
        if intl[i]:
            f.append("INTL_PRO_LEAGUE_STATS_NOT_NCAA(wide_uncertainty)")
        if unverified[i]:
            f.append("ADV_STATS_UNVERIFIED_TREATED_MISSING")
        if pd.isna(m.wingspan_in[i]):
            f.append("NO_COMBINE_ANTHRO")
            merge_log.append(f"no combine wingspan/reach: {m.player[i]}")
        inj = str(m.injury_notes[i]).lower()
        if not inj.startswith("none") and inj != "nan":
            f.append("INJURY_NOTE_SEE_SOURCE")
        if m.games[i] < 15:
            f.append(f"SMALL_SAMPLE_{int(m.games[i])}GP")
        flags.append(";".join(f))
    m["flags"] = flags
    return m, X[SKILL_FEATURES], merge_log


def main():
    rng = np.random.RandomState(SEED)
    h = load_historical(os.path.join(BASE, "data/processed/historical_enriched.csv"))
    h["tier"] = h.apply(assign_tier, axis=1)
    h["bust"] = assign_bust(h)
    with open(os.path.join(MODELS, "metrics_regression.json")) as f:
        reg_metrics = json.load(f)
    tname = reg_metrics["chosen_transform"]
    fwd, inv = TRANSFORMS[tname]

    m, X26, merge_log = build_2026_features()
    print(f"built features for {len(m)} prospects; merge log:")
    for line in merge_log:
        print("  -", line)

    # ---- point models fit on all 22 classes ----
    ridge = make_ridge().fit(h[SKILL_FEATURES], fwd(h.career_vorp.values))
    tier_clf = make_logit_multi().fit(h[SKILL_FEATURES], h.tier)
    bust_clf = make_bust_logit().fit(h[SKILL_FEATURES], h.bust)

    tier_proba = pd.DataFrame(
        tier_clf.predict_proba(X26), columns=[f"tier_prob_{c}" for c in tier_clf.classes_]
    )[[f"tier_prob_{c}" for c in TIER_ORDER]]
    bust_prob = bust_clf.predict_proba(X26)[:, 1]

    # ---- residual pool: LODCO OOF ridge residuals, picks 1-45, asinh scale ----
    oof = pd.read_csv(os.path.join(MODELS, "cv_oof_predictions.csv"))
    sub = oof[oof["pick"] <= 45]
    resid = fwd(sub.career_vorp.values) - fwd(sub.oof_ridge_skill.values)
    print(f"residual pool: n={len(resid)}, sd={resid.std():.3f} (asinh scale)")

    # ---- bootstrap over draft classes ----
    # draws_model: bootstrap model uncertainty only (central estimate).
    # draws_outcome: + residual noise (full predicted-value distribution for
    # the percentile columns). Means of draws_outcome are NOT reported: the
    # inverse asinh is convex, so noise on the transformed scale inflates the
    # back-transformed mean (documented in iterations.md).
    years = sorted(h.year.unique())
    draws_model = np.zeros((N_BOOT, len(m)))
    draws = np.zeros((N_BOOT, len(m)))
    for r in range(N_BOOT):
        ys = rng.choice(years, size=len(years), replace=True)
        boot = pd.concat([h[h.year == y] for y in ys], ignore_index=True)
        mod = make_ridge().fit(boot[SKILL_FEATURES], fwd(boot.career_vorp.values))
        z = mod.predict(X26)
        draws_model[r] = inv(z)
        draws[r] = inv(z + rng.choice(resid, size=len(m), replace=True))

    # Winsorize outcome draws at the best career in the 22-class training
    # sample (LeBron, VORP 159.4): the multiplicative residual occasionally
    # produces physically implausible draws (>250 VORP) for elite profiles.
    # Documented in iterations.md.
    vmax = float(h.career_vorp.max())
    draws = np.clip(draws, None, vmax)

    out = pd.DataFrame(
        {
            "player": m.player,
            "pred_vorp_mean": draws_model.mean(axis=0),
            "pred_vorp_p10": np.percentile(draws, 10, axis=0),
            "pred_vorp_p25": np.percentile(draws, 25, axis=0),
            "pred_vorp_p50": np.percentile(draws, 50, axis=0),
            "pred_vorp_p75": np.percentile(draws, 75, axis=0),
            "pred_vorp_p90": np.percentile(draws, 90, axis=0),
        }
    )
    out = pd.concat([out, tier_proba.round(4)], axis=1)
    out["bust_prob"] = np.round(bust_prob, 4)
    out["flags"] = m["flags"].values
    out["pred_vorp_point"] = inv(ridge.predict(X26))  # full-data fit, no noise
    out["consensus_median_rank"] = m.median_rank.values
    out["model_rank"] = out.pred_vorp_mean.rank(ascending=False).astype(int)
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(3)
    out = out.sort_values("model_rank")
    out.to_csv(os.path.join(MODELS, "predictions_2026.csv"), index=False)
    print(out[["player", "model_rank", "consensus_median_rank", "pred_vorp_mean",
               "pred_vorp_p10", "pred_vorp_p90", "bust_prob"]].to_string(index=False))

    # ---- figure: model rank vs consensus median rank ----
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 10))
    x, y = out.consensus_median_rank.values, out.model_rank.values
    ax.scatter(x, y, s=30, color="tab:blue", zorder=3)
    lim = max(np.nanmax(x), y.max()) + 2
    ax.plot([0, lim], [0, lim], "k--", lw=1, alpha=0.5, label="agreement line")
    for _, r in out.iterrows():
        short = r.player.split()[-1] if not r.player.endswith(("Jr.", "II", "III")) else r.player.split()[-2]
        ax.annotate(short, (r.consensus_median_rank, r.model_rank), fontsize=7,
                    xytext=(4, 2), textcoords="offset points")
    ax.set_xlabel("Consensus median rank (6 outlets)")
    ax.set_ylabel("Model rank (ridge skill model, pred VORP mean)")
    ax.set_title("2026 draft: model rank vs consensus rank\n"
                 "below line = model higher than consensus; above = model lower")
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "pred_vs_consensus.png"), dpi=150)
    plt.close(fig)
    print("saved models/predictions_2026.csv and figures/pred_vs_consensus.png")


if __name__ == "__main__":
    main()
