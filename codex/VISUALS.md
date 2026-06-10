# Visuals and Diagrams Index

Use this file to pick the right graphic for the right job.

## Share Graphics

- `figures/shareable_mock_draft_16x9.png`
  - Best for slides, X/Twitter, Discord, Notion, and landscape embeds.
  - Shows all 30 fit-adjusted mock picks on one board.
- `figures/shareable_mock_draft_story_deck.pdf`
  - Best for sending as a compact three-page story deck.
  - Contains picks 1-10, 11-20, and 21-30.
- `figures/shareable_mock_draft_story_picks_01_10.png`
  - Vertical story slide for picks 1-10.
- `figures/shareable_mock_draft_story_picks_11_20.png`
  - Vertical story slide for picks 11-20.
- `figures/shareable_mock_draft_story_picks_21_30.png`
  - Vertical story slide for picks 21-30.

## Report Figures

- `figures/consensus_spread_top30.png`
  - Shows disagreement across public boards; used as a risk signal.
- `figures/model_vs_consensus.png`
  - Plots predicted NBA MPG-equivalent value against public consensus rank.
- `figures/feature_importance.png`
  - Shows permutation importance for the final gradient boosting model.
- `figures/cv_predicted_vs_actual.png`
  - Leave-one-draft-class-out predictions versus actual outcome.
- `figures/comp_cohort_medians.png`
  - Median historical-comp cohort outcome by prospect.

## Film Frames

- `film/frames/_report_picks/`
  - Selected still frames used in the LaTeX report for the top ten prospects.
- `film/notes/`
  - Per-prospect film notes with separate sections for frame observations and sourced scouting.

## Regeneration

```bash
make visuals
make report
```

The visuals are generated from `src/create_shareable_graphic.py` and `src/run_modeling_and_comps.py`. The LaTeX report embeds both model figures and selected film frames.
