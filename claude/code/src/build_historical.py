"""Merge raw sources into data/processed/historical.csv.

One row per drafted player, classes 2000-2021, both rounds.

Sources (all under data/raw/historical/):
  bbr_draft_2000_2021.csv   pick, team, college, career totals (BBR draft pages)
  bbr_draft_dates.csv       actual draft date per year (parsed from BBR pages)
  bbr_player_index.csv      birth date + listed ht/wt keyed by BBR slug
  nba_draft_combine_anthro.csv  NBA combine anthro (GitHub snapshot of
                                stats.nba.com draftcombineplayeranthro)
  allstars.csv              every All-Star ever (Wikipedia list)

Rules: no imputation. Blank where unknown. Notes column records provenance
quirks (listed vs combine measurements, prior-year combine match, etc.).
"""

import re
import unicodedata
from datetime import datetime

import pandas as pd

from fetch_util import PROCESSED_DIR, RAW_DIR, log

OUT_COLS = ["year", "pick", "player", "team", "college_or_intl",
            "age_at_draft", "height_in", "weight_lbs", "wingspan_in",
            "standing_reach_in", "career_games", "career_minutes",
            "career_ws", "career_ws48", "career_bpm", "career_vorp",
            "allstar", "notes"]


def norm_name(name: str) -> str:
    """Accent-strip, lowercase, drop punctuation; keep suffixes (jr/iii)."""
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


def listed_height_to_in(h: str):
    """'6-9' -> 81.0"""
    m = re.match(r"^(\d+)-(\d+)$", str(h).strip())
    if not m:
        return None
    return int(m.group(1)) * 12 + int(m.group(2))


