#!/usr/bin/env python3
"""How many people are actually talking about your coin?

For each of the top 1,000 coins by market cap, the median number of distinct
accounts posting about it per day, over the most recent 90 days of cached
history. The answer for the median coin is small enough to be worth a post on
its own.

Contributors rather than interactions or posts, because a contributor is a
person (or at least an account), and the question is how many of them there
are. Pegged and wrapped assets are excluded: their conversation belongs to the
asset they track, and they would otherwise dominate the "big coin, no crowd"
list for a boring reason.

Usage: python3 headcount.py
"""

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
WINDOW = 90
BANDS = [(1, 10), (11, 50), (51, 100), (101, 250), (251, 500), (501, 1000)]
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH", "USD0", "YLDS",
          "LSETH", "RSETH", "USDF", "SUSDE", "SUSDS", "SDAI", "USDY", "USTB", "BUIDL",
          "USYC", "FIGR_HELOC", "JLP", "GHO", "JITOSOL", "METH", "CNX", "BSOL", "JUPSOL",
          "EZETH", "SFRXETH", "OSETH", "SWETH", "STBTC", "TBTC", "FBTC", "PUMPBTC", "UNIBTC"}


def main() -> None:
    blobs = [json.load(open(f)) for f in sorted(glob.glob(str(RAW / "*.json")))]
    # A fixed date window, not "the last N rows": a sparsely covered coin's
    # last 90 rows can reach back a year and would be compared against
    # everyone else's last 90 days.
    latest = max(b["rows"][-1]["time"] for b in blobs if b["rows"])
    cutoff = latest - WINDOW * 86400
    rows, span = [], [cutoff, latest]
    for d in blobs:
        c = d["coin"]
        if c["symbol"] in PEGGED or len(c["symbol"]) < 2:
            continue
        recent = [r for r in d["rows"] if r["time"] > cutoff]
        if len(recent) < WINDOW // 2:
            continue
        for r in recent:
            rows.append((c["symbol"], c["name"], c.get("market_cap_rank"),
                         r.get("contributors_active") or 0, r.get("posts_active") or 0,
                         r.get("market_cap") or 0))
    df = pd.DataFrame(rows, columns=["sym", "name", "rank", "contrib", "posts", "mcap"])
    per = (df.groupby(["sym", "name", "rank"])
             .agg(contrib=("contrib", "median"), posts=("posts", "median"), mcap=("mcap", "median"))
             .reset_index())
    per = per[per["mcap"] > 0].sort_values("rank")
    start = pd.Timestamp(span[0], unit="s").strftime("%b %Y")
    end = pd.Timestamp(span[1], unit="s").strftime("%b %Y")
    print(f"{len(per)} coins, median daily contributors over the last {WINDOW} days ({start} to {end})\n")

    med = per["contrib"].median()
    print(f"THE MEDIAN COIN: {med:.0f} people a day, {per['posts'].median():.0f} posts a day")
    q = {p: float(per["contrib"].quantile(p)) for p in (0.1, 0.25, 0.5, 0.75, 0.9)}
    for p, v in q.items():
        print(f"  p{int(p * 100):<3} {v:>6.0f} people/day")

    print("\nBY MARKET-CAP RANK")
    bands = []
    for lo, hi in BANDS:
        s = per[(per["rank"] >= lo) & (per["rank"] <= hi)]
        bands.append({"lo": lo, "hi": hi, "n": int(len(s)), "contrib": float(s["contrib"].median()),
                      "posts": float(s["posts"].median())})
        print(f"  #{lo}-{hi:<5} median {s['contrib'].median():>6,.0f} people/day  {s['posts'].median():>6,.0f} posts   n={len(s)}")

    thresholds = {t: float((per["contrib"] < t).mean()) for t in (10, 50, 100)}
    print()
    for t, share in thresholds.items():
        print(f"  {share * 100:.0f}% of coins have fewer than {t} people a day")

    ranked = per.sort_values("contrib", ascending=False).reset_index(drop=True)
    cut = {n: float(ranked["contrib"].iloc[n - 1]) for n in (10, 50, 100, 250)}
    print("\nPEOPLE A DAY NEEDED TO RANK #N BY CROWD")
    for n, v in cut.items():
        print(f"  #{n:<4} {v:>6,.0f}")

    quiet = per[(per["rank"] <= 100) & (per["contrib"] < 50)].sort_values("contrib")
    print("\nTOP-100 COINS BY MARKET CAP WITH UNDER 50 PEOPLE A DAY")
    for _, r in quiet.head(10).iterrows():
        print(f"  {r['sym']:<8} #{int(r['rank']):<4} ${r['mcap'] / 1e9:>5.1f}B  {r['contrib']:>4.0f} people/day")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "headcount.json").write_text(json.dumps({
        "window": WINDOW, "start": start, "end": end, "coins": int(len(per)),
        "median": float(med), "medianPosts": float(per["posts"].median()),
        "quantiles": {str(int(p * 100)): v for p, v in q.items()},
        "bands": bands, "belowThreshold": {str(t): v for t, v in thresholds.items()},
        "rankCutoffs": {str(n): v for n, v in cut.items()},
        "quietBigCaps": [{"symbol": r["sym"], "name": r["name"], "rank": int(r["rank"]),
                          "mcap": float(r["mcap"]), "contrib": float(r["contrib"])}
                         for _, r in quiet.head(10).iterrows()],
        "distribution": sorted(float(x) for x in per["contrib"]),
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'headcount.json'}")


if __name__ == "__main__":
    main()
