# The 2026 NBA Draft Big Board, Built by an Autonomous AI Pipeline

An end-to-end evaluation of the 2026 NBA Draft class, researched, modeled, filmed, written, and typeset by an AI scouting department in a single day (June 10, 2026). Everything from raw data collection to the final 34-page research paper happened inside one autonomous loop.

## Start here

| File | What it is |
|---|---|
| `final_report.pdf` | The paper. Data, methodology, model results, film study, the full board, mock draft, and limitations |
| `big_board.md` | The board in readable form. Top 30 plus 8 honorable mentions with comps, model bands, and verdicts |
| `social_board.png` | The one-image version of the board |
| `code/` | Everything that produced the above |

## The headline calls

1. Cameron Boozer at No. 1 over the market's near-unanimous No. 1 AJ Dybantsa. The model has Boozer first by a wide margin, his comp cohort (Love, Bosh, Bogut) hits at a 40 percent All-Star rate, and he is the youngest top prospect with the best efficiency in the class.
2. Mikel Brown Jr. faded from consensus 7.5 to 14. Worst bust probability in the top 20, a back injury season, and production that does not support the pedigree.
3. Ebuka Okorie rises from 20 to 11 and Allen Graves from 20 to 15. The model and the comp cohorts both say the market is slow on them, and the Graves conference caveat is documented rather than ignored.
4. Mock top three reads Washington Dybantsa, Utah Peterson, Memphis Boozer. Fit bends picks, the board does not.

## How it was built

Five evidence streams, kept deliberately separate so no single one silently dominates.

1. A six-outlet consensus board (ESPN, The Ringer, Yahoo, Tankathon, CBS, Bleacher Report), where per-player disagreement itself becomes a risk signal.
2. A 1,309-player historical dataset of the 2000 to 2021 draft classes with final college season stats and career outcomes, scraped and cached reproducibly.
3. Models validated by leaving out entire draft classes. A ridge regression on skill features beats the pick-slot market baseline on first-round rank correlation (Spearman 0.256 vs 0.145). The bust model loses to the pick baseline on AUC and the paper says so plainly.
4. A nearest-neighbor comps engine over 781 NCAA draftees that turns each prospect into a 15-player historical cohort with empirical floor, median, ceiling, bust rate, and All-Star rate.
5. Frame-based film study of the consensus top 20. Clips were downloaded and sampled at 1 fps into roughly 12,000 stills, and every film claim is labeled as stills-only. Stills cannot show speed, burst, or timing, and no claim in the project pretends otherwise.

A team-fit layer then simulates all 30 picks as a separate artifact, because what a team should do and what a team will do are different questions.

## Inside `code/`

```
code/
  src/         every Python script (scrapers, dataset build, models, comps, figures)
  data/        raw fetched snapshots and the processed CSVs
  models/      metrics, predictions with uncertainty bands, and a log of every model iteration
  film/        per-prospect film notes and the report-cited frames
  dossiers/    one full scouting dossier per prospect
  figures/     all charts plus the social graphic
  report/      the paper source (markdown and LaTeX) and build files
  sources.md   every external URL used, around 206 of them, organized by phase
  progress.md  the full project chronology, including failures and recovery
  PROMPT.md    the original mission brief the AI executed
```

Film source videos and the bulk frame archives are excluded from the repo for size. The frames the paper actually cites live in `code/film/frames/_report_picks/`.

## Reproducing it

You need Python 3.11 with pandas, numpy, scikit-learn, and matplotlib, plus yt-dlp, ffmpeg, pandoc, and tectonic. Seeds are fixed wherever randomness exists.

Run the `code/src/` scripts in this order. Each one is idempotent and reuses cached raw files.

1. `scrape_bbr_draft.py`, `scrape_bbr_player_index.py`, `fetch_combine_and_allstars.py`, then `build_historical.py`
2. `enrich_college_stats.py`
3. `build_consensus.py`
4. `train_models.py`, then `apply_2026.py`
5. `comps_engine.py`
6. `make_social_graphic.py`
7. `fix_report_tables.py`, then from `code/report/` run pandoc into tectonic

```
pandoc report.md --shift-heading-level-by=-1 -s --toc --columns=80 \
  -V geometry:margin=1in -V fontsize=10pt -V colorlinks=true \
  -H latex_header.tex -o final_report.tex && tectonic final_report.tex
```

The compiled PDF lands in `code/report/` and a copy is kept at the repo root.

## Honesty notes

Every number in the paper traces to a fetched source logged in `code/sources.md`, and anything unverifiable is flagged instead of guessed. Known model blind spots (conference strength, role context, injury priors) are documented in the limitations section, and every place the board overrides the model carries a written rationale in `code/data/processed/final_board.csv`.

Built with Claude Code. A twin prompt exists for a comparison run on another coding agent.
