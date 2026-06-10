# Sources / provenance: Phase 3 modeling (2026-06-10)

No external data fetched in this phase. All modeling inputs are
project-internal processed files:

- `data/processed/historical_enriched.csv` (1,309 drafted players 2000-2021;
  outcomes from Basketball-Reference draft pages, NCAA pre-draft stats from
  barttorvik (2009+) and sports-reference (older first-rounders), combine
  anthro where available; see sources_historical.md and
  sources_historical_college.md for original provenance).
- `data/processed/prospect_stats_2026.csv` (40 prospects; see
  sources_prospect_stats.md).
- `data/processed/combine_2026.csv` (78 prospects; see sources_combine.md).
- `data/processed/consensus_board.csv` (45 prospects, 6 outlets; see
  sources_consensus.md).

## Code and outputs

- `src/model_common.py` - shared features, tier/bust label definitions.
- `src/train_models.py` - LODCO CV (22 folds by draft year), baselines,
  ridge/lasso/HistGB regression, multinomial tier classifier, bust logistic,
  permutation importance, calibration.
- `src/apply_2026.py` - 2026 feature build, bootstrap predictions.
- `models/tier_definitions.md`, `models/iterations.md` (full run log,
  every config + CV score + honest verdicts),
  `models/metrics_{regression,tiers,bust}.json`,
  `models/cv_oof_predictions.csv`, `models/predictions_2026.csv`.
- `figures/feature_importance.png`, `figures/calibration_bust.png`,
  `figures/pred_vs_consensus.png`.

## Library versions (reproducibility)

Python 3.11.8, scikit-learn 1.4.2, pandas 2.1.0, numpy 1.26.4,
scipy (bundled with sklearn 1.4.2 env), matplotlib 3.10.8. Seed 42
everywhere (numpy RandomState; sklearn random_state args). Bootstrap:
200 reps over draft classes.

## Methodological notes for citation in the report

- Consensus-rank baseline could not be reconstructed for 2000-2021 (no
  archived multi-outlet boards collected); draft pick slot is used as the
  market-consensus proxy baseline throughout. 2026 consensus ranks are only
  used for comparison plots, never as model input.
- 2026 STL%/BLK% approximated from per-game stats (68 poss/40min, 35 opp
  2PA/game assumptions) because true rates are not published for prospects;
  exact formulas in src/apply_2026.py.
- Career-to-date outcomes for the 2020/2021 classes are 4-6 seasons
  (data cut 2025-26), accepted per project design.
