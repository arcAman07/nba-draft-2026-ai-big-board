# Project Progress

Last updated: 2026-06-10 19:15 IST (loop iteration 11)

## Currently running agents
- report.md writer (launched ~20:15 IST) -> report/report.md. After it lands: main loop renders PDF via pandoc + headless Chrome.

## Dossiers status
All 31 files verified on disk 19:50 IST: 30 full dossiers + honorable_mentions.md (8 HM entries incl. Braden Smith via cited web lookup).

## Phase status

- [x] Phase 0: Setup. Directory structure created. Tooling verified: Python 3.11.8, pandas 2.1.0, numpy 1.26.4, sklearn 1.4.2, matplotlib 3.10.8, yt-dlp, ffmpeg, pandoc all present. weasyprint and xelatex MISSING, PDF path will be pandoc with another engine or pip install weasyprint later.
- [x] Phase 1: Live data collection. COMPLETE 2026-06-10. All 5 collectors done:
  - [DONE] draft order agent -> data/processed/draft_order.csv (30 rows validated; lottery: WAS 1, UTA 2, MEM 3, CHI 4; pick 22/30 routing details single-source, flagged UNVERIFIED in notes)
  - [DONE] consensus boards agent -> data/processed/consensus_board.csv (45 players, 6 boards: ESPN, Ringer, Yahoo, Tankathon, CBS, B/R; consensus top 5: Dybantsa, Peterson, Boozer, Wilson, Wagler; biggest disagreements: Suigo spread 17, Lopez spread 16, Jefferson spread 13; NBADraft.net 403, Athletic paywalled, skipped)
  - [DONE] combine 2026 agent -> data/processed/combine_2026.csv (78 rows validated, ranges plausible; 75 with anthro, 71 with athletic testing; height_shoes/hand/body_fat columns empty for all, only on stats.nba.com which timed out, documented in combine_notes.md; Quaintance + Saunders skipped testing post-injury; Kayil + de Larrea no-shows)
  - [DONE] prospect stats + bios agent -> data/processed/prospect_stats_2026.csv (40 rows validated, 100% birthdate/TS%/BPM coverage; 3 internationals have UNVERIFIED usage/BPM, not published for their leagues; key injury flags: Peterson hamstring 24 GP, Wilson broken thumb 24 GP, Brown back 21 GP, Quaintance knee 4 GP, Saunders ACL out)
  - [DONE] team context agent -> data/processed/team_context.md (24 team entries by pick slot, verified vs Tankathon + CBS; major 2025-26 shakeups captured: WAS got Trae Young + AD yet won lottery at 17-65, Giannis trade likely pre-draft, MEM teardown, Harden-Garland swap, ATL traded Young, SAS in Finals vs NYK)
- [x] Phase 2: Historical dataset. COMPLETE. data/processed/historical_enriched.csv validated (1,309 rows, 36 cols; NCAA final-season stats coverage: 100% of NCAA first-rounders 2009-2021, 98.5% 2000-2008; usage/advanced rates thinner pre-2009 at 34%, sourced from sports-reference where torvik absent; internationals blank by design). Note: the enrichment agent was killed by a usage limit AFTER finishing its merge, output verified good via enrich_run.log + direct inspection.
- [x] Phase 3: ML modeling. COMPLETE 2026-06-10. LODCO CV (22 folds by year) on historical_enriched.csv (1,309 players). Pick-slot isotonic baseline vs ridge/lasso/HistGB on skill features (asinh VORP target): skill ridge beats baseline (first-round Spearman 0.256 vs 0.145, MAE 7.25 vs 8.14); HGB underperforms linear; bust logistic well calibrated (AUC 0.794) but pick baseline edges it on AUC (0.806), documented honestly. Top features: age_at_draft, ncaa_bpm, ncaa_ast_pct. 2026 predictions for all 40 prospects with 200-rep bootstrap distributions -> models/predictions_2026.csv; figures: feature_importance.png, calibration_bust.png, pred_vs_consensus.png. Full log in models/iterations.md, tier defs in models/tier_definitions.md, provenance in data/raw/sources_models.md. Biggest model-vs-consensus gaps: UP Onyenso/Ejiofor/Graves/Okorie, DOWN Mikel Brown/Quaintance/Ament/Carr.
- [x] Phase 4: Film study. COMPLETE 2026-06-10 14:35 IST. All 20 consensus top-20 prospects: clips downloaded (480p), ~11k frames at 1fps, film/notes/<slug>.md written for all 20 (two-section format: frame-based vs sourced, observations tagged to frame files). All 10 top-10 prospects have 3-4 report frames in film/frames/_report_picks/. Caveats logged in notes: philon and graves had no clean jumper reps sampled (no mechanics claims made), burries source was 360p.
- [x] Phase 5: Comps engine. COMPLETE 19:00 IST. comps_2026.csv (40 rows) + comps_2026_detail.json + figures/comp_cohorts_top10.png. Pool 781 NCAA draftees, weighted z-space kNN, spot checks passed first iteration (Boozer->Love/Bogut, Mara->Hibbert/Mobley/Thabeet; Boozer cohort 40% All-Star rate best in class). 3 internationals LOW confidence. Caveat: Peterson cohort suppressed by injury-shortened 24 GP season, documented.
- [x] Phase 6: Team fit. COMPLETE 19:15 IST. team_fit.md (all 30 slots) + mock_draft.csv (validated: 30 unique, availability within +/-6 of median). Mock 1-3: WAS Dybantsa, UTA Peterson, MEM Boozer. Headline divergences: LAC takes Ament (median 10) at 5 for Kawhi insurance over guard logjam; CHA takes Cenac early at 18; LAL Veesaar at 25.
- [x] Phase 7: Big board. COMPLETE ~20:10 IST. big_board.md written (398 lines: preamble, tier definitions, 30-row summary table, 30 per-player entries, 8 HMs, honesty footer). sources.md merged (12/17 fragments, ~206 unique URLs; 5 fragments never written by limit-killed film agents, noted with fallback provenance). FINAL RANKING DECIDED by head scout (main loop) 2026-06-10 -> data/processed/final_board.csv (30 + 8 HM, tiers 1-5, per-player delta rationale vs consensus/model). Headline calls: Boozer 1 over Dybantsa 2 (model+comps+age), Brown falls 7.5->14 (0.33 bust prob, 21 GP back injury), Okorie rises 20->11 and Graves 20->15 (model+cohort, WCC caveat split), Ament held at 8 over model rank 25 (Tatum/Deng cohort override), Quaintance 25 as priced medical swing. 4 dossier agents running. Remaining: big_board.md assembly after dossiers land.
- [x] Phase 8: Final PDF report. COMPLETE 2026-06-10 20:03 IST. report/report.md (909 lines, 15 sections) -> pandoc -> report/final_report.tex -> tectonic 0.16.9 -> report/final_report.pdf (34 pages, 750KB, LaTeX research-paper formatting per user request). Visually verified: title page + TOC, film frames with captions (pp. 13-15), wide appendix tables fit at scriptsize, xurl fix applied for long reference URLs. Social deliverable also done: figures/social_board.png (src/make_social_graphic.py).

