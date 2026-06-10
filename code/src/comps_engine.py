#!/usr/bin/env python3
"""
Phase 5 - Historical comps engine for the 2026 NBA Draft consensus top 40.

Method
------
Nearest-neighbor search in a z-scored, weighted feature space over the
historical pool of drafted NCAA players (2000-2021) with adequate stat
coverage. For each 2026 prospect we report the 5 nearest neighbors and an
empirical floor/median/ceiling from the wider 15-neighbor cohort.

Feature space (15 dims), z-scored within the historical candidate pool:
    age_at_draft, height_in, weight_lbs, wingspan_in,
    ncaa_ts_pct, ncaa_usg_pct, ncaa_ast_pct, ncaa_tov_pct,
    ncaa_stl_pct, ncaa_blk_pct, ncaa_3pa_pg, ncaa_ft_pct,
    ncaa_ppg, ncaa_rpg, ncaa_apg

Weight vector and rationale
---------------------------
    age_at_draft  1.50  age is the strongest historical signal for upside;
                        a 19yo and a 23yo with identical stats are different
                        prospects
    height_in     1.25  primary archetype/role anchor
    weight_lbs    0.75  secondary anthro, correlated with height
    wingspan_in   1.00  rim/defense projection, but missing for much of pool
    ncaa_ts_pct   1.25  efficiency translates better than raw volume
    ncaa_usg_pct  1.25  efficiency only means something at a usage level;
                        usage*efficiency is the core of the offensive profile
    ncaa_ast_pct  1.00  creation/playmaking archetype
    ncaa_tov_pct  0.75  noisy but separates careful vs loose handlers
    ncaa_stl_pct  0.75  defensive event signal (noisier than blocks)
    ncaa_blk_pct  1.00  strong rim-protection / archetype signal
    ncaa_3pa_pg   1.00  shooting VOLUME defines modern role more than 3P%
    ncaa_ft_pct   0.75  touch indicator, more stable than 3P%
    ncaa_ppg      0.50  raw scoring is context/role dependent, deprioritized
    ncaa_rpg      0.75  positional rebounding signal
    ncaa_apg      0.75  redundant with ast_pct, kept at low weight

Missingness handling
--------------------
- Candidate pool: NCAA players (college_or_intl not null), ncaa_games >= 10,
  and non-missing CORE features (age, height, weight, ts, ppg, rpg, apg,
  3pa_pg, ft_pct, tov_pct). Wingspan (~22% missing in pool), usg/ast/blk
  (~13%) and stl (~24%) are allowed to be missing.
- Distance for a prospect/candidate pair uses only the dims present for BOTH
  sides, then is rescaled by sqrt(W_total / W_used) (the standard
  expected-squared-distance correction), so candidates are not rewarded for
  having missing data. Pairs sharing < 60% of total feature weight are
  excluded.
- Drafted players with no NBA stats on BBR never appeared in an NBA game:
  career_games -> 0, career_vorp/ws -> 0.0 (definitionally, no NBA minutes
  means 0 VORP/WS; this is not imputation).

Prospect-side feature notes
---------------------------
- height: roster height (e.g. "6-9" -> 81) to match the historical
  BBR-listed convention; weight from prospect_stats_2026.csv.
- wingspan: from combine_2026.csv (name-normalized join; Jr./case variants).
- stl_pct/blk_pct are NOT in prospect_stats_2026.csv; they are ESTIMATED
  from spg/bpg + mpg with an assumed NCAA pace of 68 possessions/40 min and
  ~37 opponent 2PA/40:
      stl_pct ~= 100 * spg / (mpg/40 * 68)
      blk_pct ~= 100 * bpg / (mpg/40 * 37)
  This is an approximation (true rates use team possessions/opp 2PA); it is
  documented in sources_comps.md and only carries 0.75/1.00 of 15.25 total
  weight.

International prospects (Karim Lopez, Sergio De Larrea, Luigi Suigo)
--------------------------------------------------------------------
Their stats come from non-NCAA pro leagues and are not comparable on
usage/rate dims. They are comped on a restricted set only:
age, height, weight, wingspan, ts_pct, 3pa_pg, ft_pct, ppg, rpg, apg
(same weights), and flagged confidence = LOW.

Floor/ceiling (15-neighbor cohort)
----------------------------------
floor = 25th pct career_vorp, median = 50th, ceiling = 90th (numpy linear
interpolation). bust rate = share with career_games < 100; All-Star rate =
share with allstar == 1. Caveat: 2019-2021 draftees have truncated careers
(<= 7 seasons by 2026), which biases cohort VORP slightly downward.

Stylistic mismatch check (mismatch_note, comps are kept, not deleted)
---------------------------------------------------------------------
A comp is annotated if any of:
  |height delta| > 3.5 in; 3pa_pg differs by > 3.5 (shooter vs non-shooter);
  ast_pct differs by > 15 (hub vs play-finisher); blk_pct differs by > 5.

Deterministic: no randomness anywhere; ties broken by (distance, year, pick).

Weight iterations: v1 weights above produced sane comps for all four
spot-check players (Boozer, Dybantsa, Peterson, Mara) on first pass; no
iteration was required. See sources_comps.md.

Outputs:
  data/processed/comps_2026.csv
  data/processed/comps_2026_detail.json
  figures/comp_cohorts_top10.png
  data/raw/sources_comps.md
"""

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
RAW = BASE / "data" / "raw"
FIG = BASE / "figures"

