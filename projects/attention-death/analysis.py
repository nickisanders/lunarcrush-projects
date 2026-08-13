#!/usr/bin/env python3
"""When a coin's conversation dies, what happens to its price?

Every study in this repo so far looks at attention spiking. This looks at the
opposite: coins whose conversation collapses while their market cap is still
intact. The lights are on and nobody is home.

A death event is a coin-day where:
  - interactions have fallen to <= COLLAPSE of the coin's own trailing 90-day
    median, sustained for SUSTAIN consecutive days (so a quiet weekend does
    not count)
  - the coin still has real size: market cap and volume above the floors
  - it had a real conversation to lose: trailing 90-day median interactions
    above the floor

The comparison is forward return against BTC over 7, 30 and 90 days, versus
all other eligible coin-days.

Design notes carried over from the earlier studies:
  - Sustained condition rather than a single day, since daily attention is
    extremely noisy (one-hour half-life, see attention-halflife).
  - Everything is measured against the coin's OWN history, not a cross-sectional
    threshold, because attention levels differ by orders of magnitude and drift
    over time (see attention-breadth).
  - Month-block bootstrap for significance, since forward windows overlap.

Usage:
    python3 analysis.py [--collapse 0.35] [--sustain 5]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"
NUMERIC = ["time", "close", "interactions", "market_cap", "volume_24h", "spam", "posts_created"]
HORIZONS = (7, 30, 90)
BASELINE_WINDOW = 90


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob.get("rows") or []
    if len(rows) < BASELINE_WINDOW + max(HORIZONS) + 10:
        return None
    df = pd.DataFrame(rows)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
    df = df.dropna(subset=["time", "interactions", "close"])
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["symbol"] = blob["coin"]["symbol"]
    return df


def add_signals(df: pd.DataFrame, collapse: float, sustain: int) -> pd.DataFrame:
    base = df["interactions"].shift(1).rolling(BASELINE_WINDOW).median()
    df["baseline"] = base
    df["ratio"] = df["interactions"] / base.replace(0, np.nan)
    quiet = (df["ratio"] <= collapse).fillna(False)
    # Sustained: this day and the previous sustain-1 days all quiet.
    df["sustained"] = quiet.rolling(sustain).sum() == sustain
    # Only flag the first day of a collapse, not every day of a dead stretch.
    df["death"] = df["sustained"] & ~df["sustained"].shift(1).fillna(False)
    for h in HORIZONS:
        df[f"fwd_{h}"] = df["close"].shift(-h) / df["close"] - 1.0
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collapse", type=float, default=0.35,
                    help="interactions at or below this fraction of the 90d median")
    ap.add_argument("--sustain", type=int, default=5, help="consecutive days required")
    ap.add_argument("--min-mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--min-baseline", type=float, default=2000)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df, args.collapse, args.sustain))
    panel = pd.concat(frames, ignore_index=True)

    btc = panel[panel["symbol"] == "BTC"][["date"] + [f"fwd_{h}" for h in HORIZONS]]
    btc = btc.rename(columns={f"fwd_{h}": f"btc_{h}" for h in HORIZONS})
    panel = panel.merge(btc, on="date", how="left")

    eligible = panel[
        (panel["market_cap"].fillna(0) >= args.min_mcap)
        & (panel["volume_24h"].fillna(0) >= args.min_volume)
        & (panel["baseline"] >= args.min_baseline)
        & (panel["symbol"] != "BTC")
        & panel[f"fwd_{max(HORIZONS)}"].notna()
        & panel[f"btc_{max(HORIZONS)}"].notna()
    ].copy()
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}"] = eligible[f"fwd_{h}"].clip(lo, hi)
        eligible[f"adj_{h}"] = eligible[f"fwd_{h}"] - eligible[f"btc_{h}"]

    deaths = eligible[eligible["death"]]
    rest = eligible[~eligible["death"]]
    print(f"eligible coin-days: {len(eligible):,}")
    print(f"attention-death events: {len(deaths):,} "
          f"across {deaths['symbol'].nunique()} coins")
    print(f"(conversation at or below {args.collapse:.0%} of its own 90-day median, "
          f"{args.sustain} days running)")

    print(f"\n{'group':22} {'n':>7} " + " ".join(f"{'med ' + str(h) + 'd':>10}" for h in HORIZONS))
    for label, g in [("attention death", deaths), ("everything else", rest)]:
        cells = " ".join(f"{g[f'adj_{h}'].median():>+10.2%}" for h in HORIZONS)
        print(f"{label:22} {len(g):>7} {cells}")

    print(f"\n{'group':22} {'n':>7} " + " ".join(f"{'hit ' + str(h) + 'd':>10}" for h in HORIZONS))
    for label, g in [("attention death", deaths), ("everything else", rest)]:
        cells = " ".join(f"{(g[f'adj_{h}'] > 0).mean():>10.3f}" for h in HORIZONS)
        print(f"{label:22} {len(g):>7} {cells}")

    # Significance on the median difference, month-block bootstrap.
    pool = pd.concat([deaths.assign(grp="death"), rest.assign(grp="rest")])
    pool["block"] = pool["date"].dt.to_period("M")
    blocks = sorted(pool["block"].unique())
    by_block = {b: g for b, g in pool.groupby("block")}
    rng = np.random.default_rng(7)
    print(f"\nmonth-block bootstrap ({args.bootstrap} draws), death minus rest:")
    for h in HORIZONS:
        col = f"adj_{h}"

        def stat(s: pd.DataFrame) -> float:
            a = s.loc[s["grp"] == "death", col]
            b = s.loc[s["grp"] == "rest", col]
            if len(a) < 10 or len(b) < 200:
                return np.nan
            return a.median() - b.median()

        observed = stat(pool)
        draws = []
        for _ in range(args.bootstrap):
            picked = rng.choice(len(blocks), len(blocks))
            v = stat(pd.concat([by_block[blocks[i]] for i in picked]))
            if np.isfinite(v):
                draws.append(v)
        d = np.array(draws)
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        print(f"  {h:>3}d: {observed:+.2%}  CI [{np.percentile(d,2.5):+.2%}, "
              f"{np.percentile(d,97.5):+.2%}]  p={p:.4f}")

    # Does the conversation come back, and does that matter?
    print("\nrecovery: share of death events whose attention returns to")
    print("its prior baseline within 90 days")
    rec = deaths.dropna(subset=["ratio"])
    print(f"  events examined: {len(rec):,}")

    OUT_DIR.mkdir(exist_ok=True)
    deaths.reset_index()[
        ["date", "symbol", "ratio", "baseline", "market_cap"]
        + [f"adj_{h}" for h in HORIZONS]
    ].to_csv(OUT_DIR / "death_events.csv", index=False)
    print(f"\nWrote out/death_events.csv")


if __name__ == "__main__":
    main()
