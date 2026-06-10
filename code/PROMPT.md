# 2026 NBA Draft Big Board, Full Research Project (Claude Code Edition)

You are an autonomous AI scouting department. Your job is to produce a complete, defensible big board for the 2026 NBA Draft (first round, top 30 picks) and document the entire process in a final research-paper-quality PDF report, written like a Kaggle competition solution writeup crossed with an academic paper.

Work inside this directory (`nba_draft_claude/`). Everything you produce lives here. You have no restrictions on which public signals to use. Combine talent evaluation, historical comps, film study, external scouting consensus, ML models, combine measurements, data analysis of previous drafts, and team requirements. Use anything and everything that improves the board.

## Ground rules (read first, these override convenience)

1. **Today matters.** Check the current date first. The 2026 NBA Draft is in late June 2026. Your training data does not cover the full 2025-26 college/international season, the May 2026 draft combine, or the 2026 lottery results. NEVER answer from memory when a fresh fact is available. Use web search and page fetches for every season stat, measurement, draft order slot, and lottery result. Treat your prior knowledge of the 2026 class as a hypothesis to verify, not a source.
2. **No fabrication, ever.** Every number in the final report (stat, measurement, age, pick slot) must trace to a fetched source. Keep a `sources.md` log mapping each data file to its URL and fetch date. If you cannot verify a number, mark it clearly as unverified or drop it.
3. **Be honest about video.** You cannot perceive motion. Frame-sampled film study is a supplementary signal. Label your own film observations separately from aggregated human scouting reports. Never present a frame-based observation as if you watched live film.
4. **Show your failures.** If a model underperforms, a data source is unavailable, or a clip will not download, log it and write it into the limitations section. A Kaggle-style report that hides iteration is a bad report.
5. **Reproducibility.** All analysis happens in versioned scripts (Python preferred) inside `src/`, not in throwaway shell one-liners. Saved data in `data/`, figures in `figures/`, film artifacts in `film/`, report source in `report/`.
6. **Parallelize aggressively.** You are Claude Code. Use subagents / multi-agent workflows to fan out per-prospect research dossiers, per-team needs analysis, and per-source data collection concurrently. One agent per prospect dossier is the right granularity.

## Project structure to create

```
nba_draft_claude/
  PROMPT.md            (this file)
  sources.md           (every URL used, what it provided, fetch date)
  data/
    raw/               (fetched HTML/JSON/CSV snapshots)
    processed/         (clean CSVs: prospects, combine, college stats, historical drafts)
  src/                 (all Python scripts: scraping, cleaning, modeling, comps, figures)
  film/
    clips/             (downloaded video, keep short)
    frames/            (extracted frames, organized per prospect)
    notes/             (per-prospect film notes, your observations vs sourced observations)
  dossiers/            (one markdown dossier per prospect)
  models/              (saved models, metrics JSONs, iteration log)
  figures/             (all charts used in the report)
  report/
    report.md          (report source)
    final_report.pdf   (the deliverable)
  big_board.md         (the final ranked board, human-readable summary)
```

## Phase 0: Setup

- Verify/install tooling: `python3` with pandas, numpy, scikit-learn, matplotlib, plus `yt-dlp`, `ffmpeg`, and a markdown-to-PDF path (prefer `pandoc` with a LaTeX engine, fallback to `weasyprint` or Python `reportlab`). Install what is missing.
- Record environment versions in `sources.md`.

## Phase 1: Live data collection (web, current as of run date)

Collect and snapshot to `data/raw/`, then clean into `data/processed/`:

1. **Draft order.** The actual 2026 first-round order, picks 1-30, post-lottery, including traded picks and which team currently owns each pick.
2. **Consensus boards.** At least 4-6 current external big boards / mock drafts (e.g., ESPN, The Athletic, The Ringer, Yahoo, Tankathon, NBADraft.net, CBS, Bleacher Report, whatever is accessible). Build a consensus rank table (mean, median, spread per prospect). The spread is itself a signal (disagreement = risk).
3. **2026 combine results.** Anthropometrics (height w/ and w/o shoes, wingspan, standing reach, weight, hand size), athletic testing (vertical, lane agility, sprint), shooting drills where reported. Note who skipped the combine or specific drills.
4. **Season stats.** 2025-26 college stats (per game, per 40, advanced: TS%, usage, BPM/OBPM/DBPM, assist/TO, block/steal rates, 3P volume and %, FT%) for every prospect in the top 35-40 of consensus. Use Sports Reference / Barttorvik style sources. For international and non-NCAA prospects (e.g., overseas pros, G League Ignite style paths, Overtime Elite), get their league-appropriate stats and note league strength.
5. **Biographical.** Birthdates (age at draft is a major predictive feature), height/weight history, injury history, positions, handedness.
6. **Team context.** For each of the 30 teams holding first-round picks: current roster core, timeline (contending/retooling/rebuilding), positional and skill needs, cap situation in broad strokes, recent draft tendencies.

## Phase 2: Historical training dataset (previous drafts)

Build `data/processed/historical.csv` covering at least draft classes 2000-2021 (older is fine if data quality holds, stop at 2021 or 2022 so outcomes have had time to mature):

- **Pre-draft features:** age at draft, anthropometrics (combine where available), college/international advanced stats (mirror the Phase 1 feature set), pick slot, consensus rank where recoverable.
- **Outcome labels:** career value metrics over first 4-5 seasons and career-to-date (VORP, Win Shares, BPM, minutes played), plus categorical outcomes (All-NBA/All-Star, quality starter, rotation player, bench, bust/out of league). Define each tier precisely in the report.
- Handle the survivorship and era issues explicitly (pace/3P era shifts, one-and-done rule changes, combine participation bias). Document every cleaning decision.

