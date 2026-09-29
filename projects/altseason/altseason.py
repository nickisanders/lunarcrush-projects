#!/usr/bin/env python3
"""Is it altseason? A number instead of a vibe.

The question crypto asks every week, answered the only way it can be: count
how many of the top 100 coins beat Bitcoin over the last 30 days, then put
today's count next to every other day since 2020.

The measure is deliberately plain. No index, no weighting, no threshold
somebody picked. The top 100 by market cap as of 30 days ago, excluding
Bitcoin itself, pegged assets and wrapped assets, and the share of them whose
30-day return beat Bitcoin's.

History comes from the cached daily files; today's reading comes from the
live API, so the series runs to the current day.

Usage: LUNARCRUSH_API_KEY=... python3 altseason.py
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
WINDOW = 30
TOP_N = 100
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


def history() -> pd.DataFrame:
    px = {}
    for f in glob.glob(str(RAW / "*.json")):
        d = json.load(open(f))
        s = d["coin"]["symbol"]
        if s in PEGGED or len(s) < 2:
            continue
        df = pd.DataFrame([(dt.datetime.fromtimestamp(r["time"], dt.UTC).date(),
                            r.get("close"), r.get("market_cap")) for r in d["rows"]],
                          columns=["date", "close", "mcap"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["mcap"] = pd.to_numeric(df["mcap"], errors="coerce")
        px[s] = df.dropna(subset=["close"]).set_index("date")

    btc = px["BTC"]
    dates = sorted(btc.index)
    out = []
    for i in range(WINDOW, len(dates)):
        d0, d1 = dates[i - WINDOW], dates[i]
        if d0 not in btc.index or d1 not in btc.index:
            continue
        br = btc.loc[d1, "close"] / btc.loc[d0, "close"] - 1
        caps = [(px[s].loc[d0, "mcap"], s) for s in px
                if s != "BTC" and d0 in px[s].index and d1 in px[s].index
                and pd.notna(px[s].loc[d0, "mcap"]) and px[s].loc[d0, "mcap"] > 0]
        caps.sort(reverse=True)
        top = [s for _, s in caps[:TOP_N]]
        if len(top) < 50:
            continue
        beat = sum(1 for s in top if (px[s].loc[d1, "close"] / px[s].loc[d0, "close"] - 1) > br)
        out.append((d1, beat / len(top), br))
    return pd.DataFrame(out, columns=["date", "share", "btc"]).set_index("date")


def today_reading() -> tuple[float, float, int, list]:
    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    L["nm"] = L["name"].astype(str)
    for c in ("market_cap", "percent_change_30d", "volume_24h"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L.sort_values("market_cap", ascending=False).drop_duplicates("symbol")
    L = L[~L["symbol"].isin(PEGGED) & (L["symbol"].str.len() >= 2) & L["percent_change_30d"].notna()]
    btc = float(L[L["symbol"] == "BTC"]["percent_change_30d"].iloc[0])
    alts = L[L["symbol"] != "BTC"].nlargest(TOP_N, "market_cap")
    beat = alts[alts["percent_change_30d"] > btc]
    winners = [{"symbol": r["symbol"], "name": r["nm"], "pct30d": float(r["percent_change_30d"]),
                "mcap": float(r["market_cap"])} for _, r in beat.nlargest(10, "percent_change_30d").iterrows()]
    return len(beat) / len(alts), btc / 100, len(alts), winners


def main() -> None:
    df = history()
    share, btc30, n, winners = today_reading()
    today = dt.date.today()
    pct = float((df["share"] < share).mean())

    print(f"History: {len(df):,} days, {df.index[0]} to {df.index[-1]}\n")
    print(f"SHARE OF THE TOP {TOP_N} BEATING BITCOIN OVER {WINDOW} DAYS")
    print(f"  today ({today}): {share * 100:.0f}%   Bitcoin {btc30 * 100:+.0f}% over the window, n={n}")
    print(f"  all-time median: {df['share'].median() * 100:.0f}%")
    print(f"  today sits at the {pct * 100:.0f}th percentile of {len(df):,} days")
    print(f"  days above 50% ever: {(df['share'] > 0.5).mean() * 100:.0f}%")

    print(f"\nBY YEAR   median   max   share of days above 50%")
    years = []
    for y in range(2020, today.year + 1):
        g = df[[d.year == y for d in df.index]]
        if len(g) < 10:
            continue
        years.append({"year": y, "median": float(g["share"].median()),
                      "max": float(g["share"].max()), "above": float((g["share"] > 0.5).mean())})
        print(f"  {y}:      {g['share'].median() * 100:>3.0f}%   {g['share'].max() * 100:>3.0f}%   {(g['share'] > 0.5).mean() * 100:>3.0f}%")

    print(f"\nTOP 100 COINS BEATING BITCOIN OVER {WINDOW} DAYS, BEST FIRST")
    for w in winners:
        print(f"  {w['symbol']:<8}{w['pct30d']:>+8.0f}%   ${w['mcap'] / 1e6:>8,.0f}M  {w['name'][:22]}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "altseason.json").write_text(json.dumps({
        "asOf": today.isoformat(), "window": WINDOW, "topN": TOP_N,
        "today": share, "btc30d": btc30, "n": n,
        "median": float(df["share"].median()), "percentile": pct,
        "daysAbove50": float((df["share"] > 0.5).mean()), "days": int(len(df)),
        "years": years, "winners": winners,
        "series": [{"date": d.isoformat(), "share": float(r["share"])} for d, r in df.iterrows()],
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'altseason.json'}")


if __name__ == "__main__":
    main()
