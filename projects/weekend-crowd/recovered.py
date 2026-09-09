#!/usr/bin/env python3
"""Do the events a deseasoned z-score recovers actually carry the edge?

deseason.py shows that removing the weekly seasonal from the baseline finds
12.9% more weekend events. That is only worth doing if those events behave like
real ones. This scores three groups against the same baseline, using the
organic-spike definition and month-block bootstrap from the main backtest:

  - kept:      organic spikes both scorers agree on
  - recovered: organic spikes only the deseasoned scorer finds
  - dropped:   organic spikes only the standard scorer finds

If "recovered" carries the edge and "dropped" does not, the seasonal adjustment
is finding signal rather than manufacturing events.

Usage: python3 recovered.py [--z 3.0] [--bootstrap 2000]
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
from analysis import HORIZONS, FLOOR, load_coin, add_signals, bootstrap_diffs  # noqa: E402
from deseason import add_deseasoned  # noqa: E402


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
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_deseasoned(add_signals(df)))
    all_days = pd.concat(frames)
    all_days["dow"] = all_days.index.dayofweek

    btc = all_days[all_days["symbol"] == "BTC"]
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS})
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    el = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna() & all_days["z_deseasoned"].notna()
        & all_days["fwd_7d"].notna() & (all_days["symbol"] != "BTC")
    ].copy()
    for h in HORIZONS:
        lo, hi = el[f"fwd_{h}d"].quantile([0.01, 0.99])
        el[f"fwd_{h}d"] = el[f"fwd_{h}d"].clip(lo, hi)
        el[f"adj_{h}d"] = el[f"fwd_{h}d"] - el[f"btc_{h}d"]

    organic = (el["ret_1d"].abs() <= args.flat) & (el["spam_ratio"] <= args.spam_split)
    a, b = el["z"] >= args.z, el["z_deseasoned"] >= args.z
    el["group"] = "baseline"
    el.loc[organic & a & b, "group"] = "kept"
    el.loc[organic & ~a & b, "group"] = "recovered"
    el.loc[organic & a & ~b, "group"] = "dropped"

    for g in ("kept", "recovered", "dropped"):
        sub = el[el["group"] == g]
        wknd = int(sub["dow"].isin([5, 6]).sum())
        print(f"  {g:<10} {len(sub):>5,} coin-days  ({wknd} on weekends, {wknd / max(len(sub), 1) * 100:.0f}%)")

    print(f"\n{'group':<12}{'horizon':>8}{'beats-BTC vs baseline':>24}{'95% CI':>22}{'p':>8}")
    recs = []
    for g in ("kept", "recovered", "dropped"):
        r = bootstrap_diffs(el, "group", g, "baseline", args.bootstrap)
        recs.append(r)
        for _, row in r[r["metric"] == "hit_rate_adj"].iterrows():
            print(f"{g:<12}{row['horizon']:>8}{row['diff'] * 100:>23.1f}pp"
                  f"{f'[{row.ci_lo * 100:+.1f}, {row.ci_hi * 100:+.1f}]':>22}{row['p_two_sided']:>8.3f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "recovered.json").write_text(json.dumps({
        "counts": {g: int((el["group"] == g).sum()) for g in ("kept", "recovered", "dropped")},
        "weekendShare": {g: float(el[el["group"] == g]["dow"].isin([5, 6]).mean())
                         for g in ("kept", "recovered", "dropped")},
        "results": pd.concat(recs).to_dict("records")}, indent=2))
    print(f"\nWrote {HERE / 'out' / 'recovered.json'}")


if __name__ == "__main__":
    main()
