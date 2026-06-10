# Phase 3 model iterations log

All runs: `python3 src/train_models.py`, seed 42 everywhere, LODCO CV =
leave-one-draft-class-out, 22 folds grouped by `year` (2000-2021), n=1,309.
Python 3.11.8, sklearn 1.4.2, pandas 2.1.0, numpy 1.26.4.

## Setup decisions (apply to all iterations)

- **Target**: career VORP (career-to-date). 2020 and 2021 classes have only
  5-6 / 4-5 seasons of career accumulated; accepted per project design, but
  their LODCO folds understate upside and the Starter tier is nearly
  unreachable for 2021 (see models/tier_definitions.md).
- **Never-played players** (161, notes verified "never played"): career
  games/minutes/WS/VORP filled with 0. Real outcomes, not missing data.
- **Missing features**: median impute (SimpleImputer fit inside each CV train
  fold) + explicit missingness indicators computed up front (miss_age,
  miss_anthro, miss_wingspan, miss_ncaa_core, miss_ncaa_adv). Nothing silent.
  Internationals (487) have all NCAA columns missing -> miss_ncaa_core=1.
- **Features (skill set, 21 cols)**: age_at_draft; height, weight, wingspan,
  standing reach, wingspan-height differential; NCAA TS%, USG%, AST%, TOV%,
  STL%, BLK%, FT%, 3PA per 40 (3pa_pg*40/mpg, minutes-normalized), OBPM, BPM;
  5 missingness indicators. **Pick slot excluded** from skill models by
  design (talent signal, not market echo); with-pick variants reported for
  comparison only.
- **Consensus-rank baseline is not recoverable historically** (no archived
  2000-2021 multi-outlet boards in our data). Draft pick slot serves as the
  market-consensus proxy baseline; this is standard and documented here.

## Iteration 1 — baseline + transform scan (2026-06-10)

Config: pick-slot isotonic baseline (monotone decreasing, fit per train fold);
ridge (RidgeCV, inner LOO over 30 alphas) and HistGB (300 iters, depth 3,
lr 0.05, leaf 30, l2 1.0) on skill features; target transforms identity /
asinh / signed-sqrt, metrics always on raw VORP scale.

| model | transform | MAE | RMSE | Spearman (pooled) | Spearman (within-yr mean) |
|---|---|---|---|---|---|
| pick isotonic (baseline) | - | 5.26 | 10.21 | 0.208 | 0.245 |
| ridge | identity | 5.64 | 10.34 | 0.255 | 0.248 |
| ridge | asinh | 4.59 | 11.04 | 0.273 | 0.269 |
| ridge | signed_sqrt | 4.57 | 10.86 | 0.273 | 0.266 |
| hgb | identity | 5.65 | 10.53 | 0.210 | 0.205 |
| hgb | asinh | 4.59 | 10.91 | 0.249 | 0.246 |
| hgb | signed_sqrt | 4.61 | 10.67 | 0.247 | 0.244 |

**Chosen transform: asinh** (best combined pooled Spearman; sqrt essentially
tied, asinh handles negative VORP without the sign hack). Documented per spec:
the transform helps clearly (MAE 5.64 -> 4.59 for ridge, Spearman +0.02)
because raw VORP is extremely right-skewed (max 159 vs median 0). Note RMSE is
slightly worse under the transform: transformed models stop chasing the
Jokic/LeBron tail, which is the right trade for ranking prospects.

## Iteration 2 — full model set, asinh target

Regression (all 1,309 picks):

| model | MAE | RMSE | Spearman pooled | Spearman within-yr |
|---|---|---|---|---|
| pick isotonic baseline | 5.26 | 10.21 | 0.208 | 0.245 |
| ridge (skill) | 4.59 | 11.04 | 0.273 | 0.269 |
| lasso (skill) | 4.59 | 11.09 | 0.274 | 0.277 |
| hgb (skill) | 4.59 | 10.91 | 0.249 | 0.246 |
| ridge (+pick) | 4.55 | 10.99 | 0.288 | 0.287 |
| hgb (+pick) | 4.53 | 10.65 | 0.277 | 0.281 |

First-round-only evaluation (same LODCO OOF preds, picks 1-30, n=658 — the
2026 use case):

| model | MAE | Spearman pooled | Spearman within-yr |
|---|---|---|---|
| pick isotonic baseline | 8.14 | 0.145 | 0.211 |
| ridge (skill) | 7.25 | **0.256** | 0.245 |
| lasso (skill) | 7.26 | 0.246 | 0.245 |
| hgb (skill) | 7.25 | 0.213 | 0.197 |
| ridge (+pick) | 7.24 | 0.275 | 0.268 |
| hgb (+pick) | 7.20 | 0.268 | 0.260 |

