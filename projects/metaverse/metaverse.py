#!/usr/bin/env python3
"""The 2021 metaverse bags moved together. Did anyone turn up for it?

A price move across a recognisable cohort is easy to spot and easy to
overstate. This takes the cohort, checks it really did move together against
the market, then asks the question the price alone cannot answer: has the
crowd come back, or is this only money?

Cohort membership is by LunarCrush's own `gaming` and `nft` categories plus a
drawdown filter, not by a hand-written list of names, so the cohort cannot be
assembled after seeing the returns.

Usage: LUNARCRUSH_API_KEY=... python3 metaverse.py
"""

import datetime as dt
import glob
import json
import os
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
API = "https://lunarcrush.com/api4"
MIN_MCAP, MIN_VOL = 20e6, 5e5
DOWN_FROM_PEAK = -0.90   # the cohort is defined by how far it fell, not by name
PEAK_BY = 2022
TAGS = ("gaming", "nft")
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
                return {}
            time.sleep(3)


def peaks() -> dict:
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
          & (L["symbol"].str.len() >= 2) & ~L["symbol"].isin(PEGGED)].copy()
    market = float(f["percent_change_24h"].median())

    pk = peaks()
    f["peakMcap"] = [pk.get(s, (None, None))[0] for s in f["symbol"]]
    f["peakYear"] = [pk.get(s, (None, None))[1] for s in f["symbol"]]
    f["offPeak"] = f["market_cap"] / f["peakMcap"] - 1
    tagged = f["categories"].astype(str).str.contains("|".join(TAGS), na=False)
    cohort = f[tagged & (f["peakYear"] <= PEAK_BY) & (f["offPeak"] <= DOWN_FROM_PEAK)].copy()

    print(f"{len(f)} coins over ${MIN_MCAP/1e6:.0f}M. Market median today: {market:+.1f}%")
    print(f"Cohort: tagged {' or '.join(TAGS)}, peaked {PEAK_BY} or earlier, "
          f"{abs(DOWN_FROM_PEAK)*100:.0f}%+ below that peak. {len(cohort)} coins.\n")
    print(f"median today {cohort['percent_change_24h'].median():+.1f}%, "
          f"{int((cohort['percent_change_24h'] > market).sum())} of {len(cohort)} beat the market")

    # Has the crowd come back, or is this only price?
    rows = []
    for _, r in cohort.sort_values("market_cap", ascending=False).iterrows():
        d = get(f"/public/coins/{r['symbol']}/time-series/v2?bucket=day&interval=3m")
        data = (d or {}).get("data") or []
        if len(data) < 40:
            continue
        h = pd.DataFrame(data)
        h["c"] = pd.to_numeric(h["contributors_active"], errors="coerce")
        before, after = h["c"].iloc[-37:-7].median(), h["c"].iloc[-7:].median()
        rows.append({"symbol": r["symbol"], "name": r["nm"], "pct24h": float(r["percent_change_24h"]),
                     "pct7d": float(r["percent_change_7d"]), "mcap": float(r["market_cap"]),
                     "peakMcap": float(r["peakMcap"]), "offPeak": float(r["offPeak"]),
                     "peakYear": int(r["peakYear"]),
                     "crowdBefore": float(before), "crowdAfter": float(after),
                     "crowdChange": float(after / before - 1) if before else None})
        time.sleep(0.15)

    d = pd.DataFrame(rows)
    print(f"\n{'coin':<9}{'24h':>8}{'7d':>7}{'mcap':>9}{'peak':>10}{'off peak':>10}{'crowd':>9}  name")
    for _, r in d.iterrows():
        cc = f"{r['crowdChange']*100:+.0f}%" if r["crowdChange"] is not None else "n/a"
        print(f"{r['symbol']:<9}{r['pct24h']:>+7.1f}%{r['pct7d']:>+6.0f}%{r['mcap']/1e6:>8,.0f}M"
              f"{r['peakMcap']/1e9:>9.1f}B{r['offPeak']*100:>9.0f}%{cc:>9}  {r['name'][:20]}")

    cm = d["crowdChange"].median()
    print(f"\nmedian crowd change over the last week vs the prior month: {cm*100:+.0f}%")
    print(f"coins whose crowd grew: {int((d['crowdChange'] > 0).sum())} of {len(d)}")
    print(f"combined market cap now ${d['mcap'].sum()/1e9:.1f}B against ${d['peakMcap'].sum()/1e9:.1f}B at their peaks")

    (HERE / "out").mkdir(exist_ok=True)
    payload = json.dumps({
        "asOf": dt.date.today().isoformat(), "market": market, "universe": int(len(f)),
        "cohortMedian": float(cohort["percent_change_24h"].median()),
        "beat": int((cohort["percent_change_24h"] > market).sum()), "n": int(len(cohort)),
        "crowdMedian": float(cm), "crowdGrew": int((d["crowdChange"] > 0).sum()),
        "mcapNow": float(d["mcap"].sum()), "mcapPeak": float(d["peakMcap"].sum()),
        "coins": d.to_dict("records"),
    }, indent=2)
    (HERE / "out" / "metaverse.json").write_text(payload)

    # Keep a dated copy. The latest run used to be the only run, so asking
    # "what happened after the last post" meant having copied the file aside
    # by hand first. A cohort's follow-up is often the better story than its
    # first appearance, and that comparison is impossible to reconstruct after
    # the fact: these are point-in-time market and crowd readings, not history
    # the API will hand back.
    snaps = HERE / "out" / "history"
    snaps.mkdir(exist_ok=True)
    (snaps / f"metaverse-{dt.date.today().isoformat()}.json").write_text(payload)

    print(f"\nWrote {HERE / 'out' / 'metaverse.json'} and a dated copy in out/history/")


if __name__ == "__main__":
    main()
