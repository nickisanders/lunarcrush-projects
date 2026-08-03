#!/usr/bin/env python3
"""Pull hourly interaction windows around historical spikes.

Reads out/spikes.csv (from analysis.py), takes every organic spike plus a
2x random sample of spam-heavy spikes, and fetches hourly data from 48h
before each spike day to 168h after (9 days total). One request per spike,
cached under data/hourly/, resumable.

Usage:
    python3 pull_hourly.py [--spam-multiple 2]
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
HOURLY_DIR = PROJECT_DIR / "data" / "hourly"
BASE = "https://lunarcrush.com/api4"
USER_AGENT = "lunarcrush-projects-halflife/0.1"
ENV_CANDIDATES = [
    PROJECT_DIR / ".env",
    PROJECT_DIR.parent / "altrank-movers" / ".env",
]
DAY = 86400


def load_api_key() -> str:
    for env in ENV_CANDIDATES:
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            m = re.match(r"^LUNARCRUSH_API_KEY=(.+)$", line.strip())
            if m:
                return m.group(1)
    sys.exit("No LUNARCRUSH_API_KEY found")


def symbol_to_id() -> dict[str, int]:
    """Map symbol -> coin id from the cached raw files; drop ambiguous symbols."""
    seen: dict[str, int] = {}
    dupes: set[str] = set()
    for p in RAW_DIR.glob("*.json"):
        coin = json.loads(p.read_text())["coin"]
        sym = coin["symbol"]
        if sym in seen and seen[sym] != coin["id"]:
            dupes.add(sym)
        else:
            seen[sym] = coin["id"]
    for sym in dupes:
        seen.pop(sym, None)
    if dupes:
        print(f"Dropping {len(dupes)} ambiguous symbols: {sorted(dupes)[:10]}...")
    return seen


def get(url: str, key: str) -> tuple[dict, dict]:
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        headers = {k.lower(): v for k, v in r.headers.items()}
        return json.load(r), headers


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spam-multiple", type=int, default=2)
    args = ap.parse_args()

    key = load_api_key()
    sp = pd.read_csv(PROJECT_DIR / "out" / "spikes.csv", parse_dates=["date"])
    ids = symbol_to_id()
    sp = sp[sp["symbol"].isin(ids)]

    organic = sp[sp["group"] == "organic"]
    spam = sp[sp["group"] == "spam"].sample(
        n=min(len(sp[sp["group"] == "spam"]), len(organic) * args.spam_multiple),
        random_state=7,
    )
    targets = pd.concat([organic, spam])
    print(f"Pulling hourly windows: {len(organic)} organic + {len(spam)} spam spikes")

    HOURLY_DIR.mkdir(parents=True, exist_ok=True)
    done = skipped = errors = 0
    started = time.time()
    for _, row in targets.iterrows():
        ts = int(row["date"].timestamp())
        out = HOURLY_DIR / f"{ids[row['symbol']]}_{row['date'].date()}.json"
        if out.exists():
            skipped += 1
            continue
        url = (
            f"{BASE}/public/coins/{ids[row['symbol']]}/time-series/v2"
            f"?bucket=hour&start={ts - 2 * DAY}&end={ts + 8 * DAY}"
        )
        try:
            body, headers = get(url, key)
            out.write_text(
                json.dumps(
                    {
                        "symbol": row["symbol"],
                        "spike_ts": ts,
                        "group": row["group"],
                        "spam_ratio": row["spam_ratio"],
                        "rows": body.get("data", []),
                    }
                )
            )
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
        if (done + skipped) % 100 == 0 and done > 0:
            rate = done / max(1, time.time() - started)
            left = len(targets) - done - skipped
            print(f"progress: {done} fetched, {skipped} cached, {errors} errors, "
                  f"~{int(left / max(rate, 0.01) / 60)}min left", flush=True)

    print(f"Done. {done} fetched, {skipped} cached, {errors} errors")


if __name__ == "__main__":
    main()
