"""Shared BLS Public Data API v2 client for the v2/ pipeline.

Replaces the flat-file streaming in scripts/ with API pulls plus an on-disk
cache, so re-running an analysis costs zero API queries.

Usage from sibling scripts:

    import bls_client, series_registry
    df = bls_client.fetch(["LNS12000000", "LNU02000000"])

Quick smoke test from the shell:

    python v2/bls_client.py LNS12000000

Conventions this module enforces for the whole v2/ pipeline:
  - observations are unique per (series_id, date) -- hard failure, never
    silent averaging (REVIEW_FINDINGS F11)
  - footnote codes survive the loader (F11)
  - output paths never resolve against a data/cache directory (F7)

API key: put BLS_API_KEY=<key> in a gitignored .env at the repo root, or
export it in the environment. Registered v2 limits: 500 queries/day,
50 series/query, 20 years/query.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import os
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd
import requests

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
EARLIEST_YEAR = 1948
MAX_SERIES_PER_QUERY = 50
MAX_YEARS_PER_QUERY = 20

V2_DIR = Path(__file__).resolve().parent
REPO_ROOT = V2_DIR.parent
CACHE_DIR = V2_DIR / "cache"
OUT_DIR = V2_DIR / "output"

_queries_made = 0
_cache_hits = 0


class BLSAPIError(RuntimeError):
    """Raised when the API refuses or fails a request."""

    def __init__(self, status, messages):
        self.status = status
        self.messages = list(messages)
        lines = "\n".join(f"  - {m}" for m in self.messages) or "  (no detail)"
        super().__init__(
            f"BLS API request failed (status: {status}):\n{lines}\n"
            "Hint: the registered daily quota is 500 queries; check that "
            "BLS_API_KEY in .env (repo root) is valid."
        )


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from <repo>/.env into os.environ (setdefault)."""
    path = path or REPO_ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, val)


def get_api_key() -> str:
    load_dotenv()
    key = os.environ.get("BLS_API_KEY", "").strip()
    if not key:
        sys.exit(
            "ERROR: no API key found. Add a line\n"
            "    BLS_API_KEY=<your key>\n"
            f"to {REPO_ROOT / '.env'} (gitignored), or export BLS_API_KEY.\n"
            "Keys are free: https://data.bls.gov/registrationEngine/"
        )
    return key


def queries_made() -> int:
    """POST requests actually sent to the API by this process."""
    return _queries_made


def add_client_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument(
        "--refresh", action="store_true",
        help="refetch from the API even if the cache looks fresh",
    )


# --------------------------------------------------------------------------
# cache
#
# One JSON per series, named <ID>_<slugified-official-BLS-title>.json (e.g.
# LNS12000000_seas-employment-level.json) so a directory listing is human
# readable. The title comes from the API's own catalog metadata; a series
# with no catalog entry falls back to the bare <ID>.json, and reads accept
# either form.

def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0]  # cut at a word boundary
    return slug


def _find_cache(series_id: str) -> Path | None:
    bare = CACHE_DIR / f"{series_id}.json"
    if bare.is_file():
        return bare
    hits = sorted(CACHE_DIR.glob(f"{series_id}_*.json"))
    return hits[0] if hits else None


def _cache_path_for(series_id: str, title: str) -> Path:
    if title:
        return CACHE_DIR / f"{series_id}_{_slugify(title)}.json"
    return CACHE_DIR / f"{series_id}.json"


def _read_cache(series_id: str) -> dict | None:
    p = _find_cache(series_id)
    if p is None:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None  # corrupt cache entry -> treat as a miss


