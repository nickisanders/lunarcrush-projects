#!/usr/bin/env python3
"""The month that just ended: who gained price, and who gained the crowd.

Most month-in-review posts rank by price. This ranks by both and puts them
side by side, because the overlap is the interesting part: a coin can double
without anyone noticing, and a coin can triple its audience without moving.

Attention is measured as the change in daily active contributors, comparing
the last seven days of the month against the seven days before the month
started, so a single viral day cannot carry it.

Usage: LUNARCRUSH_API_KEY=... python3 month_review.py [--top 40]
"""

import argparse
import datetime as dt
import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
API = "https://lunarcrush.com/api4"
MIN_MCAP, MIN_VOL = 100e6, 2e6
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
            time.sleep(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40, help="how many coins to pull history for")
    args = ap.parse_args()

    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    L["nm"] = L["name"].astype(str)
    for c in ("market_cap", "percent_change_30d", "volume_24h", "interactions_24h"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L.sort_values("market_cap", ascending=False).drop_duplicates("symbol")
    f = L[(L["market_cap"] > MIN_MCAP) & (L["volume_24h"] > MIN_VOL)
          & (L["symbol"].str.len() >= 2) & ~L["symbol"].isin(PEGGED)
          & L["percent_change_30d"].notna()].copy()

    btc = float(f[f["symbol"] == "BTC"]["percent_change_30d"].iloc[0])
    market = float(f["percent_change_30d"].median())
    print(f"{len(f)} coins over ${MIN_MCAP/1e6:.0f}M. Bitcoin {btc:+.1f}%, market median {market:+.1f}% over 30 days.\n")

    # Pull daily history for the loudest and the biggest movers, since those
    # are the only ones that can top either list.
    pool = pd.concat([f.nlargest(args.top, "percent_change_30d"),
                      f.nlargest(args.top, "interactions_24h")]).drop_duplicates("symbol")
    # The month that just ended, and the week before it started.
    today = dt.date.today()
    month_end = today.replace(day=1) - dt.timedelta(days=1)
    month_start = month_end.replace(day=1)
    win_a1, win_a0 = month_end, month_end - dt.timedelta(days=6)
    win_b1, win_b0 = month_start - dt.timedelta(days=1), month_start - dt.timedelta(days=7)
    print(f"{month_start:%B %Y}: crowd over {win_a0} to {win_a1}, against {win_b0} to {win_b1}")
    print(f"Pulling history for {len(pool)} coins...")
    rows = []
    for _, r in pool.iterrows():
        d = get(f"/public/coins/{r['symbol']}/time-series/v2?bucket=day&interval=3m")
        data = (d or {}).get("data") or []
        if len(data) < 40:
            continue
        h = pd.DataFrame(data)
        h["contributors_active"] = pd.to_numeric(h["contributors_active"], errors="coerce")
        h["d"] = pd.to_datetime(h["time"], unit="s").dt.date
        # Index by date, not position: a coin with a gap in its history would
        # otherwise have its two windows silently shifted against each other.
        before = h[(h["d"] >= win_b0) & (h["d"] <= win_b1)]["contributors_active"].median()
        after = h[(h["d"] >= win_a0) & (h["d"] <= win_a1)]["contributors_active"].median()
        if not before or before <= 0 or pd.isna(after):
            continue
        rows.append({"symbol": r["symbol"], "name": r["nm"], "pct30d": float(r["percent_change_30d"]),
                     "mcap": float(r["market_cap"]), "crowdBefore": float(before),
                     "crowdAfter": float(after), "crowdChange": float(after / before - 1)})
        time.sleep(0.15)

    d = pd.DataFrame(rows)
    if d.empty:
        raise SystemExit("no coins returned usable history")
    price = d.nlargest(10, "pct30d")
    crowd = d.nlargest(10, "crowdChange")
    both = set(price["symbol"]) & set(crowd["symbol"])

    print(f"\nBIGGEST PRICE GAINS")
    for _, r in price.iterrows():
        mark = "  <-- also top 10 by crowd" if r["symbol"] in both else ""
        print(f"  {r['symbol']:<9}{r['pct30d']:>+7.0f}%   crowd {r['crowdChange']*100:>+6.0f}%   {r['name'][:20]}{mark}")
    print(f"\nBIGGEST CROWD GAINS")
    for _, r in crowd.iterrows():
        mark = "  <-- also top 10 by price" if r["symbol"] in both else ""
        print(f"  {r['symbol']:<9}{r['crowdChange']*100:>+7.0f}%   price {r['pct30d']:>+6.0f}%   "
              f"{r['crowdBefore']:>5,.0f} to {r['crowdAfter']:>6,.0f} people/day  {r['name'][:16]}{mark}")
    print(f"\nin both lists: {len(both)} of 10  ({', '.join(sorted(both)) if both else 'none'})")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "month.json").write_text(json.dumps({
        "asOf": dt.date.today().isoformat(), "month": month_start.strftime("%B %Y"), "btc": btc, "market": market, "universe": int(len(f)),
        "price": price.to_dict("records"), "crowd": crowd.to_dict("records"),
        "both": sorted(both),
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'month.json'}")


if __name__ == "__main__":
    main()