**Verdict, stated plainly:**
- Skill-only linear models BEAT the pick baseline on every regression metric
  except RMSE (tail effect above): pooled Spearman 0.27 vs 0.21 overall,
  0.25 vs 0.15 within the first round. The talent signal is real but modest.
- Adding pick on top of skills helps a little more (0.288), i.e. the market
  knows things our box-score features do not (intel, film, character). The
  gap skill-only vs with-pick is small (~0.015), so most of the market's
  ranking information is recoverable from age + NCAA stats + anthro.
- HGB UNDERPERFORMS ridge/lasso here (0.249 vs 0.273) - with ~20 mostly-linear
  features and n=1.3k, trees add variance, not signal. Honest result; linear
  models are the headline models.
- Lasso vs ridge is a statistical tie (lasso +0.001 pooled, ridge +0.010 on
  the first-round subset). **Ridge chosen for the 2026 application** because
  the first-round subset is our use case and its coefficients are stable;
  lasso confirms feature selection (it zeroes 6 of 21 features and keeps the
  same leaders).

Tier classifier (5 tiers, LODCO):

| model | accuracy | macro-F1 |
|---|---|---|
| pick-only logistic baseline | 0.494 | 0.222 |
| multinomial logistic (skill) | 0.466 | 0.266 |
| hgb classifier (skill) | 0.441 | 0.294 |

Honest read: the pick baseline wins raw accuracy by predicting the dominant
classes (Bust/Rotation); the skill models win macro-F1 by actually
discriminating the rare tiers (AllStar/Starter). Neither is great - 5-way
career-tier prediction from pre-draft stats is hard. Multinomial logistic used
for 2026 tier probabilities (better calibrated probabilities than HGB; HGB's
macro-F1 edge comes mostly from the Bench tier).

Bust model (bust = games<100 or WS<2; base rate 43.6% all picks, 19.9% FR):

| model | AUC | Brier | log loss | AUC (FR only) |
|---|---|---|---|---|
| pick-only logistic baseline | 0.806 | 0.178 | 0.532 | 0.668 |
| logistic (skill) | 0.794 | 0.176 | 0.516 | 0.642 |
| hgb (skill) | 0.776 | 0.184 | 0.539 | - |

Honest read: **the pick baseline beats the skill models on bust AUC** (0.806
vs 0.794 overall, 0.668 vs 0.642 within round 1). Where a player gets picked
is genuinely the single best washout predictor - the market aggregates intel
we do not have. The skill logistic is still well calibrated (see
figures/calibration_bust.png: near-diagonal, Brier 0.176, slight
underconfidence below p=0.3) and it is the model we can actually apply to
2026 prospects (who have no pick yet), so it is the production bust model.
Treat 2026 bust_prob as "skills-only risk", not market-informed risk.

## Iteration 3 — train on first round only?

Question: since the 2026 board is a top-45, does training only on picks 1-30
(n=658) help? Answer: **no.** FR-only-trained ridge gets FR pooled Spearman
0.235 vs 0.256 for the all-picks model evaluated on FR; HGB collapses (0.150).
Second-rounders roughly double n and sharpen the age/BPM gradients. Kept
all-picks training.

## Feature analysis (permutation importance, LODCO test folds, 5 repeats/fold)

figures/feature_importance.png. Top features, VORP model (best skill linear):

1. **age_at_draft** (importance 0.091; standardized ridge coef -0.38) - the
   dominant signal. Younger at the same production level = far better career.
2. **ncaa_bpm** (0.084; coef +0.36) - overall college impact metric, second pillar.
3. miss_age (0.050; coef -0.18) - missing age = obscure/unscouted player, bad sign.
4. miss_ncaa_core (0.040; coef -0.25) - no NCAA stats = mostly internationals
   and pre-2009 deep second-rounders; net negative after other features.
5. **ncaa_ast_pct** (0.006; coef +0.10) - passing/feel travels. The clearest
   skill predictor after age and BPM.
6. ncaa_ts_pct (+0.05 coef) - efficiency helps.
7. ncaa_ft_pct (+0.04 coef) - touch/shooting projection signal.
8. ncaa_blk_pct, ncaa_stl_pct (+0.04, +0.03) - defensive event creation.

Surprises / signs worth noting:
- **ncaa_obpm gets a NEGATIVE coefficient (-0.04) conditional on ncaa_bpm** -
  i.e. given total BPM, the defense-leaning college players age better than
  offense-leaning ones. Small but consistent with lasso keeping it negative.
