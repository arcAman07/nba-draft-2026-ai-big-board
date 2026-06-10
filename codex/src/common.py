from __future__ import annotations

import csv
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "figures"
MODELS_DIR = BASE_DIR / "models"
SOURCES_MD = BASE_DIR / "sources.md"


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}

NBA_STATS_HEADERS = {
    **REQUEST_HEADERS,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nba.com/stats/draft/combine",
    "Origin": "https://www.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}


def ensure_dirs() -> None:
    for path in [
        RAW_DIR,
        PROCESSED_DIR,
        FIGURES_DIR,
        MODELS_DIR,
        BASE_DIR / "film" / "clips",
        BASE_DIR / "film" / "frames",
        BASE_DIR / "film" / "notes",
        BASE_DIR / "dossiers",
        BASE_DIR / "report",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str, max_len: int = 90) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value[:max_len] or "item"


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    aliases = {
        "cam boozer": "cameron boozer",
        "a j dybantsa": "aj dybantsa",
        "labaron philon": "labaron philon",
        "darius acuff": "darius acuff",
        "mikel brown": "mikel brown",
    }
    return aliases.get(value, value)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def append_source_log(
    source_id: str,
    url: str,
    raw_path: Optional[Path],
    provided: str,
    status: str,
    notes: str = "",
) -> None:
    raw_display = ""
    if raw_path:
        try:
            raw_display = str(raw_path.relative_to(BASE_DIR))
        except ValueError:
            raw_display = str(raw_path)
    safe_notes = notes.replace("\n", " ").replace("|", "/")
    row = (
        f"| {now_iso()} | {source_id} | {url} | {raw_display} | "
        f"{provided.replace('|', '/')} | {status.replace('|', '/')} | {safe_notes} |\n"
    )
    with SOURCES_MD.open("a", encoding="utf-8") as handle:
        handle.write(row)

    csv_path = PROCESSED_DIR / "sources_log.csv"
    first = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["fetch_date", "source_id", "url", "raw_snapshot", "provided", "status", "notes"],
        )
        if first:
            writer.writeheader()
        writer.writerow(
            {
                "fetch_date": now_iso(),
                "source_id": source_id,
                "url": url,
                "raw_snapshot": raw_display,
                "provided": provided,
                "status": status,
                "notes": notes,
            }
        )


def fetch_url(
    session: requests.Session,
    url: str,
    raw_rel: str,
    source_id: str,
    provided: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Path:
    ensure_dirs()
    raw_path = RAW_DIR / raw_rel
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path = raw_path.with_suffix(raw_path.suffix + ".meta.json")
    used_headers = {**REQUEST_HEADERS, **(headers or {})}
    status = "not-started"
    notes = ""
    try:
        response = session.get(url, headers=used_headers, timeout=timeout)
        status = f"HTTP {response.status_code}"
        raw_path.write_bytes(response.content)
        notes = f"content_type={response.headers.get('content-type', '')}; bytes={len(response.content)}"
        meta = {
            "url": url,
            "source_id": source_id,
            "provided": provided,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "fetched_at": now_iso(),
        }
        write_json(meta_path, meta)
    except Exception as exc:
        status = f"ERROR {type(exc).__name__}"
        notes = str(exc)
        raw_path.write_text("", encoding="utf-8")
        write_json(
            meta_path,
            {
                "url": url,
                "source_id": source_id,
                "provided": provided,
                "error": notes,
                "fetched_at": now_iso(),
            },
        )
    append_source_log(source_id, url, raw_path, provided, status, notes)
    return raw_path


def nba_stats_get(
    session: requests.Session,
    endpoint: str,
    params: Dict[str, str],
    raw_rel: str,
    source_id: str,
    provided: str,
    timeout: int = 10,
) -> Path:
    url = f"https://stats.nba.com/stats/{endpoint}"
    raw_path = RAW_DIR / raw_rel
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path = raw_path.with_suffix(raw_path.suffix + ".meta.json")
    status = "not-started"
    notes = ""
    try:
        response = session.get(url, params=params, headers=NBA_STATS_HEADERS, timeout=timeout)
        status = f"HTTP {response.status_code}"
        raw_path.write_bytes(response.content)
        notes = f"params={params}; content_type={response.headers.get('content-type', '')}; bytes={len(response.content)}"
        write_json(
            meta_path,
            {
                "url": response.url,
                "source_id": source_id,
                "provided": provided,
                "status_code": response.status_code,
                "params": params,
                "headers": dict(response.headers),
                "fetched_at": now_iso(),
            },
        )
    except Exception as exc:
        status = f"ERROR {type(exc).__name__}"
        notes = str(exc)
        raw_path.write_text("", encoding="utf-8")
        write_json(
            meta_path,
            {
                "url": url,
                "source_id": source_id,
                "provided": provided,
                "params": params,
                "error": notes,
                "fetched_at": now_iso(),
            },
        )
    append_source_log(source_id, url, raw_path, provided, status, notes)
    return raw_path


def resultset_to_rows(payload: dict, preferred_name: Optional[str] = None) -> List[dict]:
    result_sets = payload.get("resultSets") or payload.get("result_sets") or []
    if isinstance(result_sets, dict):
        result_sets = [result_sets]
    chosen = None
    if preferred_name:
        for rs in result_sets:
            if str(rs.get("name") or rs.get("Name") or "").lower() == preferred_name.lower():
                chosen = rs
                break
    if chosen is None and result_sets:
        chosen = result_sets[0]
    if not chosen:
        return []
    headers = chosen.get("headers") or chosen.get("Headers") or []
    rows = chosen.get("rowSet") or chosen.get("RowSet") or []
    return [dict(zip(headers, row)) for row in rows]


def inches_from_height_text(value: str) -> Optional[float]:
    if value is None:
        return None
    text = str(value)
    fraction_map = {
        "\u00bc": " 1/4",
        "\u00bd": " 1/2",
        "\u00be": " 3/4",
        "\u215b": " 1/8",
        "\u215c": " 3/8",
        "\u215d": " 5/8",
        "\u215e": " 7/8",
    }
    for src, dst in fraction_map.items():
        text = text.replace(src, dst)
    text = (
        text.replace("`", "'")
        .replace("\u2019", "'")
        .replace("\u2032", "'")
        .replace("\u201d", '"')
        .replace("\u2033", '"')
        .strip()
    )
    if not text or text.lower() in {"nan", "none", "-"}:
        return None
    dash_match = re.search(r"^(\d+)\s*-\s*(\d+(?:\.\d+)?)(?:\s+(\d+)/(\d+))?", text)
    if dash_match:
        inches = float(dash_match.group(2))
        if dash_match.group(3) and dash_match.group(4):
            inches += float(dash_match.group(3)) / float(dash_match.group(4))
        return int(dash_match.group(1)) * 12 + inches
    match = re.search(r"(\d+)\s*'\s*(\d+(?:\.\d+)?)(?:\s+(\d+)/(\d+))?", text)
    if match:
        inches = float(match.group(2))
        if match.group(3) and match.group(4):
            inches += float(match.group(3)) / float(match.group(4))
        return int(match.group(1)) * 12 + inches
    match = re.search(r"(\d+)\s*ft\s*(\d+(?:\.\d+)?)", text, flags=re.I)
    if match:
        return int(match.group(1)) * 12 + float(match.group(2))
    try:
        return float(text)
    except ValueError:
        return None


def numeric(value) -> Optional[float]:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("%", "").strip()
    if text in {"", "-", "nan", "None"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def save_csv(path: Path, rows: Iterable[dict], fieldnames: Optional[List[str]] = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
