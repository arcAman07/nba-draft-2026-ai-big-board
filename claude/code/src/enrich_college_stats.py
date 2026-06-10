"""Enrich historical.csv with each player's FINAL pre-draft NCAA season stats.

Phase A (offline): merge Barttorvik bulk player-season file (2009-2021 seasons)
  -> covers draft classes 2009-2021.
Phase B (network, optional --sref flag): Sports-Reference college pages for
  2000-2008 FIRST-ROUND picks only. Polite: curl with browser UA, 3.5s delay,
  backoff on 403, snapshot every fetched page.

Output: data/processed/historical_enriched.csv
Logs:   data/raw/historical/college/match_log.md

Column formulas (torvik source):
  ncaa_games   = GP
  ncaa_mpg     = mp                      (minutes per game)
  ncaa_ppg     = pts                     (points per game)
  ncaa_rpg     = treb                    (total rebounds per game)
  ncaa_apg     = ast                     (assists per game)
  ncaa_fg_pct  = (twoPM+TPM)/(twoPA+TPA) (torvik has no direct FG%; makes/attempts are season totals)
  ncaa_3p_pct  = TP_per                  (already a fraction; blank if TPA==0)
  ncaa_3pa_pg  = TPA/GP
  ncaa_ft_pct  = FT_per                  (fraction; blank if FTA==0)
  ncaa_ts_pct  = TS_per/100              (torvik stores TS as percent, e.g. 58.1)
  ncaa_usg_pct = usg                     (percent form, e.g. 24.5)
  ncaa_ast_pct = AST_per
  ncaa_tov_pct = TO_per
  ncaa_stl_pct = stl_per
  ncaa_blk_pct = blk_per
  ncaa_obpm    = obpm
  ncaa_bpm     = bpm

Column formulas (sports-reference source, per-game table; advanced table used
where present for that season):
  ncaa_ts_pct  = pts_pg/(2*(fga_pg+0.44*fta_pg)) if not in advanced table
                 (0.44 FT coefficient, standard TS formula)
  usage/ast%/tov%/stl%/blk%/obpm/bpm blank unless present in advanced table
  (sports-reference CBB advanced coverage is sparse before 2009-10).
"""

import argparse
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

WORKDIR = Path(__file__).resolve().parent.parent
PROCESSED = WORKDIR / "data" / "processed"
COLLEGE_RAW = WORKDIR / "data" / "raw" / "historical" / "college"
SREF_DIR = COLLEGE_RAW / "sref"
SREF_DIR.mkdir(parents=True, exist_ok=True)

HIST_CSV = PROCESSED / "historical.csv"
TORVIK_CSV = COLLEGE_RAW / "torvik_players_2009_2021.csv"
OUT_CSV = PROCESSED / "historical_enriched.csv"
MATCH_LOG = COLLEGE_RAW / "match_log.md"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY = 10.0  # 3.5s spacing drew a 403 from sports-reference every ~3rd request; 10s avoids it

NCAA_COLS = ["ncaa_games", "ncaa_mpg", "ncaa_ppg", "ncaa_rpg", "ncaa_apg",
             "ncaa_fg_pct", "ncaa_3p_pct", "ncaa_3pa_pg", "ncaa_ft_pct",
             "ncaa_ts_pct", "ncaa_usg_pct", "ncaa_ast_pct", "ncaa_tov_pct",
             "ncaa_stl_pct", "ncaa_blk_pct", "ncaa_obpm", "ncaa_bpm",
             "ncaa_source"]

SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}

# Documented manual aliases (normalized historical name -> normalized torvik name).
# Trey Thompkins appears in torvik 2010-11 under his legal name Howard Thompkins III.
# Dewan Hernandez played at Miami as Dewan Huell (changed name before 2019 draft).
NAME_ALIASES = {
    "trey thompkins": "howard thompkins",
    "dewan hernandez": "dewan huell",
}

