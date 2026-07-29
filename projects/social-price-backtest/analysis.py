#!/usr/bin/env python3
"""Backtest: does a social interaction spike lead price?

Event definition (per coin, per day):
  - z-score of log(1 + interactions) vs the trailing 30 days >= Z_MIN
  - price flat on event day: |close-to-close return| <= FLAT_MAX
  - eligibility: market cap >= MCAP_MIN at event time, trailing median
    interactions >= FLOOR (so z-scores aren't computed on noise)

Forward returns are measured close-to-close at +1d, +3d, +7d, both raw and
BTC-adjusted (subtracting BTC's return over the same window). The baseline is
every eligible coin-day that did NOT have a spike, same filters.

Usage:
    python3 analysis.py [--z 3.0] [--flat 0.02] [--mcap 50e6] [--spam-max 0.5]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"

HORIZONS = [1, 3, 7]
TRAILING = 30
FLOOR = 2000  # trailing median interactions floor


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob["rows"]
    if len(rows) < TRAILING + max(HORIZONS) + 5:
        return None
    df = pd.DataFrame(rows)
    need = {"time", "close", "interactions", "market_cap"}
    if not need.issubset(df.columns):
        return None
    for col in ["time", "close", "interactions", "market_cap", "spam", "posts_created", "volume_24h"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["time", "close", "interactions"])
    df["date"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    df["symbol"] = blob["coin"]["symbol"]
    df["coin_id"] = blob["coin"]["id"]
    return df


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    li = np.log1p(df["interactions"].astype(float))
    roll = li.shift(1).rolling(TRAILING)  # trailing window excludes today
    df["z"] = (li - roll.mean()) / roll.std()
    df["med_interactions"] = df["interactions"].shift(1).rolling(TRAILING).median()
    df["ret_1d"] = df["close"].pct_change()
    for h in HORIZONS:
        df[f"fwd_{h}d"] = df["close"].shift(-h) / df["close"] - 1
    if "spam" in df.columns and "posts_created" in df.columns:
        df["spam_ratio"] = df["spam"] / df["posts_created"].clip(lower=1)
    else:
        df["spam_ratio"] = np.nan
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--spam-max", type=float, default=0.5)
    ap.add_argument("--min-volume", type=float, default=1e6)
    args = ap.parse_args()

    frames = []
    files = sorted(RAW_DIR.glob("*.json"))
    print(f"Loading {len(files)} coins...")
    for p in files:
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    all_days = pd.concat(frames)
    print(f"{len(frames)} coins usable, {len(all_days):,} coin-days")

    # BTC as the market proxy for adjusted returns
    btc = all_days[all_days["symbol"] == "BTC"]
    if btc.empty:
        raise SystemExit("BTC missing from raw data; cannot compute adjusted returns")
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}
    )
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    eligible = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days.get("volume_24h", 0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ]
    # Winsorize forward returns at the 1st/99th percentile of the eligible set.
    # Raw crypto price data contains redenominations and near-zero-price
    # glitches that produce fake 10,000%+ "returns" and destroy means.
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}d"].quantile([0.01, 0.99])
        eligible = eligible.assign(**{f"fwd_{h}d": eligible[f"fwd_{h}d"].clip(lo, hi)})
    spike = (eligible["z"] >= args.z) & (eligible["ret_1d"].abs() <= args.flat)
    if args.spam_max < 1:
        spike &= eligible["spam_ratio"].fillna(0) <= args.spam_max
    events = eligible[spike]
    baseline = eligible[~spike]
    print(f"eligible coin-days: {len(eligible):,} | events: {len(events):,}")

    rows = []
    for h in HORIZONS:
        for name, grp in [("event", events), ("baseline", baseline)]:
            raw = grp[f"fwd_{h}d"]
            adj = raw - grp[f"btc_{h}d"]
            rows.append(
                {
                    "horizon": f"+{h}d",
                    "group": name,
                    "n": len(grp),
                    "mean_raw": raw.mean(),
                    "median_raw": raw.median(),
                    "mean_btc_adj": adj.mean(),
                    "median_btc_adj": adj.median(),
                    "hit_rate_adj": (adj > 0).mean(),
                }
            )
    summary = pd.DataFrame(rows)

    OUT_DIR.mkdir(exist_ok=True)
    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    events.reset_index()[
        ["date", "symbol", "z", "ret_1d", "market_cap", "spam_ratio"]
        + [f"fwd_{h}d" for h in HORIZONS]
    ].to_csv(OUT_DIR / "events.csv", index=False)

    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
    print("\n=== Forward returns: social spike events vs baseline ===")
    print(summary.to_string(index=False))
    print(f"\nWrote {OUT_DIR / 'summary.csv'} and {OUT_DIR / 'events.csv'}")


if __name__ == "__main__":
    main()
