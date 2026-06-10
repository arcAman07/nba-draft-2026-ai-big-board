# Source Scripts

Scripts are intended to be run from the repository root.

## Pipeline Order

1. `fetch_live_data.py`
   - Fetches current draft order, public boards/mocks, combine pages, and other live sources.
2. `fetch_historical_data.py`
   - Fetches public historical draft/model datasets.
3. `fetch_additional_sources.py`
   - Fetches extra live combine and historical sources discovered during iteration.
4. `build_live_datasets.py`
   - Cleans 2026 prospect, consensus, combine, scouting, order, and team-context tables.
5. `build_historical_dataset.py`
   - Builds `data/processed/historical.csv` and historical coverage metadata.
6. `run_modeling_and_comps.py`
   - Trains regression/classifier models, validates with leave-one-draft-class-out CV, creates comps, assigns board ranks, and writes model figures.
7. `import_film_archive.py`
   - Imports public-video clips, frame archives, selected report frames, and note metadata.
8. `generate_report.py`
   - Legacy markdown/HTML report generator kept for traceability.
9. `generate_latex_report.py`
   - Primary final paper generator. Writes `report/report.tex` and compiles `report/final_report.pdf`.
10. `create_shareable_graphic.py`
   - Builds shareable PNG/PDF graphics from the mock draft and model-score tables.

## Shared Utilities

- `common.py`
  - Base paths, source logging, name normalization, slugging, height parsing, and fetch helpers.

## Verification

```bash
python3 -m py_compile src/*.py
make verify
```
