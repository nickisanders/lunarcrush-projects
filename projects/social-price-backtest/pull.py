#!/usr/bin/env python3
"""Pull daily time-series history for the top N coins from the LunarCrush API.

Caches one JSON file per coin under data/raw/ (keyed by LunarCrush numeric id)
and is safe to re-run: already-cached coins are skipped, so an interrupted pull
resumes where it left off. Paces requests against the x-rate-limit-* headers.

Usage:
    python3 pull.py [--top 1000] [--force-universe]
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
USER_AGENT = "lunarcrush-projects-backtest/0.1"
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ENV_CANDIDATES = [
    PROJECT_DIR / ".env",
    PROJECT_DIR.parent / "altrank-movers" / ".env",
]


def load_api_key() -> str:
    for env in ENV_CANDIDATES:
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            m = re.match(r"^LUNARCRUSH_API_KEY=(.+)$", line.strip())
            if m:
                return m.group(1)
    sys.exit("No LUNARCRUSH_API_KEY found in " + ", ".join(str(e) for e in ENV_CANDIDATES))


def get(url: str, key: str) -> tuple[dict, dict]:
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        headers = {k.lower(): v for k, v in r.headers.items()}
        return json.load(r), headers


def pace(headers: dict) -> None:
    """Sleep as needed based on the API's rate limit headers."""
    remaining = int(headers.get("x-rate-limit-minute-remaining", "100"))
    if remaining < 5:
        reset = int(headers.get("x-rate-limit-minute-reset", "0"))
        wait = max(1, reset - int(time.time()) + 1)
        print(f"  minute budget low, sleeping {wait}s")
        time.sleep(wait)
    else:
        time.sleep(0.65)  # ~90/min steady state, under the 100/min cap


def fetch_universe(key: str, top: int, force: bool) -> list[dict]:
    path = DATA_DIR / "universe.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    body, _ = get(f"{BASE}/public/coins/list/v2?sort=market_cap_rank&limit={top}&page=0", key)
    universe = [
        {
            "id": r["id"],
            "symbol": r["symbol"],
            "name": r["name"],
            "market_cap_rank": r["market_cap_rank"],
        }
        for r in body["data"]
        if r.get("market_cap_rank") and r["market_cap_rank"] <= top
    ]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(universe, indent=1))
    print(f"Universe: {len(universe)} coins (as of today, saved to {path})")
    return universe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=1000)
    ap.add_argument("--force-universe", action="store_true")
    args = ap.parse_args()

    key = load_api_key()
    universe = fetch_universe(key, args.top, args.force_universe)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    errors: dict[str, str] = {}
    done = skipped = 0
    started = time.time()

    for i, coin in enumerate(universe):
        out = RAW_DIR / f"{coin['id']}.json"
        if out.exists():
            skipped += 1
            continue
        url = f"{BASE}/public/coins/{coin['id']}/time-series/v2?bucket=day&interval=all"
        try:
            body, headers = get(url, key)
            rows = body.get("data", [])
            out.write_text(json.dumps({"coin": coin, "rows": rows}))
            done += 1
            pace(headers)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  429 on {coin['symbol']}, sleeping 65s")
                time.sleep(65)
                universe.append(coin)  # retry at the end
            else:
                errors[str(coin["id"])] = f"{coin['symbol']}: HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 - keep the long pull alive
            errors[str(coin["id"])] = f"{coin['symbol']}: {e}"

        if (done + skipped) % 25 == 0 and done > 0:
            rate = done / max(1, time.time() - started)
            left = len(universe) - (i + 1)
            print(
                f"progress: {done} fetched, {skipped} cached, {len(errors)} errors, "
                f"~{int(left / max(rate, 0.1) / 60)}min remaining"
            )

    if errors:
        (DATA_DIR / "errors.json").write_text(json.dumps(errors, indent=1))
    print(
        f"Done. {done} fetched, {skipped} already cached, {len(errors)} errors"
        + (" (see data/errors.json)" if errors else "")
    )


if __name__ == "__main__":
    main()
