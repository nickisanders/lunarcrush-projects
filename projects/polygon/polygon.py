#!/usr/bin/env python3
"""Where did Polygon go? Its rank in crypto conversation, 2020 to 2026.

Polygon (MATIC, then POL from September 2024) was one of the most discussed
coins in crypto for four years. This traces its position by ranking it
against every other coin on every day, and does the same for peer chains so
the fall can be read as either Polygon's or a narrative's.

Three data decisions, each forced by the source:

- **MATIC + POL are summed.** LunarCrush delisted MATIC as a coin at the
  rebrand and the conversation moved to POL. Either ticker alone shows a
  false cliff in September 2024.
- **The "polygon" topic is not used.** It is a word: geometry, a games
  website. Its series rises while MATIC+POL falls (correlation 0.27 since
  2023). See projects/name-collision.
- **Rank by daily active contributors, not interactions.** MATIC's 2020
  interactions contain bot spikes (2.4M interactions from 35 accounts on
  2020-02-15), and interactions-per-contributor jumps from 16 to 1,482 across
  LunarCrush's 2023 counting change. Contributor counts are stable across
  both, and rank against the market is stable across everything.

Peers: SOL, BNB, AVAX, ARB, OP, SUI, APT. Pegged assets and per-day name
collisions are removed from the ranking universe as in projects/top-ten.

Usage: python3 polygon.py    (reads raw_coins.json; refresh with pull.py)
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
PEERS = ["SOL", "BNB", "AVAX", "ARB", "OP", "SUI", "APT"]
COLLISION_X = 100
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "MSOL", "CBETH", "WBETH"}


def by_day(rows, key="contributors_active") -> dict:
    return {dt.datetime.fromtimestamp(r["time"], dt.UTC).date(): (r.get(key) or 0) for r in rows}


def main() -> None:
    day = defaultdict(list)
    for f in sorted(glob.glob(str(RAW / "*.json"))):
        d = json.load(open(f))
        sym = d["coin"]["symbol"]
        if sym in PEGGED or len(sym) < 2 or sym == "POL":
            continue
        for r in d["rows"]:
            c, it, mc = r.get("contributors_active") or 0, r.get("interactions") or 0, r.get("market_cap") or 0
            if c > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((c, it / mc))
    universe = {}
    for dd, lst in day.items():
        med = np.median([x[1] for x in lst])
        universe[dd] = sorted([c for c, ratio in lst if ratio <= med * COLLISION_X], reverse=True)

    raw = json.load(open(HERE / "raw_coins.json"))
    series = {"Polygon": defaultdict(int)}
    for sym in ("MATIC", "POL"):
        for dd, v in by_day(raw[sym]).items():
            series["Polygon"][dd] += v
    for sym in PEERS:
        series[sym] = by_day(raw[sym])

    rows = []
    for name, s in series.items():
        for dd in sorted(universe):
            v = s.get(dd, 0)
            if v > 0:
                rows.append((name, pd.Timestamp(dd), v, 1 + sum(1 for c in universe[dd] if c > v)))
    df = pd.DataFrame(rows, columns=["coin", "date", "contributors", "rank"])

    poly = df[df.coin == "Polygon"].set_index("date")
    m = poly.resample("ME").agg(rank=("rank", "median"), contributors=("contributors", "mean"),
                                top20=("rank", lambda s: (s <= 20).mean()))
    df["half"] = df.date.dt.year.astype(str) + "H" + ((df.date.dt.month > 6) + 1).astype(str)
    halves = df.groupby(["half", "coin"])["rank"].median().unstack("coin")[["Polygon"] + PEERS]

    print("POLYGON, median rank by daily contributors, by half-year")
    print(f"{'half':<8}{'rank':>6}{'top-20 days':>13}{'contributors':>14}")
    hp = poly.copy()
    hp["half"] = hp.index.year.astype(str) + "H" + ((hp.index.month > 6) + 1).astype(str)
    for h, g in hp.groupby("half"):
        print(f"{h:<8}{g['rank'].median():>6.0f}{(g['rank'] <= 20).mean() * 100:>12.0f}%{g['contributors'].mean():>14,.0f}")

    best = m["rank"].idxmin()
    peak_c = m["contributors"].idxmax()
    last = m.iloc[-1]
    first_out = m[(m.index >= "2024-01-01") & (m["top20"] == 0)].index.min()
    print(f"\nbest month: {best:%b %Y}, median rank {m['rank'].min():.0f}")
    print(f"most contributors: {peak_c:%b %Y}, {m['contributors'].max():,.0f} a day")
    print(f"first month since 2024 with zero top-20 days: {first_out:%b %Y}")
    print(f"latest: {m.index[-1]:%b %Y}, rank {last['rank']:.0f}, {last['contributors']:,.0f} contributors a day")

    print("\nPEERS, median rank by half-year")
    print(halves.round(0).to_string())
    print("\nH1 2024 -> latest, places lost (positive = fell)")
    moves = {}
    for c in halves.columns:
        a, b = halves[c].get("2024H1"), halves[c].iloc[-1]
        moves[c] = {"from": float(a), "to": float(b), "change": float(b - a)}
        print(f"  {c:<8}{a:>5.0f} -> {b:>5.0f}   {b - a:+.0f}")

    (HERE / "out").mkdir(exist_ok=True)
    m.to_csv(HERE / "out" / "polygon_monthly.csv")
    halves.to_csv(HERE / "out" / "peer_halves.csv")
    (HERE / "out" / "polygon.json").write_text(json.dumps({
        "monthly": [{"month": d.strftime("%Y-%m"), "rank": float(r["rank"]),
                     "contributors": float(r["contributors"]), "top20": float(r["top20"])}
                    for d, r in m.iterrows()],
        "bestMonth": best.strftime("%Y-%m"), "bestRank": float(m["rank"].min()),
        "peakContributorsMonth": peak_c.strftime("%Y-%m"), "peakContributors": float(m["contributors"].max()),
        "firstMonthOutOfTop20": first_out.strftime("%Y-%m"),
        "latestMonth": m.index[-1].strftime("%Y-%m"), "latestRank": float(last["rank"]),
        "latestContributors": float(last["contributors"]),
        "peers": {h: {c: (None if pd.isna(v) else float(v)) for c, v in row.items()}
                  for h, row in halves.iterrows()},
        "moves": moves,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'polygon.json'}")


if __name__ == "__main__":
    main()
