"""Build 2026 NBA Draft consensus board from 6 extracted sources.

Sources and rank lists transcribed verbatim from pages fetched 2026-06-10:
- espn: ESPN big board, updated May 29 2026 (ranks 1-40)
- ringer: The Ringer mock draft, Danny Chau, May 27 2026 (picks 1-30 accessible)
- yahoo: Yahoo Sports KOC Mock Draft 7.0, June 5 2026 (picks 1-40)
- tankathon: Tankathon big board, updated ~May 29 2026 (ranks 1-40)
- cbs: CBS Sports big board / prospect rankings, May 28 2026 (ranks 1-28 accessible)
- br: Bleacher Report mock draft, June 9 2026 (picks 1-40)
"""
import csv
import statistics

SOURCES = ["espn", "ringer", "yahoo", "tankathon", "cbs", "br"]
COL_NAMES = {
    "espn": "espn_rank",
    "ringer": "ringer_rank",
    "yahoo": "yahoo_rank",
    "tankathon": "tankathon_rank",
    "cbs": "cbs_rank",
    "br": "bleacher_report_rank",
}

# player: (position, team_school, {source: rank})
players = {
    "AJ Dybantsa":        ("SF", "BYU",                 {"espn": 1,  "ringer": 1,  "yahoo": 1,  "tankathon": 3,  "cbs": 1,  "br": 1}),
    "Darryn Peterson":    ("SG/PG", "Kansas",           {"espn": 2,  "ringer": 2,  "yahoo": 2,  "tankathon": 2,  "cbs": 2,  "br": 2}),
    "Cameron Boozer":     ("PF", "Duke",                {"espn": 3,  "ringer": 3,  "yahoo": 3,  "tankathon": 1,  "cbs": 3,  "br": 3}),
    "Caleb Wilson":       ("PF", "North Carolina",      {"espn": 4,  "ringer": 4,  "yahoo": 4,  "tankathon": 4,  "cbs": 4,  "br": 4}),
    "Keaton Wagler":      ("PG/SG", "Illinois",         {"espn": 5,  "ringer": 9,  "yahoo": 8,  "tankathon": 5,  "cbs": 5,  "br": 5}),
    "Darius Acuff Jr.":   ("PG", "Arkansas",            {"espn": 6,  "ringer": 6,  "yahoo": 7,  "tankathon": 6,  "cbs": 6,  "br": 6}),
    "Mikel Brown Jr.":    ("PG", "Louisville",          {"espn": 7,  "ringer": 7,  "yahoo": 5,  "tankathon": 9,  "cbs": 8,  "br": 8}),
    "Kingston Flemings":  ("PG", "Houston",             {"espn": 8,  "ringer": 8,  "yahoo": 10, "tankathon": 7,  "cbs": 7,  "br": 7}),
    "Nate Ament":         ("SF/PF", "Tennessee",        {"espn": 9,  "ringer": 10, "yahoo": 6,  "tankathon": 10, "cbs": 10, "br": 10}),
    "Aday Mara":          ("C", "Michigan",             {"espn": 10, "ringer": 12, "yahoo": 11, "tankathon": 18, "cbs": 11, "br": 12}),
    "Brayden Burries":    ("SG", "Arizona",             {"espn": 11, "ringer": 5,  "yahoo": 9,  "tankathon": 8,  "cbs": 9,  "br": 9}),
    "Yaxel Lendeborg":    ("PF", "Michigan",            {"espn": 12, "ringer": 14, "yahoo": 13, "tankathon": 12, "cbs": 12, "br": 13}),
    "Karim Lopez":        ("SF/PF", "New Zealand Breakers", {"espn": 13, "ringer": 27, "yahoo": 12, "tankathon": 13, "cbs": 15, "br": 11}),
    "Morez Johnson Jr.":  ("PF/C", "Michigan",          {"espn": 14, "ringer": 26, "yahoo": 14, "tankathon": 17, "cbs": 17, "br": 17}),
    "Hannes Steinbach":   ("PF/C", "Washington",        {"espn": 15, "ringer": 17, "yahoo": 18, "tankathon": 15, "cbs": 16, "br": 18}),
    "Labaron Philon Jr.": ("PG", "Alabama",             {"espn": 16, "ringer": 11, "yahoo": 19, "tankathon": 11, "cbs": 14, "br": 14}),
    "Allen Graves":       ("PF", "Santa Clara",         {"espn": 17, "ringer": 20, "yahoo": 20, "tankathon": 23, "cbs": 28, "br": 20}),
    "Christian Anderson": ("PG", "Texas Tech",          {"espn": 18, "ringer": 21, "yahoo": 26, "tankathon": 22, "cbs": 21, "br": 19}),
    "Bennett Stirtz":     ("PG", "Iowa",                {"espn": 19, "ringer": 19, "yahoo": 28, "tankathon": 20, "cbs": 19, "br": 21}),
    "Cameron Carr":       ("SG/SF", "Baylor",           {"espn": 20, "ringer": 15, "yahoo": 15, "tankathon": 14, "cbs": 20, "br": 15}),
    "Chris Cenac Jr.":    ("PF/C", "Houston",           {"espn": 21, "ringer": 25, "yahoo": 22, "tankathon": 16, "cbs": 22, "br": 22}),
    "Jayden Quaintance":  ("PF/C", "Kentucky",          {"espn": 22, "ringer": 18, "yahoo": 24, "tankathon": 19, "cbs": 13, "br": 23}),
    "Dailyn Swain":       ("SG/SF", "Texas",            {"espn": 23, "ringer": 13, "yahoo": 23, "tankathon": 21, "cbs": 25, "br": 25}),
    "Isaiah Evans":       ("SG/SF", "Duke",             {"espn": 24, "ringer": 28, "yahoo": 34, "tankathon": 26, "cbs": 26, "br": 28}),
    "Koa Peat":           ("PF", "Arizona",             {"espn": 25, "ringer": 29, "yahoo": 29, "tankathon": 25, "cbs": 18, "br": 27}),
    "Meleek Thomas":      ("SG/PG", "Arkansas",         {"espn": 26, "ringer": 30, "yahoo": 21, "tankathon": 28, "br": 24}),
    "Ebuka Okorie":       ("PG", "Stanford",            {"espn": 27, "ringer": 16, "yahoo": 16, "tankathon": 24, "cbs": 24, "br": 16}),
    "Henri Veesaar":      ("C", "North Carolina",       {"espn": 28, "ringer": 23, "yahoo": 32, "tankathon": 29, "cbs": 23, "br": 30}),
    "Zuby Ejiofor":       ("PF/C", "St. John's",        {"espn": 29, "yahoo": 25, "tankathon": 33, "br": 31}),
    "Alex Karaban":       ("SF/PF", "UConn",            {"espn": 30, "yahoo": 31, "tankathon": 32, "br": 34}),
    "Joshua Jefferson":   ("SF/PF", "Iowa State",       {"espn": 31, "ringer": 22, "yahoo": 35, "tankathon": 27, "br": 33}),
    "Luigi Suigo":        ("C", "Mega Basket",          {"espn": 32, "yahoo": 17, "tankathon": 34, "br": 26}),
    "Tarris Reed Jr.":    ("C", "UConn",                {"espn": 33, "yahoo": 33, "tankathon": 30, "cbs": 27, "br": 32}),
    "Sergio de Larrea":   ("PG/SG", "Valencia",         {"espn": 34, "yahoo": 27, "tankathon": 31, "br": 29}),
    "Ryan Conwell":       ("SG", "Louisville",          {"espn": 35, "yahoo": 37, "tankathon": 36}),
    "Baba Miller":        ("PF", "Cincinnati",          {"espn": 36, "tankathon": 40, "br": 35}),
    "Jack Kayil":         ("PG/SG", "Alba Berlin",      {"espn": 37, "yahoo": 30, "br": 37}),
    "Braden Smith":       ("PG", "Purdue",              {"espn": 38, "yahoo": 39, "br": 38}),
    "Jaden Bradley":      ("PG", "Arizona",             {"espn": 39, "yahoo": 38, "tankathon": 38}),
    "Trevon Brazile":     ("PF", "Arkansas",            {"espn": 40, "tankathon": 39, "br": 36}),
    "Richie Saunders":    ("SG", "BYU",                 {"tankathon": 35}),
    "Ugonna Onyenso":     ("C", "Virginia",             {"yahoo": 40, "tankathon": 37, "br": 39}),
    "Amari Allen":        ("SF/PF", "Alabama",          {"ringer": 24}),
    "Maliq Brown":        ("PF", "Duke",                {"yahoo": 36}),
    "Izaiyah Nelson":     ("PF", "South Florida",       {"br": 40}),
}

