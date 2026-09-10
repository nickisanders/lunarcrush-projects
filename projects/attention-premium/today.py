#!/usr/bin/env python3
"""Today's attention premium, ranked within market-cap decile.

Applies the same within-decile ranking premium.py uses on history to the live
coins list, so the loudest and quietest names on a given day are directly
comparable to the buckets the backtest scored.

Usage: python3 today.py [--json out/today.json]
"""

import argparse
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
API = "https://lunarcrush.com/api4/public/coins/list/v2"
MCAP_FLOOR, VOL_FLOOR = 50e6, 1e6
MCAP_DECILES, PREMIUM_BUCKETS = 10, 5
LABELS = ["quietest", "quiet", "middle", "loud", "loudest"]
# Pegged and wrapped assets track something else by construction and their
# conversation is about the underlying, not the wrapper.
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE",
          "BUSD", "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG",
          "WBTC", "WETH", "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="out/today.json")
    args = ap.parse_args()

    key = os.environ["LUNARCRUSH_API_KEY"]
    req = urllib.request.Request(f"{API}?limit=1000",
                                 headers={"Authorization": f"Bearer {key}",
                                          "User-Agent": "lunarcrush-projects/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.load(r)["data"]

    df = pd.DataFrame(rows)
    for c in ("social_dominance", "market_dominance", "market_cap", "volume_24h",
              "percent_change_24h"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df[(df["market_cap"] >= MCAP_FLOOR) & (df["volume_24h"] >= VOL_FLOOR)
            & df["social_dominance"].notna() & (df["market_dominance"] > 0)
            & (df["symbol"] != "BTC") & (~df["symbol"].isin(PEGGED))].copy()
    df["premium"] = df["social_dominance"] / df["market_dominance"]
    df["mcap_decile"] = pd.qcut(df["market_cap"].rank(method="first"), MCAP_DECILES,
                                labels=False, duplicates="drop")
    df["group"] = df.groupby("mcap_decile")["premium"].transform(
        lambda s: pd.qcut(s.rank(method="first"), PREMIUM_BUCKETS, labels=LABELS).astype(object)
        if len(s) >= PREMIUM_BUCKETS * 2 else np.nan)
    df = df.dropna(subset=["group"])
    print(f"{len(df)} coins ranked within {df['mcap_decile'].nunique()} market-cap deciles\n")

    for lab, head in (("loudest", "LOUDEST for their size"), ("quietest", "QUIETEST for their size")):
        s = df[df["group"] == lab].nlargest(10, "market_cap") if lab == "loudest" \
            else df[df["group"] == lab].nlargest(10, "market_cap")
        print(f"{head}  (top 10 by market cap in the bucket)")
        print(f"{'symbol':<10}{'market cap':>14}{'premium':>11}{'soc dom':>10}{'24h':>9}")
        for _, r in s.iterrows():
            print(f"{r['symbol']:<10}${r['market_cap']/1e6:>12,.0f}M{r['premium']:>10.1f}x"
                  f"{r['social_dominance']:>9.2f}%{r.get('percent_change_24h', float('nan')):>8.1f}%")
        print()

    out = HERE / args.json
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "buckets": {lab: df[df["group"] == lab].nlargest(10, "market_cap")[
            ["symbol", "name", "market_cap", "premium", "social_dominance",
             "market_dominance", "percent_change_24h"]].to_dict("records")
            for lab in LABELS},
        "n": len(df)}, indent=2, default=float))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
