from __future__ import annotations

import time

import requests

from common import append_source_log, ensure_dirs, fetch_url


ADDITIONAL_LIVE_SOURCES = [
    {
        "source_id": "wayback_nbadraftnet_combine_measurements_2026",
        "url": "https://web.archive.org/web/20260604142442/https://www.nbadraft.net/2026-nba-draft-combine-measurements/",
        "raw_rel": "live/wayback_nbadraftnet_combine_measurements_2026.html",
        "provided": "Wayback snapshot of NBADraft.net 2026 combine anthropometric table: height without shoes, weight, wingspan, standing reach.",
    },
    {
        "source_id": "wayback_nbadraftnet_combine_athleticism_2026",
        "url": "https://web.archive.org/web/20260610084324/https://www.nbadraft.net/2026-nba-draft-combine-athleticism-testing/",
        "raw_rel": "live/wayback_nbadraftnet_combine_athleticism_2026.html",
        "provided": "Wayback snapshot of NBADraft.net 2026 combine athletic testing table: standing/max vertical, lane agility, shuttle, sprint.",
    },
    {
        "source_id": "nba_combine_top_performers_2026",
        "url": "https://www.nba.com/news/2026-nba-draft-combine-top-performers",
        "raw_rel": "live/nba_combine_top_performers_2026.html",
        "provided": "NBA.com combine article with official context, drill leaders, selected measurements, and shooting drill results.",
    },
    {
        "source_id": "nba_combine_invitees_2026",
        "url": "https://www.nba.com/news/nba-announces-73-players-invited-to-2026-nba-draft-combine",
        "raw_rel": "live/nba_combine_invitees_2026.html",
        "provided": "NBA.com official list of 73 players invited to the 2026 NBA Draft Combine.",
    },
    {
        "source_id": "combine_data_hub_home_2026",
        "url": "https://combine.nba.com/",
        "raw_rel": "live/combine_data_hub_home.html",
        "provided": "NBA/AWS Draft Combine Data Hub React shell, used to document official dashboard availability.",
    },
    {
        "source_id": "combine_data_hub_config_2026",
        "url": "https://combine.nba.com/config.json",
        "raw_rel": "live/combine_data_hub_config.json",
        "provided": "NBA/AWS Draft Combine Data Hub configuration showing embedded QuickSight dashboard metadata.",
    },
]


HISTORICAL_FEATURE_SOURCES = [
    {
        "source_id": "jasong_draft_model_model_db",
        "url": "https://raw.githubusercontent.com/JasonG7234/NBA-Draft-Model/master/data/model_db.csv",
        "raw_rel": "historical/jasong_model_db.csv",
        "provided": "Public NBA draft model dataset with college pre-draft features, age, draft pick, and NBA MPG proxy outcomes.",
    },
    {
        "source_id": "jasong_draft_model_draft_db_nba",
        "url": "https://raw.githubusercontent.com/JasonG7234/NBA-Draft-Model/master/data/draft_db_nba.csv",
        "raw_rel": "historical/jasong_draft_db_nba.csv",
        "provided": "Public NBA draft model dataset variant with NBA shooting outcome columns for historical prospects.",
    },
    {
        "source_id": "jasong_draft_model_draft_db",
        "url": "https://raw.githubusercontent.com/JasonG7234/NBA-Draft-Model/master/data/draft_db.csv",
        "raw_rel": "historical/jasong_draft_db.csv",
        "provided": "Public NBA draft model full prospect feature table, used for coverage checks and related-work context.",
    },
]


def main() -> None:
    ensure_dirs()
    session = requests.Session()
    for source in ADDITIONAL_LIVE_SOURCES + HISTORICAL_FEATURE_SOURCES:
        fetch_url(
            session,
            source["url"],
            source["raw_rel"],
            source["source_id"],
            source["provided"],
            timeout=45,
        )
        time.sleep(0.4)

    append_source_log(
        "sports_reference_blocked_draft_pages",
        "https://www.basketball-reference.com/draft/NBA_2019.html",
        None,
        "Attempted direct Basketball Reference historical draft page fetches for 2019-2022; Cloudflare returned HTTP 403 from this environment.",
        "HTTP 403",
        "Historical builder therefore uses public GitHub datasets and documents outcome coverage limitations.",
    )


if __name__ == "__main__":
    main()
