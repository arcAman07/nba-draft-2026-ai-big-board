from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup

from common import (
    BASE_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    inches_from_height_text,
    normalize_name,
    numeric,
    save_csv,
)


LIVE_DIR = RAW_DIR / "live"
STAT_LABELS = {"pts", "reb", "ast", "blk", "stl", "ts%", "usg", "obpm", "dbpm", "bpm"}
CLASS_WORDS = {"Freshman", "Sophomore", "Junior", "Senior", "International", "Other"}


def html_lines(path: Path) -> List[str]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    return [x.strip() for x in soup.get_text("\n").splitlines() if x.strip()]


def clean_rank_token(value: str) -> Optional[int]:
    text = str(value).strip().replace(".", "")
    if re.fullmatch(r"\d{1,3}", text):
        return int(text)
    return None


def parse_pos_school(value: str) -> Tuple[str, str]:
    if "|" not in value:
        return "", value.strip()
    pos, school = value.split("|", 1)
    return pos.strip(), school.strip()


def is_next_tankathon_record(lines: List[str], idx: int) -> bool:
    rank = clean_rank_token(lines[idx]) if idx < len(lines) else None
    if rank is None:
        return False
    if idx + 2 >= len(lines):
        return False
    return "|" in lines[idx + 2] and not lines[idx + 1].startswith("TIER")


def parse_tankathon_stats(lines: List[str], idx: int) -> Tuple[dict, int]:
    row = {
        "rank": clean_rank_token(lines[idx]),
        "name": lines[idx + 1],
    }
    pos, school = parse_pos_school(lines[idx + 2])
    row["position"] = pos
    row["team_school"] = school
    row["height_listed"] = lines[idx + 3]
    row["height_in"] = inches_from_height_text(lines[idx + 3])

    weight = lines[idx + 4]
    if idx + 5 < len(lines) and lines[idx + 5].lower() == "lbs":
        row["weight_lbs"] = numeric(weight)
        class_idx = idx + 6
    else:
        row["weight_lbs"] = numeric(weight.replace("lbs", ""))
        class_idx = idx + 5

    row["class"] = lines[class_idx] if class_idx < len(lines) else ""
    row["age"] = numeric(lines[class_idx + 1].replace("yrs", "")) if class_idx + 1 < len(lines) else None

    j = class_idx + 2
    label_counts = defaultdict(int)
    while j + 1 < len(lines):
        token = lines[j].lower()
        if lines[j].startswith("TIER") or lines[j].startswith("Determining the NBA Draft Order"):
            break
        if is_next_tankathon_record(lines, j):
            break
        if token in STAT_LABELS:
            label_counts[token] += 1
            val = numeric(lines[j + 1])
            if token in {"pts", "reb", "ast", "blk", "stl"}:
                suffix = "pg" if label_counts[token] == 1 else "per36"
                key = f"{token}_{suffix}"
            else:
                key = token.replace("%", "_pct")
            row[key] = val
            j += 2
        else:
            j += 1
    row["source"] = "Tankathon"
    row["norm_name"] = normalize_name(row["name"])
    return row, j


def parse_tankathon_big_board() -> pd.DataFrame:
    lines = html_lines(LIVE_DIR / "tankathon_big_board_2026.html")
    rows = []
    i = 0
    while i < len(lines) - 8:
        if is_next_tankathon_record(lines, i):
            row, i = parse_tankathon_stats(lines, i)
            rows.append(row)
        else:
            i += 1
    df = pd.DataFrame(rows).drop_duplicates("norm_name")
    df = df.sort_values("rank")
    df.to_csv(PROCESSED_DIR / "prospects_tankathon.csv", index=False)
    return df