def _write_cache(series_id: str, observations: list[dict], end_year: int,
                 title: str = "") -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # a refetch must never leave a stale duplicate under an old name
    for old in CACHE_DIR.glob(f"{series_id}*.json"):
        old.unlink()
    _cache_path_for(series_id, title).write_text(
        json.dumps(
            {
                "series_id": series_id,
                "series_title": title,
                "fetched_at": dt.date.today().isoformat(),
                "start_year": EARLIEST_YEAR,
                "end_year": end_year,
                "observations": observations,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def is_cached(series_id: str) -> bool:
    """True if this series already has a cache entry, i.e. costs no query.
    Lets a caller price a large fetch before starting it."""
    return _read_cache(series_id) is not None


def _is_fresh(meta: dict) -> bool:
    """Fresh if fetched today, or if it already holds the newest month the
    most recent monthly release could have delivered (today - 2 months,
    deliberately one release conservative)."""
    today = dt.date.today()
    if meta.get("fetched_at") == today.isoformat():
        return True
    monthly = [
        (o["year"], o["period"])
        for o in meta.get("observations", [])
        if "M01" <= o["period"] <= "M12"
    ]
    if not monthly:
        return False
    y, p = max(monthly)
    latest = dt.date(int(y), int(p[1:]), 1)
    horizon_month = today.month - 2
    horizon = (
        dt.date(today.year, horizon_month, 1)
        if horizon_month >= 1
        else dt.date(today.year - 1, horizon_month + 12, 1)
    )
    return latest >= horizon


# --------------------------------------------------------------------------
# HTTP

# A non-success status is only worth retrying when the cause could be
# momentary. These substrings mark the causes that will still be true on the
# next attempt, so we fail fast on them instead of burning three queries.
_PERMANENT_API_ERRORS = (
    "threshold",        # daily quota exhausted
    "exceeded",         # ditto, other phrasing
    "invalid",          # bad registration key / bad series id
    "unauthoriz",       # key not accepted
    "not authoriz",
)


# Attempts per query. Release mornings serve 503s and bare REQUEST_FAILEDs
# for a minute or two while the API absorbs the press-release load.
_MAX_ATTEMPTS = 5


def _post(payload: dict) -> dict:
    """One API query. Retries transport errors, 5xx, and non-success statuses
    that look momentary -- BLS returns a bare REQUEST_FAILED both for genuinely
    bad requests and for transient load, and release mornings produce the
    latter. Permanent causes (quota, bad key) still fail immediately.

    Worst case one query costs 5 attempts and ~30s of waiting; that is cheap
    against losing a ~176-query rebuild."""
    global _queries_made
    last_err = None
    for attempt in range(_MAX_ATTEMPTS):
        if attempt:
            # Exponential, not linear: the 8:30 release spike takes tens of
            # seconds to clear, and a run that gives up after ~6s throws away
            # a whole rebuild over a blip. 2, 4, 8, 16s.
            time.sleep(2 ** attempt)
        try:
            _queries_made += 1
            resp = requests.post(API_URL, json=payload, timeout=60)
        except requests.RequestException as e:
            last_err = e
            continue
        if resp.status_code >= 500:
            last_err = RuntimeError(f"HTTP {resp.status_code} from BLS API")
            continue
        if resp.status_code != 200:
            raise BLSAPIError(f"HTTP {resp.status_code}", [resp.text[:500]])
        body = resp.json()
        if body.get("status") != "REQUEST_SUCCEEDED":
            status, messages = body.get("status"), body.get("message", [])
            blob = " ".join([str(status)] + list(messages)).lower()
            if any(p in blob for p in _PERMANENT_API_ERRORS):
                raise BLSAPIError(status, messages)
            last_err = BLSAPIError(status, messages)
            continue
        return body
    raise BLSAPIError("TRANSPORT_ERROR", [str(last_err)])


def _year_windows(start: int, end: int) -> list[tuple[int, int]]:
    windows = []
    y = start
    while y <= end:
        windows.append((y, min(y + MAX_YEARS_PER_QUERY - 1, end)))
        y += MAX_YEARS_PER_QUERY
    return windows


def _fetch_full_history(series_ids: list[str], key: str, end_year: int) -> None:
    """Fetch EARLIEST_YEAR..end_year for the given IDs and rewrite their
    cache entries. Fetches full history regardless of the caller's window so
    each series costs queries at most once per release cycle."""
    collected: dict[str, list[dict]] = {sid: [] for sid in series_ids}
    titles: dict[str, str] = {}
    info_msgs: list[str] = []
    dropped: list[str] = []
    for i in range(0, len(series_ids), MAX_SERIES_PER_QUERY):
        batch = series_ids[i : i + MAX_SERIES_PER_QUERY]
        for y0, y1 in _year_windows(EARLIEST_YEAR, end_year):
            body = _post(
                {
                    "seriesid": batch,
                    "startyear": str(y0),
                    "endyear": str(y1),
                    "registrationkey": key,
                    # always cache annual (M13) rows too, so a later
                    # include_annual=True call never needs a refetch
                    "annualaverage": True,
                    # official series titles, used for the cache filenames
                    "catalog": True,
                }
            )
            info_msgs.extend(body.get("message", []))
            for s in body.get("Results", {}).get("series", []):
                sid = s.get("seriesID", "")
                if sid and not titles.get(sid):
                    titles[sid] = (s.get("catalog") or {}).get("series_title", "")
                for row in s.get("data", []):
                    if not row.get("period", "").startswith("M"):
                        continue
                    raw = row.get("value", "").strip()
                    try:
                        value = float(raw.replace(",", ""))
                    except ValueError:
                        dropped.append(
                            f"{sid} {row.get('year')}-{row.get('period')} ({raw!r})"
                        )
                        continue
                    codes = ",".join(
                        c for c in (f.get("code", "") for f in row.get("footnotes", []))
                        if c
                    )
                    collected[sid].append(
                        {
                            "year": int(row["year"]),
                            "period": row["period"],
                            "value": value,
                            "footnotes": codes,
                        }
                    )
    if dropped:
        print(
            f"[bls_client] note: {len(dropped)} non-numeric observation(s) "
            f"dropped (first: {dropped[0]})"
        )
    if info_msgs:
        shown = info_msgs[:3]
        for m in shown:
            print(f"[bls_client] note: {m}")
        if len(info_msgs) > len(shown):
            print(f"[bls_client] note: ... and {len(info_msgs) - len(shown)} more API messages")
    missing = [sid for sid in series_ids if not collected[sid]]
    if missing:
        print(
            "[bls_client] WARNING: no observations returned for: "
            + ", ".join(missing)
        )
    for sid in series_ids:
        collected[sid].sort(key=lambda o: (o["year"], o["period"]))
        _write_cache(sid, collected[sid], end_year, titles.get(sid, ""))


# --------------------------------------------------------------------------
# public fetch

def fetch(
    series_ids: Iterable[str],
    start_year: int = EARLIEST_YEAR,
    end_year: int | None = None,
    *,
    refresh: bool = False,
    include_annual: bool = False,
) -> pd.DataFrame:
    """Return tidy observations for the requested series.

    Columns: series_id (str), date (month-start Timestamp), value (float),
    footnote_codes (str, comma-joined, "" if none). Annual-average (M13)
    rows are excluded unless include_annual=True. Cache-first: series
    missing or stale in v2/cache/ are fetched (full history) and cached.
    """
    global _cache_hits
    ids = list(dict.fromkeys(series_ids))
    if not ids:
        raise ValueError("fetch() called with no series ids")
    end_year = end_year or dt.date.today().year

    to_fetch = []
    for sid in ids:
        meta = _read_cache(sid)
        if not refresh and meta and _is_fresh(meta):
            _cache_hits += 1
        else:
            to_fetch.append(sid)
    if to_fetch:
        _fetch_full_history(to_fetch, get_api_key(), dt.date.today().year)

    frames = []
    for sid in ids:
        meta = _read_cache(sid)
        obs = meta.get("observations", []) if meta else []
        if not obs:
            continue
        f = pd.DataFrame(obs)
        f.insert(0, "series_id", sid)
        frames.append(f)
    if not frames:
        sys.exit(
            "ERROR: none of the requested series returned any data: "
            + ", ".join(ids)
        )
    df = pd.concat(frames, ignore_index=True)

    if not include_annual:
        df = df[df["period"].between("M01", "M12")]
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["period"].str[1:].astype(int).where(
                df["period"] != "M13", 12
            ),
            "day": 1,
        }
    )
    df = df.rename(columns={"footnotes": "footnote_codes"})
    keep = ["series_id", "date", "value", "footnote_codes"]
    if include_annual:
        keep.append("period")
    else:
        dupes = df.duplicated(["series_id", "date"])
        if dupes.any():
            raise AssertionError(
                "duplicate (series_id, date) observations from the API/cache: "
                + ", ".join(
                    df.loc[dupes, "series_id"].unique()
                )
            )
    df = df[keep].sort_values(["series_id", "date"]).reset_index(drop=True)

    print(
        f"[bls_client] API queries this run: {_queries_made} "
        f"(cache hits: {_cache_hits} series)"
    )
    return df


def to_wide(df: pd.DataFrame, id_to_label: Mapping[str, str]) -> pd.DataFrame:
    """Month-indexed wide frame, one labelled column per series.

    Uses DataFrame.pivot, which raises on duplicates -- never pivot_table,
    which would silently average them (F11).
    """
    d = df[df["series_id"].isin(id_to_label)].copy()
    d["label"] = d["series_id"].map(id_to_label)
    return d.pivot(index="date", columns="label", values="value").sort_index()


def resolve_out(out_arg: str | None, default_name: str) -> Path:
    """Resolve an output path: explicit -o as given (cwd/absolute), default
    under v2/output/. Never joined to a data or cache directory (F7)."""
    path = Path(out_arg).expanduser() if out_arg else OUT_DIR / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Smoke test: fetch one or more LN series and print the tail."
    )
    ap.add_argument("series", nargs="+", help="series ids, e.g. LNS12000000")
    ap.add_argument("-n", type=int, default=6, help="months to show (default 6)")
    add_client_args(ap)
    args = ap.parse_args()
    out = fetch(args.series, refresh=args.refresh)
    for sid, g in out.groupby("series_id"):
        print(f"\n{sid} - last {args.n} observations:")
        tail = g.tail(args.n)[["date", "value", "footnote_codes"]]
        print(tail.to_string(index=False))
