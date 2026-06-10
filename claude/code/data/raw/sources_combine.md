# Sources, 2026 NBA Draft Combine Data Collection

Accessed 2026-06-10.

## Primary data sources (numbers in the CSV)

1. https://web.archive.org/web/2026/https://www.nbadraft.net/2026-nba-draft-combine-measurements/ (Wayback snapshot of NBADraft.net, live page is Cloudflare-blocked)
   Provided: full anthropometric table, 75 players: height without shoes, weight (decimal lbs), wingspan, standing reach. Source of all anthro columns in combine_2026.csv.
2. https://web.archive.org/web/2026/https://www.nbadraft.net/2026-nba-draft-combine-athleticism-testing/ (Wayback snapshot, captured 2026-06-09)
   Provided: full athletic testing table, 78 player rows: position, standing vertical, max vertical, lane agility, shuttle run, 3/4-court sprint. Source of all testing columns in combine_2026.csv. Dashes for Bilodeau, De Larrea, Harris, Kayil, Quaintance, Saunders, Suigo.

## Cross-checks and context

3. https://sports.yahoo.com/articles/nba-draft-combine-live-results-200900363.html
   Provided: independent 73-row measurements table (height, weight, wingspan, reach) used to cross-validate NBADraft.net; blank rows for Juke Harris, Jack Kayil, Sergio de Larrea; note that 73 invitees were required to participate. Published May 12, 2026.
4. https://www.espn.com/nba/story/_/id/48751836/2026-nba-draft-combine-prospects-highlights-measurements-standouts-dybantsa-peterson
   Provided: scrimmage skips (Dybantsa, Peterson, Boozer, most first-rounders; Peat; Carr and Swain Thursday withdrawals); spot-check measurements (Carr 6'4.5"/42.5 max vert, Dybantsa 7'0.5" wingspan and 42.0 max vert, Reed 7'4.25" wingspan, Smith 5'10.25"/166).
5. Web search results (Yahoo/SI/ESPN preview snippets) for attendance context
   Provided: Juke Harris draft withdrawal and transfer to Tennessee; Jack Kayil unavailable (German season); Sergio de Larrea unavailable (Valencia EuroLeague playoffs); Quaintance skipping testing post-ACL; Saunders ACL tear. Key result URLs: https://www.espn.com/nba/story/_/id/48694379/2026-nba-draft-combine-preview-players-workouts-watch-chicago-dybantsa-peterson-boozer-wilson and https://www.si.com/nba/draft/newsfeed/nba-announces-73-participants-for-the-2026-nba-draft-combine
6. https://sports.yahoo.com/articles/2026-nba-draft-combine-full-172747601.html
   Provided: note that non-invitees could earn participation via the G League Draft Combine starting two days earlier (basis for the call-up inference for the 5 extra participants).
7. Search-result snippets from https://bleacherreport.com/articles/25427241-cameron-boozer-nba-combine-2026-measurements-highlights-results-latest-mock-draft-landing-spots and https://bleacherreport.com/articles/25427014-winners-and-losers-2026-nba-combine-measurements-and-scrimmages
   Provided: Boozer 252.8 lbs decimal confirmation, Mara 7'3"/9'9" confirmation, vert spot-checks (Richmond 41.0 max, 10.23 lane agility; Brazile 36.0/41.5; Flemings 40.5 max; Wilson 39.5 max).

## Attempted but unusable

- https://stats.nba.com/stats/draftcombinestats?LeagueID=00&SeasonYear=2025-26 — official NBA API with hand length/width, body fat, height with shoes; timed out on every attempt (curl with full browser headers, WebFetch). No Wayback snapshot exists.
- https://www.nba.com/stats/draft/combine-anthro — fetched HTML is a client-side app shell; no measurement data embedded in __NEXT_DATA__.
- https://www.nbadraft.net/2026-nba-draft-combine-measurements/ (live) — HTTP 403 / Cloudflare challenge; used Wayback snapshot instead.
- https://basketball.realgm.com/nba/draft/combine/2026 — 403 via WebFetch; curl returned a "Page Not Found" page (no 2026 combine table at that path).
- https://www.babcockhoops.com/post/2026-nba-draft-combine-measurements-height-weight-wingspan-and-standing-reach — article fetched but the measurement table itself was not in the page content, narrative highlights only.
- https://forums.realgm.com/boards/viewtopic.php?t=2292017 and ?f=25&t=2290595 — fetched, but both threads cover the 2023 combine, not 2026.