def parse_tankathon_mock() -> pd.DataFrame:
    lines = html_lines(LIVE_DIR / "tankathon_mock_2026.html")
    rows = []
    try:
        start = lines.index("Round 1") + 1
    except ValueError:
        start = 0
    i = start
    while i < len(lines) - 8:
        pick = clean_rank_token(lines[i])
        if pick is not None and i + 3 < len(lines):
            rank = clean_rank_token(lines[i + 1])
            name_idx = i + 2 if rank is not None else i + 1
            if name_idx + 1 < len(lines) and "|" in lines[name_idx + 1]:
                name = lines[name_idx]
                pos, school = parse_pos_school(lines[name_idx + 1])
                rows.append(
                    {
                        "source": "Tankathon mock",
                        "rank": pick,
                        "tankathon_big_board_rank_in_mock": rank,
                        "name": name,
                        "position": pos,
                        "team_school": school,
                        "norm_name": normalize_name(name),
                    }
                )
                i = name_idx + 2
                continue
        i += 1
    df = pd.DataFrame(rows).drop_duplicates(["source", "rank"])
    df.to_csv(PROCESSED_DIR / "tankathon_mock.csv", index=False)
    return df


def parse_draft_order() -> pd.DataFrame:
    lines = html_lines(LIVE_DIR / "nba_official_draft_order_2026.html")
    start = next(i for i, line in enumerate(lines) if "2026 First Round Draft Order" in line)
    end = next(i for i, line in enumerate(lines[start + 1 :], start + 1) if "2026 Second Round Draft Order" in line)
    rows = []
    i = start + 1
    while i < end:
        pick = clean_rank_token(lines[i])
        if pick is None:
            i += 1
            continue
        i += 1
        parts = []
        while i < end and clean_rank_token(lines[i]) is None:
            parts.append(lines[i])
            i += 1
        text = " ".join(parts).strip()
        text = re.sub(r"\s+", " ", text)
        owner = text
        acquired = ""
        match = re.search(r"^(.*?)\s*\((.*)$", text)
        if match:
            owner = match.group(1).strip()
            acquired = match.group(2).strip().rstrip(")")
        rows.append({"pick": pick, "owner": owner, "acquired_note": acquired, "source": "NBA.com"})
    df = pd.DataFrame(rows)
    df = df[df["pick"].between(1, 30)].sort_values("pick")
    df.to_csv(PROCESSED_DIR / "draft_order_2026.csv", index=False)
    return df


def parse_rookiescale() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "rookiescale_consensus_2026.html")
    try:
        start = lines.index("Agency") + 1
    except ValueError:
        start = 0
    rows = []
    i = start
    while i + 8 < len(lines):
        rank = clean_rank_token(lines[i])
        if rank is None:
            i += 1
            continue
        row = {
            "source": "Rookie Scale consensus",
            "rank": rank,
            "name": lines[i + 1],
            "age": numeric(lines[i + 2]),
            "team_school": lines[i + 3],
            "class": lines[i + 4],
            "position": lines[i + 5],
            "height_listed": lines[i + 6],
            "height_in": inches_from_height_text(lines[i + 6]),
            "weight_lbs": numeric(lines[i + 7]),
            "agency": lines[i + 8],
        }
        row["norm_name"] = normalize_name(row["name"])
        rows.append(row)
        i += 9
    prospects = pd.DataFrame(rows)
    ranks = prospects[["source", "rank", "name", "norm_name"]].copy()
    prospects.to_csv(PROCESSED_DIR / "rookiescale_consensus_table.csv", index=False)
    return prospects, ranks


def parse_simple_rank_table(path: Path, source: str, start_marker: str = "") -> pd.DataFrame:
    lines = html_lines(path)
    if start_marker:
        try:
            start = next(i for i, line in enumerate(lines) if start_marker.lower() in line.lower())
        except StopIteration:
            start = 0
    else:
        start = 0
    rows = []
    i = start
    while i + 4 < len(lines):
        rank = clean_rank_token(lines[i])
        if rank is not None:
            name = lines[i + 1].strip()
            class_line = lines[i + 3].strip()
            if re.search(r"[A-Za-z]", name) and class_line in {"Fr", "Fr.", "So", "So.", "Jr", "Jr.", "Sr", "Sr.", ", Fr", ", So", ", Jr", ", Sr"}:
                rows.append({"source": source, "rank": rank, "name": name, "norm_name": normalize_name(name)})
                i += 4
                continue
        i += 1
    return pd.DataFrame(rows).drop_duplicates(["source", "rank"])


