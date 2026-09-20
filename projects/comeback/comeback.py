#!/usr/bin/env python3
"""A coin that was written off, month by month, until it wasn't.

Zcash launched in 2016 and was a top-ten coin by 2018. By mid-2024 it was
$20, a $300M market cap, and ranked around #100 in crypto conversation. In
January 2025 it hit #126. Nine months later it was #4.

This traces a single coin's price and its seat in the conversation, month by
month, from the cached history and the live API. Rank is by daily active
contributors against every other coin, pegged assets and single-character
tickers removed, so it is the same ranking used in projects/top-ten and
projects/where-are-they-now.

Usage: LUNARCRUSH_API_KEY=... python3 comeback.py ZEC
"""

import argparse
import datetime as dt
import glob
import json
import os
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
API = "https://lunarcrush.com/api4"
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def get(path: str) -> dict:
    key = os.environ["LUNARCRUSH_API_KEY"]
    req = urllib.request.Request(f"{API}{path}", headers={
        "Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    args = ap.parse_args()
    sym = args.symbol.upper()

    # Monthly rank by crowd from the cache.
    day = defaultdict(list)
    series = None
    for f in glob.glob(str(RAW / "*.json")):
        d = json.load(open(f))
        s = d["coin"]["symbol"]
        if s == sym:
            series = pd.DataFrame(d["rows"])
        if s in PEGGED or len(s) < 2:
            continue
        for r in d["rows"]:
            c, mc = r.get("contributors_active") or 0, r.get("market_cap") or 0
            if c > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((s, c))
    if series is None:
        raise SystemExit(f"{sym} not in cache")
    ranks = defaultdict(list)
    for dd, rows in day.items():
        rows.sort(key=lambda x: -x[1])
        for i, (s, _) in enumerate(rows, 1):
            if s == sym:
                ranks[f"{dd.year}-{dd.month:02d}"].append(i)

    series["date"] = pd.to_datetime(series["time"], unit="s")
    for c in ("close", "contributors_active", "market_cap"):
        series[c] = pd.to_numeric(series[c], errors="coerce")
    series["ym"] = series["date"].dt.strftime("%Y-%m")
    m = series.groupby("ym").agg(close=("close", "last"), mcap=("market_cap", "last"),
                                 contrib=("contributors_active", "mean")).reset_index()
    m["rank"] = [float(np.median(ranks[y])) if y in ranks else np.nan for y in m["ym"]]

    # Live: today's price, market cap rank, and the last 90 days daily.
    live = [x for x in get("/public/coins/list/v2?limit=1000")["data"] if x["symbol"] == sym][0]
    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    for c in ("market_cap", "interactions_24h"):
        L[c] = pd.to_numeric(L[c], errors="coerce")
    Lf = L[(L["market_cap"] > 0) & (L["interactions_24h"] > 0) & (L["symbol"].str.len() >= 2)
           & ~L["symbol"].isin(PEGGED)].copy()
    Lf["ratio"] = Lf["interactions_24h"] / Lf["market_cap"]
    Lf = Lf[Lf["ratio"] <= Lf["ratio"].median() * 100].sort_values("interactions_24h", ascending=False).reset_index(drop=True)
    live_rank = int(Lf[Lf["symbol"] == sym].index[0]) + 1
    h = pd.DataFrame(get(f"/public/coins/{sym}/time-series/v2?bucket=day&interval=3m")["data"])
    h["date"] = pd.to_datetime(h["time"], unit="s")
    for c in ("close", "contributors_active"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h = h.iloc[:-1]  # drop the partial day

    lowest = m.loc[m["rank"].idxmax()]
    lowest_price = m.loc[m["close"].idxmin()]
    print(f"${sym}  {live['name']}\n")
    print(f"lowest price month:  {lowest_price['ym']}  ${lowest_price['close']:,.2f}  mcap ${lowest_price['mcap'] / 1e9:.2f}B")
    print(f"worst crowd rank:    {lowest['ym']}  #{lowest['rank']:.0f}  ({lowest['contrib']:,.0f} people/day)")
    print(f"today:               ${float(live['price']):,.2f}  mcap ${float(live['market_cap']) / 1e9:.1f}B  "
          f"#{int(live['market_cap_rank'])} by market cap  #{live_rank} by conversation  "
          f"{h['contributors_active'].iloc[-7:].median():,.0f} people/day")
    print(f"price from low:      {float(live['price']) / lowest_price['close']:.0f}x")
    print(f"\n{'month':<9}{'close':>10}{'mcap':>8}{'people/day':>12}{'crowd rank':>12}")
    for _, r in m.iterrows():
        if r["ym"] >= "2025-01" or r["ym"].endswith(("-06", "-12")):
            print(f"{r['ym']:<9}${r['close']:>9,.2f}{r['mcap'] / 1e9:>7.1f}B{r['contrib']:>12,.0f}{r['rank']:>11.0f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{sym.lower()}.json").write_text(json.dumps({
        "symbol": sym, "name": live["name"],
        "monthly": [{"ym": r["ym"], "close": float(r["close"]), "mcap": float(r["mcap"]),
                     "contrib": float(r["contrib"]), "rank": float(r["rank"]) if pd.notna(r["rank"]) else None}
                    for _, r in m.iterrows()],
        "lowestPrice": {"ym": lowest_price["ym"], "close": float(lowest_price["close"]), "mcap": float(lowest_price["mcap"])},
        "worstRank": {"ym": lowest["ym"], "rank": float(lowest["rank"]), "contrib": float(lowest["contrib"])},
        "live": {"price": float(live["price"]), "mcap": float(live["market_cap"]),
                 "mcapRank": int(live["market_cap_rank"]), "crowdRank": live_rank,
                 "contrib7d": float(h["contributors_active"].iloc[-7:].median()),
                 "pct7d": float(live.get("percent_change_7d") or 0), "pct30d": float(live.get("percent_change_30d") or 0),
                 "asOf": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")},
        "recent": [{"date": r["date"].strftime("%Y-%m-%d"), "close": float(r["close"]),
                    "contrib": float(r["contributors_active"])} for _, r in h.iterrows()],
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / f'{sym.lower()}.json'}")


if __name__ == "__main__":
    main()
