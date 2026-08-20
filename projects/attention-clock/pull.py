#!/usr/bin/env python3
"""Cache hourly posting volume for every coin over $1B.

One request per coin, resumable: coins already in data/ are skipped, so an
interrupted run costs nothing to restart.

Usage:
    python3 pull.py [--min-market-cap 1e9]
"""

import argparse
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BASE = "https://lunarcrush.com/api4"

# Their conversation is plumbing (transfer alerts, yield mechanics), not a
# community keeping hours, so they would measure something else entirely.
SKIP = {
    "USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE",
    "XAUT", "PAXG", "USDS", "USDD", "BFUSD", "BSC-USD",
    "WBTC", "WETH", "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC",
}


def load_key() -> str:
    for path in (HERE / ".env", HERE / ".." / "altrank-movers" / ".env"):
        try:
            for line in path.read_text().splitlines():
                if line.startswith("LUNARCRUSH_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
        except OSError:
            continue
    key = os.environ.get("LUNARCRUSH_API_KEY")
    if not key:
        raise SystemExit("LUNARCRUSH_API_KEY not set and no .env found")
    return key


def get(path: str, key: str) -> dict:
    req = Request(f"{BASE}{path}", headers={
        "Authorization": f"Bearer {key}",
        # Without a User-Agent the API answers 403.
        "User-Agent": "lunarcrush-projects-attention-clock/0.1",
    })
    with urlopen(req) as r:
        body = json.loads(r.read())
    time.sleep(0.7)  # stay under 100 requests/min
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-market-cap", type=float, default=1e9)
    args = ap.parse_args()
    key = load_key()
    DATA.mkdir(exist_ok=True)

    coins = get("/public/coins/list/v2", key)["data"]
    universe = sorted(
        (c for c in coins
         if c.get("market_cap", 0) >= args.min_market_cap
         and c.get("market_cap_rank", 0) > 0
         and c["symbol"] not in SKIP),
        key=lambda c: c["market_cap_rank"],
    )
    print(f"{len(universe)} coins over ${args.min_market_cap/1e9:.0f}B")

    for c in universe:
        out = DATA / f"{c['symbol']}.json"
        if out.exists():
            continue
        try:
            rows = get(f"/public/coins/{c['id']}/time-series/v2?bucket=hour&interval=1m", key)["data"]
        except Exception as e:  # a single dead coin must not end the run
            print(f"  skip {c['symbol']}: {e}")
            continue
        out.write_text(json.dumps({
            "symbol": c["symbol"], "name": c["name"], "rank": c["market_cap_rank"],
            "rows": [{"time": r["time"], "posts": r.get("posts_created")} for r in rows],
        }))
        print(f"  {c['symbol']} {len(rows)} hours")


if __name__ == "__main__":
    main()
