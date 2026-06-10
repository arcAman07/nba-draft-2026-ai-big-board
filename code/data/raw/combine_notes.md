# 2026 NBA Draft Combine, Notes on Attendance, Skips, and Source Discrepancies

Collected 2026-06-10. Combine held May 10-17, 2026 at Wintrust Arena and the Marriott Marquis, Chicago. 73 players received invitations (participation required for invitees per Yahoo Sports); the republished measurement and testing tables contain 78 player rows, so 5 additional participants joined beyond the initial invite list (see below).

## Did not attend at all (invited, no measurements, no testing)

- Juke Harris (Wake Forest) — withdrew from the draft before the combine and returned to college (transferred to Tennessee). Listed in tables with no data.
- Jack Kayil — could not attend, club season still ongoing in Germany. Remained in the draft.
- Sergio de Larrea — could not attend, playing EuroLeague playoffs with Valencia.

No other notable no-shows surfaced in fetched coverage; the consensus top prospects (AJ Dybantsa, Darryn Peterson, Cameron Boozer, Caleb Wilson) all attended and were measured and tested.

## Measured but skipped athletic testing

- Jayden Quaintance — no testing numbers; coming off 2025 ACL tear, per coverage his stock hinges on medicals; he dunked without restriction at his pro day.
- Richie Saunders — no testing numbers; tore his ACL during the BYU season.
- Tyler Bilodeau — measured, no testing numbers recorded; no reason given in fetched sources.
- Luigi Suigo — measured (7'2.75" barefoot, 289.0 lbs, 7'5.5" wingspan, 9'6" reach), no testing numbers recorded; no reason given in fetched sources.

## Skipped scrimmages (per ESPN)

- AJ Dybantsa, Darryn Peterson, Cameron Boozer skipped 5-on-5 entirely, as did "the vast majority of other surefire first-round picks".
- Koa Peat opted not to scrimmage.
- Cameron Carr and Dailyn Swain played Wednesday, then withdrew from Thursday's scrimmages.

## Added participants beyond the initial 73-invite list

Rafael Castro, Jacob Cofie, Bryce Hopkins, Trey Kaufman-Renn, and Aaron Nkrumah appear in the NBADraft.net combine tables but not in Yahoo's published 73-man invite table. Yahoo noted players could earn a spot via the G League Draft Combine held two days earlier, so these are likely call-ups (inference, not explicitly confirmed per player in fetched sources).

## Data not obtainable

- Height with shoes, hand length, hand width, and body fat percent are measured at the combine and live on NBA.com's official stats pages (nba.com/stats/draft/combine-anthro). That page is a client-side app and its API (stats.nba.com/stats/draftcombinestats) timed out from this environment on repeated attempts (curl with browser headers and WebFetch). No Wayback snapshot of the endpoint exists, and no secondary source (Yahoo, ESPN, NBADraft.net, Bleacher Report, Babcock Hoops) republished those columns. Those CSV columns are therefore blank for all players. No standing-vertical/max-vertical/agility data is missing for tested players.

## Source discrepancies

- AJ Dybantsa wingspan: 7'0.5" per NBADraft.net and ESPN, 7'0.25" per Yahoo's table. CSV uses 84.5 in.
- Darius Acuff Jr. wingspan: 6'6.5" per NBADraft.net (and one Yahoo article), 6'7" per Yahoo's live-results table. CSV uses 78.5 in.
- Christian Anderson: 6'1.00" barefoot per NBADraft.net vs 6'0.75" per Yahoo. CSV uses 73.0 in.
- Weights: Yahoo rounds to whole pounds (e.g., Boozer 253); NBADraft.net carries official decimals (252.8, confirmed by Bleacher Report). CSV uses decimal weights from NBADraft.net.
- A search-result summary attributed a "40-inch standing vertical" to Bennett Stirtz "for a frontcourt player"; the full NBADraft.net table shows Stirtz (PG) at 30.5/37.5 and Tobi Lawal (PF) at 40.0 standing / 45.5 max, so that snippet almost certainly garbled Lawal's number. CSV follows the full table.
- An ESPN-article summary mentioned Chris Cenac Jr. with a "41.5-inch standing vertical"; the full table shows 33.0 standing / 37.0 max for Cenac. Treated as a summarization artifact, not used.
- Minor name variants across sources: Ja'Kobi/Jakobi Gillespie, Christian Anderson (Jr.), Mikel Brown (Jr.), Chris Cenac (Jr.), Labaron Philon (Jr.), Morez Johnson (Jr.). CSV uses NBADraft.net spellings.
