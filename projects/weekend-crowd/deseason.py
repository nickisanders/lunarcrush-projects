#!/usr/bin/env python3
"""A z-score against a mixed window under-detects weekend events.

The standard attention-spike detector takes log interactions, subtracts a
trailing 30-day mean and divides by the trailing standard deviation. That
window contains both weekdays and weekends. Because weekend conversation runs
about 7% below weekday conversation, every Saturday and Sunday starts below the
mean it is scored against, and needs a larger real jump to clear the same
threshold. The weekly seasonal also inflates the standard deviation in the
denominator, which raises the bar for every day of the week.

This measures the size of that distortion and tests the fix: subtract each
coin's own day-of-week offset before scoring.

Usage: python3 deseason.py [--z 3.0]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BACKTEST = HERE.parent / "social-price-backtest"
sys.path.insert(0, str(BACKTEST))
from analysis import HORIZONS, FLOOR, load_coin, add_signals  # noqa: E402

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TRAILING = 30


def add_deseasoned(df: pd.DataFrame) -> pd.DataFrame:
    """z-score after removing the coin's own day-of-week offset.

    The offset is estimated on a trailing 8-week window of the same weekday,
    shifted so it never sees today. Using the coin's own history rather than a
    market-wide constant keeps coins with genuinely different weekly rhythms
    from being forced onto one shape.
    """
    li = np.log1p(df["interactions"].astype(float))
    dow = df.index.dayofweek
    # Trailing mean of log interactions for this weekday, excluding today.
    same_dow = li.groupby(dow).transform(lambda s: s.shift(1).rolling(8, min_periods=4).mean())
    overall = li.shift(1).rolling(TRAILING, min_periods=20).mean()
    offset = (same_dow - overall).fillna(0.0)
    adj = li - offset
    roll = adj.shift(1).rolling(TRAILING)
    df["z_deseasoned"] = (adj - roll.mean()) / roll.std()
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    args = ap.parse_args()

    frames = []
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_deseasoned(add_signals(df)))
    all_days = pd.concat(frames)
    all_days["dow"] = all_days.index.dayofweek

    el = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna() & all_days["z_deseasoned"].notna()
        & all_days["fwd_7d"].notna() & (all_days["symbol"] != "BTC")
    ].copy()
    print(f"{len(el):,} eligible coin-days\n")

    print(f"{'day':<6}{'standard z':>14}{'deseasoned z':>16}{'events gained':>16}")
    rows = {}
    for d in range(7):
        s = el[el["dow"] == d]
        a, b = (s["z"] >= args.z).mean(), (s["z_deseasoned"] >= args.z).mean()
        na, nb = int((s["z"] >= args.z).sum()), int((s["z_deseasoned"] >= args.z).sum())
        rows[DAYS[d]] = {"standard": a, "deseasoned": b, "nStandard": na, "nDeseasoned": nb}
        print(f"{DAYS[d]:<6}{a * 100:>13.2f}%{b * 100:>15.2f}%{nb - na:>16,}")

    def spread(key):
        v = [rows[DAYS[d]][key] for d in range(7)]
        return (max(v) - min(v)) / np.mean(v) * 100

    wa = np.mean([rows[DAYS[d]]["standard"] for d in range(5)])
    ea = np.mean([rows[DAYS[d]]["standard"] for d in (5, 6)])
    wb = np.mean([rows[DAYS[d]]["deseasoned"] for d in range(5)])
    eb = np.mean([rows[DAYS[d]]["deseasoned"] for d in (5, 6)])
    print(f"\nweekend deficit, standard z:   {ea / wa * 100 - 100:+.1f}%")
    print(f"weekend deficit, deseasoned z: {eb / wb * 100 - 100:+.1f}%")
    print(f"max-min spread across the week, standard:   {spread('standard'):.1f}% of mean")
    print(f"max-min spread across the week, deseasoned: {spread('deseasoned'):.1f}% of mean")
    tot_a = sum(rows[d]["nStandard"] for d in rows)
    tot_b = sum(rows[d]["nDeseasoned"] for d in rows)
    print(f"\ntotal events: {tot_a:,} -> {tot_b:,}  ({tot_b / tot_a * 100 - 100:+.1f}%)")
    wknd_a = sum(rows[DAYS[d]]["nStandard"] for d in (5, 6))
    wknd_b = sum(rows[DAYS[d]]["nDeseasoned"] for d in (5, 6))
    print(f"weekend events: {wknd_a:,} -> {wknd_b:,}  ({wknd_b / wknd_a * 100 - 100:+.1f}%)")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "deseason.json").write_text(json.dumps({
        "byDay": rows, "weekendDeficitStandard": ea / wa - 1,
        "weekendDeficitDeseasoned": eb / wb - 1,
        "totalStandard": tot_a, "totalDeseasoned": tot_b,
        "weekendStandard": wknd_a, "weekendDeseasoned": wknd_b}, indent=2))
    print(f"\nWrote {HERE / 'out' / 'deseason.json'}")


if __name__ == "__main__":
    main()
