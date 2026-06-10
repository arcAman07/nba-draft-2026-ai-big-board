# Sources, historical draft dataset (classes 2000-2021)

All fetches performed 2026-06-10 with a browser-like User-Agent
(Chrome 124 on macOS) and 3.5 s delays between requests. Full request log
in `data/raw/historical/fetch_log.txt`. Scripts in `src/`
(scrape_bbr_draft.py, scrape_bbr_player_index.py,
fetch_combine_and_allstars.py, build_historical.py).

## 1. Basketball-Reference draft pages (picks, teams, college, career outcomes)

- URL pattern: `https://www.basketball-reference.com/draft/NBA_{YYYY}.html`
  for YYYY in 2000..2021 (22 pages).
- Provides: every pick both rounds, drafting team, college, career-to-date
  totals (G, MP, WS, WS/48, BPM, VORP), and the actual draft date
  (parsed from page text, used for exact age-at-draft; includes the
  Nov 18, 2020 COVID-delayed draft and the Jul 29, 2021 draft).
- Raw snapshots: `data/raw/historical/bbr_draft_{YYYY}.html`,
  parsed to `bbr_draft_2000_2021.csv` (1309 rows) and `bbr_draft_dates.csv`.
- Rate-limit incidents: one transient HTTP 403 on the first request
  (NBA_2000.html) at 04:01:52 local; recovered after a single 15 s backoff.
  No further blocks across all 48 BBR requests.

## 2. Basketball-Reference player index pages (birthdates, listed ht/wt)

- URL pattern: `https://www.basketball-reference.com/players/{a..z}/`
  (26 pages, 5416 player rows).
- Provides: birth date, listed roster height/weight per BBR player slug.
  Used instead of ~1300 per-player page fetches to stay polite.
- Raw snapshots: `data/raw/historical/bbr_players_{letter}.html`,
  parsed to `bbr_player_index.csv`. Joined to draft rows by player slug,
  so drafted players who never appeared in the NBA have no birthdate
  (blank age_at_draft, ~12% of rows).

## 3. NBA Draft Combine anthropometrics (height w/o shoes, weight, wingspan, standing reach)

- Primary recommended source `stats.nba.com/stats/draftcombineplayeranthro`
  was UNREACHABLE from this network (curl timeouts after 45 s on
  2026-06-10, headers per nba_api conventions). Documented switch:
- Fallback used: public GitHub snapshot of that exact API, pulled via the
  `nba_api` package by the repo author:
  `https://raw.githubusercontent.com/BryanDfor3/nba-draft-combine-command-center/HEAD/data/nba_draft_combine_data.csv`
  (repo: BryanDfor3/nba-draft-combine-command-center, script
  `scripts/01_nba_draft_data_pull.py` in that repo shows the API pull).
  1788 rows, combine seasons 2000-2025, columns include HEIGHT_WO_SHOES,
  WEIGHT, WINGSPAN, STANDING_REACH (inches/lbs).
- Raw snapshot: `data/raw/historical/nba_draft_combine_anthro.csv`.
- Matching: normalized player name + draft year, fallback to draft year
  minus 1 (16 players matched a prior-year combine, flagged in notes).
  Ambiguous duplicate (name, season) combine rows were excluded rather
  than guessed. Combine coverage is structurally incomplete (many lottery
  picks and internationals skip measurement); nothing was imputed.

## 4. All-Star flag

- `https://en.wikipedia.org/wiki/List_of_NBA_All-Stars` (fetched
  2026-06-10), table of all 466 players ever selected, with selection
  years. Raw snapshot: `data/raw/historical/wikipedia_allstars.html`,
  parsed to `allstars.csv`.
- Flag logic: normalized exact name match AND first All-Star selection
  year strictly after draft year (rejects same-name collisions, e.g.
  2006 draftee Bobby Jones vs the 1970s All-Star, 2008 draftee Patrick
  Ewing vs the Hall of Famer). allstar is career-to-date through the
  2026 All-Star Game.

## Known limitations

- height_in mixes combine barefoot height (preferred) with BBR listed
  roster height where no combine record exists; rows using listed values
  are flagged in the notes column (387 rows).
- college_or_intl is blank for players BBR lists without a college
  (international and preps-to-pros draftees).
- Career outcome columns are blank for the ~12% of draftees who never
  played an NBA game.