FEATURES = [
    "age_at_draft", "height_in", "weight_lbs", "wingspan_in",
    "ncaa_ts_pct", "ncaa_usg_pct", "ncaa_ast_pct", "ncaa_tov_pct",
    "ncaa_stl_pct", "ncaa_blk_pct", "ncaa_3pa_pg", "ncaa_ft_pct",
    "ncaa_ppg", "ncaa_rpg", "ncaa_apg",
]
WEIGHTS = {
    "age_at_draft": 1.50, "height_in": 1.25, "weight_lbs": 0.75,
    "wingspan_in": 1.00, "ncaa_ts_pct": 1.25, "ncaa_usg_pct": 1.25,
    "ncaa_ast_pct": 1.00, "ncaa_tov_pct": 0.75, "ncaa_stl_pct": 0.75,
    "ncaa_blk_pct": 1.00, "ncaa_3pa_pg": 1.00, "ncaa_ft_pct": 0.75,
    "ncaa_ppg": 0.50, "ncaa_rpg": 0.75, "ncaa_apg": 0.75,
}
# restricted set for internationals: anthro + age + basic box only
INTL_FEATURES = [
    "age_at_draft", "height_in", "weight_lbs", "wingspan_in",
    "ncaa_ts_pct", "ncaa_3pa_pg", "ncaa_ft_pct",
    "ncaa_ppg", "ncaa_rpg", "ncaa_apg",
]
CORE_REQUIRED = [
    "age_at_draft", "height_in", "weight_lbs", "ncaa_ts_pct", "ncaa_ppg",
    "ncaa_rpg", "ncaa_apg", "ncaa_3pa_pg", "ncaa_ft_pct", "ncaa_tov_pct",
]
INTL_PROSPECTS = {"karim lopez", "sergio de larrea", "luigi suigo"}
MIN_WEIGHT_FRACTION = 0.60
NCAA_PACE_PER40 = 68.0   # assumed possessions per 40 min, 2025-26 D1 average
OPP_2PA_PER40 = 37.0     # assumed opponent 2PA per 40 min


