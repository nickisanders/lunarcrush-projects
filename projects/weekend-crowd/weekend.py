#!/usr/bin/env python3
"""Crypto never closes. The people talking about it do.

Markets run 24/7, so the standard assumption is that a weekday and a weekend
are the same trading environment. The conversation is not. This measures the
gap and then asks the only question that matters: does an attention spike that
lands on a Saturday mean something different from one that lands on a Tuesday?

Three things get measured:

1. **How much smaller the weekend crowd is**, market-wide, by weekday.
2. **Whether spikes fire disproportionately on any weekday.** A z-score against
   a trailing 30-day window mixes weekdays and weekends, so a weekly seasonal
   component sits inside the baseline every spike is measured against.
3. **Whether weekend spikes carry the same forward edge**, using the same
   organic-spike definition, BTC adjustment and month-block bootstrap as the
   main backtest in projects/social-price-backtest.

Usage:
    python3 weekend.py [--z 3.0] [--flat 0.02] [--bootstrap 2000]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BACKTEST = HERE.parent / "social-price-backtest"
RAW_DIR = BACKTEST / "data" / "raw"
sys.path.insert(0, str(BACKTEST))

from analysis import HORIZONS, FLOOR, load_coin, add_signals, bootstrap_diffs  # noqa: E402

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# LunarCrush changed how spam is counted during 2023: the share of rows where
# spam exceeds posts_created jumps from 4.7% (2022) to 55.5% (2023). Anything
# using spam_ratio is therefore split at this boundary and reported both ways.
BREAK = pd.Timestamp("2023-01-01")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--spam-split", type=float, default=0.5)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    files = sorted(RAW_DIR.glob("*.json"))
    print(f"Loading {len(files)} coins...")
    for p in files:
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    all_days = pd.concat(frames)
    all_days["dow"] = all_days.index.dayofweek
    print(f"{len(frames)} coins usable, {len(all_days):,} coin-days\n")

    # 1. How big is the crowd, by weekday.
    print("=" * 68)
    print("1. THE CROWD IS SMALLER ON WEEKENDS")
    print("=" * 68)
    per_day = all_days[all_days["interactions"] > 0].groupby("dow").agg(
        interactions=("interactions", "median"),
        contributors=("contributors_active", "median")
        if "contributors_active" in all_days.columns else ("interactions", "median"),
    )
    wk = per_day.loc[0:4, "interactions"].mean()
    print(f"{'day':<6}{'median interactions':>22}{'vs weekday mean':>18}")
    for d in range(7):
        v = per_day.loc[d, "interactions"]
        print(f"{DAYS[d]:<6}{v:>22,.0f}{v / wk * 100 - 100:>17.1f}%")
    sat_sun = per_day.loc[5:6, "interactions"].mean()
    print(f"\nweekend vs weekday, median interactions: {sat_sun / wk * 100 - 100:.1f}%")

    # 2. Does the spike detector fire evenly across the week?
    btc = all_days[all_days["symbol"] == "BTC"]
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS})
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    eligible = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}d"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}d"] = eligible[f"fwd_{h}d"].clip(lo, hi)
        eligible[f"adj_{h}d"] = eligible[f"fwd_{h}d"] - eligible[f"btc_{h}d"]

    eligible["spike"] = eligible["z"] >= args.z
    print("\n" + "=" * 68)
    print("2. BUT THE SPIKE DETECTOR FIRES EVENLY")
    print("=" * 68)
    print(f"{'day':<6}{'coin-days':>12}{'spikes':>9}{'spike rate':>13}")
    rates = {}
    for d in range(7):
        sub = eligible[eligible["dow"] == d]
        r = sub["spike"].mean()
        rates[d] = r
        print(f"{DAYS[d]:<6}{len(sub):>12,}{int(sub['spike'].sum()):>9,}{r * 100:>12.2f}%")
    wr = np.mean([rates[d] for d in range(5)])
    er = np.mean([rates[d] for d in (5, 6)])
    print(f"\nweekday spike rate {wr * 100:.2f}%  weekend {er * 100:.2f}%  ({er / wr * 100 - 100:+.1f}%)")

    # 3. Do weekend spikes carry the same edge?
    organic = eligible["spike"] & (eligible["ret_1d"].abs() <= args.flat) & \
              (eligible["spam_ratio"] <= args.spam_split)
    eligible["group"] = "baseline"
    eligible.loc[organic & eligible["dow"].isin([5, 6]), "group"] = "weekend_organic"
    eligible.loc[organic & ~eligible["dow"].isin([5, 6]), "group"] = "weekday_organic"

    print("\n" + "=" * 68)
    print("3. DO WEEKEND SPIKES CARRY THE SAME EDGE?")
    print("=" * 68)
    for g in ("weekday_organic", "weekend_organic"):
        print(f"  {g}: {int((eligible['group'] == g).sum()):,} coin-days")

    out = []
    for g in ("weekday_organic", "weekend_organic"):
        r = bootstrap_diffs(eligible, "group", g, "baseline", args.bootstrap)
        out.append(r)
    res = pd.concat(out)
    hits = res[res["metric"] == "hit_rate_adj"]
    print(f"\n{'comparison':<34}{'horizon':>8}{'beats-BTC diff':>17}{'95% CI':>22}{'p':>8}")
    for _, r in hits.iterrows():
        print(f"{r['comparison']:<34}{r['horizon']:>8}{r['diff'] * 100:>16.1f}pp"
              f"{f'[{r.ci_lo * 100:+.1f}, {r.ci_hi * 100:+.1f}]':>22}{r['p_two_sided']:>8.3f}")

    # Head-to-head, so the difference is not read off two separate comparisons.
    print("\nweekend vs weekday directly (not against baseline):")
    h2h = bootstrap_diffs(eligible, "group", "weekend_organic", "weekday_organic", args.bootstrap)
    for _, r in h2h[h2h["metric"] == "hit_rate_adj"].iterrows():
        print(f"  {r['horizon']}: {r['diff'] * 100:+.1f}pp  "
              f"[{r.ci_lo * 100:+.1f}, {r.ci_hi * 100:+.1f}]  p={r['p_two_sided']:.3f}")

    HERE.joinpath("out").mkdir(exist_ok=True)
    payload = {
        "byDay": {DAYS[d]: {"medianInteractions": float(per_day.loc[d, "interactions"]),
                            "spikeRate": float(rates[d]),
                            "coinDays": int((eligible["dow"] == d).sum())} for d in range(7)},
        "weekendCrowdGap": float(sat_sun / wk - 1),
        "weekdaySpikeRate": float(wr), "weekendSpikeRate": float(er),
        "counts": {g: int((eligible["group"] == g).sum())
                   for g in ("weekday_organic", "weekend_organic")},
        "results": res.to_dict("records"),
        "headToHead": h2h.to_dict("records"),
    }
    (HERE / "out" / "weekend.json").write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {HERE / 'out' / 'weekend.json'}")


if __name__ == "__main__":
    main()
