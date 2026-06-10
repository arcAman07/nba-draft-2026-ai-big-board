# The 2026 NBA Draft, Scouted by Two AI Agents

The same experiment, run twice. Claude Code (Fable 5) and Codex each received an identical mission brief in an empty folder. Build a complete 2026 NBA Draft big board from scratch, fully autonomously, with zero hints from a human. Scrape live data, train models on two decades of draft history, build historical comps, frame-sample game film, account for team needs, and write the whole thing up as a research paper.

Both finished in a single day (June 10, 2026). They disagree at No. 1.

## The two reports

| File | Agent | Pages | No. 1 pick |
|---|---|---|---|
| `final_report_claude.pdf` | Claude Code (Fable 5) | 32 | Cameron Boozer |
| `final_report_codex.pdf` | Codex | 59 | AJ Dybantsa |

## The split at the top

Codex stayed aligned with the public market and took AJ Dybantsa first, with Darryn Peterson second and Cameron Boozer third. Claude overrode the market and took Boozer first. Its case rests on the model having Boozer No. 1 by a wide margin (0.70 All-Star probability), the best comp cohort in the class (Love, Bosh, and Bogut, a 40 percent All-Star rate), and the youngest age among the top prospects paired with the best efficiency. Draft night settles the argument.

Elsewhere on the Claude board, Mikel Brown Jr. falls from consensus 7.5 to 14 on the worst bust probability in the top 20, while Ebuka Okorie (20 to 11) and Allen Graves (20 to 15) rise on model and cohort evidence. Every override carries a written rationale in `claude/code/data/processed/final_board.csv`.

## Repository layout

```
final_report_claude.pdf   the Claude run's paper
final_report_codex.pdf    the Codex run's paper
claude/                   the Claude Code (Fable 5) run
  big_board.md            the board in readable form, top 30 plus honorable mentions
  social_board.png        the one-image version of the board
  code/                   all source, data, models, film notes, dossiers, figures, paper source
codex/                    the Codex run, as it left its workspace
  big_board.md, src/, data/, models/, film/, dossiers/, figures/, report/, sources.md
```

Each run kept its own sources log (`claude/code/sources.md`, `codex/sources.md`), its own progress chronology, and its own per-prospect dossiers. The original mission brief both agents executed is in each folder as `PROMPT.md`.

Film source videos and bulk frame archives are excluded from the repo for size. The stills the Claude paper cites live in `claude/code/film/frames/_report_picks/`.

## What both agents had to do

1. Fetch everything live. The 2025-26 season, the May 2026 combine, and the lottery all post-date their training data, so every stat, measurement, and pick slot had to come from a fetched, logged source.
2. Build a historical training set of the 2000 to 2021 draft classes with pre-draft features and career outcomes, then validate models by leaving out entire draft classes.
3. Study film without pretending. Clips were sampled into stills at 1 fps and read as images. Stills cannot show speed, burst, or timing, and both papers label every film claim accordingly.
4. Show the failures. Iteration logs include the models that lost to baselines, the sources that blocked scraping, and the runs that got interrupted.

## Reproducing the Claude run

Python 3.11 with pandas, numpy, scikit-learn, and matplotlib, plus yt-dlp, ffmpeg, pandoc, and tectonic. Run the scripts in `claude/code/src/` in the order documented there, then build the paper from `claude/code/report/` with pandoc into tectonic. The Codex run documents its own pipeline in `codex/README.md` and `codex/Makefile`.

Built as an experiment in autonomous AI research work. Both boards are evidence-first, every number traces to a logged source, and the disagreements between the two agents are the most interesting part.