def parse_cbs_prospect_rankings() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "cbs_prospect_rankings_2026.html")
    rows = []
    i = 0
    while i + 20 < len(lines):
        rank = clean_rank_token(lines[i])
        if rank is not None and re.search(r"[A-Za-z]", lines[i + 1]):
            # CBS table layout: rank, player, school, year, pos, pos rank, HT, WT, analysis, stats labels/values.
            year = lines[i + 3]
            if year in {"Fr", "So", "Jr", "Sr", "Fr.", "So.", "Jr.", "Sr."}:
                row = {
                    "source": "CBS prospect rankings",
                    "rank": rank,
                    "name": lines[i + 1],
                    "team_school": lines[i + 2],
                    "class": year,
                    "position": lines[i + 4],
                    "height_listed": lines[i + 6],
                    "height_in": inches_from_height_text(lines[i + 6].replace("-", "'") + '"') if "-" in lines[i + 6] else inches_from_height_text(lines[i + 6]),
                    "weight_lbs": numeric(lines[i + 7]),
                    "norm_name": normalize_name(lines[i + 1]),
                }
                # Find the first 2025-26 College Stats block after this record.
                for j in range(i + 8, min(i + 40, len(lines))):
                    if lines[j] == "2025-26 College Stats" and j + 10 < len(lines):
                        labels = [x.lower().replace("%", "_pct") for x in lines[j + 1 : j + 6]]
                        vals = [numeric(x) for x in lines[j + 6 : j + 11]]
                        for label, val in zip(labels, vals):
                            row[f"cbs_{label}"] = val
                        break
                rows.append(row)
                i += 8
                continue
        i += 1
    df = pd.DataFrame(rows).drop_duplicates("norm_name")
    df.to_csv(PROCESSED_DIR / "cbs_prospect_rankings.csv", index=False)
    ranks = df[["source", "rank", "name", "norm_name"]].copy()
    return df, ranks


def parse_cbs_mock() -> pd.DataFrame:
    df = parse_simple_rank_table(LIVE_DIR / "cbs_mock_2026.html", "CBS mock", "Full NBA Mock Draft")
    return df


