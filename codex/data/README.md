# Data

## `raw/`

Fetched source snapshots. These are the audit trail for live web pages, JSON endpoints, CSV downloads, and failed fetch attempts.

## `processed/`

Clean tables used by the models, report, dossiers, and visualizations.

Key files:

- `draft_order_2026.csv`: actual first-round pick owners.
- `consensus_board_2026.csv`: aggregated public ranking table.
- `prospects_2026.csv`: cleaned 2026 prospect table.
- `prospect_model_scores_2026.csv`: final model outputs, probabilities, board rank, tiers, and comp summaries.
- `historical.csv`: 2000-2021 historical modeling dataset.
- `historical_comps_2026.csv`: nearest-neighbor historical comps.
- `fit_adjusted_mock_2026.csv`: pick-by-pick mock draft.
- `team_context_2026.csv`: broad team needs and timeline context.
- `sources_log.csv`: structured source log mirrored by `sources.md`.
