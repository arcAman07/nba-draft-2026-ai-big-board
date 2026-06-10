# Sources: historical college stats enrichment

Fetch date: 2026-06-10. Script: `src/enrich_college_stats.py` (idempotent; caches all fetched pages).
Output: `data/processed/historical_enriched.csv`. Match decisions: `data/raw/historical/college/match_log.md`.

## Source 1: Barttorvik bulk player-season data (draft classes 2009-2021)

- File: `data/raw/historical/college/torvik_players_2009_2021.csv` (61,061 player-season rows, seasons 2009-2021, downloaded 2026-06-10 ~04:14 IST by the previous enrichment agent before it was killed; Barttorvik bulk getgamestats/playerstat endpoint, barttorvik.com).
- Matching: normalized name (accents stripped, punctuation removed, Jr/Sr/II/III/IV suffixes dropped) + season year == draft year. Fallbacks, in order: (a) season year == draft year - 1 (player sat out the year before the draft), (b) torvik `pick` column == draft pick + last-name token match (catches nickname differences like Bam Adebayo / Edrice Adebayo). Every fallback use, school mismatch, ambiguity, and failure is logged in match_log.md. Two documented manual aliases: Trey Thompkins -> Howard Thompkins III, Dewan Hernandez -> Dewan Huell (name change).
- Column formulas (torvik fields):
  - ncaa_games = GP; ncaa_mpg = mp; ncaa_ppg = pts; ncaa_rpg = treb; ncaa_apg = ast (all per-game)
  - ncaa_fg_pct = (twoPM+TPM)/(twoPA+TPA) (torvik stores season-total makes/attempts, no direct FG%)
  - ncaa_3p_pct = TP_per (blank if 0 attempts); ncaa_3pa_pg = TPA/GP; ncaa_ft_pct = FT_per (blank if 0 FTA)
  - ncaa_ts_pct = TS_per/100 (torvik stores TS as a percent; converted to a fraction for consistency with the other shooting columns)
  - ncaa_usg_pct = usg; ncaa_ast_pct = AST_per; ncaa_tov_pct = TO_per; ncaa_stl_pct = stl_per; ncaa_blk_pct = blk_per (kept in percent form, e.g. 24.5)
  - ncaa_obpm = obpm; ncaa_bpm = bpm (torvik's college BPM model)
- Spot-checked against public season lines: Zion Williamson 2019 (22.6/8.9/2.1, .680 FG), Stephen Curry 2009 (28.6 ppg), Anthony Davis 2012 (14.2/10.4), Trae Young 2018 (27.4 ppg/8.7 apg), Buddy Hield 2016 (25.0 ppg). All match.

## Source 2: Sports-Reference college pages (draft classes 2000-2008, FIRST-ROUND picks only)

- URLs: https://www.sports-reference.com/cbb/players/{slug}-{n}.html, slug from normalized player name, n=1..4 tried until the page's school matches historical.csv's college and the final season ends on/before the draft year (prevents same-name mismatches). Pages snapshotted to `data/raw/historical/college/sref/`.
- Politeness: curl with a desktop Chrome User-Agent (a generic fetcher was 403'd earlier on 2026-06-10; curl with browser UA confirmed working), 3.5 s between requests, 90 s/240 s backoff on 403, hard abort after 6 consecutive 403s.
- Stats from the per-game table (`players_per_game`, data-stat fields g/mp_per_g/pts_per_g/...). TS%, TOV% taken from the `players_advanced` table where present for that season; ncaa_ts_pct otherwise computed as pts/(2*(fga+0.44*fta)) (0.44 FT coefficient). usage/ast%/stl%/blk%/obpm/bpm are blank for this era unless present in the advanced table (Sports-Reference CBB advanced coverage is sparse before 2009-10).
- Scope cut (by design, documented in historical_coverage.md): 2000-2008 SECOND-ROUND picks were not fetched (rate-limit budget); their ncaa_* columns are blank. First round defined as picks 1-29 for 2000-2004 (29 picks: 29 teams / forfeited 2004 pick), 1-30 for 2005-2008.

## Non-NCAA players

Rows with blank `college_or_intl` (internationals, preps-to-pros, G League/overseas routes) get blank ncaa_* columns and the note "non-NCAA" appended to `notes`. Non-D1 colleges (e.g. junior colleges) are not in either source; they are logged as failures in match_log.md, never imputed.

## Incidents

- (filled in after the run; see match_log.md for per-player detail)
