#!/usr/bin/env python3
"""Crypto's ten most-discussed coins: who holds the seats, and for how long.

Every day, rank every coin by social interactions and take the top ten. Then
ask two things: which coins are always there, and when a coin that is not
always there breaks in, how long does it stay?

Two filters are applied before ranking, because the raw list is not a list of
coins people are discussing:

- **Pegged and wrapped assets** are removed. Their conversation belongs to the
  asset they track.
- **Name collisions** are removed per coin-day: any coin carrying more than
  COLLISION_X times the day's median interactions per dollar of market cap.
  Without this filter, $GIGA, $S, $SHELL and $NIGHT are "top ten" on 30-60%
  of days, because those are words. See projects/name-collision. Single
  character tickers are dropped outright.

Usage: python3 top_ten.py
"""

import datetime as dt
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
TOP_N = 10
COLLISION_X = 100
FIXTURE_SHARE = 0.5  # in the top ten on more than half of all days
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def main() -> None:
    day = defaultdict(list)
    for f in sorted(glob.glob(str(RAW / "*.json"))):
        d = json.load(open(f))
        sym = d["coin"]["symbol"]
        # A one-character ticker collides with everything and survives the
        # per-day ratio test whenever the coin is large enough. $S is Sonic,
        # and also the letter s.
        if sym in PEGGED or len(sym) < 2:
            continue
        for r in d["rows"]:
            it, mc = r.get("interactions") or 0, r.get("market_cap") or 0
            if it > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((it, sym, it / mc))
    dates = sorted(day)

    top, dropped = {}, defaultdict(int)
    for dd in dates:
        rows = day[dd]
        med = np.median([x[2] for x in rows])
        clean = [(it, s) for it, s, ratio in rows if ratio <= med * COLLISION_X]
        for it, s, ratio in rows:
            if ratio > med * COLLISION_X:
                dropped[s] += 1
        top[dd] = set(s for _, s in sorted(clean, reverse=True)[:TOP_N])

    cnt = defaultdict(int)
    for dd in dates:
        for s in top[dd]:
            cnt[s] += 1
    n = len(dates)
    fixtures = sorted((s for s, c in cnt.items() if c / n > FIXTURE_SHARE), key=lambda s: -cnt[s])
    open_seats = TOP_N - len(fixtures)

    print(f"{n} days, {len(cnt)} distinct coins ever in the top {TOP_N}\n")
    print(f"FIXTURES: in the top {TOP_N} on more than {FIXTURE_SHARE * 100:.0f}% of days")
    for s in fixtures:
        print(f"  {s:<6}{cnt[s] / n * 100:>6.1f}%")
    print(f"\nThat leaves about {open_seats} seats for the other {len(cnt) - len(fixtures)} coins.\n")

    eps = []
    for s in cnt:
        run = 0
        for dd in dates:
            if s in top[dd]:
                run += 1
            else:
                if run:
                    eps.append((s, run))
                run = 0
        if run:
            eps.append((s, run))
    rot = np.array([l for s, l in eps if s not in fixtures])
    print(f"When one of them breaks in ({len(rot):,} stints):")
    print(f"  median stay        {np.median(rot):.0f} day")
    print(f"  gone next day      {(rot == 1).mean() * 100:.0f}%")
    print(f"  gone within 3 days {(rot <= 3).mean() * 100:.0f}%")
    print(f"  gone within a week {(rot <= 7).mean() * 100:.0f}%")
    print(f"  lasted a month     {(rot >= 30).mean() * 100:.1f}%")

    longest = sorted(((s, l) for s, l in eps if s not in fixtures), key=lambda x: -x[1])[:8]
    print("\nLongest stints by a non-fixture:")
    for s, l in longest:
        print(f"  {s:<8}{l:>4} days")

    churn = [len(top[b] - top[a]) for a, b in zip(dates, dates[1:])]
    print(f"\nNew entrants per day: {np.mean(churn):.2f}")

    hist = {str(k): int(v) for k, v in zip(*np.unique(np.clip(rot, 1, 31), return_counts=True))}
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "top_ten.json").write_text(json.dumps({
        "days": n, "distinctCoins": len(cnt), "topN": TOP_N,
        "fixtures": [{"symbol": s, "share": cnt[s] / n} for s in fixtures],
        "openSeats": open_seats,
        "stints": int(len(rot)), "medianStay": float(np.median(rot)),
        "goneNextDay": float((rot == 1).mean()), "goneWithin3": float((rot <= 3).mean()),
        "goneWithin7": float((rot <= 7).mean()), "lastedMonth": float((rot >= 30).mean()),
        "longest": [{"symbol": s, "days": int(l)} for s, l in longest],
        "newPerDay": float(np.mean(churn)),
        "stayHistogram": hist,
        "collisionsDropped": sorted(dropped.items(), key=lambda x: -x[1])[:12],
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'top_ten.json'}")


if __name__ == "__main__":
    main()
