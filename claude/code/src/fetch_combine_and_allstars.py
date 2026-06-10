"""Fetch combine anthropometrics and the All-Star roll.

1. Combine anthro: stats.nba.com's draftcombineplayeranthro API is the
   primary recommended source but is unreachable from this network (curl
   timeouts on 2026-06-10). Fallback: a public GitHub snapshot of that exact
   API (BryanDfor3/nba-draft-combine-command-center, pulled via nba_api),
   covering combine seasons 2000-2025 with HEIGHT_WO_SHOES, WEIGHT,
   WINGSPAN, STANDING_REACH.

2. All-Stars: Wikipedia "List of NBA All-Stars" page, parsed for every
   player ever selected to an All-Star Game (exact-name match downstream).
"""

import csv
import re

from bs4 import BeautifulSoup

from fetch_util import RAW_DIR, log, make_session, polite_fetch

COMBINE_URL = ("https://raw.githubusercontent.com/BryanDfor3/"
               "nba-draft-combine-command-center/HEAD/data/"
               "nba_draft_combine_data.csv")
ALLSTAR_URL = "https://en.wikipedia.org/wiki/List_of_NBA_All-Stars"


def parse_allstars(html: str):
    """Extract (name, first/last selection year, n_selections) per All-Star.

    Selection years let downstream code reject same-name collisions: a
    drafted player's first All-Star selection must postdate his draft year.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table", class_="wikitable"):
        header = [th.get_text(strip=True)
                  for th in table.find_all("tr")[0].find_all(["th", "td"])]
        if not header or "Player" not in header[0]:
            continue
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            link = cells[0].find("a")
            name = (link.get_text(strip=True) if link
                    else cells[0].get_text(strip=True))
            name = name.replace("^", "").replace("*", "").strip()
            years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b",
                                                cells[2].get_text(" "))]
            if name and years:
                rows.append({"player": name,
                             "first_selection": min(years),
                             "last_selection": max(years),
                             "n_selections": cells[1].get_text(strip=True)})
    return rows


def main():
    session = make_session()

    dest = RAW_DIR / "nba_draft_combine_anthro.csv"
    ok = polite_fetch(session, COMBINE_URL, dest, delay=1.0)
    if not ok:
        log.error("combine snapshot download FAILED")

    dest_as = RAW_DIR / "wikipedia_allstars.html"
    ok = polite_fetch(session, ALLSTAR_URL, dest_as, delay=1.0)
    if ok:
        rows = parse_allstars(dest_as.read_text(encoding="utf-8",
                                                errors="replace"))
        log.info("parsed %d All-Star entries", len(rows))
        with open(RAW_DIR / "allstars.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["player", "first_selection",
                                              "last_selection",
                                              "n_selections"])
            w.writeheader()
            w.writerows(rows)
    else:
        log.error("All-Star page download FAILED")


if __name__ == "__main__":
    main()
