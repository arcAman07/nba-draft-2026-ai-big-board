"""Scrape Basketball-Reference player index pages (a-z).

Each letter page lists every NBA player whose last name starts with that
letter, with birth date, listed height, and listed weight. Keyed by the BBR
player slug, this gives birthdates for nearly every drafted player who
appeared in the NBA, in 26 requests instead of ~1300 per-player pages.

Output: data/raw/historical/bbr_player_index.csv
        (slug, name, birth_date, height_listed, weight_listed, colleges)
"""

import csv
import string

from bs4 import BeautifulSoup

from fetch_util import RAW_DIR, log, make_session, polite_fetch


def parse_letter_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="players")
    if table is None:
        return []
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cell = tr.find(attrs={"data-stat": "player"})
        if cell is None:
            continue
        link = cell.find("a")
        if not link:
            continue
        slug = link["href"].split("/")[-1].replace(".html", "")

        def stat(name):
            c = tr.find(attrs={"data-stat": name})
            return c.get_text(strip=True) if c else ""

        rows.append({
            "slug": slug,
            "name": cell.get_text(strip=True).replace("*", ""),
            "birth_date": stat("birth_date"),
            "height_listed": stat("height"),
            "weight_listed": stat("weight"),
            "colleges": stat("colleges"),
        })
    return rows


def main():
    session = make_session()
    all_rows = []
    failures = []
    for letter in string.ascii_lowercase:
        url = f"https://www.basketball-reference.com/players/{letter}/"
        dest = RAW_DIR / f"bbr_players_{letter}.html"
        if not polite_fetch(session, url, dest):
            failures.append(letter)  # 'x' has no players and 404s; expected
            continue
        rows = parse_letter_page(dest.read_text(encoding="utf-8",
                                                errors="replace"))
        log.info("letter %s: %d players", letter, len(rows))
        all_rows.extend(rows)

    out = RAW_DIR / "bbr_player_index.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "name", "birth_date",
                                          "height_listed", "weight_listed",
                                          "colleges"])
        w.writeheader()
        w.writerows(all_rows)
    log.info("wrote %d player-index rows; failed letters: %s",
             len(all_rows), failures)


if __name__ == "__main__":
    main()
