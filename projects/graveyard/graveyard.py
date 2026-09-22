#!/usr/bin/env python3
"""This week's biggest winners are coins that were left for dead.

Takes the largest 7-day gainers live, then looks each one up in six years of
cached history: how far below its own peak market cap it still sits, and the
best seat it ever held in crypto conversation (its rank by daily active
contributors on its best day).

The pairing is the point. A coin can be 99% below its peak and still be a name
people recognise, because it was once top-ten by conversation. Those are the
ones moving this week.

Companion to projects/where-are-they-now, which found 130 coins have held a
top-20 conversation seat since 2020 and 17 still do.

Usage: LUNARCRUSH_API_KEY=... python3 graveyard.py [--top 20]
"""

import argparse
import datetime as dt
import glob
import json
import os
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
API = "https://lunarcrush.com/api4"
DEAD = -0.80          # this far below peak market cap counts as left for dead
MIN_MCAP, MIN_VOL = 20e6, 1e6
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def get(path: str, tries: int = 3) -> dict:
    key = os.environ["LUNARCRUSH_API_KEY"]
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{API}{path}", headers={
                "Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3)


def history() -> tuple[dict, dict, dict]:
    """Peak market cap, best conversation seat, and name, per symbol."""
    day, peak, names = defaultdict(list), {}, {}
    for f in glob.glob(str(RAW / "*.json")):
        d = json.load(open(f))
        s = d["coin"]["symbol"]
        if s in PEGGED or len(s) < 2:
            continue
        names[s] = d["coin"]["name"]
        caps = [r.get("market_cap") or 0 for r in d["rows"]]
        if caps:
            peak[s] = max(caps)
        for r in d["rows"]:
            c, mc = r.get("contributors_active") or 0, r.get("market_cap") or 0
            if c > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((s, c))
    seat = defaultdict(list)
    for _, rows in day.items():
        rows.sort(key=lambda x: -x[1])
        for i, (s, _) in enumerate(rows, 1):
            seat[s].append(i)
    best = {s: min(v) for s, v in seat.items()}
    return peak, best, names


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    for c in ("market_cap", "volume_24h", "percent_change_7d", "price"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L[(L["market_cap"] > MIN_MCAP) & (L["volume_24h"] > MIN_VOL) & (L["symbol"].str.len() >= 2)
          & ~L["symbol"].isin(PEGGED)]
    top = L.nlargest(args.top, "percent_change_7d")
    peak, best, names = history()

    rows = []
    for _, r in top.iterrows():
        s = r["symbol"]
        pk = peak.get(s)
        rows.append({"symbol": s, "name": names.get(s, str(r["name"])), "pct7d": float(r["percent_change_7d"]),
                     "mcap": float(r["market_cap"]), "peakMcap": float(pk) if pk else None,
                     "offPeak": float(r["market_cap"] / pk - 1) if pk else None,
                     "bestSeat": int(best[s]) if s in best else None})
    dead = [x for x in rows if x["offPeak"] is not None and x["offPeak"] <= DEAD]
    dead.sort(key=lambda x: x["bestSeat"] if x["bestSeat"] else 9999)

    print(f"Top {args.top} coins by 7-day gain, checked against six years of history\n")
    print(f"{'coin':<10}{'7d':>8}{'mcap now':>11}{'peak mcap':>12}{'off peak':>10}{'best seat':>11}  name")
    for x in rows:
        off = f"{x['offPeak'] * 100:.0f}%" if x["offPeak"] is not None else "n/a"
        pk = f"${x['peakMcap'] / 1e6:,.0f}M" if x["peakMcap"] else "n/a"
        bs = f"#{x['bestSeat']}" if x["bestSeat"] else "n/a"
        mark = "  <-- left for dead" if x in dead else ""
        print(f"{x['symbol']:<10}{x['pct7d']:>+7.0f}%{x['mcap'] / 1e6:>10,.0f}M{pk:>12}{off:>10}{bs:>11}  {x['name'][:20]}{mark}")

    print(f"\n{len(dead)} of the top {args.top} sit {abs(DEAD) * 100:.0f}%+ below their own peak market cap.")
    print("Best conversation seat each one ever held:")
    for x in dead:
        print(f"  {x['symbol']:<9} #{x['bestSeat']:<4} once, {x['offPeak'] * 100:.0f}% off peak, {x['pct7d']:+.0f}% this week")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "graveyard.json").write_text(json.dumps({
        "asOf": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"), "top": args.top,
        "deadThreshold": DEAD, "rows": rows, "dead": dead,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'graveyard.json'}")


if __name__ == "__main__":
    main()
