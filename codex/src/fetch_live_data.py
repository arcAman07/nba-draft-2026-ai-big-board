from __future__ import annotations

import time

import requests

from common import ensure_dirs, fetch_url, nba_stats_get


LIVE_PAGES = [
    {
        "source_id": "nba_official_draft_order_2026",
        "url": "https://www.nba.com/news/2026-nba-draft-order",
        "raw_rel": "live/nba_official_draft_order_2026.html",
        "provided": "Official 2026 draft order, pick owners, traded-pick notes, lottery date/order.",
    },
    {
        "source_id": "tankathon_big_board_2026",
        "url": "https://www.tankathon.com/big-board",
        "raw_rel": "live/tankathon_big_board_2026.html",
        "provided": "External big board, prospect biographical fields, per-game/per-36 and advanced stat display.",
    },
    {
        "source_id": "tankathon_mock_2026",
        "url": "https://www.tankathon.com/mock-draft",
        "raw_rel": "live/tankathon_mock_2026.html",
        "provided": "External mock draft, pick/team context and prospect stat display.",
    },
    {
        "source_id": "rookiescale_consensus_2026",
        "url": "https://www.rookiescale.com/2026-consensus-board/",
        "raw_rel": "live/rookiescale_consensus_2026.html",
        "provided": "External consensus board with ranks, ages, positions, listed measurements and agencies.",
    },
    {
        "source_id": "espn_big_board_2026",
        "url": "https://www.espn.com/nba/story/_/id/46886245/2026-nba-draft-big-board-rankings-top-100-prospects-players",
        "raw_rel": "live/espn_big_board_2026.html",
        "provided": "ESPN top-100 board attempt; used only if HTML exposes ranking data.",
    },
    {
        "source_id": "espn_post_combine_mock_2026",
        "url": "https://www.espn.com/nba/story/_/id/48790115/2026-nba-mock-draft-projecting-60-picks-post-combine-peterson-dybantsa-boozer",
        "raw_rel": "live/espn_post_combine_mock_2026.html",
        "provided": "ESPN post-combine mock draft attempt; used only if HTML exposes pick data.",
    },
    {
        "source_id": "cbs_prospect_rankings_2026",
        "url": "https://www.cbssports.com/nba/draft/prospect-rankings/",
        "raw_rel": "live/cbs_prospect_rankings_2026.html",
        "provided": "CBS prospect rankings attempt; used only if HTML exposes ranking data.",
    },
    {
        "source_id": "cbs_mock_2026",
        "url": "https://www.cbssports.com/nba/draft/mock-draft/",
        "raw_rel": "live/cbs_mock_2026.html",
        "provided": "CBS mock draft attempt; used only if HTML exposes pick data.",
    },
    {
        "source_id": "bleacher_mock_2026",
        "url": "https://bleacherreport.com/articles/25262746-2026-nba-mock-draft",
        "raw_rel": "live/bleacher_mock_2026.html",
        "provided": "Bleacher Report full mock draft attempt; used only if accessible.",
    },
    {
        "source_id": "yahoo_koc_big_board_2026",
        "url": "https://sports.yahoo.com/nba/draft/pre-draft-board/",
        "raw_rel": "live/yahoo_koc_big_board_2026.html",
        "provided": "Yahoo/Kevin O'Connor pre-draft board attempt; used only if accessible.",
    },
    {
        "source_id": "yahoo_big_board_2026_article",
        "url": "https://sports.yahoo.com/articles/2026-nba-draft-big-board-161442173.html",
        "raw_rel": "live/yahoo_big_board_2026_article.html",
        "provided": "Yahoo top-50/best-fits article attempt; used only if accessible.",
    },
    {
        "source_id": "ringer_big_board_2026",
        "url": "https://theringer.com/nba-draft/2026/big-board",
        "raw_rel": "live/ringer_big_board_2026.html",
        "provided": "The Ringer draft guide big board attempt; used only if accessible.",
    },
    {
        "source_id": "nbadraftroom_mock_2026",
        "url": "https://nbadraftroom.com/2026-nba-mock-draft/",
        "raw_rel": "live/nbadraftroom_mock_2026.html",
        "provided": "NBA Draft Room mock draft, measurements, comps and scouting blurbs.",
    },
    {
        "source_id": "nbadraftroom_big_board_8_2026",
        "url": "https://nbadraftroom.com/2026-nba-draft-big-board-8-0/",
        "raw_rel": "live/nbadraftroom_big_board_8_2026.html",
        "provided": "NBA Draft Room Big Board 8.0 and scouting blurbs.",
    },
    {
        "source_id": "nbadraftnet_combine_measurements_2026",
        "url": "https://www.nbadraft.net/2026-nba-draft-combine-measurements/",
        "raw_rel": "live/nbadraftnet_combine_measurements_2026.html",
        "provided": "NBA Draft.net table of 2026 combine measurements.",
    },
    {
        "source_id": "on3_combine_measurements_2026",
        "url": "https://www.on3.com/pro/news/2026-nba-draft-winners-losers-from-combine-measurements-notable-numbers/",
        "raw_rel": "live/on3_combine_measurements_2026.html",
        "provided": "On3 combine measurement notes for cross-checking selected prospects.",
    },
    {
        "source_id": "noceilings_combine_recap_2026",
        "url": "https://www.noceilingsnba.com/p/the-2026-nba-combine-week-recap",
        "raw_rel": "live/noceilings_combine_recap_2026.html",
        "provided": "No Ceilings combine recap and sourced scouting notes where accessible.",
    },
    {
        "source_id": "basketball_reference_2026_standings",
        "url": "https://www.basketball-reference.com/leagues/NBA_2026_standings.html",
        "raw_rel": "live/basketball_reference_2026_standings.html",
        "provided": "2025-26 team records/standings context.",
    },
]


NBA_STATS_ENDPOINTS = [
    ("draftcombineplayeranthro", "NBA combine anthropometrics"),
    ("draftcombinedrillresults", "NBA combine strength and agility testing"),
    ("draftcombinespotshooting", "NBA combine spot shooting drills"),
    ("draftcombinenonstationaryshooting", "NBA combine non-stationary shooting drills"),
    ("draftcombinestats", "NBA combine all-in-one stats table"),
]


def main() -> None:
    ensure_dirs()
    session = requests.Session()
    for item in LIVE_PAGES:
        fetch_url(
            session,
            item["url"],
            item["raw_rel"],
            item["source_id"],
            item["provided"],
        )
        time.sleep(0.5)

    # NBA.com's public stats endpoints have historically used inconsistent
    # season strings across combine endpoints. Keep this probe short because the
    # endpoints can hang from non-browser clients; failed attempts are useful
    # evidence and the cleaner falls back to accessible HTML measurement sources.
    for endpoint, provided in NBA_STATS_ENDPOINTS:
        for season_year in ["2026-27", "2025-26"]:
            raw_rel = f"live/nba_stats_{endpoint}_{season_year.replace('-', '_')}.json"
            nba_stats_get(
                session,
                endpoint,
                {"LeagueID": "00", "SeasonYear": season_year},
                raw_rel,
                f"nba_stats_{endpoint}_{season_year}",
                provided,
                timeout=8,
            )
            time.sleep(0.5)


if __name__ == "__main__":
    main()