log_lines = []          # match_log.md content
def logm(msg):
    log_lines.append(msg)
    print(msg)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def norm_name(name: str) -> str:
    s = strip_accents(str(name)).lower()
    s = s.replace("'", "").replace(".", "").replace(",", "")
    s = s.replace("-", " ")
    toks = [t for t in s.split() if t not in SUFFIXES]
    return " ".join(toks)


SCHOOL_ALIASES = {
    "unc": "north carolina", "uconn": "connecticut", "lsu": "louisiana state",
    "usc": "southern california", "smu": "southern methodist",
    "byu": "brigham young", "vcu": "virginia commonwealth",
    "ucf": "central florida", "unlv": "nevada las vegas",
    "utep": "texas el paso", "ole miss": "mississippi",
    "uab": "alabama birmingham", "st": "saint",
    # sports-reference team_name_abbr abbreviations
    "ga": "georgia", "va": "virginia", "fla": "florida", "ala": "alabama",
    "tenn": "tennessee", "miss": "mississippi", "okla": "oklahoma",
    "ark": "arkansas", "mich": "michigan", "minn": "minnesota",
    "wis": "wisconsin", "colo": "colorado", "conn": "connecticut",
    "tex": "texas", "ariz": "arizona", "wash": "washington",
    "ill": "illinois", "ky": "kentucky", "ore": "oregon",
    "pitt": "pittsburgh",
}

def norm_school(s: str) -> str:
    x = strip_accents(str(s)).lower()
    x = x.replace("(", " ").replace(")", " ").replace(".", "").replace("'", "")
    x = x.replace("-", " ").replace("&", " ")
    raw = x.split()
    toks = []
    for i, t in enumerate(raw):
        if t in ("st", "state"):
            # leading "St" = Saint (St John's); trailing "St" = State (Ohio St)
            toks.append("saint" if i == 0 else "state")
        else:
            toks.append(SCHOOL_ALIASES.get(t, t))
    x = " ".join(toks)
    return SCHOOL_ALIASES.get(x, x)


def school_match(a, b) -> bool:
    """Loose match: normalized equality or token-subset containment."""
    if pd.isna(a) or pd.isna(b):
        return False
    na, nb = norm_school(a), norm_school(b)
    if na == nb:
        return True
    ta, tb = set(na.split()) - {"university"}, set(nb.split()) - {"university"}
    # guard: "Michigan" must never loosely match "Michigan State"
    if ("state" in ta) != ("state" in tb):
        return False
    ta -= {"state", "saint"}
    tb -= {"state", "saint"}
    if not ta or not tb:
        return na in nb or nb in na
    return ta <= tb or tb <= ta or na in nb or nb in na


