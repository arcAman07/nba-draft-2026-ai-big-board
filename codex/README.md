# 2026 NBA Draft Big Board Research Project

Run date: 2026-06-10 IST.

This repository contains a sourced, reproducible 2026 NBA Draft first-round big board. It combines current public draft order, consensus boards and mocks, prospect statistics, combine measurements where available, sourced scouting notes, still-frame film study, historical draft modeling, nearest-neighbor comps, and a fit-adjusted mock draft.

## Final Deliverables

- Final LaTeX PDF report: `report/final_report.pdf`
- LaTeX source: `report/report.tex`
- Human-readable board: `big_board.md`
- Shareable full-round graphic: `figures/shareable_mock_draft_16x9.png`
- Shareable story deck: `figures/shareable_mock_draft_story_deck.pdf`

## Confidence Statement

I am confident in the board as a defensible, sourced, evidence-labeled prediction as of 2026-06-10. I am not claiming certainty. The report is explicit that public market rank is still the strongest signal, the ML edge over the market baseline is modest, and some live endpoints were unavailable. The ranking is therefore a conservative blend of consensus, model value, uncertainty, comps, film notes, and team context.

## Project Layout

- `data/raw/`: fetched HTML, JSON, and CSV snapshots.
- `data/processed/`: cleaned modeling and report tables.
- `src/`: reproducible fetch, cleaning, modeling, figure, and report scripts.
- `models/`: fitted models, metrics, predictions, and iteration log.
- `figures/`: report charts plus share graphics.
- `film/`: public clips, extracted frames, selected report frames, and film notes.
- `dossiers/`: one markdown dossier per top-40 prospect.
- `report/`: LaTeX source and final PDF.
- `sources.md`: source audit trail with fetch dates and failures.

## Rebuild Commands

The current final artifacts are already built. To rerun the full project from scratch, use:

```bash
make all
```

To rebuild only the paper and share graphics:

```bash
make report visuals
```

To run a fast health check:

```bash
make verify
```

## Core Modeling Artifacts

- `models/metrics.json`: leave-one-draft-class-out regression/classifier metrics.
- `models/feature_importance.csv`: permutation importance.
- `models/logo_regression_predictions.csv`: cross-validated predictions.
- `data/processed/prospect_model_scores_2026.csv`: final prospect scores, prediction bands, probabilities, tiers, board rank, and comps summary.
- `data/processed/historical_comps_2026.csv`: five nearest historical comps per prospect.

## Important Limitations

- NBA.com/stats combine endpoints timed out from this environment.
- Basketball Reference bulk pages were blocked, so the primary target is NBA MPG-equivalent value rather than a fully refreshed WS/VORP target.
- Still-frame film study supports static visual observations only. It is not full live-film charting.
- Team context is broad and qualitative. It is not a cap-sheet optimizer.
