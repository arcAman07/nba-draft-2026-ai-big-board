# Career outcome tier definitions (Phase 3)

Defined 2026-06-10 from `data/processed/historical_enriched.csv` (1,309 drafted
players, 2000-2021). Applied in `src/model_common.py::assign_tier` in this exact
priority order (first match wins):

| Tier | Exact rule | n | median career VORP |
|---|---|---|---|
| AllStar | `allstar == 1` (made at least one All-Star team) | 119 | 21.0 |
| Starter | `career_minutes >= 12000 AND career_ws >= 25` | 158 | 9.1 |
| Rotation | `career_minutes >= 5000 AND career_ws >= 5` | 297 | 1.7 |
| Bench | `career_games >= 100 AND career_ws > 2` | 158 | -0.2 |
| Bust | everything else (`career_games < 100 OR career_ws <= 2`) | 577 | -0.1 |

Rationale for thresholds:
- 12,000 minutes is roughly 5-6 seasons at starter-level minutes (~28 mpg over
  65 games is ~1,800 min/season); 25 WS over that span is solid-starter
  production (~4-5 WS/yr).
- 5,000 minutes / 5 WS marks a multi-year rotation player.
- 100 games separates players who stuck in the league at all from washouts;
  the same 100-game line is used in the binary bust label.
- Tiers are monotone in median career VORP (21.0 / 9.1 / 1.7 / -0.2 / -0.1),
  which sanity-checks the ordering. Bench vs Bust separate on longevity
  rather than VORP, by design.

## Binary bust label (for the bust-probability logistic model)

`bust = (career_games < 100) OR (career_ws < 2.0)`

Base rates: 43.6% of all 1,309 picks, 19.9% of first-rounders, 11.0% of
lottery picks. This is the "near-zero contribution for a drafted player"
definition required by the spec, applied uniformly to all picks (pick slot is
not used in the skill models, so the label must not depend on draft position).

## Known censoring caveat

Career-to-date for the 2020 and 2021 classes is only 5-6 and 4-5 seasons
respectively (data cut at 2025-26). Accepted per project design. Effect on
tiers: the 12,000-minute Starter bar is barely reachable for 2021 draftees,
so those classes skew toward Rotation/Bench/Bust (2020-21 combined: 1 Starter,
10 AllStars, 50 Busts out of 120). LODCO folds for 2020/2021 therefore
understate true upside; documented in `models/iterations.md`.

Never-played-NBA players (161, mostly second-rounders; notes column confirms
"never played") have career_games/minutes/WS/VORP filled with 0 - these are
real outcomes (the players never appeared), not missing data.