def norm_name(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[.’']", "", s)
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)$", "", s)
    return re.sub(r"\s+", " ", s)


def parse_height(h: str) -> float:
    ft, inches = str(h).split("-")
    return int(ft) * 12 + int(inches)


def load_pool() -> pd.DataFrame:
    h = pd.read_csv(PROC / "historical_enriched.csv")
    # never-played draftees: 0 NBA games -> 0 VORP/WS by definition
    never = h["career_games"].isna()
    h.loc[never, ["career_games", "career_minutes", "career_ws",
                  "career_vorp"]] = 0.0
    pool = h[h["college_or_intl"].notna() & (h["ncaa_games"] >= 10)].copy()
    pool = pool.dropna(subset=CORE_REQUIRED)
    pool = pool.reset_index(drop=True)
    return pool


def build_prospects() -> pd.DataFrame:
    p = pd.read_csv(PROC / "prospect_stats_2026.csv")
    c = pd.read_csv(PROC / "combine_2026.csv")
    board = pd.read_csv(PROC / "consensus_board.csv")
    p["key"] = p["player"].map(norm_name)
    c["key"] = c["player"].map(norm_name)
    board["key"] = board["player"].map(norm_name)
    p = p.merge(c[["key", "wingspan_in", "height_no_shoes_in"]],
                on="key", how="left")
    p = p.merge(board[["key", "mean_rank"]], on="key", how="left")
    p = p.sort_values("mean_rank", kind="stable").reset_index(drop=True)

    # internationals carry "UNVERIFIED" in usage/ast/tov -> NaN (blanked below)
    for col in ["usage_pct", "ast_pct", "tov_pct", "obpm", "dbpm", "bpm"]:
        p[col] = pd.to_numeric(p[col], errors="coerce")

    p["height_in"] = p["height"].map(parse_height).astype(float)
    p["weight_lbs"] = p["weight"].astype(float)
    p["ncaa_ts_pct"] = p["ts_pct"]
    p["ncaa_usg_pct"] = p["usage_pct"]
    p["ncaa_ast_pct"] = p["ast_pct"]
    p["ncaa_tov_pct"] = p["tov_pct"]
    p["ncaa_3pa_pg"] = p["three_pa_pg"]
    p["ncaa_ft_pct"] = p["ft_pct"]
    p["ncaa_ppg"] = p["ppg"]
    p["ncaa_rpg"] = p["rpg"]
    p["ncaa_apg"] = p["apg"]
    # estimated rates from per-game counts (documented approximation)
    opp_poss = p["mpg"] / 40.0 * NCAA_PACE_PER40
    opp_2pa = p["mpg"] / 40.0 * OPP_2PA_PER40
    p["ncaa_stl_pct"] = 100.0 * p["spg"] / opp_poss
    p["ncaa_blk_pct"] = 100.0 * p["bpg"] / opp_2pa
    p["is_intl"] = p["key"].isin(INTL_PROSPECTS)
    # internationals: usage/rate dims not comparable across leagues -> blank
    rate_only = ["ncaa_usg_pct", "ncaa_ast_pct", "ncaa_tov_pct",
                 "ncaa_stl_pct", "ncaa_blk_pct"]
    p.loc[p["is_intl"], rate_only] = np.nan
    return p


def zscore_params(pool: pd.DataFrame):
    mu = pool[FEATURES].mean()
    sd = pool[FEATURES].std(ddof=0)
    return mu, sd


def distances(prospect_row, pool_z, weights_vec, feat_idx):
    """Weighted Euclidean distance with pairwise renormalization."""
    pz = prospect_row[feat_idx].astype(float)
    w_total = weights_vec.sum()
    diffs = pool_z - pz  # NaN where either side missing
    valid = ~np.isnan(diffs)
    w_used = (valid * weights_vec).sum(axis=1)
    sq = np.where(valid, diffs ** 2, 0.0) * weights_vec
    raw = sq.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.sqrt(raw * (w_total / w_used))
    frac = w_used / w_total
    d = np.where(frac >= MIN_WEIGHT_FRACTION, d, np.inf)
    return d, frac


def mismatch_check(prospect, comp) -> list[str]:
    notes = []
    if abs(prospect["height_in"] - comp["height_in"]) > 3.5:
        notes.append(f"size mismatch ({prospect['height_in']:.0f}in vs "
                     f"{comp['height_in']:.0f}in)")
    a, b = prospect.get("ncaa_3pa_pg"), comp.get("ncaa_3pa_pg")
    if pd.notna(a) and pd.notna(b) and abs(a - b) > 3.5:
        notes.append(f"shooting-volume mismatch (3PA/g {a:.1f} vs {b:.1f})")
    a, b = prospect.get("ncaa_ast_pct"), comp.get("ncaa_ast_pct")
    if pd.notna(a) and pd.notna(b) and abs(a - b) > 15:
        notes.append(f"creation-role mismatch (AST% {a:.1f} vs {b:.1f})")
    a, b = prospect.get("ncaa_blk_pct"), comp.get("ncaa_blk_pct")
    if pd.notna(a) and pd.notna(b) and abs(a - b) > 5:
        notes.append(f"rim-protection mismatch (BLK% {a:.1f} vs {b:.1f})")
    return notes


def main():
    pool = load_pool()
    prospects = build_prospects()
    mu, sd = zscore_params(pool)
    pool_z_full = ((pool[FEATURES] - mu) / sd).to_numpy()
    w_full = np.array([WEIGHTS[f] for f in FEATURES])
    intl_idx = [FEATURES.index(f) for f in INTL_FEATURES]

    print(f"candidate pool: {len(pool)} NCAA players (2000-2021) "
          f"with core stat coverage")

    rows, detail = [], []
    for _, pr in prospects.iterrows():
        pz = ((pr[FEATURES].astype(float) - mu) / sd).to_numpy(dtype=float)
        if pr["is_intl"]:
            d, frac = distances(pz[intl_idx], pool_z_full[:, intl_idx],
                                w_full[intl_idx], np.arange(len(intl_idx)))
            feats_used = INTL_FEATURES
            confidence = "LOW (international: anthro+age+basic stats only; "\
                         "non-NCAA league context)"
        else:
            d, frac = distances(pz, pool_z_full, w_full,
                                np.arange(len(FEATURES)))
            feats_used = FEATURES
            confidence = ("HIGH" if pd.notna(pr["wingspan_in"])
                          else "MEDIUM (no combine wingspan)")

        order = np.lexsort((pool["pick"].to_numpy(),
                            pool["year"].to_numpy(), d))
        order = [i for i in order if np.isfinite(d[i])][:15]

        nbrs = pool.iloc[order].copy()
        nbrs["distance"] = d[order]
        nbrs["weight_frac_used"] = frac[order]

        cohort_vorp = nbrs["career_vorp"].to_numpy(dtype=float)
        floor_v = float(np.percentile(cohort_vorp, 25))
        med_v = float(np.percentile(cohort_vorp, 50))
        ceil_v = float(np.percentile(cohort_vorp, 90))
        bust = float((nbrs["career_games"] < 100).mean())
        asr = float((nbrs["allstar"] == 1).mean())

        mismatches = []
        rec = {"player": pr["player"]}
        for k in range(5):
            cp = nbrs.iloc[k]
            rec[f"comp{k+1}"] = (f"{cp['player']} ({int(cp['year'])}, "
                                 f"{int(cp['pick'])})")
            rec[f"comp{k+1}_vorp"] = round(float(cp["career_vorp"]), 1)
            mm = mismatch_check(pr, cp)
            if mm:
                mismatches.append(f"comp{k+1} {cp['player']}: " +
                                  "; ".join(mm))
        rec.update({
            "cohort15_floor_vorp": round(floor_v, 1),
            "cohort15_median_vorp": round(med_v, 1),
            "cohort15_ceiling_vorp": round(ceil_v, 1),
            "cohort15_bust_rate": round(bust, 3),
            "cohort15_allstar_rate": round(asr, 3),
            "confidence": confidence,
            "mismatch_note": " | ".join(mismatches),
        })
        rows.append(rec)

        nbr_list = []
        for _, cp in nbrs.iterrows():
            deltas = {}
            for f in feats_used:
                pv, cv = pr.get(f), cp.get(f)
                if pd.notna(pv) and pd.notna(cv):
                    deltas[f] = {
                        "prospect": round(float(pv), 3),
                        "comp": round(float(cv), 3),
                        "delta": round(float(pv) - float(cv), 3),
                        "z_delta": round((float(pv) - float(cv)) / sd[f], 3),
                    }
                else:
                    deltas[f] = None
            nbr_list.append({
                "name": cp["player"], "year": int(cp["year"]),
                "pick": int(cp["pick"]),
                "distance": round(float(cp["distance"]), 4),
                "weight_fraction_used": round(float(cp["weight_frac_used"]), 3),
                "career_vorp": round(float(cp["career_vorp"]), 1),
                "career_ws": round(float(cp["career_ws"]), 1),
                "career_games": int(cp["career_games"]),
                "allstar": int(cp["allstar"]),
                "feature_deltas": deltas,
            })
        detail.append({
            "player": pr["player"],
            "consensus_mean_rank": (None if pd.isna(pr["mean_rank"])
                                    else float(pr["mean_rank"])),
            "confidence": confidence,
            "features_used": feats_used,
            "neighbors": nbr_list,
            "cohort15": {
                "floor_vorp_p25": round(floor_v, 1),
                "median_vorp_p50": round(med_v, 1),
                "ceiling_vorp_p90": round(ceil_v, 1),
                "bust_rate_games_lt_100": round(bust, 3),
                "allstar_rate": round(asr, 3),
            },
        })

    out = pd.DataFrame(rows)
    out.to_csv(PROC / "comps_2026.csv", index=False)
    with open(PROC / "comps_2026_detail.json", "w") as f:
        json.dump(detail, f, indent=2)

    # ---- figure: top 10 cohort VORP distributions ----
    FIG.mkdir(exist_ok=True)
    top10 = detail[:10]
    fig, axes = plt.subplots(2, 5, figsize=(18, 8), sharey=True)
    for ax, dd in zip(axes.flat, top10):
        vals = np.array([n["career_vorp"] for n in dd["neighbors"]])
        rng_x = (np.arange(len(vals)) % 7 - 3) * 0.035  # deterministic jitter
        ax.scatter(rng_x, vals, s=38, alpha=0.75, color="#1f77b4",
                   edgecolors="white", linewidths=0.5, zorder=3)
        c = dd["cohort15"]
        for val, lab, col in [
                (c["floor_vorp_p25"], "floor (p25)", "#d62728"),
                (c["median_vorp_p50"], "median (p50)", "#2ca02c"),
                (c["ceiling_vorp_p90"], "ceiling (p90)", "#9467bd")]:
            ax.axhline(val, color=col, lw=1.4, ls="--", zorder=2,
                       label=lab)
        ax.set_title(dd["player"]
                     + (" *" if dd["confidence"].startswith("LOW") else ""),
                     fontsize=10)
        ax.text(0.97, 0.97,
                f"{c['floor_vorp_p25']:.1f} / {c['median_vorp_p50']:.1f} / "
                f"{c['ceiling_vorp_p90']:.1f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                color="#444444")
        ax.set_xlim(-0.25, 0.45)
        ax.set_xticks([])
        ax.grid(axis="y", alpha=0.25)
    axes[0, 0].set_ylabel("career VORP of 15-NN cohort")
    axes[1, 0].set_ylabel("career VORP of 15-NN cohort")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=3, fontsize=9,
               frameon=False)
    fig.suptitle("2026 consensus top 10, historical comp cohorts "
                 "(15 nearest neighbors, drafted NCAA players 2000-2021)\n"
                 "* = LOW confidence (international, restricted feature set); "
                 "corner text = floor / median / ceiling VORP",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(FIG / "comp_cohorts_top10.png", dpi=150)
    plt.close(fig)

    # ---- spot verification ----
    print("\n=== SPOT VERIFICATION ===")
    for name in ["Cameron Boozer", "AJ Dybantsa", "Darryn Peterson",
                 "Aday Mara"]:
        dd = next(d for d in detail if d["player"] == name)
        rec = next(r for r in rows if r["player"] == name)
        print(f"\n{name} ({rec['confidence']}):")
        for n in dd["neighbors"][:5]:
            print(f"  {n['name']:<26} ({n['year']}, pk {n['pick']:>2}) "
                  f"d={n['distance']:.2f}  VORP={n['career_vorp']:>6.1f}  "
                  f"WS={n['career_ws']:>5.1f}  AS={n['allstar']}")
        c = dd["cohort15"]
        print(f"  cohort15 floor/med/ceil VORP: {c['floor_vorp_p25']}/"
              f"{c['median_vorp_p50']}/{c['ceiling_vorp_p90']}  "
              f"bust={c['bust_rate_games_lt_100']:.2f}  "
              f"AS rate={c['allstar_rate']:.2f}")
        if rec["mismatch_note"]:
            print(f"  mismatch: {rec['mismatch_note']}")

    print(f"\nwrote {PROC/'comps_2026.csv'} ({len(out)} rows), "
          f"{PROC/'comps_2026_detail.json'}, {FIG/'comp_cohorts_top10.png'}")


if __name__ == "__main__":
    main()