def parse_bleacher_mock() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "bleacher_mock_2026.html")
    rows = []
    scouting = []
    for i, line in enumerate(lines):
        match = re.match(r"^(\d+)\.\s+(.+?):\s+(.+?)\s+\((.+?)\)$", line)
        if not match:
            continue
        pick = int(match.group(1))
        team = match.group(2).strip()
        name = match.group(3).strip()
        school = match.group(4).strip()
        row = {
            "source": "Bleacher Report mock",
            "rank": pick,
            "name": name,
            "team": team,
            "team_school": school,
            "norm_name": normalize_name(name),
        }
        rows.append(row)
        size = ""
        age = None
        comp = ""
        snippet_parts = []
        for j in range(i + 1, min(i + 18, len(lines))):
            if lines[j] == "Size:" and j + 1 < len(lines):
                size = lines[j + 1].replace("|", "").strip()
            if lines[j] == "Age:" and j + 1 < len(lines):
                age = numeric(lines[j + 1])
            if lines[j] == "Pro Comp:" and j + 1 < len(lines):
                comp = lines[j + 1].replace("|", "").strip()
            if len(lines[j]) > 80 and len(snippet_parts) < 2:
                snippet_parts.append(lines[j])
        scouting.append(
            {
                "source": "Bleacher Report mock",
                "name": name,
                "norm_name": normalize_name(name),
                "size_text": size,
                "age": age,
                "pro_comp": comp,
                "scouting_text": " ".join(snippet_parts),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(scouting)


def parse_yahoo_koc() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "yahoo_koc_big_board_2026.html")
    rows = []
    scouting = []
    for i, line in enumerate(lines):
        match = re.match(r"^Rank\s+(\d+)$", line)
        if not match or i + 12 >= len(lines):
            continue
        rank = int(match.group(1))
        name = lines[i + 1]
        row = {
            "source": "Yahoo/KOC big board",
            "rank": rank,
            "name": name,
            "team_school": lines[i + 2],
            "class": lines[i + 3],
            "position": lines[i + 4],
            "height_listed": lines[i + 5],
            "height_in": inches_from_height_text(lines[i + 5].replace(" ", "")),
            "weight_lbs": numeric(lines[i + 7]),
            "wingspan_listed": lines[i + 9] if i + 9 < len(lines) else "",
            "wingspan_in": inches_from_height_text(lines[i + 9].replace(" ", "")) if i + 9 < len(lines) else None,
            "age": numeric(lines[i + 11]),
            "norm_name": normalize_name(name),
        }
        rows.append(row)
        summary = ""
        if "Summary" in lines[i : i + 20]:
            sidx = i + lines[i : i + 20].index("Summary")
            if sidx + 1 < len(lines):
                summary = lines[sidx + 1]
        scouting.append(
            {
                "source": "Yahoo/KOC big board",
                "name": name,
                "norm_name": normalize_name(name),
                "scouting_text": summary,
            }
        )
    df = pd.DataFrame(rows)
    ranks = df[["source", "rank", "name", "norm_name"]].copy() if not df.empty else pd.DataFrame()
    df.to_csv(PROCESSED_DIR / "yahoo_koc_big_board.csv", index=False)
    return ranks, pd.DataFrame(scouting)


def parse_ringer() -> pd.DataFrame:
    lines = html_lines(LIVE_DIR / "ringer_big_board_2026.html")
    try:
        start = next(i for i, line in enumerate(lines) if line == "April 29, 2026.") + 1
    except StopIteration:
        start = 0
    rows = []
    i = start
    while i + 2 < len(lines):
        rank = clean_rank_token(lines[i])
        if rank is not None and re.search(r"[A-Za-z]", lines[i + 1]) and "," in lines[i + 2]:
            name = lines[i + 1]
            pos, school = [x.strip() for x in lines[i + 2].split(",", 1)]
            rows.append(
                {
                    "source": "The Ringer big board",
                    "rank": rank,
                    "name": name,
                    "position": pos,
                    "team_school": school,
                    "norm_name": normalize_name(name),
                }
            )
            i += 3
        else:
            i += 1
    return pd.DataFrame(rows)


def parse_nbadraftroom_big_board() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "nbadraftroom_big_board_8_2026.html")
    rows = []
    scouting = []
    for i in range(len(lines) - 3):
        rank = clean_rank_token(lines[i])
        if rank is None:
            continue
        name = lines[i + 1]
        detail = lines[i + 2]
        if not re.search(r"[A-Za-z]", name):
            continue
        if not (detail.startswith("\u2013") or detail.startswith("-") or "6-" in detail):
            continue
        rows.append({"source": "NBA Draft Room big board", "rank": rank, "name": name, "norm_name": normalize_name(name)})
        blurb = ""
        if i + 3 < len(lines):
            blurb = lines[i + 3]
            if len(blurb) < 30 and i + 4 < len(lines):
                blurb += " " + lines[i + 4]
        scouting.append(
            {
                "source": "NBA Draft Room big board",
                "name": name,
                "norm_name": normalize_name(name),
                "measurement_text": detail,
                "scouting_text": blurb,
            }
        )
    return pd.DataFrame(rows).drop_duplicates(["source", "rank"]), pd.DataFrame(scouting)


