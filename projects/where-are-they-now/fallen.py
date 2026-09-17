#!/usr/bin/env python3
"""Every coin that ever made crypto's top-20 conversation, and where it is now.

Rank every coin by daily active contributors, take the monthly median rank,
and find each coin's best month. 130 coins have held a top-20 seat at some
point since 2020. This reports how many still hold one, how many fell out of
the top 100, and the biggest falls by name, with the size of the crowd then
and now.

Same universe hygiene as projects/top-ten: pegged assets, single-character
tickers and per-day name collisions removed before ranking.

Survivorship: the universe is the top 1,000 coins by market cap today. A coin
that held a seat in 2021 and has since dropped out of the top 1,000 is not
here at all, so every number below is a floor. The real attrition is worse.

Usage: python3 fallen.py
"""

import datetime as dt
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
TOP = 20
NOW_FROM = "2026-05"
COLLISION_X = 100
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def main() -> None:
    day = defaultdict(list)
    names = {}
    for f in sorted(glob.glob(str(RAW / "*.json"))):
        d = json.load(open(f))
        sym = d["coin"]["symbol"]
        if sym in PEGGED or len(sym) < 2:
            continue
        names[sym] = d["coin"]["name"]
        for r in d["rows"]:
            c, it, mc = r.get("contributors_active") or 0, r.get("interactions") or 0, r.get("market_cap") or 0
            if c > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((sym, c, it / mc))

    rows = []
    for dd in sorted(day):
        med = np.median([x[2] for x in day[dd]])
        clean = sorted([(s, c) for s, c, ratio in day[dd] if ratio <= med * COLLISION_X], key=lambda x: -x[1])
        for i, (s, c) in enumerate(clean, 1):
            rows.append((pd.Timestamp(dd), s, i, c))
    df = pd.DataFrame(rows, columns=["date", "sym", "rank", "contrib"])
    m = (df.set_index("date").groupby("sym").resample("ME")
           .agg(rank=("rank", "median"), contrib=("contrib", "mean")).reset_index())
    m["ym"] = m["date"].dt.strftime("%Y-%m")

    now = m[m["ym"] >= NOW_FROM].groupby("sym").agg(now_rank=("rank", "median"), now_contrib=("contrib", "mean"))
    peak = (m.loc[m.groupby("sym")["rank"].idxmin()][["sym", "ym", "rank", "contrib"]]
              .rename(columns={"ym": "peak_month", "rank": "peak_rank", "contrib": "peak_contrib"})
              .set_index("sym"))
    j = peak.join(now, how="inner")
    j["fall"] = j["now_rank"] - j["peak_rank"]
    once = j[j["peak_rank"] <= TOP].copy()
    once["name"] = [names.get(s, s) for s in once.index]

    held = once[once["now_rank"] <= TOP]
    top50 = once[once["now_rank"] <= 50]
    past100 = once[once["now_rank"] > 100]
    print(f"{len(once)} coins have held a top-{TOP} seat by crowd in some month since 2020.\n")
    print(f"  still top {TOP}:      {len(held):>3}  ({len(held) / len(once) * 100:.0f}%)")
    print(f"  still top 50:      {len(top50):>3}  ({len(top50) / len(once) * 100:.0f}%)")
    print(f"  fell past #100:    {len(past100):>3}  ({len(past100) / len(once) * 100:.0f}%)")
    print(f"  median rank now:   {once['now_rank'].median():.0f}")

    fallers = once.sort_values("fall", ascending=False)
    print(f"\nBIGGEST FALLS (peak month, crowd then, crowd now)")
    for s, r in fallers.head(16).iterrows():
        print(f"  {s:<8} #{r['peak_rank']:<3.0f} {r['peak_month']}  {r['peak_contrib']:>6,.0f} → {r['now_contrib']:>5,.0f} people/day   now #{r['now_rank']:.0f}")

    print(f"\nSTILL THERE ({len(held)})")
    for s, r in held.sort_values("now_rank").iterrows():
        print(f"  {s:<6} peak #{r['peak_rank']:.0f} ({r['peak_month']})  now #{r['now_rank']:.0f}")

    # By the year of the peak: what share of that year's top-20 class is still top 20?
    once["peak_year"] = once["peak_month"].str[:4]
    print("\nBY THE YEAR THEY PEAKED")
    classes = []
    for y, g in once.groupby("peak_year"):
        classes.append({"year": y, "n": int(len(g)), "held": int((g["now_rank"] <= TOP).sum()),
                        "past100": int((g["now_rank"] > 100).sum())})
        print(f"  {y}: {len(g):>3} coins peaked, {int((g['now_rank'] <= TOP).sum()):>2} still top {TOP}, "
              f"{int((g['now_rank'] > 100).sum()):>2} past #100")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "fallen.json").write_text(json.dumps({
        "top": TOP, "everTop": int(len(once)), "held": int(len(held)), "top50": int(len(top50)),
        "past100": int(len(past100)), "medianNow": float(once["now_rank"].median()),
        "fallers": [{"symbol": s, "name": r["name"], "peakRank": float(r["peak_rank"]),
                     "peakMonth": r["peak_month"], "peakContrib": float(r["peak_contrib"]),
                     "nowRank": float(r["now_rank"]), "nowContrib": float(r["now_contrib"])}
                    for s, r in fallers.head(24).iterrows()],
        "heldList": [{"symbol": s, "peakRank": float(r["peak_rank"]), "peakMonth": r["peak_month"],
                      "nowRank": float(r["now_rank"])} for s, r in held.sort_values("now_rank").iterrows()],
        "classes": classes,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'fallen.json'}")


if __name__ == "__main__":
    main()