rows = []
for name, (pos, school, ranks) in players.items():
    vals = [ranks[s] for s in SOURCES if s in ranks]
    rows.append({
        "player": name,
        "position": pos,
        "team_school": school,
        **{COL_NAMES[s]: ranks.get(s, "") for s in SOURCES},
        "mean_rank": round(statistics.mean(vals), 2),
        "median_rank": statistics.median(vals),
        "min_rank": min(vals),
        "max_rank": max(vals),
        "spread": max(vals) - min(vals),
    })

rows.sort(key=lambda r: (r["median_rank"], r["mean_rank"]))

out = "/Users/arcaman07/Documents/Robotics/Imitation learning/nba_draft_claude/data/processed/consensus_board.csv"
fields = ["player", "position", "team_school"] + [COL_NAMES[s] for s in SOURCES] + [
    "mean_rank", "median_rank", "min_rank", "max_rank", "spread"]
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"wrote {len(rows)} players")
print("\nTop 10 by median:")
for r in rows[:10]:
    print(f"  {r['median_rank']:>5} {r['player']} ({r['team_school']})")
print("\nBiggest spreads (players ranked by 3+ sources):")
for r in sorted([r for r in rows if sum(1 for s in SOURCES if r[COL_NAMES[s]] != "") >= 3],
                key=lambda x: -x["spread"])[:6]:
    print(f"  spread {r['spread']:>2}  {r['player']} (min {r['min_rank']}, max {r['max_rank']})")
