"""Shared polite-fetch utilities for historical draft data collection.

All fetches use a browser-like User-Agent, a minimum delay between requests,
and exponential backoff on 429/5xx. Failures are logged and skipped, never
silently dropped.
"""

import time
import logging
from pathlib import Path

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

BASE_DELAY = 3.5  # seconds between requests (BBR allows ~20 req/min)

WORKDIR = Path(__file__).resolve().parent.parent
RAW_DIR = WORKDIR / "data" / "raw" / "historical"
PROCESSED_DIR = WORKDIR / "data" / "processed"
LOG_PATH = RAW_DIR / "fetch_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger("fetch")


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def polite_fetch(session: requests.Session, url: str, dest: Path,
                 delay: float = BASE_DELAY, max_retries: int = 4) -> bool:
    """Fetch url to dest with caching, delay, and backoff. Returns success.

    If dest already exists and is non-empty, skips the network entirely.
    """
    if dest.exists() and dest.stat().st_size > 1000:
        log.info("cached  %s (%s)", dest.name, url)
        return True

    backoff = 15.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as e:
            log.warning("error   %s attempt %d: %s", url, attempt, e)
            time.sleep(backoff)
            backoff *= 2
            continue

        if resp.status_code == 200:
            dest.write_bytes(resp.content)
            log.info("fetched %s -> %s (%d bytes)", url, dest.name, len(resp.content))
            time.sleep(delay)
            return True
        if resp.status_code in (429, 403, 502, 503):
            log.warning("HTTP %d on %s, backing off %.0fs (attempt %d)",
                        resp.status_code, url, backoff, attempt)
            time.sleep(backoff)
            backoff *= 2
            continue
        log.error("HTTP %d on %s, giving up", resp.status_code, url)
        time.sleep(delay)
        return False

    log.error("FAILED after %d attempts: %s", max_retries, url)
    return False
