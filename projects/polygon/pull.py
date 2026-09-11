#!/usr/bin/env python3
"""Refresh raw_coins.json from the LunarCrush API.

MATIC is delisted as a coin but its social time series still resolves by
symbol. Needs LUNARCRUSH_API_KEY.

Usage: python3 pull.py
"""

import json
import os
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYMBOLS = ["MATIC", "POL", "SOL", "BNB", "AVAX", "ARB", "OP", "SUI", "APT"]


def main() -> None:
    key = os.environ["LUNARCRUSH_API_KEY"]
    out = {}
    for sym in SYMBOLS:
        req = urllib.request.Request(
            f"https://lunarcrush.com/api4/public/coins/{sym}/time-series/v2?bucket=day&interval=all",
            headers={"Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            out[sym] = json.load(r)["data"]
        print(f"{sym}: {len(out[sym])} rows")
    (HERE / "raw_coins.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
