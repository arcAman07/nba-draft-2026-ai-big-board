# Historical dataset coverage (classes 2000-2021)

Built 2026-06-10 by src/build_historical.py. Total rows: 1309 (both rounds, one per drafted player).

## Per-year row counts and feature coverage (%)

| year | rows | age | height | weight | wingspan | reach | games | WS | WS/48 | BPM | VORP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 58 | 86 | 93 | 93 | 41 | 41 | 86 | 86 | 86 | 86 | 86 |
| 2001 | 57 | 86 | 91 | 91 | 70 | 70 | 86 | 86 | 86 | 86 | 86 |
| 2002 | 57 | 84 | 95 | 95 | 67 | 67 | 84 | 84 | 84 | 84 | 84 |
| 2003 | 58 | 81 | 83 | 83 | 50 | 50 | 81 | 81 | 81 | 81 | 81 |
| 2004 | 59 | 78 | 90 | 90 | 61 | 61 | 78 | 78 | 78 | 78 | 78 |
| 2005 | 60 | 92 | 92 | 92 | 63 | 63 | 92 | 92 | 92 | 92 | 92 |
| 2006 | 60 | 87 | 88 | 88 | 50 | 50 | 87 | 87 | 87 | 87 | 87 |
| 2007 | 60 | 82 | 92 | 92 | 65 | 65 | 82 | 82 | 80 | 80 | 82 |
| 2008 | 60 | 85 | 97 | 97 | 55 | 55 | 85 | 85 | 85 | 85 | 85 |
| 2009 | 60 | 83 | 87 | 87 | 70 | 70 | 83 | 83 | 83 | 83 | 83 |
| 2010 | 60 | 85 | 90 | 90 | 73 | 73 | 85 | 85 | 85 | 85 | 85 |
| 2011 | 60 | 90 | 92 | 92 | 70 | 70 | 90 | 90 | 90 | 90 | 90 |
| 2012 | 60 | 93 | 95 | 95 | 83 | 83 | 93 | 93 | 93 | 93 | 93 |
| 2013 | 60 | 85 | 88 | 88 | 70 | 68 | 85 | 85 | 85 | 85 | 85 |
| 2014 | 60 | 90 | 95 | 95 | 70 | 70 | 90 | 90 | 90 | 90 | 90 |
| 2015 | 60 | 73 | 80 | 80 | 58 | 58 | 73 | 73 | 73 | 73 | 73 |
| 2016 | 60 | 92 | 93 | 93 | 62 | 62 | 92 | 92 | 92 | 92 | 92 |
| 2017 | 60 | 95 | 95 | 95 | 63 | 63 | 95 | 95 | 95 | 95 | 95 |
| 2018 | 60 | 95 | 98 | 98 | 63 | 63 | 95 | 95 | 95 | 95 | 95 |
| 2019 | 60 | 97 | 98 | 98 | 68 | 68 | 97 | 97 | 97 | 97 | 97 |
| 2020 | 60 | 97 | 97 | 97 | 40 | 40 | 97 | 97 | 97 | 97 | 97 |
| 2021 | 60 | 93 | 95 | 95 | 63 | 63 | 93 | 93 | 93 | 93 | 93 |

## Overall column coverage

- year: 100%
- pick: 100%
- player: 100%
- team: 100%
- college_or_intl: 78%
- age_at_draft: 88%
- height_in: 92%
- weight_lbs: 92%
- wingspan_in: 63%
- standing_reach_in: 63%
- career_games: 88%
- career_minutes: 88%
- career_ws: 88%
- career_ws48: 88%
- career_bpm: 88%
- career_vorp: 88%
- allstar: 100%

## Per-decade wingspan / VORP coverage

- 2000-2009: wingspan 59%, VORP 84% (n=589)
- 2010-2019: wingspan 68%, VORP 90% (n=600)
- 2020-2021: wingspan 52%, VORP 95% (n=120)

## Notes

- height_in is combine height without shoes where available; otherwise BBR listed roster height (flagged in notes column).
- college_or_intl is blank where BBR lists no college (international or preps-to-pros players).
- allstar is exact normalized-name match against the Wikipedia all-time All-Star list (career-to-date as of 2026-06-10).
- Career totals are career-to-date from BBR draft pages, fetched 2026-06-10. Blank career columns = never played an NBA game.
- No values were imputed.
