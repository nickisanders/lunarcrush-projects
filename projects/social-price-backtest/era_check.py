#!/usr/bin/env python3
"""Era-split audit of the headline backtest result.

The spam/posts ratio's scale shifted across eras (see hype-detector v1.1
calibration): it behaves like a ratio in 2020-2022, saturates above 1 in
2023-2025, and partially normalizes in 2026. That skews WHICH days get the
"organic" label by era, so the pooled organic-vs-baseline comparison could be
confounded by era-specific return regimes. This re-runs the key comparison
within each era.

Usage:
    python3 era_check.py [--bootstrap 2000]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import HORIZONS, RAW_DIR, add_signals, bootstrap_diffs, load_coin

ERAS = {
    "2020-2022 (ratio behaves)": (2020, 2022),
    "2023-2025 (ratio saturated)": (2023, 2025),
    "2026 (partially normalized)": (2026, 2026),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    all_days = pd.concat(frames)

    btc = all_days[all_days["symbol"] == "BTC"]
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}
    )
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    eligible = all_days[
        (all_days["market_cap"] >= 50e6)
        & (all_days["volume_24h"].fillna(0) >= 1e6)
        & (all_days["med_interactions"] >= 2000)
        & all_days["z"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}d"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}d"] = eligible[f"fwd_{h}d"].clip(lo, hi)
        eligible[f"adj_{h}d"] = eligible[f"fwd_{h}d"] - eligible[f"btc_{h}d"]

    spike = (eligible["z"] >= 3.0) & (eligible["ret_1d"].abs() <= 0.02)
    organic = spike & (eligible["spam_ratio"].fillna(0) <= 0.5)
    eligible["grp"] = np.select(
        [organic, spike & ~organic], ["organic spike", "spam spike"], default="baseline"
    )
    eligible["year"] = eligible.index.year

    print("Headline claim under audit: organic spikes lift the +3d BTC-adjusted hit rate")
    print("(pooled result was 49.0% vs 41.9%, diff +7.2pp, p=0.003)\n")

    for era, (y0, y1) in ERAS.items():
        sub = eligible[(eligible["year"] >= y0) & (eligible["year"] <= y1)]
        n_org = (sub["grp"] == "organic spike").sum()
        n_base = (sub["grp"] == "baseline").sum()
        if n_org < 10:
            print(f"=== {era}: only {n_org} organic events, skipping ===\n")
            continue
        org3 = (sub.loc[sub["grp"] == "organic spike", "adj_3d"] > 0).mean()
        base3 = (sub.loc[sub["grp"] == "baseline", "adj_3d"] > 0).mean()
        print(f"=== {era} ===")
        print(f"organic events: {n_org:,} | baseline days: {n_base:,}")
        print(f"+3d hit rate: organic {org3:.3f} vs baseline {base3:.3f} (diff {org3 - base3:+.3f})")
        boots = bootstrap_diffs(sub, "grp", "organic spike", "baseline", args.bootstrap)
        key = boots[(boots["horizon"] == "+3d") & (boots["metric"] == "hit_rate_adj")].iloc[0]
        print(
            f"bootstrap: diff {key['diff']:+.3f}  CI [{key['ci_lo']:+.3f}, {key['ci_hi']:+.3f}]"
            f"  p={key['p_two_sided']:.4f}\n"
        )


if __name__ == "__main__":
    main()
