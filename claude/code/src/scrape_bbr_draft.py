"""Scrape Basketball-Reference draft pages for classes 2000-2021.

Saves raw HTML snapshots to data/raw/historical/bbr_draft_YYYY.html and
parses every drafted player (both rounds) into
data/raw/historical/bbr_draft_2000_2021.csv with career outcome totals.
Also extracts the actual draft date from each page (needed for exact
age-at-draft) into bbr_draft_dates.csv.
"""

import csv
import re

from bs4 import BeautifulSoup

from fetch_util import RAW_DIR, log, make_session, polite_fetch

YEARS = range(2000, 2022)

# data-stat attribute -> output column
STAT_MAP = {
    "pick_overall": "pick",
    "team_id": "team",
    "college_name": "college",
    "seasons": "yrs",
    "g": "career_games",
    "mp": "career_minutes",
    "ws": "career_ws",
    "ws_per_48": "career_ws48",
    "bpm": "career_bpm",
    "vorp": "career_vorp",
}

DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December) \d{1,2}, \d{4}"
)


def parse_draft_page(html: str, year: int):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="stats")
    if table is None:
        log.error("no stats table found for %d", year)
        return [], None

    # Draft date appears in the page intro text.
    draft_date = None
    meta = soup.find(id="meta")
    text = meta.get_text(" ") if meta else soup.get_text(" ")
    m = DATE_RE.search(text)
    if m:
        draft_date = m.group(0)

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        if tr.get("class") and "thead" in tr.get("class"):
            continue
        player_cell = tr.find(attrs={"data-stat": "player"})
        if player_cell is None:
            continue
        name = player_cell.get_text(strip=True)
        if not name:
            continue
        link = player_cell.find("a")
        slug = ""
        if link and link.get("href", "").startswith("/players/"):
            slug = link["href"].split("/")[-1].replace(".html", "")
        row = {"year": year, "player": name, "slug": slug}
        for stat, col in STAT_MAP.items():
            cell = tr.find(attrs={"data-stat": stat})
            row[col] = cell.get_text(strip=True) if cell else ""
        rows.append(row)
    return rows, draft_date


def main():
    session = make_session()
    all_rows = []
    dates = []
    failures = []
    for year in YEARS:
        url = f"https://www.basketball-reference.com/draft/NBA_{year}.html"
        dest = RAW_DIR / f"bbr_draft_{year}.html"
        if not polite_fetch(session, url, dest):
            failures.append(year)
            continue
        rows, draft_date = parse_draft_page(dest.read_text(encoding="utf-8",
                                                           errors="replace"), year)
        log.info("parsed %d: %d picks, draft date %s", year, len(rows), draft_date)
        all_rows.extend(rows)
        dates.append({"year": year, "draft_date": draft_date or ""})

    cols = ["year", "pick", "team", "player", "slug", "college", "yrs",
            "career_games", "career_minutes", "career_ws", "career_ws48",
            "career_bpm", "career_vorp"]
    out = RAW_DIR / "bbr_draft_2000_2021.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)
    with open(RAW_DIR / "bbr_draft_dates.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "draft_date"])
        w.writeheader()
        w.writerows(dates)
    log.info("wrote %d rows to %s; failures: %s", len(all_rows), out, failures)


if __name__ == "__main__":
    main()
