#!/usr/bin/env python3
"""Pull daily history for the top N stocks: out-of-sample data for the
organic-spike finding.

Same shape as pull.py, but the stocks list caps at 100 rows per page so it
paginates. Cached under data/stocks/, resumable.

Usage:
    python3 pull_stocks.py [--top 400]
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://lunarcrush.com/api4"
UA = "lunarcrush-projects-backtest/0.1"
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "stocks"
ENV_CANDIDATES = [PROJECT_DIR / ".env", PROJECT_DIR.parent / "altrank-movers" / ".env"]


def load_api_key() -> str:
    for env in ENV_CANDIDATES:
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            m = re.match(r"^LUNARCRUSH_API_KEY=(.+)$", line.strip())
            if m:
                return m.group(1)
    sys.exit("No LUNARCRUSH_API_KEY found")


def get(url: str, key: str) -> tuple[dict, dict]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), {k.lower(): v for k, v in r.headers.items()}


def fetch_universe(key: str, top: int) -> list[dict]:
    path = DATA_DIR / "stocks_universe.json"
    if path.exists():
        return json.loads(path.read_text())
    rows, page = [], 0
    while len(rows) < top:
        body, _ = get(f"{BASE}/public/stocks/list/v2?sort=market_cap_rank&limit=100&page={page}", key)
        batch = body.get("data") or []
        if not batch:
            break
        rows.extend(batch)
        page += 1
        time.sleep(0.7)
    universe = [
        {"id": r["id"], "symbol": r["symbol"], "name": r.get("name"),
         "market_cap_rank": r.get("market_cap_rank")}
        for r in rows[:top]
    ]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(universe, indent=1))
    print(f"Universe: {len(universe)} stocks (saved)")
    return universe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=400)
    args = ap.parse_args()

    key = load_api_key()
    universe = fetch_universe(key, args.top)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    done = skipped = errors = 0
    started = time.time()
    for i, s in enumerate(universe):
        out = RAW_DIR / f"{s['id']}.json"
        if out.exists():
            skipped += 1
            continue
        url = f"{BASE}/public/stocks/{s['id']}/time-series/v2?bucket=day&interval=all"
        try:
            body, headers = get(url, key)
            out.write_text(json.dumps({"stock": s, "rows": body.get("data", [])}))
            done += 1
            remaining = int(headers.get("x-rate-limit-minute-remaining", "100"))
            time.sleep(0.65 if remaining > 10 else 30)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(65)
            else:
                errors += 1
        except Exception:
            errors += 1
        if (done + skipped) % 50 == 0 and done > 0:
            rate = done / max(1, time.time() - started)
            left = len(universe) - i - 1
            print(f"progress: {done} fetched, {skipped} cached, {errors} errors, "
                  f"~{int(left / max(rate, 0.01) / 60)}min left", flush=True)

    print(f"Done. {done} fetched, {skipped} cached, {errors} errors")


if __name__ == "__main__":
    main()
