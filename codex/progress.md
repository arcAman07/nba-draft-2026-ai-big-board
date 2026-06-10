# Progress

Last updated: 2026-06-10 19:05 IST

## Phase Status

| Phase | Status | Notes |
| --- | --- | --- |
| 0. Setup | Complete | Python/pandas/numpy/sklearn/matplotlib, yt-dlp, ffmpeg, pandoc, Chrome PDF path verified. |
| 1. Live data collection | Complete with limitations | Official order, nine rank sources, Tankathon/CBS stats, combine Wayback/NBA.com/On3 context fetched. NBA stats endpoints timed out. |
| 2. Historical dataset | Complete with limitations | `historical.csv` covers 2000-2021, 984 rows; primary target is NBA MPG-equivalent because WS/VORP coverage is partial. |
| 3. ML modeling | Complete | LODO validation, metrics, feature importance, saved models, iterations log. |
| 4. Film study | Complete with limitations | Public video/frame archive imported from local yt-dlp/ffmpeg outputs; top notes separate frame observations from sourced scouting. |
| 5. Historical comparisons | Complete | `historical_comps_2026.csv` with five nearest neighbors per prospect. |
| 6. Team fit | Complete | Broad fit-adjusted mock generated from actual pick owners and inferred needs. |
| 7. Big board | Complete | `big_board.md` and per-prospect dossiers generated. |
| 8. Final report PDF | Complete | `report/final_report.pdf` rendered. |
| Share graphics | Complete | 16:9 full-round PNG, three vertical story PNGs, and a three-page story PDF deck rendered in `figures/`. |
| LaTeX research report | Complete | `report/report.tex`, `report/final_report.pdf`, and `report/final_report_latex.pdf` generated; 59-page paper includes data, ML/regression, classifier, comps, film-frame protocol, player dossiers, mock draft, limitations, and references. |
| Project cleanup | Complete | Added root and folder README files, `VISUALS.md`, `requirements.txt`, `Makefile`, reproducibility commands, visual index, and cleaned cache/intermediate files. |

## Known Constraints

- NBA.com/stats combine endpoints timed out; height-with-shoes, hand size, body fat, and some official drill details are incomplete.
- Basketball Reference blocked bulk direct fetches; historical outcomes use public GitHub datasets and document coverage.
- Film is still-frame sampled; no live-motion claims are made from frames.