def fnum(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def rnd(v, n):
    return round(v, n) if v is not None else None


# ---------------------------------------------------------------- Phase A

def torvik_row_to_stats(r) -> dict:
    gp = fnum(r["GP"]) or 0
    twoPM, twoPA = fnum(r["twoPM"]) or 0, fnum(r["twoPA"]) or 0
    tpm, tpa = fnum(r["TPM"]) or 0, fnum(r["TPA"]) or 0
    fta = fnum(r["FTA"]) or 0
    fga = twoPA + tpa
    out = {
        "ncaa_games": int(gp) if gp else None,
        "ncaa_mpg": rnd(fnum(r["mp"]), 1),
        "ncaa_ppg": rnd(fnum(r["pts"]), 1),
        "ncaa_rpg": rnd(fnum(r["treb"]), 1),
        "ncaa_apg": rnd(fnum(r["ast"]), 1),
        "ncaa_fg_pct": rnd((twoPM + tpm) / fga, 3) if fga > 0 else None,
        "ncaa_3p_pct": rnd(fnum(r["TP_per"]), 3) if tpa > 0 else None,
        "ncaa_3pa_pg": rnd(tpa / gp, 1) if gp > 0 else None,
        "ncaa_ft_pct": rnd(fnum(r["FT_per"]), 3) if fta > 0 else None,
        "ncaa_ts_pct": rnd((fnum(r["TS_per"]) or 0) / 100, 3) if fnum(r["TS_per"]) else None,
        "ncaa_usg_pct": rnd(fnum(r["usg"]), 1),
        "ncaa_ast_pct": rnd(fnum(r["AST_per"]), 1),
        "ncaa_tov_pct": rnd(fnum(r["TO_per"]), 1),
        "ncaa_stl_pct": rnd(fnum(r["stl_per"]), 1),
        "ncaa_blk_pct": rnd(fnum(r["blk_per"]), 1),
        "ncaa_obpm": rnd(fnum(r["obpm"]), 2),
        "ncaa_bpm": rnd(fnum(r["bpm"]), 2),
        "ncaa_source": "barttorvik",
    }
    return out


def match_torvik(hist: pd.DataFrame, tv: pd.DataFrame) -> dict:
    """Return {hist_index: stats_dict}. Logs ambiguous/failed matches."""
    tv = tv.copy()
    tv["nname"] = tv["player_name"].map(norm_name)
    by_name_year = {k: g for k, g in tv.groupby(["nname", "year"])}
    by_year = {k: g for k, g in tv.groupby("year")}

    results, n_fail, n_amb = {}, 0, 0
    sub = hist[(hist.year >= 2009) & (hist.year <= 2021)]
    for idx, p in sub.iterrows():
        if pd.isna(p.college_or_intl):
            results[idx] = {"ncaa_source": "", "_non_ncaa": True}
            continue
        nn = norm_name(p.player)
        if nn in NAME_ALIASES:
            logm(f"- INFO {int(p.year)} pick {int(p.pick)} {p.player}: using "
                 f"documented alias '{NAME_ALIASES[nn]}'")
            nn = NAME_ALIASES[nn]
        tag = f"{int(p.year)} pick {int(p.pick)} {p.player} ({p.college_or_intl})"

        def pick_candidate(cands, label):
            if len(cands) == 1:
                c = cands.iloc[0]
                # accept if pick confirms OR school confirms; else flag
                pick_ok = fnum(c["pick"]) == float(p["pick"])
                sch_ok = school_match(p.college_or_intl, c["team"])
                if pick_ok or sch_ok:
                    if not sch_ok:
                        logm(f"- WARN school-mismatch {tag}: torvik team "
                             f"'{c['team']}' (accepted via pick match){label}")
                    return c
                logm(f"- AMBIGUOUS {tag}: single name/year candidate but "
                     f"neither pick nor school confirms (torvik team "
                     f"'{c['team']}', torvik pick {c['pick']}){label} -> blank")
                return None
            # multiple: narrow by pick then school
            byp = cands[cands["pick"] == float(p["pick"])]
            if len(byp) == 1:
                return byp.iloc[0]
            bys = cands[[school_match(p.college_or_intl, t) for t in cands["team"]]]
            if len(bys) == 1:
                return bys.iloc[0]
            logm(f"- AMBIGUOUS {tag}: {len(cands)} torvik candidates, "
                 f"could not disambiguate{label} -> blank")
            return None

        cands = by_name_year.get((nn, int(p.year)))
        chosen, note = None, ""
        if cands is not None and len(cands):
            chosen = pick_candidate(cands, "")
            if chosen is None:
                n_amb += 1
                results[idx] = {}
                continue
        else:
            # fallback 1: final season the year before the draft
            cands = by_name_year.get((nn, int(p.year) - 1))
            if cands is not None and len(cands):
                chosen = pick_candidate(cands, " [season=draft_year-1]")
                if chosen is not None:
                    note = " (used final season = draft year - 1)"
                    logm(f"- INFO {tag}: matched to {int(p.year)-1} season "
                         f"(no draft-year season in torvik)")
                else:
                    n_amb += 1
                    results[idx] = {}
                    continue
            else:
                # fallback 2: same draft year + same pick number, last name check
                yg = by_year.get(int(p.year))
                if yg is not None:
                    byp = yg[yg["pick"] == float(p["pick"])]
                    last = nn.split()[-1] if nn else ""
                    byp = byp[[last in norm_name(x).split() for x in byp["player_name"]]]
                    if len(byp) == 1:
                        chosen = byp.iloc[0]
                        logm(f"- INFO {tag}: matched via pick+lastname to torvik "
                             f"name '{chosen['player_name']}'")
        if chosen is None:
            n_fail += 1
            logm(f"- FAIL {tag}: no torvik match (name+year, year-1, "
                 f"pick+lastname all empty) -> blank")
            results[idx] = {}
            continue
        results[idx] = torvik_row_to_stats(chosen)
    return results, n_fail, n_amb


# ---------------------------------------------------------------- Phase B

def curl_fetch(url: str, dest: Path):
    """Fetch with curl + browser UA. Returns (status_code, used_cache)."""
    if dest.exists() and dest.stat().st_size > 500:
        # validate cached content (a killed run can leave an error page behind)
        head = dest.read_text(errors="ignore")
        if "players_per_game" in head:
            return 200, True
        dest.unlink()
    r = subprocess.run(
        ["curl", "-s", "-o", str(dest), "-w", "%{http_code}",
         "-A", USER_AGENT, "-H", "Accept-Language: en-US,en;q=0.9",
         "--max-time", "30", url],
        capture_output=True, text=True)
    code = int(r.stdout.strip() or 0)
    if code != 200 and dest.exists():
        dest.unlink()  # don't cache error pages
    return code, False


def slug_for(name: str) -> str:
    s = strip_accents(name).lower()
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def season_end_year(season: str):
    """'1999-00' -> 2000"""
    m = re.match(r"(\d{4})-(\d{2})", str(season))
    if not m:
        return None
    start, yy = int(m.group(1)), int(m.group(2))
    end = (start // 100) * 100 + yy
    if end < start:
        end += 100
    return end


def parse_sref_page(html: str):
    """Return list of season dicts from per-game (+advanced) tables."""
    html = html.replace("<!--", "").replace("-->", "")
    soup = BeautifulSoup(html, "lxml")
    pg = soup.find("table", id="players_per_game") or soup.find("table", id="per_game")
    if pg is None:
        return None
    seasons = []
    for tr in pg.find("tbody").find_all("tr"):
        cells = {td.get("data-stat"): td.get_text(strip=True)
                 for td in tr.find_all(["th", "td"])}
        season = cells.get("season") or cells.get("year_id")
        if not season or not re.match(r"\d{4}-\d{2}", season):
            continue
        seasons.append(cells)
    # advanced table (may be absent for early-2000s seasons)
    adv = soup.find("table", id="players_advanced") or soup.find("table", id="advanced")
    advmap = {}
    if adv is not None and adv.find("tbody"):
        for tr in adv.find("tbody").find_all("tr"):
            cells = {td.get("data-stat"): td.get_text(strip=True)
                     for td in tr.find_all(["th", "td"])}
            season = cells.get("season") or cells.get("year_id")
            if season:
                advmap[season] = cells
    for s in seasons:
        s["_adv"] = advmap.get(s.get("season") or s.get("year_id"), {})
    return seasons


def sref_season_to_stats(c: dict) -> dict:
    adv = c.get("_adv", {})
    g = fnum(c.get("games") or c.get("g"))
    pts = fnum(c.get("pts_per_g"))
    fga = fnum(c.get("fga_per_g"))
    fta = fnum(c.get("fta_per_g"))
    ts = fnum(adv.get("ts_pct"))
    if ts is None and pts is not None and fga is not None and fta is not None \
            and (fga + 0.44 * fta) > 0:
        ts = pts / (2 * (fga + 0.44 * fta))
    fg3a = fnum(c.get("fg3a_per_g"))
    out = {
        "ncaa_games": int(g) if g else None,
        "ncaa_mpg": rnd(fnum(c.get("mp_per_g")), 1),
        "ncaa_ppg": rnd(pts, 1),
        "ncaa_rpg": rnd(fnum(c.get("trb_per_g")), 1),
        "ncaa_apg": rnd(fnum(c.get("ast_per_g")), 1),
        "ncaa_fg_pct": rnd(fnum(c.get("fg_pct")), 3),
        "ncaa_3p_pct": rnd(fnum(c.get("fg3_pct")), 3) if (fg3a or 0) > 0 else None,
        "ncaa_3pa_pg": rnd(fg3a, 1),
        "ncaa_ft_pct": rnd(fnum(c.get("ft_pct")), 3) if (fta or 0) > 0 else None,
        "ncaa_ts_pct": rnd(ts, 3),
        "ncaa_usg_pct": rnd(fnum(adv.get("usg_pct")), 1),
        "ncaa_ast_pct": rnd(fnum(adv.get("ast_pct")), 1),
        "ncaa_tov_pct": rnd(fnum(adv.get("tov_pct")), 1),
        "ncaa_stl_pct": rnd(fnum(adv.get("stl_pct")), 1),
        "ncaa_blk_pct": rnd(fnum(adv.get("blk_pct")), 1),
        "ncaa_obpm": rnd(fnum(adv.get("obpm")), 2),
        "ncaa_bpm": rnd(fnum(adv.get("bpm")), 2),
        "ncaa_source": "sports-reference",
    }
    return out


def first_round_cutoff(year: int) -> int:
    # 29 first-round picks 2000-2004 (29 teams / forfeited pick in 2004)
    return 29 if year <= 2004 else 30


def run_sref(hist: pd.DataFrame, lottery_only=False) -> dict:
    results = {}
    n_fail = 0
    consecutive_403 = 0
    targets = hist[(hist.year <= 2008) &
                   (hist.pick <= (14 if lottery_only else 30))]
    targets = targets[[p <= first_round_cutoff(y) or p <= 14
                       for y, p in zip(targets.year, targets.pick)]]
    fetched_urls = []
    for idx, p in targets.iterrows():
        tag = f"{int(p.year)} pick {int(p.pick)} {p.player} ({p.college_or_intl})"
        if pd.isna(p.college_or_intl):
            results[idx] = {"ncaa_source": "", "_non_ncaa": True}
            continue
        base = slug_for(p.player)
        found = False
        for n in range(1, 5):
            slug = f"{base}-{n}"
            url = f"https://www.sports-reference.com/cbb/players/{slug}.html"
            dest = SREF_DIR / f"{slug}.html"
            code, cached = curl_fetch(url, dest)
            if not cached:
                fetched_urls.append((url, code))
                time.sleep(DELAY)
            if code == 403:
                consecutive_403 += 1
                logm(f"- 403 on {url} (consecutive={consecutive_403}), backing off 90s")
                time.sleep(90)
                code, cached = curl_fetch(url, dest)
                if code == 403:
                    consecutive_403 += 1
                    logm(f"- 403 again on {url}, backing off 240s")
                    time.sleep(240)
                    code, cached = curl_fetch(url, dest)
                if consecutive_403 >= 6:
                    logm("- ABORT sports-reference phase: persistent 403s")
                    return results, n_fail, fetched_urls, True
            if code == 404:
                break  # no higher-index slug will exist
            if code != 200:
                logm(f"- HTTP {code} on {url}, skipping slug")
                continue
            consecutive_403 = 0
            seasons = parse_sref_page(dest.read_text(errors="ignore"))
            if not seasons:
                continue
            pre = [s for s in seasons
                   if (season_end_year(s.get("season") or s.get("year_id")) or 9999)
                   <= int(p.year)]
            if not pre:
                continue  # wrong player (career starts after draft year)
            final = pre[-1]
            sch = (final.get("team_name_abbr") or final.get("team_name")
                   or final.get("school_name") or final.get("team"))
            if not school_match(p.college_or_intl, sch):
                continue  # wrong same-named player, try next slug index
            endy = season_end_year(final.get("season") or final.get("year_id"))
            if endy != int(p.year):
                logm(f"- INFO {tag}: final college season ends {endy}, "
                     f"not draft year (sat out / early entry gap)")
            results[idx] = sref_season_to_stats(final)
            found = True
            break
        if not found:
            n_fail += 1
            logm(f"- FAIL {tag}: no verified sports-reference page "
                 f"(slugs {base}-1..4) -> blank")
            results[idx] = {}
    return results, n_fail, fetched_urls, False


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sref", action="store_true",
                    help="run phase B (sports-reference 2000-2008 first round)")
    ap.add_argument("--lottery-only", action="store_true")
    args = ap.parse_args()

    hist = pd.read_csv(HIST_CSV)
    tv = pd.read_csv(TORVIK_CSV, low_memory=False)

    logm(f"# College stats match log\n\nGenerated by src/enrich_college_stats.py. "
         f"Run date 2026-06-10.\n\n## Torvik merge (draft classes 2009-2021)\n")
    tv_res, tv_fail, tv_amb = match_torvik(hist, tv)

    logm(f"\nTorvik phase: {sum(1 for v in tv_res.values() if v.get('ncaa_source')=='barttorvik')} "
         f"matched, {tv_fail} failed, {tv_amb} ambiguous-blanked, "
         f"{sum(1 for v in tv_res.values() if v.get('_non_ncaa'))} non-NCAA.\n")

    sref_res, sref_fail, fetched, aborted = ({}, 0, [], False)
    if args.sref:
        logm("## Sports-Reference (draft classes 2000-2008, first round)\n")
        sref_res, sref_fail, fetched, aborted = run_sref(hist, args.lottery_only)
        logm(f"\nSports-Reference phase: "
             f"{sum(1 for v in sref_res.values() if v.get('ncaa_source')=='sports-reference')} "
             f"matched, {sref_fail} failed, "
             f"{sum(1 for v in sref_res.values() if v.get('_non_ncaa'))} non-NCAA, "
             f"aborted={aborted}, fetches={len(fetched)}.\n")

    # assemble output
    for col in NCAA_COLS:
        hist[col] = None
    all_res = {**tv_res, **sref_res}
    for idx, stats in all_res.items():
        if stats.get("_non_ncaa"):
            cur = hist.at[idx, "notes"]
            hist.at[idx, "notes"] = ("non-NCAA" if pd.isna(cur) or not str(cur).strip()
                                     else f"{cur}; non-NCAA")
            continue
        for col in NCAA_COLS:
            if col in stats and stats[col] is not None:
                hist.at[idx, col] = stats[col]

    hist.to_csv(OUT_CSV, index=False)
    MATCH_LOG.write_text("\n".join(log_lines) + "\n")
    print(f"\nWrote {OUT_CSV} ({len(hist)} rows) and {MATCH_LOG}")

    # coverage summary
    def cov(df):
        return f"{df['ncaa_source'].notna().mean()*100:.1f}% ({df['ncaa_source'].notna().sum()}/{len(df)})"
    out = pd.read_csv(OUT_CSV)
    for lo, hi in [(2000, 2008), (2009, 2021)]:
        era = out[(out.year >= lo) & (out.year <= hi)]
        fr = era[[p <= first_round_cutoff(y) for y, p in zip(era.year, era.pick)]]
        ncaa_era = era[era.college_or_intl.notna()]
        ncaa_fr = fr[fr.college_or_intl.notna()]
        print(f"{lo}-{hi}: all={cov(era)} firstround={cov(fr)} "
              f"| NCAA-only: all={cov(ncaa_era)} firstround={cov(ncaa_fr)}")


if __name__ == "__main__":
    main()