## PROJECT COMPLETE 2026-06-10 20:03 IST
Deliverables: report/final_report.pdf (34pp LaTeX), big_board.md, dossiers/ (30+HM), mock_draft.csv, team_fit.md, models/, figures/social_board.png, sources.md (~206 URLs), full reproducible src/.

## Polish pass 2026-06-10 evening (user-requested)
- Fixed PDF table layout: src/fix_report_tables.py rewrites pipe-table delimiter rows proportional to content width; pandoc --columns=80 then emits proportional p-columns. Mock draft table went from a squeezed 2-page mess to a clean single page; board glance no longer wraps player names; verified pages 16-17, 25-28, 31-32 visually.
- Removed stray bold date line that crowded the TOC (date moved into \date metadata), Abstract now starts on its own page.
- Repo cleanup: removed src/__pycache__ and .DS_Store, moved build_consensus.py from data/raw/ to src/, added README.md (deliverables, structure, reproduce steps, honesty notes).
- Decision: NO further model iteration. Models beat the market baseline where claimed, documented losses stand (bust AUC vs pick baseline), further gains need new data (conference strength, multi-season stats) not tuning. Board is final.

## Next actions (for next loop iteration)

1. When agents complete: validate each output CSV (row counts, obvious junk, UNVERIFIED flags), merge per-agent sources_*.md fragments into sources.md.
2. Once consensus_board.csv exists: launch film study (Phase 4) clip downloads for working top 15-20, and per-prospect dossier agents.
3. Once historical.csv exists: start Phase 3 baselines (pick-slot baseline, consensus baseline), then ridge/GBM.
4. [DONE] PDF path solved: pandoc -s report.md -o report.html, then headless Chrome ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --print-to-pdf=...) renders PDF. Tested OK 2026-06-10. weasyprint pip-installed but unusable (missing libpango, would need brew install pango; not required given Chrome path).

## Notes / incidents

- 2026-06-10 ~04:45 IST: Claude session usage limit hit (resets 08:10 Asia/Calcutta). All 5 then-running agents (4 film, 1 historical enrichment) died mid-task. Loop continues on hourly heartbeats until reset, then resumes.

## Resume plan after limit reset (08:10 IST)

Film state on disk (clips + 1fps frames survived):
- Notes COMPLETE (13): acuff, boozer, brown_mikel, dybantsa, flemings, johnson_morez, lendeborg, lopez, mara, okorie, peterson, steinbach, stirtz
- Frames done but NOTES MISSING (4): wilson (724 frames), burries (703), philon (286), graves (1476). Relaunch note-writing only: read 15-25 frames + WebSearch scout quotes + write film/notes/<slug>.md (wilson/burries are top-10: also report picks to film/frames/_report_picks/).
- NOTHING on disk (3): wagler, ament, carr. Full pipeline: find clip, yt-dlp 480p, ffmpeg 1fps, notes (wagler/ament top-10: report picks too).
- _report_picks has 23 frames already; verify which top-10 prospects are covered.
- sources_film_group*.md fragments may be missing; agents must log video URLs in notes files at minimum.

Enrichment state: data/raw/historical/college/torvik_players_2009_2021.csv downloaded; merge NOT done, historical_enriched.csv absent, src/enrich_college_stats.py may be partial. Relaunch enrichment agent pointing at the existing torvik CSV (merge 2009-2021 classes; pre-2008 sports-reference scrape still TODO or cut with documentation).