def parse_nbadraftroom_mock_measurements() -> Tuple[pd.DataFrame, pd.DataFrame]:
    lines = html_lines(LIVE_DIR / "nbadraftroom_mock_2026.html")
    meas = []
    scouting = []
    for i, line in enumerate(lines):
        # Position lines are followed by a measurement/scouting line in this source.
        if line not in {"PG", "SG", "SF", "PF", "C"}:
            continue
        if i == 0 or i + 1 >= len(lines):
            continue
        name = lines[i - 1]
        detail = lines[i + 1]
        if not re.search(r"HT:\s*6-|HT:\s*7-", detail):
            continue
        sep = r"\s+[\-\u2013]\s+"
        height = re.search(r"HT:\s*(.*?)" + sep + r"WT", detail)
        weight = re.search(r"WT:\s*([0-9.]+)", detail)
        wing = re.search(r"WING:\s*(.*?)(?:" + sep + r"|$)", detail)
        meas.append(
            {
                "source": "NBA Draft Room mock",
                "name": name,
                "norm_name": normalize_name(name),
                "height_listed": height.group(1).strip() if height else "",
                "height_in": inches_from_height_text(height.group(1).strip()) if height else None,
                "weight_lbs": numeric(weight.group(1)) if weight else None,
                "wingspan_listed": wing.group(1).strip() if wing else "",
                "wingspan_in": inches_from_height_text(wing.group(1).strip()) if wing else None,
            }
        )
        blurb = lines[i + 2] if i + 2 < len(lines) else ""
        comp = ""
        if i + 3 < len(lines) and lines[i + 3].startswith("PLAYER COMP"):
            comp = lines[i + 3].replace("PLAYER COMP:", "").strip()
        scouting.append(
            {
                "source": "NBA Draft Room mock",
                "name": name,
                "norm_name": normalize_name(name),
                "scouting_text": blurb,
                "pro_comp": comp,
            }
        )
    return pd.DataFrame(meas), pd.DataFrame(scouting)


def parse_on3_measurements() -> pd.DataFrame:
    lines = html_lines(LIVE_DIR / "on3_combine_measurements_2026.html")
    rows = []
    for i, line in enumerate(lines):
        if i + 3 >= len(lines):
            continue
        hline = lines[i + 2] if lines[i + 1].startswith(",") else lines[i + 1]
        # The source usually uses name, school, then measurement line. Some rows
        # split the comma onto the school line, so scan nearby.
        window = " ".join(lines[i + 1 : i + 5])
        measure_pat = r"([0-9][0-9'\u2019\u2032\u201d\u2033\".\s/\u00bc\u00bd\u00be]+)"
        match = re.search(
            r"H:\s*" + measure_pat + r"\|\s*W:\s*([0-9.]+)\s*\|\s*WS:\s*" + measure_pat + r"\|\s*SR:\s*" + measure_pat,
            window,
        )
        if not match:
            continue
        name = line.strip(", ")
        if not re.search(r"[A-Za-z]", name) or len(name.split()) > 4:
            continue
        rows.append(
            {
                "source": "On3 combine measurements",
                "name": name,
                "norm_name": normalize_name(name),
                "height_wo_shoes": match.group(1).strip(),
                "height_wo_shoes_in": inches_from_height_text(match.group(1).strip()),
                "weight_lbs": numeric(match.group(2)),
                "wingspan_listed": match.group(3).strip(),
                "wingspan_in": inches_from_height_text(match.group(3).strip()),
                "standing_reach": match.group(4).strip(),
                "standing_reach_in": inches_from_height_text(match.group(4).strip()),
            }
        )
    df = pd.DataFrame(rows).drop_duplicates("norm_name")
    df.to_csv(PROCESSED_DIR / "combine_on3_measurements.csv", index=False)
    return df


def build_combine_table(on3: pd.DataFrame, ndr_meas: pd.DataFrame, yahoo_ranks: pd.DataFrame, prospects: pd.DataFrame) -> pd.DataFrame:
    by_name: Dict[str, dict] = {}
    for df in [prospects, ndr_meas, yahoo_ranks, on3]:
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            key = row.get("norm_name")
            if not key:
                continue
            out = by_name.setdefault(key, {"norm_name": key, "name": row.get("name", "")})
            if not out.get("name") and row.get("name"):
                out["name"] = row.get("name")
            for col in [
                "height_listed",
                "height_in",
                "height_wo_shoes",
                "height_wo_shoes_in",
                "weight_lbs",
                "wingspan_listed",
                "wingspan_in",
                "standing_reach",
                "standing_reach_in",
            ]:
                if col in row and pd.notna(row[col]) and row[col] != "" and not out.get(col):
                    out[col] = row[col]
            sources = set(str(out.get("sources", "")).split(";")) if out.get("sources") else set()
            if row.get("source"):
                sources.add(row.get("source"))
            out["sources"] = ";".join(sorted(sources))
    df = pd.DataFrame(by_name.values())
    df.to_csv(PROCESSED_DIR / "combine_measurements_2026.csv", index=False)
    return df


