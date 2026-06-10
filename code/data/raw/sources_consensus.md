# Sources Used, 2026 NBA Draft Consensus Board

Date collected, June 10, 2026

## Boards used in the consensus (6)

1. **ESPN big board**
   https://www.espn.com/nba/story/_/id/46886245/2026-nba-draft-big-board-rankings-top-100-prospects-players
   Updated May 29, 2026. Provided ranks 1-40 (column `espn_rank`).

2. **The Ringer mock draft (Danny Chau)**
   https://theringer.com/nba-draft/2026/mock-draft
   Updated May 27, 2026. Provided picks 1-30 only, page content truncated after pick 30 on two fetch attempts (column `ringer_rank`, ranks 31-40 blank).

3. **Yahoo Sports Mock Draft 7.0 (Kevin O'Connor)**
   https://sports.yahoo.com/nba/article/nba-mock-draft-70-who-goes-no-1-the-latest-on-every-pick-of-the-draft-with-three-weeks-to-go-190746763.html
   Published June 5, 2026. Provided picks 1-40 (column `yahoo_rank`).

4. **Tankathon big board**
   https://www.tankathon.com/big-board
   "Updated 12 days ago" as of June 10, 2026 (approximately May 29, 2026). Provided ranks 1-40 (column `tankathon_rank`).

5. **CBS Sports big board**
   https://www.cbssports.com/nba/news/2026-nba-draft-big-board-prospect-rankings-withdraw-deadline/ (updated May 28, 2026, gave ranks 1-20)
   https://www.cbssports.com/nba/draft/prospect-rankings/ (gave ranks 1-28, consistent with the article)
   Combined into column `cbs_rank`, ranks 29-40 not accessible, left blank.

6. **Bleacher Report mock draft**
   https://bleacherreport.com/articles/25262746-2026-nba-mock-draft
   Updated June 9, 2026. Provided picks 1-40 (column `bleacher_report_rank`).

## Sources attempted and skipped

- **NBADraft.net big board**, https://www.nbadraft.net/ranking/bigboard/ — HTTP 403 Forbidden, could not read.
- **The Athletic** — paywalled, skipped without fetching.
- **NBA.com reprint of Yahoo post-lottery mock**, https://www.nba.com/news/yahoo-sports-mock-draft-the-wizards-won-the-lottery-heres-how-every-pick-could-play-out-now — fetch timed out twice; superseded by the newer Yahoo Mock 7.0 fetched directly.

## Discovery searches (WebSearch)

- "2026 NBA Draft big board top 40 prospects June 2026"
- "2026 NBA mock draft post-lottery June 2026 ESPN Yahoo Tankathon"
- "Kevin O'Connor Yahoo Sports 2026 NBA mock draft Wizards Dybantsa"
- "sports.yahoo.com Kevin O'Connor 2026 NBA mock draft all 30 picks"

## Processing

- Build script, `/Users/arcaman07/Documents/Robotics/Imitation learning/nba_draft_claude/data/raw/build_consensus.py`
- Raw extracts, `/Users/arcaman07/Documents/Robotics/Imitation learning/nba_draft_claude/data/raw/consensus_notes.md`
- Output, `/Users/arcaman07/Documents/Robotics/Imitation learning/nba_draft_claude/data/processed/consensus_board.csv` (45 players, sorted by median rank; mean/median/min/max/spread computed over available ranks only)