def main():
    draft = pd.read_csv(RAW_DIR / "bbr_draft_2000_2021.csv")
    dates = pd.read_csv(RAW_DIR / "bbr_draft_dates.csv")
    pindex = pd.read_csv(RAW_DIR / "bbr_player_index.csv")
    combine = pd.read_csv(RAW_DIR / "nba_draft_combine_anthro.csv")
    allstars = pd.read_csv(RAW_DIR / "allstars.csv")

    # --- draft dates ---
    date_by_year = {}
    for _, r in dates.iterrows():
        if isinstance(r["draft_date"], str) and r["draft_date"]:
            date_by_year[int(r["year"])] = datetime.strptime(
                r["draft_date"], "%B %d, %Y")

    # --- birthdates / listed ht-wt by slug ---
    pindex = pindex.drop_duplicates(subset="slug", keep="first")
    pidx = pindex.set_index("slug")

    # --- combine lookup: (norm_name, season) -> measurements ---
    combine["name_norm"] = combine["PLAYER_NAME"].map(norm_name)
    dup_mask = combine.duplicated(subset=["name_norm", "SEASON"], keep=False)
    n_dup = int(dup_mask.sum())
    if n_dup:
        log.warning("%d ambiguous (name, season) combine rows excluded", n_dup)
    cmb = combine[~dup_mask].set_index(["name_norm", "SEASON"])

    # --- All-Star lookup: name -> list of first-selection years ---
    # A drafted player only gets credit if some same-name All-Star's first
    # selection came AFTER his draft year (rejects e.g. 2006 draftee Bobby
    # Jones matching the 1970s All-Star Bobby Jones).
    allstar_first = {}
    for _, r in allstars.iterrows():
        allstar_first.setdefault(norm_name(r["player"]), []).append(
            int(r["first_selection"]))

    out_rows = []
    stats = {"birthdate": 0, "combine": 0, "combine_prev_year": 0,
             "listed_htwt": 0, "allstar": 0}

    for _, r in draft.iterrows():
        year = int(r["year"])
        name = r["player"]
        slug = r["slug"] if isinstance(r["slug"], str) else ""
        notes = []

        # age at draft
        age = ""
        if slug and slug in pidx.index:
            bd = pidx.loc[slug, "birth_date"]
            if isinstance(bd, str) and bd and year in date_by_year:
                try:
                    born = datetime.strptime(bd, "%B %d, %Y")
                    age = round((date_by_year[year] - born).days / 365.25, 2)
                    stats["birthdate"] += 1
                except ValueError:
                    notes.append("unparseable birthdate")

        # combine anthro (match draft year, fallback previous year)
        height = weight = wingspan = reach = ""
        nn = norm_name(name)
        hit = None
        for season, tag in ((year, ""), (year - 1, "combine matched year-1")):
            if (nn, season) in cmb.index:
                hit = cmb.loc[(nn, season)]
                if tag:
                    notes.append(tag)
                    stats["combine_prev_year"] += 1
                else:
                    stats["combine"] += 1
                break
        if hit is not None:
            def num(v):
                return round(float(v), 2) if pd.notna(v) else ""
            height = num(hit["HEIGHT_WO_SHOES"])
            weight = num(hit["WEIGHT"])
            wingspan = num(hit["WINGSPAN"])
            reach = num(hit["STANDING_REACH"])

        # fallback ht/wt: BBR listed (roster) values, flagged in notes
        if (height == "" or weight == "") and slug and slug in pidx.index:
            used = False
            if height == "":
                h_in = listed_height_to_in(pidx.loc[slug, "height_listed"])
                if h_in:
                    height = h_in
                    used = True
            if weight == "":
                w = pidx.loc[slug, "weight_listed"]
                if pd.notna(w) and str(w).strip():
                    weight = int(float(w))
                    used = True
            if used:
                notes.append("ht/wt from BBR listed (not combine barefoot)")
                stats["listed_htwt"] += 1

        # All-Star flag (normalized name match + selection postdates draft)
        is_as = 1 if any(fy > year for fy in allstar_first.get(nn, [])) else 0
        stats["allstar"] += is_as

        if not str(r["career_games"]).strip() or pd.isna(r["career_games"]):
            notes.append("no NBA stats on BBR (never played)")

        out_rows.append({
            "year": year,
            "pick": r["pick"],
            "player": name,
            "team": r["team"],
            "college_or_intl": r["college"] if isinstance(r["college"], str) else "",
            "age_at_draft": age,
            "height_in": height,
            "weight_lbs": weight,
            "wingspan_in": wingspan,
            "standing_reach_in": reach,
            "career_games": r["career_games"],
            "career_minutes": r["career_minutes"],
            "career_ws": r["career_ws"],
            "career_ws48": r["career_ws48"],
            "career_bpm": r["career_bpm"],
            "career_vorp": r["career_vorp"],
            "allstar": is_as,
            "notes": "; ".join(notes),
        })

    df = pd.DataFrame(out_rows, columns=OUT_COLS)
    out_path = PROCESSED_DIR / "historical.csv"
    df.to_csv(out_path, index=False)
    log.info("wrote %d rows to %s", len(df), out_path)
    log.info("match stats: %s", stats)

    # --- coverage report ---
    cov_lines = ["# Historical dataset coverage (classes 2000-2021)", "",
                 f"Built {datetime.now():%Y-%m-%d} by src/build_historical.py. "
                 f"Total rows: {len(df)} (both rounds, one per drafted player).",
                 "", "## Per-year row counts and feature coverage (%)", "",
                 "| year | rows | age | height | weight | wingspan | reach | "
                 "games | WS | WS/48 | BPM | VORP |",
                 "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    feat = {"age": "age_at_draft", "height": "height_in",
            "weight": "weight_lbs", "wingspan": "wingspan_in",
            "reach": "standing_reach_in", "games": "career_games",
            "WS": "career_ws", "WS/48": "career_ws48", "BPM": "career_bpm",
            "VORP": "career_vorp"}

    def pct(sub, col):
        nonblank = sub[col].astype(str).str.strip().replace("nan", "")
        return f"{100.0 * (nonblank != '').mean():.0f}"

    for year, sub in df.groupby("year"):
        cells = [str(year), str(len(sub))] + [pct(sub, c) for c in feat.values()]
        cov_lines.append("| " + " | ".join(cells) + " |")

    cov_lines += ["", "## Overall column coverage", ""]
    for col in OUT_COLS:
        if col in ("notes",):
            continue
        cov_lines.append(f"- {col}: {pct(df, col)}%")
    cov_lines += ["", "## Per-decade wingspan / VORP coverage", ""]
    for label, lo, hi in [("2000-2009", 2000, 2009), ("2010-2019", 2010, 2019),
                          ("2020-2021", 2020, 2021)]:
        sub = df[(df.year >= lo) & (df.year <= hi)]
        cov_lines.append(f"- {label}: wingspan {pct(sub, 'wingspan_in')}%, "
                         f"VORP {pct(sub, 'career_vorp')}% (n={len(sub)})")
    cov_lines += ["", "## Notes", "",
                  "- height_in is combine height without shoes where available; "
                  "otherwise BBR listed roster height (flagged in notes column).",
                  "- college_or_intl is blank where BBR lists no college "
                  "(international or preps-to-pros players).",
                  "- allstar is exact normalized-name match against the "
                  "Wikipedia all-time All-Star list (career-to-date as of "
                  "2026-06-10).",
                  "- Career totals are career-to-date from BBR draft pages, "
                  "fetched 2026-06-10. Blank career columns = never played "
                  "an NBA game.",
                  "- No values were imputed."]
    (RAW_DIR.parent / "historical_coverage.md").write_text(
        "\n".join(cov_lines) + "\n")
    log.info("wrote coverage report")


if __name__ == "__main__":
    main()
