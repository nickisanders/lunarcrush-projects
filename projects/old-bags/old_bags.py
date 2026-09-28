#!/usr/bin/env python3
"""The 2021 bags are beating the memecoins.

Two cohorts, both defined from data rather than by hand:

- **The 2021 bags.** Coins whose all-time-high market cap in six years of
  cached history landed in 2021 or earlier and which still sit more than 50%
  below it. The things people bought in the last cycle and never sold.
- **Memecoins.** LunarCrush's own `meme` category.

Both are measured over the same week, against the same market median, using
live prices. The universe is coins over $50M with real volume, deduplicated
by ticker because LunarCrush lists twelve symbols twice.

Usage: LUNARCRUSH_API_KEY=... python3 old_bags.py
"""

import datetime as dt
import glob
import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
API = "https://lunarcrush.com/api4"
MIN_MCAP, MIN_VOL = 50e6, 1e6
DOWN_FROM_PEAK = -0.50
PEAK_BY = 2021


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


def peaks() -> dict[str, tuple[float, int]]:
    out = {}
    for f in glob.glob(str(RAW / "*.json")):
        d = json.load(open(f))
        best = None
        for r in d["rows"]:
            mc = r.get("market_cap") or 0
            if mc and (best is None or mc > best[0]):
                best = (mc, dt.datetime.fromtimestamp(r["time"], dt.UTC).year)
        if best:
            out[d["coin"]["symbol"]] = best
    return out


def main() -> None:
    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    L["nm"] = L["name"].astype(str)
    for c in ("market_cap", "percent_change_24h", "percent_change_7d", "volume_24h"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L.sort_values("market_cap", ascending=False).drop_duplicates("symbol")
    f = L[(L["market_cap"] > MIN_MCAP) & (L["volume_24h"] > MIN_VOL)
          & (L["symbol"].str.len() >= 2)].copy()

    pk = peaks()
    f["peakMcap"] = [pk.get(s, (None, None))[0] for s in f["symbol"]]
    f["peakYear"] = [pk.get(s, (None, None))[1] for s in f["symbol"]]
    f["offPeak"] = f["market_cap"] / f["peakMcap"] - 1

    mkt = float(f["percent_change_7d"].median())
    old = f[(f["peakYear"] <= PEAK_BY) & (f["offPeak"] < DOWN_FROM_PEAK)]
    meme = f[f["categories"].astype(str).str.contains("meme", na=False)]

    print(f"{len(f)} coins over ${MIN_MCAP / 1e6:.0f}M. Market median this week: {mkt:+.1f}%\n")
    print(f"{'cohort':<34}{'n':>4}{'median 7d':>11}{'beat market':>13}")
    for label, g in (("2021 bags, still 50%+ down", old), ("memecoins", meme)):
        print(f"{label:<34}{len(g):>4}{g['percent_change_7d'].median():>10.1f}%"
              f"{(g['percent_change_7d'] > mkt).mean() * 100:>12.0f}%")

    print("\nBest of the 2021 bags this week")
    top = old.nlargest(10, "percent_change_7d")
    for _, r in top.iterrows():
        print(f"  {r['symbol']:<8}{r['percent_change_7d']:>+7.0f}%   {r['offPeak'] * 100:>+5.0f}% off its {int(r['peakYear'])} peak"
              f"   ${r['market_cap'] / 1e6:>7,.0f}M  {r['nm'][:20]}")
    print("\nWorst of the memecoins")
    bot = meme.nsmallest(6, "percent_change_7d")
    for _, r in bot.iterrows():
        print(f"  {r['symbol']:<8}{r['percent_change_7d']:>+7.0f}%   ${r['market_cap'] / 1e6:>7,.0f}M  {r['nm'][:20]}")

    qnt = f[f["symbol"] == "QNT"]
    note = None
    if len(qnt):
        q = qnt.iloc[0]
        note = {"symbol": "QNT", "pct7d": float(q["percent_change_7d"]),
                "offPeak": float(q["offPeak"]), "peakYear": int(q["peakYear"])}
        print(f"\n$QNT peaked in {note['peakYear']} and is {note['offPeak'] * 100:+.0f}% off that peak after "
              f"{note['pct7d']:+.0f}% this week, so it no longer qualifies as a bag.")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "old_bags.json").write_text(json.dumps({
        "asOf": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"), "market": mkt, "universe": int(len(f)),
        "cohorts": {
            "old": {"n": int(len(old)), "median7d": float(old["percent_change_7d"].median()),
                    "beat": float((old["percent_change_7d"] > mkt).mean())},
            "meme": {"n": int(len(meme)), "median7d": float(meme["percent_change_7d"].median()),
                     "beat": float((meme["percent_change_7d"] > mkt).mean())}},
        "topOld": [{"symbol": r["symbol"], "name": r["nm"], "pct7d": float(r["percent_change_7d"]),
                    "offPeak": float(r["offPeak"]), "mcap": float(r["market_cap"])}
                   for _, r in top.iterrows()],
        "worstMeme": [{"symbol": r["symbol"], "name": r["nm"], "pct7d": float(r["percent_change_7d"]),
                       "mcap": float(r["market_cap"])} for _, r in bot.iterrows()],
        "qnt": note,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'old_bags.json'}")


if __name__ == "__main__":
    main()
