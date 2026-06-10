from __future__ import annotations

import time

import requests

from common import ensure_dirs, fetch_url


HISTORICAL_SOURCES = [
    {
        "source_id": "fivethirtyeight_nba_draft_2015_historical_projections",
        "url": "https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-draft-2015/historical_projections.csv",
        "raw_rel": "historical/fivethirtyeight_historical_projections.csv",
        "provided": "Historical draft model projections and outcome probabilities used as related-work/model reference data.",
    },
    {
        "source_id": "tirdod_draft_history",
        "url": "https://raw.githubusercontent.com/tirdod/NBA-Draft-Pick-Value/main/draftHistory.csv",
        "raw_rel": "historical/tirdod_draftHistory.csv",
        "provided": "Historical draft pick/player table for pick-value analysis.",
    },
    {
        "source_id": "tirdod_vorp",
        "url": "https://raw.githubusercontent.com/tirdod/NBA-Draft-Pick-Value/main/vorp.csv",
        "raw_rel": "historical/tirdod_vorp.csv",
        "provided": "Historical VORP outcome table for draft pick value modeling.",
    },
    {
        "source_id": "woodfin_draft_machine_combined",
        "url": "https://raw.githubusercontent.com/woodfin8/Draft_Machine/master/combined_data.csv",
        "raw_rel": "historical/woodfin_combined_data.csv",
        "provided": "Historical NCAA plus NBA draft/outcome feature table used in a public draft model project.",
    },
    {
        "source_id": "woodfin_draft_machine_draft_data",
        "url": "https://raw.githubusercontent.com/woodfin8/Draft_Machine/master/Draft_data.csv",
        "raw_rel": "historical/woodfin_Draft_data.csv",
        "provided": "Historical draft pick data from public Draft Machine project.",
    },
    {
        "source_id": "woodfin_draft_machine_ncaa_data",
        "url": "https://raw.githubusercontent.com/woodfin8/Draft_Machine/master/NCAA_data.csv",
        "raw_rel": "historical/woodfin_NCAA_data.csv",
        "provided": "Historical NCAA player stats from public Draft Machine project.",
    },
    {
        "source_id": "woodfin_draft_machine_nba_cleaned",
        "url": "https://raw.githubusercontent.com/woodfin8/Draft_Machine/master/NBA_cleaned.csv",
        "raw_rel": "historical/woodfin_NBA_cleaned.csv",
        "provided": "Historical NBA outcome data from public Draft Machine project.",
    },
    {
        "source_id": "achou11_combine_all_years",
        "url": "https://raw.githubusercontent.com/achou11/NBA_draft_combine_measurements/master/nba_draft_combine_all_years.csv",
        "raw_rel": "historical/achou11_nba_draft_combine_all_years.csv",
        "provided": "Historical NBA Draft Combine measurements scraped from DraftExpress.",
    },
]


def main() -> None:
    ensure_dirs()
    session = requests.Session()
    for source in HISTORICAL_SOURCES:
        fetch_url(
            session,
            source["url"],
            source["raw_rel"],
            source["source_id"],
            source["provided"],
        )
        time.sleep(0.4)

    for year in range(2000, 2016):
        url = f"https://raw.githubusercontent.com/kshvmdn/nbadrafts/master/datasets/{year}_nbadraft.csv"
        fetch_url(
            session,
            url,
            f"historical/kshvmdn_{year}_nbadraft.csv",
            f"kshvmdn_nbadraft_{year}",
            "Historical draft pick/player CSV by year from kshvmdn/nbadrafts.",
        )
        time.sleep(0.15)


if __name__ == "__main__":
    main()