- Wingspan/reach contribute almost nothing once height/weight are in (+0.03
  differential coef), partly because wingspan is missing for 37% of training
  rows. In the bust model anthro matters more (wingspan_in is its #4 feature).
- height_in is slightly NEGATIVE for VORP conditional on everything else
  (skill stats already encode position); raw "big" is not a bonus by itself.
- usage is mildly positive (+0.03) - high-usage college players carry a bit
  more upside than equal-efficiency low-usage ones.
- Missingness indicators carrying real importance is a dataset artifact to
  remember when reading 2026 outputs: every 2026 NCAA prospect has
  miss_age=miss_ncaa_core=0, so their scores ride on age/BPM/AST%; the three
  internationals get the miss_ncaa_core penalty, which is exactly the "wide
  uncertainty" flag the spec asks for.

Bust model top features (AUC importance): miss_age, miss_ncaa_core,
age_at_draft, wingspan_in, ncaa_bpm - older + statless + short-armed = washout
risk.

## Iteration 4 — 2026 application (src/apply_2026.py, 2026-06-10)

Config: ridge (skill features, asinh target) refit on all 22 classes; tier
probs from multinomial logistic; bust_prob from skill logistic. Bootstrap =
200 reps resampling the 22 draft classes with replacement (seed 42), ridge
refit per rep.

Feature build for the 40 prospects:
- Name merge prospect_stats x combine x consensus: 40/40 matched on
  normalized names (suffixes stripped). Mismatch log: Sergio De Larrea has no
  combine wingspan/reach (no-show, flagged NO_COMBINE_ANTHRO); 5
  consensus-board players have no prospect-stats row and are NOT modeled
  (Amari Allen, Maliq Brown, Jack Kayil, Braden Smith, Izaiyah Nelson).
- height from listed height (matches historical BBR-listed convention),
  wingspan/reach/weight from combine when measured.
- STL%/BLK% are not published for 2026 prospects, APPROXIMATED from per-game
  steals/blocks: stl_pct ~= 100*spg*40/(mpg*68 poss), blk_pct ~=
  100*bpg*40/(mpg*35 opp 2PA). Same constants for everyone, ordering
  preserved, absolute level approximate. Documented choice.
- Internationals (Lopez, De Larrea, Suigo): source marks usage/ast/tov/
  obpm/bpm UNVERIFIED -> treated as missing (miss_ncaa_adv=1), TS%/3PA/FT%
  taken from pro-league stats with INTL flag. No league-strength adjustment
  exists in the model -> their point estimates are soft; treat the wide
  intervals as the real output.

Two distribution fixes made during this iteration (both documented in code):
1. **Convexity inflation.** First run reported pred_vorp_mean as the mean of
   residual-noised draws; inverse asinh is convex, so noise inflated means
   (Boozer 104 expected VORP - nonsense). Fix: pred_vorp_mean = mean of
   bootstrap-only draws (model uncertainty, no residual noise); percentile
   columns keep residual noise (LODCO OOF ridge residuals of picks 1-45,
   sd 1.66 asinh scale) because they are meant to describe outcome spread.
2. **Winsorized tails.** Residual noise on the asinh scale is multiplicative,
   so elite profiles drew impossible outcomes (p90 ~288 VORP > LeBron 159).
   Outcome draws clipped at the training-sample max (159.4). Only affects the
   extreme right tail of the top ~3 prospects.

Sanity checks: Boozer pred mean 22.4 ~ historical #1-pick average outcome;
bust_prob 0.006-0.545 range, highest for Quaintance (4 GP, knee, near-zero
BPM) and Mikel Brown (5.8 BPM, thin frame) - sensible. Tier probs sum to 1.

Output: models/predictions_2026.csv, figures/pred_vs_consensus.png.

Biggest model-vs-consensus gaps (full table in final report): model UP on
Onyenso (+21), Ejiofor (+18), Graves (+15), Okorie (+14); model DOWN on
Mikel Brown (-20.5), Quaintance (-19.5), Ament (-15), Carr (-14), Stirtz
(-13.5). Pattern: the model is age-and-BPM driven and has no conference
strength, role/context, or film input - it over-rewards older productive
bigs (Onyenso, Ejiofor) and WCC production (Graves), and punishes
injury-shortened or low-BPM seasons regardless of pedigree (Quaintance,
Brown, Ament). These gaps are inputs for human review in Phases 5-7, not
verdicts.

## Known limitations (read before using predictions)

- No college conference/league strength adjustment (Graves' WCC numbers and
  intl pro stats are treated at face value).
- No injury modeling beyond what shows up in reduced per-game stats; flags
  carry the injury notes forward instead.
- Skill Spearman ~0.26 within the first round: better than the pick-slot
  market proxy (0.15) but still leaves most variance unexplained. Use
  distributions, not point estimates.
- 2020-21 outcome censoring (above) slightly depresses every model's
  apparent skill in those folds and the training signal for recent profiles.
