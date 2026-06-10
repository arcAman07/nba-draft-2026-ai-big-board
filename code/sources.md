# Sources Log

Master log of every external source used across the project, merged from the per-phase fragment files in `data/raw/sources_*.md` on 2026-06-10. Duplicates across fragments are collapsed (cross-references noted). Fragment files found and merged: sources_draft_order.md, sources_consensus.md, sources_combine.md, sources_prospect_stats.md, sources_team_context.md, sources_historical.md, sources_historical_college.md, sources_film_resume.md, sources_film_resume2.md, sources_models.md, sources_comps.md, sources_dossiers.md. Fragment files NOT found (never written by their phases): sources_film_group1.md, sources_film_group2.md, sources_film_group3.md, sources_film_group4.md, sources_teamfit.md; film sources for the first film groups and the team-fit phase are therefore only as documented in `film/notes/` and `data/processed/team_fit.md` themselves.

## Environment (Phase 0, recorded 2026-06-10)

- Python 3.11.8
- pandas 2.1.0, numpy 1.26.4, scikit-learn 1.4.2, matplotlib 3.10.8
- yt-dlp at /opt/homebrew/bin/yt-dlp
- ffmpeg at /opt/homebrew/bin/ffmpeg
- pandoc at /opt/homebrew/bin/pandoc
- weasyprint: not installed at start (PDF fallback path, install if needed)
- xelatex: not installed (pandoc will need a non-LaTeX PDF engine or weasyprint)

---

## Phase 1a - 2026 draft order (fetched 2026-06-10)

Fetched successfully:
- https://www.tankathon.com/full-draft - full first-round order picks 1-30 with current pick owner and "via" notations. (Also fetched as https://www.tankathon.com/full_draft during the team-context phase; same source.)
- https://www.cbssports.com/nba/news/nba-draft-order-lottery-odds-2026/ - independent 1-30 order with via notations; matches Tankathon at every pick (omitted the "via LA Clippers" note on pick 12); also supplied lottery storylines (Wizards 14% odds, Bulls 3% top-4 jump, Clippers landing Indiana's pick at 5). (Used by both draft-order and team-context phases.)
- https://www.espn.com/nba/story/_/id/48707565/2026-nba-draft-lottery-results-questions-takeaways-top-14-picks-teams-rounds - lottery results picks 1-14 with pre-lottery odds and key movements.
- https://en.wikipedia.org/wiki/2026_NBA_draft - picks 1-30 with detailed trade provenance for every traded pick; used for the acquired_via column.

Attempted, failed to load:
- https://www.nba.com/news/2026-nba-draft-order - official order page (picks 1-60); fetch timed out twice (60s). (Also timed out in the team-context phase; order verified via Tankathon + CBS.)

Search results referenced (titles/snippets only, not fetched):
- https://www.nba.com/news/2026-nba-draft-lottery-result - "Washington Wizards win 2026 NBA Draft Lottery"; Utah, Memphis, Chicago rounded out the top 4. (Referenced by both draft-order and team-context phases.)
- https://www.cbssports.com/nba/news/nba-draft-lottery-winners-and-losers-2026/ - lottery winners/losers framing.
- https://www.nba.com/draft/2026 - draft event page, draft dates June 23-24, 2026.

Search queries: "2026 NBA Draft lottery results first round order picks 1-30"; "2026 NBA Draft order post-lottery Tankathon".

## Phase 1b - Consensus board, 6 outlets (collected 2026-06-10)

