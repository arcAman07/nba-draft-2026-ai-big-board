# Phase 5 method note, historical comps engine (2026-06-10)

Script: `src/comps_engine.py` (deterministic, no randomness; ties broken by
distance, then year, then pick). Inputs are entirely on-disk project files,
no web access used.

## Inputs
- `data/processed/historical_enriched.csv` (1,309 drafted players 2000-2021)
- `data/processed/prospect_stats_2026.csv` (40 prospects, 2025-26 season)
- `data/processed/combine_2026.csv` (wingspan join, name-normalized for
  Jr./case variants such as "Labaron Philon Jr." vs "Labaron Philon")
- `data/processed/consensus_board.csv` (ordering by mean_rank only)

## Candidate pool filters
NCAA players only (`college_or_intl` not null), `ncaa_games >= 10`, and
non-missing core features (age_at_draft, height_in, weight_lbs, ncaa_ts_pct,
ncaa_ppg, ncaa_rpg, ncaa_apg, ncaa_3pa_pg, ncaa_ft_pct, ncaa_tov_pct).
Resulting pool: 781 players, 2000-2021 (early-2000s classes are thinner
because advanced NCAA stats are sparser there).

Drafted players with no NBA stats on Basketball-Reference never appeared in
an NBA game; their career_games is set to 0 and career_vorp/career_ws to 0.0
(definitional, not imputed). Caveat, 2019-2021 draftees have truncated
careers (<= 7 seasons by 2026), so cohort ceilings that lean on recent
classes are slightly understated.

## Feature space and weights (z-scored within the 781-player pool)
| feature        | weight | rationale |
|----------------|--------|-----------|
| age_at_draft   | 1.50   | strongest historical upside signal |
| height_in      | 1.25   | primary archetype anchor |
| weight_lbs     | 0.75   | secondary anthro, correlated with height |
| wingspan_in    | 1.00   | defense/rim projection; ~22% missing in pool |
| ncaa_ts_pct    | 1.25   | efficiency translates better than volume |
| ncaa_usg_pct   | 1.25   | efficiency is only meaningful at a usage level |
| ncaa_ast_pct   | 1.00   | creation archetype |
| ncaa_tov_pct   | 0.75   | noisy, but separates handlers |
| ncaa_stl_pct   | 0.75   | defensive events, noisier than blocks |
| ncaa_blk_pct   | 1.00   | strong rim-protection archetype signal |
| ncaa_3pa_pg    | 1.00   | shooting volume defines modern role |
| ncaa_ft_pct    | 0.75   | stable touch indicator |
| ncaa_ppg       | 0.50   | raw scoring is context-dependent |
| ncaa_rpg       | 0.75   | positional rebounding |
| ncaa_apg       | 0.75   | partly redundant with ast_pct |

Distance = weighted Euclidean over dims present for BOTH players, rescaled
by sqrt(W_total / W_used) (expected-squared-distance correction) so missing
data is never an advantage. Pairs sharing < 60% of total feature weight are
excluded; in practice the minimum weight fraction among selected neighbors
was 0.65.

## Prospect-side approximations (documented, not silent)
- Heights are roster listings ("6-9" -> 81 in) to match the historical
  BBR-listed convention; weights from prospect_stats_2026.csv.
- Wingspans from combine_2026.csv. Missing for Morez Johnson Jr. and
  Labaron Philon Jr. in raw form resolved via name normalization; truly
  absent wingspans would downgrade confidence to MEDIUM (none in final run;
  all 40 matched).
- prospect stl_pct/blk_pct are not in the stats file; ESTIMATED from
  spg/bpg/mpg with assumed NCAA pace 68 poss/40 and 37 opponent 2PA/40:
  `stl_pct ~= 100*spg/(mpg/40*68)`, `blk_pct ~= 100*bpg/(mpg/40*37)`.
  Approximation error is bounded by these two dims carrying 1.75 of 15.25
  total weight.

## International prospects (LOW CONFIDENCE)
Karim Lopez (NBL), Sergio De Larrea (ACB/EuroLeague), Luigi Suigo (Adriatic)
have non-NCAA stats (usage/ast/tov listed UNVERIFIED in the stats file).
They are comped on a restricted set only: age, height, weight, wingspan,
ts_pct, 3pa_pg, ft_pct, ppg, rpg, apg (same weights), against the same NCAA
pool, and flagged `LOW (international: anthro+age+basic stats only)`.
League context is not adjusted; treat these comps as anthro/age/production
silhouettes, not stylistic matches.

## Floor/ceiling definition
From the 15 nearest neighbors: floor = 25th percentile career_vorp,
median = 50th, ceiling = 90th (numpy linear interpolation).
bust rate = share with career_games < 100; All-Star rate = share with
allstar flag = 1.

## Stylistic mismatch annotations
Comps are kept but annotated in `mismatch_note` when: |height delta| > 3.5
in; |3PA/g delta| > 3.5; |AST% delta| > 15; |BLK% delta| > 5.

## Spot verification and weight iterations
v1 weights were checked against Cameron Boozer, AJ Dybantsa, Darryn
Peterson, Aday Mara before finalizing:
- Boozer -> Kevin Love, Andrew Bogut, Ryan Anderson, Chris Bosh (skilled
  scoring/rebounding bigs): sane.
- Dybantsa -> Alec Burks, RJ Barrett, Mike Miller (young high-usage wings):
  sane.
- Peterson -> Brandon Armstrong, James Anderson, Cam Thomas, Eric Gordon
  (high-usage scoring 2-guards): sane; note his 24-game injury-shortened
  season suppresses the cohort.
- Mara (7'3") -> Hibbert, Mobley, Thabeet, Haywood, Azubuike (all centers,
  zero guards): sane.
No absurd comps appeared, so NO weight iterations were required; v1 weights
shipped unchanged.

## Outputs
- `data/processed/comps_2026.csv` (40 rows)
- `data/processed/comps_2026_detail.json` (15 neighbors per prospect with
  distances, weight fraction used, and per-feature raw + z deltas)
- `figures/comp_cohorts_top10.png`

## Library versions
python 3.11.8 with pandas 2.1.0, numpy 1.26.4, matplotlib 3.10.8 (Agg backend),
scipy 1.13.1 (installed, not used by this script).
