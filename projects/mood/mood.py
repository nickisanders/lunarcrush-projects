#!/usr/bin/env python3
"""The more people talk about a coin, the less they like it.

LunarCrush scores every coin's daily conversation for sentiment, 0 to 100.
Across 500 coins with a real crowd, the score falls steadily as the crowd
grows: a coin with 20-50 people posting a day sits at 84, and the four coins
with more than 5,000 sit at 74. Bitcoin is the least-liked coin in the top ten.

The likely mechanism is who is in the room. A small crowd is mostly holders,
and holders are cheerful. A large crowd includes traders, critics, people who
lost money, and people who are arguing, and the score averages all of them.

There is also a second thing this surfaces, which is a limitation of the
score itself: the lowest-sentiment coins in the data are the ones whose
names are negative words. A coin called USELESS scores 46, one called ASS
scores 16. The model is reading the ticker, and it cannot tell a coin named
useless from a coin people think is useless.

Usage: python3 mood.py
"""

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
WINDOW = 90
MIN_CROWD = 20      # a coin-day needs this many people for a sentiment score to mean anything
MIN_DAYS = 45       # and a coin needs this many such days in the window
BANDS = [(20, 50), (50, 100), (100, 250), (250, 1000), (1000, 5000), (5000, 10**9)]
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH", "USDY", "USYC"}


def main() -> None:
    blobs = [json.load(open(f)) for f in sorted(glob.glob(str(RAW / "*.json")))]
    latest = max(b["rows"][-1]["time"] for b in blobs if b["rows"])
    cutoff = latest - WINDOW * 86400
    rows = []
    for b in blobs:
        c = b["coin"]
        if c["symbol"] in PEGGED or len(c["symbol"]) < 2:
            continue
        for r in b["rows"]:
            if r["time"] > cutoff and (r.get("contributors_active") or 0) >= MIN_CROWD \
                    and r.get("sentiment") is not None:
                rows.append((c["symbol"], c["name"], c.get("market_cap_rank"),
                             float(r["sentiment"]), float(r["contributors_active"])))
    df = pd.DataFrame(rows, columns=["sym", "name", "rank", "sent", "contrib"])
    per = (df.groupby(["sym", "name", "rank"])
             .agg(sent=("sent", "median"), contrib=("contrib", "median"), days=("sent", "size"))
             .reset_index())
    per = per[per["days"] >= MIN_DAYS].copy()
    per["lc"] = np.log10(per["contrib"])
    start = pd.Timestamp(cutoff, unit="s").strftime("%b %Y")
    end = pd.Timestamp(latest, unit="s").strftime("%b %Y")
    print(f"{len(per)} coins with >= {MIN_DAYS} days of >= {MIN_CROWD} people, {start} to {end}\n")

    rho = per[["lc", "sent"]].corr(method="spearman").iloc[0, 1]
    rng = np.random.default_rng(7)
    bs = [per.sample(len(per), replace=True, random_state=int(rng.integers(1e9)))
             [["lc", "sent"]].corr(method="spearman").iloc[0, 1] for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"spearman(log crowd size, median sentiment) = {rho:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]")

    print("\nMEDIAN SENTIMENT BY CROWD SIZE")
    bands = []
    for b_lo, b_hi in BANDS:
        s = per[(per["contrib"] >= b_lo) & (per["contrib"] < b_hi)]
        bands.append({"lo": b_lo, "hi": b_hi, "n": int(len(s)), "sent": float(s["sent"].median()),
                      "examples": list(s.nlargest(3, "contrib")["sym"])})
        label = f"{b_lo}+" if b_hi >= 10**9 else f"{b_lo}-{b_hi}"
        print(f"  {label:<11} people/day: {s['sent'].median():>4.0f}   n={len(s):>3}   e.g. {', '.join(bands[-1]['examples'])}")

    # Within-coin: on days a coin's own crowd is larger, is its own sentiment lower?
    df["lc"] = np.log10(df["contrib"])
    wc = np.array([g[["lc", "sent"]].corr(method="spearman").iloc[0, 1]
                   for _, g in df.groupby("sym") if len(g) >= MIN_DAYS and g["lc"].std() > 0])
    wc = wc[~np.isnan(wc)]
    print(f"\nWITHIN each coin, day to day: median spearman {np.median(wc):+.3f}, "
          f"negative for {(wc < 0).mean() * 100:.0f}% of {len(wc)} coins")

    top10 = per[per["rank"] <= 10].sort_values("sent")
    print("\nTOP 10 BY MARKET CAP, least liked first")
    for _, r in top10.iterrows():
        print(f"  {r['sym']:<6}{r['sent']:>4.0f}   {r['contrib']:>7,.0f} people/day")

    print("\nLOWEST SENTIMENT OVERALL (the model is reading the ticker)")
    low = per.nsmallest(8, "sent")
    for _, r in low.iterrows():
        print(f"  {r['sym']:<9}{r['sent']:>4.0f}   {r['name'][:30]}")
    print("\nHIGHEST")
    high = per.nlargest(6, "sent")
    for _, r in high.iterrows():
        print(f"  {r['sym']:<9}{r['sent']:>4.0f}   {r['contrib']:>6,.0f} people/day  {r['name'][:30]}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "mood.json").write_text(json.dumps({
        "coins": int(len(per)), "start": start, "end": end,
        "spearman": float(rho), "ci": [float(lo), float(hi)],
        "withinCoinMedian": float(np.median(wc)), "withinCoinNegShare": float((wc < 0).mean()),
        "bands": bands,
        "top10": [{"symbol": r["sym"], "sent": float(r["sent"]), "contrib": float(r["contrib"])}
                  for _, r in top10.iterrows()],
        "lowest": [{"symbol": r["sym"], "name": r["name"], "sent": float(r["sent"])} for _, r in low.iterrows()],
        "highest": [{"symbol": r["sym"], "name": r["name"], "sent": float(r["sent"]),
                     "contrib": float(r["contrib"])} for _, r in high.iterrows()],
        "medianAll": float(per["sent"].median()),
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'mood.json'}")


if __name__ == "__main__":
    main()