Boards used in the consensus:
1. ESPN big board - https://www.espn.com/nba/story/_/id/46886245/2026-nba-draft-big-board-rankings-top-100-prospects-players (updated May 29, 2026; ranks 1-40, column `espn_rank`).
2. The Ringer mock draft (Danny Chau) - https://theringer.com/nba-draft/2026/mock-draft (updated May 27, 2026; picks 1-30 only, page truncated after pick 30 on two fetch attempts; ranks 31-40 blank).
3. Yahoo Sports Mock Draft 7.0 (Kevin O'Connor) - https://sports.yahoo.com/nba/article/nba-mock-draft-70-who-goes-no-1-the-latest-on-every-pick-of-the-draft-with-three-weeks-to-go-190746763.html (published June 5, 2026; picks 1-40).
4. Tankathon big board - https://www.tankathon.com/big-board ("updated 12 days ago" as of June 10, 2026, approximately May 29; ranks 1-40). (The prospect-stats phase fetched the same board at https://www.tankathon.com/big_board for the top-40 prospect list, ranks, positions, teams.)
5. CBS Sports big board - https://www.cbssports.com/nba/news/2026-nba-draft-big-board-prospect-rankings-withdraw-deadline/ (updated May 28, 2026, ranks 1-20) and https://www.cbssports.com/nba/draft/prospect-rankings/ (ranks 1-28); ranks 29-40 not accessible.
6. Bleacher Report mock draft - https://bleacherreport.com/articles/25262746-2026-nba-mock-draft (updated June 9, 2026; picks 1-40).

Attempted and skipped:
- https://www.nbadraft.net/ranking/bigboard/ - HTTP 403 Forbidden.
- The Athletic - paywalled, skipped without fetching.
- https://www.nba.com/news/yahoo-sports-mock-draft-the-wizards-won-the-lottery-heres-how-every-pick-could-play-out-now - fetch timed out twice; superseded by Yahoo Mock 7.0.

Discovery searches: "2026 NBA Draft big board top 40 prospects June 2026"; "2026 NBA mock draft post-lottery June 2026 ESPN Yahoo Tankathon"; "Kevin O'Connor Yahoo Sports 2026 NBA mock draft Wizards Dybantsa"; "sports.yahoo.com Kevin O'Connor 2026 NBA mock draft all 30 picks".

Processing: `data/raw/build_consensus.py`, raw extracts in `data/raw/consensus_notes.md`, output `data/processed/consensus_board.csv` (45 players).

## Phase 1c - Combine data (accessed 2026-06-10)

Primary data sources (numbers in combine_2026.csv):
- https://web.archive.org/web/2026/https://www.nbadraft.net/2026-nba-draft-combine-measurements/ - Wayback snapshot of NBADraft.net (live page Cloudflare-blocked); full anthropometric table, 75 players; source of all anthro columns.
- https://web.archive.org/web/2026/https://www.nbadraft.net/2026-nba-draft-combine-athleticism-testing/ - Wayback snapshot captured 2026-06-09; full athletic testing table, 78 rows; source of all testing columns. Dashes for Bilodeau, De Larrea, Harris, Kayil, Quaintance, Saunders, Suigo.

Cross-checks and context:
- https://sports.yahoo.com/articles/nba-draft-combine-live-results-200900363.html - independent 73-row measurements table used to cross-validate (published May 12, 2026).
- https://www.espn.com/nba/story/_/id/48751836/2026-nba-draft-combine-prospects-highlights-measurements-standouts-dybantsa-peterson - scrimmage skips (Dybantsa, Peterson, Boozer, most first-rounders; Peat; Carr and Swain Thursday withdrawals); spot-check measurements.
- https://www.espn.com/nba/story/_/id/48694379/2026-nba-draft-combine-preview-players-workouts-watch-chicago-dybantsa-peterson-boozer-wilson and https://www.si.com/nba/draft/newsfeed/nba-announces-73-participants-for-the-2026-nba-draft-combine - attendance context (Juke Harris withdrawal, Kayil and De Larrea unavailable, Quaintance skipping testing post-ACL, Saunders ACL tear).
- https://sports.yahoo.com/articles/2026-nba-draft-combine-full-172747601.html - G League Draft Combine call-up route note.
- https://bleacherreport.com/articles/25427241-cameron-boozer-nba-combine-2026-measurements-highlights-results-latest-mock-draft-landing-spots and https://bleacherreport.com/articles/25427014-winners-and-losers-2026-nba-combine-measurements-and-scrimmages - search-result snippets; Boozer 252.8 lbs, Mara 7'3"/9'9", vert spot-checks.

Attempted but unusable:
- https://stats.nba.com/stats/draftcombinestats?LeagueID=00&SeasonYear=2025-26 - timed out on every attempt; no Wayback snapshot.
- https://www.nba.com/stats/draft/combine-anthro - client-side app shell, no embedded data.
- https://www.nbadraft.net/2026-nba-draft-combine-measurements/ (live) - HTTP 403 / Cloudflare challenge.
- https://basketball.realgm.com/nba/draft/combine/2026 - 403 / page not found.
- https://www.babcockhoops.com/post/2026-nba-draft-combine-measurements-height-weight-wingspan-and-standing-reach - fetched but the table itself was not in the page content.
- https://forums.realgm.com/boards/viewtopic.php?t=2292017 and ?f=25&t=2290595 - both threads cover the 2023 combine, not 2026.

## Phase 1d - Top-40 prospect stats (all URLs fetched 2026-06-10)

Prospect list:
- https://www.tankathon.com/big_board - top-40 prospect list, ranks, positions, teams (see Phase 1b; combine-style heights/weights/ages used only as cross-checks).

Sports-Reference player pages (2025-26 per-game + advanced stats, listed height/weight, position, class; one page per prospect):
- https://www.sports-reference.com/cbb/players/aj-dybantsa-1.html
- https://www.sports-reference.com/cbb/players/aday-mara-2.html
- https://www.sports-reference.com/cbb/players/alex-karaban-1.html
- https://www.sports-reference.com/cbb/players/allen-graves-2.html
- https://www.sports-reference.com/cbb/players/baba-miller-1.html
- https://www.sports-reference.com/cbb/players/bennett-stirtz-1.html
- https://www.sports-reference.com/cbb/players/brayden-burries-1.html
- https://www.sports-reference.com/cbb/players/caleb-wilson-1.html
- https://www.sports-reference.com/cbb/players/cameron-boozer-3.html
- https://www.sports-reference.com/cbb/players/cameron-carr-2.html
- https://www.sports-reference.com/cbb/players/chris-cenac-jr-1.html
- https://www.sports-reference.com/cbb/players/christian-anderson-2.html
- https://www.sports-reference.com/cbb/players/dailyn-swain-2.html
- https://www.sports-reference.com/cbb/players/darius-acuff-jr-1.html
- https://www.sports-reference.com/cbb/players/darryn-peterson-1.html
- https://www.sports-reference.com/cbb/players/ebuka-okorie-1.html
- https://www.sports-reference.com/cbb/players/hannes-steinbach-1.html
- https://www.sports-reference.com/cbb/players/henri-veesaar-1.html
- https://www.sports-reference.com/cbb/players/isaiah-evans-1.html
- https://www.sports-reference.com/cbb/players/jaden-bradley-1.html
- https://www.sports-reference.com/cbb/players/jayden-quaintance-1.html
- https://www.sports-reference.com/cbb/players/joshua-jefferson-1.html
- https://www.sports-reference.com/cbb/players/keaton-wagler-1.html
- https://www.sports-reference.com/cbb/players/kingston-flemings-1.html
- https://www.sports-reference.com/cbb/players/koa-peat-1.html
- https://www.sports-reference.com/cbb/players/labaron-philon-1.html
- https://www.sports-reference.com/cbb/players/meleek-thomas-1.html
- https://www.sports-reference.com/cbb/players/mikel-brown-jr-1.html
- https://www.sports-reference.com/cbb/players/morez-johnson-jr-1.html
- https://www.sports-reference.com/cbb/players/nate-ament-1.html
- https://www.sports-reference.com/cbb/players/richie-saunders-1.html
- https://www.sports-reference.com/cbb/players/ryan-conwell-1.html
- https://www.sports-reference.com/cbb/players/tarris-reed-jr-1.html
- https://www.sports-reference.com/cbb/players/trevon-brazile-1.html
- https://www.sports-reference.com/cbb/players/ugonna-onyenso-1.html
- https://www.sports-reference.com/cbb/players/yaxel-lendeborg-1.html
- https://www.sports-reference.com/cbb/players/zuby-ejiofor-1.html

RealGM player pages (birthdates for all; full international stats for Lopez, Suigo, De Larrea):
- https://basketball.realgm.com/player/AJ-Dybantsa/Summary/186435
- https://basketball.realgm.com/player/Aday-Mara/Summary/177830
- https://basketball.realgm.com/player/Alex-Karaban/Summary/151218
- https://basketball.realgm.com/player/Allen-Graves/Summary/217588
- https://basketball.realgm.com/player/Baba-Miller/Summary/165593
- https://basketball.realgm.com/player/Bennett-Stirtz/Summary/201012
- https://basketball.realgm.com/player/Brayden-Burries/Summary/200247
- https://basketball.realgm.com/player/Caleb-Wilson/Summary/200430
- https://basketball.realgm.com/player/Cameron-Boozer/Summary/184287
- https://basketball.realgm.com/player/Cameron-Carr/Summary/196892
- https://basketball.realgm.com/player/Chris-Cenac-Jr/Summary/198525
- https://basketball.realgm.com/player/Christian-Anderson-Jr/Summary/187435
- https://basketball.realgm.com/player/Dailyn-Swain/Summary/192066
- https://basketball.realgm.com/player/Darius-Acuff-Jr/Summary/216187
- https://basketball.realgm.com/player/Darryn-Peterson/Summary/196886
- https://basketball.realgm.com/player/Ebuka-Okorie/Summary/193635
- https://basketball.realgm.com/player/Hannes-Steinbach/Summary/218597
- https://basketball.realgm.com/player/Henri-Veesaar/Summary/147126
- https://basketball.realgm.com/player/Isaiah-Evans/Summary/180095
- https://basketball.realgm.com/player/Jaden-Bradley/Summary/117540
- https://basketball.realgm.com/player/Jayden-Quaintance/Summary/199617
- https://basketball.realgm.com/player/Joshua-Jefferson/Summary/151416
- https://basketball.realgm.com/player/Karim-Lopez/Summary/199566 - birthdate, height/weight, 2025-26 NBL per-game stats and season totals (TS% computed from totals)
- https://basketball.realgm.com/player/Keaton-Wagler/Summary/242991
- https://basketball.realgm.com/player/Kingston-Flemings/Summary/216043
- https://basketball.realgm.com/player/Koa-Peat/Summary/180367
- https://basketball.realgm.com/player/Labaron-Philon-Jr/Summary/200450
- https://basketball.realgm.com/player/Luigi-Suigo/Summary/201784 - birthdate, height/weight, 2025-26 ABA per-game stats and season totals (TS% computed from totals)
- https://basketball.realgm.com/player/Meleek-Thomas/Summary/196884 - birthdate (also confirmed via a WebSearch result summary citing this page)
- https://basketball.realgm.com/player/Mikel-Brown-Jr/Summary/198014
- https://basketball.realgm.com/player/Morez-Johnson-Jr/Summary/194003
- https://basketball.realgm.com/player/Nate-Ament/Summary/216549
- https://basketball.realgm.com/player/Richie-Saunders/Summary/139115
- https://basketball.realgm.com/player/Ryan-Conwell/Summary/199681
- https://basketball.realgm.com/player/Sergio-De-Larrea/Summary/175825 - birthdate, height/weight, 2025-26 EuroLeague/ACB per-game stats and season totals (TS% computed from totals)
- https://basketball.realgm.com/player/Tarris-Reed-Jr/Summary/176072
- https://basketball.realgm.com/player/Trevon-Brazile/Summary/175965
- https://basketball.realgm.com/player/Ugonna-Onyenso/Summary/192946
- https://basketball.realgm.com/player/Yaxel-Lendeborg/Summary/177627
- https://basketball.realgm.com/player/Zuby-Ejiofor/Summary/176053

Index / discovery pages:
- https://basketball.realgm.com/nba/draft/prospects/stats - RealGM draft prospect stats index (player page URLs/IDs).
- https://basketball.realgm.com/international/league/5/Australian-NBL/team/407/New-Zealand/stats - NZ Breakers team page (Karim Lopez's RealGM ID).

Injury reporting (via WebSearch result summaries, 2026-06-10):
- https://www.espn.com/mens-college-basketball/story/_/id/47018644/kansas-peterson-hamstring-not-expected-long-self-says and https://abcnews.go.com/Sports/wireStory/kansas-star-freshman-darryn-peterson-hamstring-injury-evaluated-127658049 - Peterson hamstring, missed games Nov-Dec 2025.
- https://www.espn.com/mens-college-basketball/story/_/id/48124467/caleb-wilson-injury-impact-unc-duke-ncaa-tournament-nba-draft and https://www.nba.com/news/north-carolina-star-caleb-wilson-breaks-right-thumb-in-practice-and-is-out-for-the-season and https://dailytarheel.com/article/sports-mens-basketball-caleb-wilson-out-for-season-march-2026-20260306 - Wilson hand injuries, season-ending broken right thumb.
- https://www.espn.com/mens-college-basketball/story/_/id/48240538/louisville-star-freshman-mikel-brown-usf and https://www.cbssports.com/college-basketball/news/louisville-freshman-mikel-brown-out-ncaa-tournament-opener-south-florida/ - Mikel Brown Jr. lower back injury, 14 games missed.
- https://www.on3.com/teams/kentucky-wildcats/news/jayden-quaintance-opens-up-on-shutdown-that-ended-kentucky-career-after-four-games/ - Quaintance knee shutdown after 4 games.
- https://byucougars.com/news/2026/02/15/richie-saunders-suffers-season-ending-injury and https://www.espn.com/mens-college-basketball/story/_/id/47941092/byu-star-richie-saunders-suffers-season-ending-torn-acl - Saunders torn ACL (Feb 14, 2026).

Cross-check searches:
- WebSearch result summaries (RealGM/Valencia Basket) - De Larrea ACB stats cross-check and Liga Endesa Best Young Player award (https://www.valenciabasket.com/en/sergio-de-larrea-202526-liga-endesa-best-young-player).

## Phase 1e - Team context (accessed 2026-06-10)

Draft order and lottery: see Phase 1a (tankathon.com/full_draft, cbssports.com draft-order-lottery-odds, nba.com lottery-result snippet, nba.com draft-order timeout).

2025-26 standings and playoffs:
- https://www.landofbasketball.com/yearbyyear/2025_2026_standings.htm - complete final standings, all 30 teams (fetched).
- https://en.wikipedia.org/wiki/2026_NBA_playoffs - play-in results and playoff bracket (fetched; some round labels garbled, reconciled with the sources below).
- https://www.nba.com/playoffs/2026/west-semifinal-1 and https://www.basketball-reference.com/playoffs/2026-nba-western-conference-semifinals-lakers-vs-thunder.html - Thunder swept Lakers; Lakers beat Houston in round one (search snippets).
- https://sports.yahoo.com/nba/article/knicks-vs-spurs-2026-nba-finals-game-4-start-time-schedule-tv-channel-where-to-watch-and-more-180017917.html - Knicks-Spurs Finals, NYK leads 2-1 entering Game 4 on June 10 (search snippet).
- https://www.espn.com/nba/story/_/id/48419498/... - Spurs beat OKC in 7 in the WCF; Knicks swept Cleveland in the ECF (search snippet).
- https://sports.yahoo.com/nba/article/76ers-complete-comeback-against-jayson-tatum-less-celtics-in-game-7-setting-up-clash-with-knicks-020403118.html - Sixers' 3-1 comeback over Boston (search snippet).
- https://www.nbcsportsboston.com/nba/boston-celtics/first-round-exit-76ers-offseason-moves/786985/ - Celtics first-round collapse context (search snippet).

Trades and roster movement:
- https://www.hoopsrumors.com/2026/02/2026-nba-trade-deadline-recap.html - definitive deadline recap (fetched): Harden to CLE / Garland to LAC; AD + DLo + Hardy + Exum to WAS; JJJ to UTA; Porzingis to GSW; Zubac to IND; Coby White to CHA; Sexton + Dieng to CHI; Vucevic to BOS; 28 trades / 73 players.
- https://www.espn.com/nba/story/_/id/47545290/sources-hawks-trading-trae-young-wizards-mccollum-kispert and https://www.nba.com/news/hawks-trade-trae-young-to-wizards-for-cj-mccollum-corey-kispert - Trae Young to Washington, January 2026 (search snippets).
- https://www.espn.com/nba/story/_/id/47840423/sources-clippers-trading-center-ivica-zubac-pacers and https://www.cbssports.com/nba/news/ivica-zubac-trade-grades-pacers-clippers-lottery/ - Zubac trade structure and pick protections (search snippets).

Team situations:
- https://sports.yahoo.com/nba/article/giannis-antetokounmpo-reportedly-told-bucks-to-trade-him-multiple-times-during-teams-disastrous-2025-26-season-124444551.html and https://www.cbssports.com/nba/news/giannis-antetokounmpo-trade-rumors-bucks-draft-lottery/ - Bucks 32-50, Giannis trade demands (search snippets).
- https://www.espn.com/nba/story/_/id/47841699/grizzlies-keep-star-ja-morant-amid-lukewarm-trade-market and https://www.espn.com/nba/story/_/id/47561697/grizzlies-entertaining-ja-morant-trade-offers-sources-say - Morant trade status (search snippets).
- https://roundtable.io/sports/nba/wizards/news/anthony-davis-trae-young-to-miss-rest-of-wizards-2025-26-season and https://www.si.com/nba/wizards/onsi/wizards-2025-26-player-grades-alex-sarr-01kprma38dx3 - Wizards 17-65 context (search snippets).
- https://www.slcdunk.com/jazz-analysis/67988/who-were-the-most-improved-utah-jazz-players-in-2025-26 and https://www.deseret.com/sports/2026/03/22/utah-jazz-lauri-markkanen-keyonte-george-injuries/ - Jazz 22-60 context (search snippets).
- https://fadeawayworld.net/nba-trade-rumors/sacramento-kings/kings-preparing-full-rebuild-expected-explore-trades-3-all-stars and https://roundtable.io/sports/nba/kings/players/kings-may-keep-lavine-despite-plans-around-sabonis-led-core - Kings rebuild (search snippets).
- https://www.si.com/nba/mavericks/onsi/grading-cooper-flagg-2025-26-season-dallas-mavericks- and https://www.nba.com/news/kyrie-irving-wont-return-2025-26-season - Flagg 20.2/6.6/4.5, Kyrie out (search snippets).
- https://chicago.suntimes.com/bulls/2026/03/07/... and pippenainteasy.com - Bulls 31-51, Giddey, Buzelis (search snippets).
- https://www.nba.com/news/2025-26-season-preview-bkn and NetsDaily - Nets young core context (search snippets).
- https://basketnews.com/news-245354-lamelo-ball-gets-real-about-hornets-play-in-loss-season-end-it-hurts-a-lot.html and https://en.wikipedia.org/wiki/LaMelo_Ball - Hornets 44-38, play-in loss (search snippets).
- https://lakersnation.com/lebron-james-free-agency-lakers-cavs-or-retirement/ , https://www.upi.com/Sports_News/NBA/2026/05/12/Lakers-LeBron-James-uncertain-NBA-future/2751778583677/ and https://www.cbssports.com/nba/news/lebron-james-free-agency-timeline-priorities/ - LeBron free agency (search snippets).
- https://www.theringer.com/2026/02/03/nba/jaren-jackson-jr-trade-utah-jazz-lauri-markkanen-2026-nba-draft - Jazz post-JJJ outlook (search snippet).

Cap situations:
- https://www.spotrac.com/news/_/id/3290/updated-2026-cap-space-and-spending-power-projections - cap space projections (search snippet; direct fetch returned 403). Exact tax/apron positions marked UNVERIFIED in team_context.md where no June 2026 source was found.

Draft tendencies note: last-3-drafts tendencies (2023-2025) compiled from pre-2026 knowledge of completed drafts, not from a June 2026 source.

## Phase 2a - Historical draft dataset, classes 2000-2021 (fetched 2026-06-10)

All fetches with a browser-like User-Agent (Chrome 124 on macOS) and 3.5 s delays. Full request log in `data/raw/historical/fetch_log.txt`. Scripts: `src/scrape_bbr_draft.py`, `src/scrape_bbr_player_index.py`, `src/fetch_combine_and_allstars.py`, `src/build_historical.py`.

1. Basketball-Reference draft pages - URL pattern `https://www.basketball-reference.com/draft/NBA_{YYYY}.html` for YYYY in 2000..2021 (22 pages). Every pick both rounds, drafting team, college, career-to-date totals (G, MP, WS, WS/48, BPM, VORP), actual draft dates. Snapshots in `data/raw/historical/bbr_draft_{YYYY}.html`; parsed to `bbr_draft_2000_2021.csv` (1309 rows). One transient HTTP 403 on the first request, recovered after a single 15 s backoff.
2. Basketball-Reference player index pages - `https://www.basketball-reference.com/players/{a..z}/` (26 pages, 5416 rows). Birth dates, listed roster height/weight per player slug. Parsed to `bbr_player_index.csv`; drafted players who never appeared in the NBA have no birthdate (~12% of rows).
3. NBA Draft Combine anthropometrics - primary source `stats.nba.com/stats/draftcombineplayeranthro` UNREACHABLE (curl timeouts, 2026-06-10). Fallback used: public GitHub snapshot of that exact API, `https://raw.githubusercontent.com/BryanDfor3/nba-draft-combine-command-center/HEAD/data/nba_draft_combine_data.csv` (repo BryanDfor3/nba-draft-combine-command-center; 1788 rows, combine seasons 2000-2025). Snapshot at `data/raw/historical/nba_draft_combine_anthro.csv`. Matching by normalized name + draft year with prior-year fallback (16 players); ambiguous duplicates excluded; nothing imputed.
4. All-Star flag - https://en.wikipedia.org/wiki/List_of_NBA_All-Stars (fetched 2026-06-10), all 466 players ever selected with selection years. Snapshot `data/raw/historical/wikipedia_allstars.html`, parsed to `allstars.csv`; name-collision logic rejects same-name false positives.

Known limitations: height_in mixes combine barefoot height with BBR listed height (387 flagged rows); college_or_intl blank for non-college draftees; career outcome columns blank for the ~12% who never played.

## Phase 2b - Historical college stats enrichment (fetched 2026-06-10)

Script `src/enrich_college_stats.py` (idempotent, cached). Output `data/processed/historical_enriched.csv`; match decisions in `data/raw/historical/college/match_log.md`.

1. Barttorvik bulk player-season data (draft classes 2009-2021) - barttorvik.com bulk getgamestats/playerstat endpoint, saved as `data/raw/historical/college/torvik_players_2009_2021.csv` (61,061 player-season rows, downloaded 2026-06-10). Name-normalized matching with documented fallbacks and two manual aliases (Trey Thompkins, Dewan Hernandez). Spot-checked against public season lines (Zion Williamson, Curry, Davis, Trae Young, Hield), all match.
2. Sports-Reference college pages (draft classes 2000-2008, FIRST-ROUND picks only) - `https://www.sports-reference.com/cbb/players/{slug}-{n}.html`, n=1..4 tried until school and final season match. Snapshots in `data/raw/historical/college/sref/`. curl with desktop Chrome UA (generic fetcher was 403'd), 3.5 s between requests, backoff on 403. Scope cut (documented in historical_coverage.md): 2000-2008 second-round picks not fetched.

Non-NCAA players get blank ncaa_* columns and a "non-NCAA" note; non-D1 colleges logged as failures, never imputed.

## Phase 3 - Modeling (2026-06-10)

No external data fetched. All inputs are project-internal processed files: `historical_enriched.csv`, `prospect_stats_2026.csv`, `combine_2026.csv`, `consensus_board.csv` (provenance in the phases above).

Code and outputs: `src/model_common.py`, `src/train_models.py` (LODCO CV, 22 folds by draft year; baselines; ridge/lasso/HistGB regression; multinomial tier classifier; bust logistic; permutation importance; calibration), `src/apply_2026.py` (2026 features, bootstrap predictions); `models/tier_definitions.md`, `models/iterations.md`, `models/metrics_*.json`, `models/cv_oof_predictions.csv`, `models/predictions_2026.csv`; figures feature_importance.png, calibration_bust.png, pred_vs_consensus.png.

Reproducibility: Python 3.11.8, scikit-learn 1.4.2, pandas 2.1.0, numpy 1.26.4, matplotlib 3.10.8; seed 42 everywhere; bootstrap 200 reps over draft classes.

Methodological notes: draft pick slot used as the market-consensus proxy baseline for 2000-2021 (no archived multi-outlet boards); 2026 consensus ranks used only for comparison plots, never as model input; 2026 STL%/BLK% approximated from per-game stats (formulas in src/apply_2026.py); 2020/2021 outcomes are 4-6 seasons by design.

## Phase 4 - Film study (2026-06-10)

Note: fragment logs exist only for the resumed sessions below (sources_film_resume.md, sources_film_resume2.md). The earlier film-group fragments (sources_film_group1.md through sources_film_group4.md) were not found on disk; sources for those players' clips are reconstructable from `film/clips/` filenames and `film/notes/`.

Resumed session 1 (Wilson, Burries, Philon, Graves), source videos:
- Caleb Wilson (UNC) - https://www.youtube.com/watch?v=QVZgBTs4gMg (ACC Digital Network season highlights; 724 frames).
- Brayden Burries (Arizona) - https://www.youtube.com/watch?v=BIKJpih0YOA (ESPN broadcast highlights) and https://www.youtube.com/watch?v=RPNrEl-xxDU (Big 12 Studios "Inside the Edge"; 703 frames total).
- Labaron Philon Jr. (Alabama) - https://www.youtube.com/watch?v=Ah8wQ47Nql4 ("League Him" freshman-season compilation; 286 frames).
- Allen Graves (Santa Clara) - https://www.youtube.com/watch?v=7Wj0fFSJiRk (season scoring compilation; 1476 frames).

Resumed session 1, scouting sources cited in notes:
- Wilson: https://bleacherreport.com/articles/25397915-caleb-wilson-declares-2026-nba-draft-scouting-report-and-projected-landing-spot-unc-star ; https://www.babcockhoops.com/post/2026-nba-draft-caleb-wilson-scouting-report ; https://www.si.com/nba/draft/newsfeed/nba-draft-scouting-report-north-carolina-caleb-wilson ; https://floorandceiling.substack.com/p/caleb-wilson-scouting-report
- Burries: https://www.si.com/nba/draft/newsfeed/nba-draft-scouting-report-arizona-guard-brayden-burries ; https://www.babcockhoops.com/post/2026-nba-draft-brayden-burries-scouting-report ; https://sports.yahoo.com/articles/brayden-burries-nba-mock-draft-231334190.html
- Philon: https://www.babcockhoops.com/post/2026-nba-draft-labaron-philon-scouting-report ; https://sports.yahoo.com/articles/labaron-philon-jr-nba-mock-212151698.html ; https://roundtable.io/sports/ncaa/alabama/news/alabama-s-labaron-philon-invited-to-attend-2026-nba-draft
- Graves: https://sportsbusinessclassroom.com/scouting-santa-clara-forward-allen-graves/ ; https://www.babcockhoops.com/post/2026-nba-draft-allen-graves-scouting-report ; https://atthehive.com/2026/06/08/charlotte-hornets-prospect-scouting-report-allen-graves/

Resumed session 1 search queries: "Caleb Wilson North Carolina 2026 NBA draft scouting report"; "Brayden Burries Arizona 2026 NBA draft scouting report"; "Labaron Philon Alabama 2026 NBA draft scouting report"; "Allen Graves Santa Clara basketball forward scouting".

Resumed session 2 (Wagler, Ament, Carr), videos downloaded (yt-dlp, <=480p, all kept under 100 MB):
- Keaton Wagler - https://www.youtube.com/watch?v=cQPlLIaHobM (Illinois mid-season highlights; 514 frames).
- Nate Ament - https://www.youtube.com/watch?v=oxU5KKPlCu0 (Tennessee mid-season highlights; 352 frames).
- Cameron Carr - https://www.youtube.com/watch?v=Jmk5qDZUz98 (Big 12 Studios midseason highlights; 664 frames).

Resumed session 2, candidate videos surfaced by search but not downloaded:
- Wagler: https://www.youtube.com/watch?v=jlp5Gs-0kkY ; https://www.youtube.com/watch?v=p5ApErISBso ; https://www.youtube.com/watch?v=3s6dobWxP38 ; https://www.youtube.com/watch?v=IQWKck8nStA
- Ament: https://www.youtube.com/watch?v=MPCGL4VIcuQ ; https://www.youtube.com/watch?v=k1pEvPNsWKI ; https://www.youtube.com/watch?v=sBdE07njnL8 ; https://www.youtube.com/watch?v=_X4ep1yAtRg
- Carr: https://www.youtube.com/watch?v=bGC1xId8Vl8 ; https://www.youtube.com/watch?v=-dMNf3NZ1O8 ; https://www.youtube.com/watch?v=IUuvKk30ymU

Resumed session 2, scouting sources cited in notes:
- Wagler: https://www.babcockhoops.com/post/2026-nba-draft-keaton-wagler-scouting-report (quotes verified by fetch 2026-06-10) ; https://bleacherreport.com/articles/25416874-illinois-keaton-wagler-declares-2026-nba-draft-latest-br-mock-draft-projection ; https://fansided.com/nba/nba-draft-scouting-report-keaton-wagler-is-a-lottery-prospect-for-the-modern-age
- Ament: https://floorandceiling.substack.com/p/nate-ament-scouting-report (quotes verified by fetch 2026-06-10) ; https://www.si.com/nba/draft/prospect-profiles/nba-draft-scouting-report-tennessee-nate-ament ; https://www.babcockhoops.com/post/2026-nba-draft-nate-ament-scouting-report
- Carr: https://www.babcockhoops.com/post/2026-nba-draft-cameron-carr-scouting-report (quotes verified by fetch 2026-06-10) ; https://www.si.com/nba/draft/newsfeed/nba-draft-scouting-report-baylor-wing-cameron-carr ; https://atthehive.com/2026/05/20/charlotte-hornets-prospect-scouting-report-cameron-carr/

Resumed session 2 search queries: "Keaton Wagler Illinois highlights 2025-26 YouTube scouting video"; "Nate Ament Tennessee highlights 2025-26 YouTube"; "Cameron Carr Baylor highlights 2025-26 YouTube"; "Keaton Wagler Illinois 2026 NBA draft scouting report strengths weaknesses"; "Nate Ament Tennessee 2026 NBA draft scouting report shooting frame"; "Cameron Carr Baylor 2026 NBA draft scouting report wing shooter".

## Phase 5 - Historical comps engine (2026-06-10)

No web access used. Script `src/comps_engine.py` (deterministic). Inputs entirely on-disk: `historical_enriched.csv` (1,309 drafted players 2000-2021), `prospect_stats_2026.csv`, `combine_2026.csv`, `consensus_board.csv`. Candidate pool 781 NCAA players after filters. Weighted z-scored feature space (15 features; age 1.50, height 1.25, TS% 1.25, usage 1.25 the heaviest), missing-data distance correction, 60% minimum shared feature weight. International prospects (Lopez, De Larrea, Suigo) comped on a restricted anthro/age/basic-stats set and flagged LOW confidence. Floor/median/ceiling = 25th/50th/90th percentile cohort career VORP; bust = career_games < 100. Outputs `comps_2026.csv`, `comps_2026_detail.json`, `figures/comp_cohorts_top10.png`. v1 weights spot-verified on Boozer, Dybantsa, Peterson, Mara and shipped unchanged.

## Phase 6 - Team fit and mock draft

No fragment file (sources_teamfit.md not found). Per `data/processed/team_fit.md` and `data/processed/mock_draft.csv`, the phase worked from the Phase 1 team-context sources and project-internal files.

## Phase 7 - Dossiers (collected 2026-06-10)

All dossier content written from the project's processed data files. The single web-sourced exception, permitted by the phase instructions, is Braden Smith (outside the stats top-40 collection), used in dossiers/honorable_mentions.md entry 35; retrieved via WebSearch on June 10, 2026 (two lookups):
- https://www.sports-reference.com/cbb/players/braden-smith-1.html - career/season stats page (39 GP, 14.3 ppg, 8.8 apg, 3.5 rpg, 1.7 spg, 44.0 FG%, 36.2 3P%, 82.5 FT%; NCAA all-time assists leader, 1,103; two-time consensus first-team All-American).
- https://www.espn.com/mens-college-basketball/story/_/id/47496967/braden-smith-sets-big-ten-assist-record-eyes-d1-mark - assist record context.
