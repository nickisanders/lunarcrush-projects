#!/usr/bin/env python3
"""What happened the day after the graveyard post.

graveyard.py listed nine coins 80%+ below their peak that were among the week's
biggest gainers. This grades that list 24 hours later, against the market and
against what the backtest in projects/social-price-backtest predicts for
coins that have just run.

Usage: LUNARCRUSH_API_KEY=... python3 followup.py
"""

import datetime as dt
import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BACKTEST = HERE.parent / "social-price-backtest" / "out" / "after-the-run.json"
API = "https://lunarcrush.com/api4"
BIG_RUN = 150.0   # a 7-day gain this size or larger counts as a big run


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


def main() -> None:
    prior = json.loads((HERE / "out" / "graveyard.json").read_text())
    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    for c in ("market_cap", "percent_change_24h", "percent_change_7d", "volume_24h"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L.set_index("symbol")

    rows = []
    for x in prior["dead"]:
        s = x["symbol"]
        if s not in L.index:
            continue
        rows.append({"symbol": s, "name": x["name"], "run": x["pct7d"],
                     "next": float(L.loc[s, "percent_change_24h"]),
                     "mcap": float(L.loc[s, "market_cap"]),
                     "bestSeat": x["bestSeat"], "offPeak": x["offPeak"]})
    d = pd.DataFrame(rows).sort_values("run", ascending=False)

    market = L[(L["market_cap"] > 50e6) & (L["volume_24h"] > 1e6)]
    mkt = float(market["percent_change_24h"].median())
    btc = float(L.loc["BTC", "percent_change_24h"])
    rho = float(d[["run", "next"]].corr(method="spearman").iloc[0, 1])
    big, small = d[d["run"] >= BIG_RUN], d[d["run"] < BIG_RUN]

    print(f"The {len(d)} names from {prior['asOf']}, one day later\n")
    print(f"{'coin':<9}{'the run':>10}{'next day':>11}{'mcap':>10}")
    for _, r in d.iterrows():
        print(f"{r['symbol']:<9}{r['run']:>+9.0f}%{r['next']:>+10.1f}%{r['mcap'] / 1e6:>9,.0f}M")
    print(f"\nmedian next day, all {len(d)}: {d['next'].median():+.1f}%")
    print(f"  runs of {BIG_RUN:.0f}%+ (n={len(big)}): {big['next'].median():+.1f}%")
    print(f"  smaller runs (n={len(small)}): {small['next'].median():+.1f}%")
    print(f"  market median {mkt:+.1f}%, BTC {btc:+.1f}%")
    print(f"  fell: {int((d['next'] < 0).sum())} of {len(d)}")
    print(f"  spearman(size of run, next-day return) = {rho:+.2f}")

    buckets = json.loads(BACKTEST.read_text())["buckets"]
    print("\nfor context, the backtest's 90-day median after a week like this:")
    for b in buckets:
        print(f"  {b['label']:<20}{b['m90'] * 100:+6.1f}%   n={b.get('n'):,}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "followup.json").write_text(json.dumps({
        "postedOn": prior["asOf"], "asOf": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"),
        "rows": d.to_dict("records"), "medianNext": float(d["next"].median()),
        "bigRunMedian": float(big["next"].median()), "smallRunMedian": float(small["next"].median()),
        "bigRunThreshold": BIG_RUN, "marketMedian": mkt, "btc": btc,
        "fell": int((d["next"] < 0).sum()), "spearman": rho,
        "buckets": buckets,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'followup.json'}")


if __name__ == "__main__":
    main()