def build_consensus(rank_tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for df in rank_tables:
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            if pd.isna(row.get("rank")):
                continue
            rows.append(
                {
                    "source": row["source"],
                    "rank": int(row["rank"]),
                    "name": row["name"],
                    "norm_name": row["norm_name"],
                }
            )
    long = pd.DataFrame(rows).drop_duplicates(["source", "norm_name"])
    long.to_csv(PROCESSED_DIR / "consensus_ranks_long.csv", index=False)

    out = []
    for key, grp in long.groupby("norm_name"):
        ranks = [int(x) for x in grp["rank"].dropna()]
        names = grp["name"].dropna().tolist()
        row = {
            "norm_name": key,
            "name": names[0] if names else key,
            "sources_count": len(ranks),
            "consensus_mean": statistics.mean(ranks),
            "consensus_median": statistics.median(ranks),
            "consensus_std": statistics.pstdev(ranks) if len(ranks) > 1 else 0.0,
            "consensus_min": min(ranks),
            "consensus_max": max(ranks),
            "sources": ";".join(sorted(grp["source"].unique())),
        }
        for _, r in grp.iterrows():
            row[f"rank_{re.sub('[^a-z0-9]+', '_', r['source'].lower()).strip('_')}"] = int(r["rank"])
        out.append(row)
    consensus = pd.DataFrame(out).sort_values(["consensus_mean", "sources_count"], ascending=[True, False])
    consensus.to_csv(PROCESSED_DIR / "consensus_board_2026.csv", index=False)
    return consensus


def build_team_context(order: pd.DataFrame) -> pd.DataFrame:
    # Needs are intentionally broad and marked as Codex inference in the report.
    needs = {
        "Washington": ("rebuilding", "primary creator; wing scoring; defensive identity"),
        "Utah": ("rebuilding", "on-ball creation; lead guard; two-way wings"),
        "Memphis": ("retooling", "frontcourt skill; wing size; half-court offense"),
        "Chicago": ("rebuilding", "top-end talent; creator; frontcourt anchor"),
        "LA Clippers": ("rebuilding", "young creator; athleticism; long-term star equity"),
        "Brooklyn": ("rebuilding", "creation; frontcourt upside; shooting"),
        "Sacramento": ("retooling", "lead guard depth; point-of-attack defense; wing size"),
        "Atlanta": ("retooling", "defensive forward; secondary playmaking; rim pressure"),
        "Dallas": ("contending/retooling", "two-way wing; guard depth; future upside"),
        "Milwaukee": ("contending/retooling", "youth; shot creation; frontcourt depth"),
        "Golden State": ("contending/retooling", "NBA-ready guard/wing; shooting; defensive versatility"),
        "Oklahoma City": ("contending", "luxury upside swing; size; stash flexibility"),
        "Miami": ("retooling", "shot creation; forward size; shooting"),
        "Charlotte": ("rebuilding", "defensive big; connective forward; shooting"),
        "Toronto": ("retooling", "guard creation; shooting; rim protection"),
        "San Antonio": ("contending", "shooting; complementary defense; bench creation"),
        "Detroit": ("contending/retooling", "floor spacing; defensive forward; backup creation"),
        "Philadelphia": ("retooling", "two-way wing; frontcourt depth; guard stability"),
        "New York": ("contending", "cost-controlled depth; shooting; defensive versatility"),
        "Los Angeles Lakers": ("contending/retooling", "guard creation; athletic wing; frontcourt depth"),
        "Denver": ("contending", "bench creation; shooting; athletic defense"),
        "Boston": ("contending", "cost-controlled wing; guard depth; shooting"),
        "Minnesota": ("contending", "guard depth; shooting; frontcourt insurance"),
        "Cleveland": ("contending", "wing size; shooting; bench creation"),
    }
    rows = []
    for _, row in order.iterrows():
        timeline, team_needs = needs.get(row["owner"], ("unknown", "best player available; roster context pending"))
        rows.append(
            {
                "pick": row["pick"],
                "owner": row["owner"],
                "timeline_inference": timeline,
                "needs_inference": team_needs,
                "acquired_note": row.get("acquired_note", ""),
                "source_for_pick": "NBA.com official draft order",
                "context_type": "Codex broad inference from team direction and pick slot; no cap number used.",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "team_context_2026.csv", index=False)
    return df


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    order = parse_draft_order()
    tankathon = parse_tankathon_big_board()
    tank_mock = parse_tankathon_mock()
    rookie_table, rookie_ranks = parse_rookiescale()
    cbs_table, cbs_ranks = parse_cbs_prospect_rankings()
    cbs_mock = parse_cbs_mock()
    bleacher_ranks, bleacher_scouting = parse_bleacher_mock()
    yahoo_ranks, yahoo_scouting = parse_yahoo_koc()
    ringer_ranks = parse_ringer()
    ndr_board, ndr_board_scouting = parse_nbadraftroom_big_board()
    ndr_meas, ndr_mock_scouting = parse_nbadraftroom_mock_measurements()
    on3 = parse_on3_measurements()

    consensus = build_consensus(
        [
            tankathon.rename(columns={"rank": "rank"})[["source", "rank", "name", "norm_name"]],
            tank_mock[["source", "rank", "name", "norm_name"]],
            rookie_ranks,
            cbs_ranks,
            cbs_mock,
            bleacher_ranks[["source", "rank", "name", "norm_name"]],
            yahoo_ranks,
            ringer_ranks[["source", "rank", "name", "norm_name"]],
            ndr_board,
        ]
    )
    combine = build_combine_table(on3, ndr_meas, yahoo_ranks, tankathon)
    team_context = build_team_context(order)

    scouting = pd.concat(
        [bleacher_scouting, yahoo_scouting, ndr_board_scouting, ndr_mock_scouting],
        ignore_index=True,
    )
    scouting.to_csv(PROCESSED_DIR / "sourced_scouting_notes.csv", index=False)

    # Main prospect table merges the most complete stat source with consensus,
    # CBS stat cross-checks, and measurements.
    main = tankathon.merge(consensus, on="norm_name", how="outer", suffixes=("_tankathon", ""))
    if not cbs_table.empty:
        cbs_cols = [c for c in cbs_table.columns if c.startswith("cbs_")] + ["norm_name"]
        main = main.merge(cbs_table[cbs_cols], on="norm_name", how="left")
    main = main.merge(combine, on="norm_name", how="left", suffixes=("", "_combine"))
    name_cols = [c for c in ["name", "name_tankathon", "name_combine"] if c in main.columns]
    if name_cols:
        main["display_name"] = main[name_cols].bfill(axis=1).iloc[:, 0]
    main.to_csv(PROCESSED_DIR / "prospects_2026.csv", index=False)

    summary = {
        "draft_order_rows": int(len(order)),
        "tankathon_prospects": int(len(tankathon)),
        "consensus_prospects": int(len(consensus)),
        "combine_rows": int(len(combine)),
        "team_context_rows": int(len(team_context)),
        "rank_sources_used": sorted(set(pd.read_csv(PROCESSED_DIR / "consensus_ranks_long.csv")["source"])),
        "rank_sources_excluded": ["ESPN big board - static fetch returned HTTP 202 shell", "NBA Draft.net measurements - HTTP 403"],
    }
    (PROCESSED_DIR / "live_build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