## Phase 3: ML modeling (iterate, log every iteration)

In `src/`, with metrics and configs saved to `models/`:

1. **Baselines first.** Pick-slot-only baseline and consensus-rank-only baseline. Your models must beat these to matter, and you must report whether they do.
2. **Models.** Regularized linear regression (ridge/lasso) for interpretability, gradient boosting (XGBoost/LightGBM or sklearn GBM) for performance, and a classifier for outcome tiers (e.g., ordinal or multinomial). Optionally a probability-of-bust model.
3. **Validation.** Leave-one-draft-class-out cross-validation (group by draft year, never random row splits, that leaks era information). Report MAE/RMSE/Spearman for regression, calibration and confusion for classification.
4. **Feature analysis.** Permutation importance / SHAP-style attribution. Which features actually predict NBA outcomes? Age? Wingspan differential? FT% as a shooting proxy? Steal rate? Write up findings, they go in the paper.
5. **Apply to 2026.** Score every 2026 prospect. Produce predicted value distributions, not just point estimates (e.g., quantile models or bootstrap). These feed floor/ceiling.
6. **Iteration log.** `models/iterations.md`: every model run, config, scores, and what you changed and why. This is the Kaggle-writeup backbone.

## Phase 4: Film study (frame-based, honestly labeled)

For at least the top 15-20 prospects on your working board:

1. Use `yt-dlp` to download 1-3 publicly available highlight/scouting clips per prospect (keep downloads short, a few minutes each). Log URLs in `sources.md`. If a download fails, note it and move on.
2. Use `ffmpeg` to extract frames (e.g., 1-2 fps for full clips plus dense bursts around shooting motions). Store under `film/frames/<prospect>/`.
3. Read frame sequences as images. Evaluate what frames can actually support: shooting mechanics (set point, release height, base, follow-through), body frame and build in game context, defensive stance, handle posture, finishing angles.
4. Write per-prospect film notes in `film/notes/` with two clearly separated sections: "Frame-based observations (mine)" and "Sourced scouting observations (human scouts, cited)".
5. Select 2-4 illustrative frames per top-10 prospect for inclusion in the report.

## Phase 5: Historical comparisons (comps engine)

1. Build a nearest-neighbor comps engine in standardized feature space (anthro + age + statistical profile, weighted sensibly, document weights). For each 2026 prospect, surface the 3-5 closest historical prospects at the same stage.
2. For each comp cohort, report how those players actually turned out. Derive empirical floor/ceiling: e.g., 25th percentile outcome of the comp cohort = floor narrative, 90th percentile = ceiling narrative. Pair every statistical comp with a stylistic sanity check (a player can be a statistical comp but a stylistic mismatch, say so when true).
3. Each dossier gets: floor comp, ceiling comp, median expectation, and probability-flavored language grounded in the cohort outcomes.

## Phase 6: Team fit (picks 1-30)

For each actual pick slot: who is on the clock, what they need, which 3-4 prospects fit best at that slot, and where fit should and should not override talent. Keep two artifacts distinct:
- **Big board** = pure prospect ranking by expected value (talent first).
- **Fit-adjusted mock draft** = pick-by-pick prediction/recommendation for all 30 picks.

## Phase 7: The big board

`big_board.md` and the report must contain, for each of the top 30 (plus 5-10 honorable mentions):

- Rank, tier (define tiers), position, team/school, age at draft.
- Key measurements and key stats (sourced).
- Model-predicted value with uncertainty band, consensus rank vs your rank with explanation of major deltas.
- Floor comp / ceiling comp / median outcome with cohort evidence.
- Film notes summary (yours, labeled) + scouting consensus summary (cited).
- Best team fits in the actual first round.
- A 3-5 sentence scouting verdict in plain prose.

## Phase 8: The final report (PDF)

Write `report/report.md`, then render `report/final_report.pdf`. Structure it as a research paper / Kaggle solution writeup:

1. Abstract
2. Introduction and problem statement
3. Related work (public draft models, e.g., historical stat-based draft models, briefly)
4. Data (sources, collection method, cleaning, dataset tables)
5. Methodology (consensus aggregation, ML models, validation design, comps engine, film protocol, team-fit framework)
6. Model results (baselines vs models, metrics tables, feature importance figures, calibration)
7. Iteration narrative (what was tried, what failed, what changed, Kaggle style)
8. Film study (protocol, example frames, findings, explicit limitations of frame-based scouting)
9. The 2026 Big Board (the full top 30 with everything from Phase 7)
10. Fit-adjusted mock draft, picks 1-30
11. Discussion (where the model and scouts disagree and why, biggest risks in the class)
12. Limitations and threats to validity (video limits, data gaps, small-sample international stats, unverifiable numbers)
13. Reproducibility statement (how to rerun everything from `src/`)
14. References (every source URL)
15. Appendix (full data tables, all dossier summaries, extra figures)

Figures must be real generated charts from `figures/` (consensus spread, feature importance, predicted value vs consensus rank scatter, comp cohort outcome distributions, etc.) plus selected film frames. The PDF must be self-contained and readable by an NBA front office without access to your working files.

## Execution notes

- Work the phases roughly in order, but Phase 1 dossier collection, Phase 2 historical scraping, and Phase 4 clip downloads parallelize well across subagents.
- Checkpoint often: keep `progress.md` updated with phase status so an interrupted run can resume.
- Expected scale: this is a multi-hour project. Do not cut scope silently. If something must be cut, cut it loudly in the limitations section.
- Finish line: `report/final_report.pdf` exists, renders correctly, contains the full top-30 board, and every claim in it is sourced or labeled as your own inference.
