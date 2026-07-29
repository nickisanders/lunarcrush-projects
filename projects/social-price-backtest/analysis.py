#!/usr/bin/env python3
"""Backtest: does a social interaction spike lead price?

Coin-days are split into three groups:
  - organic spike: interactions z >= Z_MIN vs trailing 30d, price flat that
    day, spam share of created posts <= spam-split
  - spam spike: same spike, but spam share > spam-split
  - baseline: every other eligible coin-day

Forward returns are measured close-to-close at +1d/+3d/+7d, BTC-adjusted.
Significance for group-vs-baseline differences comes from a cluster bootstrap
on calendar months, which respects overlapping forward windows and
cross-sectional correlation within a month.

Usage:
    python3 analysis.py [--z 3.0] [--flat 0.02] [--mcap 50e6]
                        [--min-volume 1e6] [--spam-split 0.5] [--bootstrap 2000]
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
NUMERIC = ["time", "close", "interactions", "market_cap", "spam", "posts_created", "volume_24h"]


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob["rows"]
    if len(rows) < TRAILING + max(HORIZONS) + 5:
        return None
    df = pd.DataFrame(rows)
    if not {"time", "close", "interactions", "market_cap"}.issubset(df.columns):
        return None
    for col in NUMERIC:
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


def bootstrap_diffs(
    eligible: pd.DataFrame, group_col: str, target: str, baseline: str, iters: int, seed: int = 7
) -> pd.DataFrame:
    """Cluster bootstrap (calendar-month blocks) of target-vs-baseline
    differences in mean BTC-adjusted return and hit rate, per horizon."""
    df = eligible[eligible[group_col].isin([target, baseline])].copy()
    df["block"] = df.index.to_period("M")

    aggs = {}
    for h in HORIZONS:
        df[f"pos_{h}d"] = (df[f"adj_{h}d"] > 0).astype(float)
        aggs[f"s_{h}"] = (f"adj_{h}d", "sum")
        aggs[f"p_{h}"] = (f"pos_{h}d", "sum")
        aggs[f"n_{h}"] = (f"adj_{h}d", "count")
    blocks = df.groupby(["block", group_col]).agg(**aggs).unstack(group_col).fillna(0.0)

    rng = np.random.default_rng(seed)
    b = len(blocks)
    arr = blocks.to_numpy()
    cols = {name: i for i, name in enumerate(blocks.columns)}

    def stat(sample: np.ndarray) -> dict[str, float]:
        out = {}
        for h in HORIZONS:
            res = {}
            for grp in (target, baseline):
                n = sample[:, cols[(f"n_{h}", grp)]].sum()
                res[grp] = (
                    sample[:, cols[(f"s_{h}", grp)]].sum() / n,
                    sample[:, cols[(f"p_{h}", grp)]].sum() / n,
                )
            out[f"mean_{h}"] = res[target][0] - res[baseline][0]
            out[f"hit_{h}"] = res[target][1] - res[baseline][1]
        return out

    observed = stat(arr)
    draws = {k: [] for k in observed}
    for _ in range(iters):
        sample = arr[rng.integers(0, b, b)]
        for k, v in stat(sample).items():
            draws[k].append(v)

    rows = []
    for h in HORIZONS:
        for metric in ("mean", "hit"):
            d = np.array(draws[f"{metric}_{h}"])
            obs = observed[f"{metric}_{h}"]
            rows.append(
                {
                    "comparison": f"{target} vs {baseline}",
                    "horizon": f"+{h}d",
                    "metric": "mean_btc_adj" if metric == "mean" else "hit_rate_adj",
                    "diff": obs,
                    "ci_lo": np.percentile(d, 2.5),
                    "ci_hi": np.percentile(d, 97.5),
                    "p_two_sided": 2 * min((d <= 0).mean(), (d >= 0).mean()),
                }
            )
    return pd.DataFrame(rows)


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
    print(f"{len(frames)} coins usable, {len(all_days):,} coin-days")

    btc = all_days[all_days["symbol"] == "BTC"]
    if btc.empty:
        raise SystemExit("BTC missing from raw data; cannot compute adjusted returns")
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}
    )
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    eligible = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()

    # Winsorize forward returns at the 1st/99th percentile of the eligible set.
    # Raw crypto price data contains redenominations and near-zero-price
    # glitches that produce fake 10,000%+ "returns" and destroy means.
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}d"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}d"] = eligible[f"fwd_{h}d"].clip(lo, hi)
        eligible[f"adj_{h}d"] = eligible[f"fwd_{h}d"] - eligible[f"btc_{h}d"]

    spike = (eligible["z"] >= args.z) & (eligible["ret_1d"].abs() <= args.flat)
    organic = spike & (eligible["spam_ratio"].fillna(0) <= args.spam_split)
    eligible["grp"] = np.select(
        [organic, spike & ~organic], ["organic spike", "spam spike"], default="baseline"
    )
    counts = eligible["grp"].value_counts()
    print(
        f"eligible coin-days: {len(eligible):,} | organic spikes: {counts.get('organic spike', 0):,}"
        f" | spam spikes: {counts.get('spam spike', 0):,}"
    )

    rows = []
    for h in HORIZONS:
        for name, grp in eligible.groupby("grp"):
            adj = grp[f"adj_{h}d"]
            rows.append(
                {
                    "horizon": f"+{h}d",
                    "group": name,
                    "n": len(grp),
                    "mean_raw": grp[f"fwd_{h}d"].mean(),
                    "median_raw": grp[f"fwd_{h}d"].median(),
                    "mean_btc_adj": adj.mean(),
                    "median_btc_adj": adj.median(),
                    "hit_rate_adj": (adj > 0).mean(),
                }
            )
    summary = pd.DataFrame(rows).sort_values(["horizon", "group"])

    OUT_DIR.mkdir(exist_ok=True)
    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    eligible[eligible["grp"] != "baseline"].reset_index()[
        ["date", "symbol", "grp", "z", "ret_1d", "market_cap", "spam_ratio"]
        + [f"adj_{h}d" for h in HORIZONS]
    ].to_csv(OUT_DIR / "events.csv", index=False)

    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
    print("\n=== Forward returns by group (BTC-adjusted) ===")
    print(summary.to_string(index=False))

    if args.bootstrap > 0:
        print(f"\n=== Cluster bootstrap ({args.bootstrap} draws, month blocks) ===")
        boots = pd.concat(
            [
                bootstrap_diffs(eligible, "grp", "organic spike", "baseline", args.bootstrap),
                bootstrap_diffs(eligible, "grp", "spam spike", "baseline", args.bootstrap),
            ]
        )
        boots.to_csv(OUT_DIR / "bootstrap.csv", index=False)
        print(boots.to_string(index=False))

    print(f"\nWrote out/summary.csv, out/events.csv, out/bootstrap.csv")


if __name__ == "__main__":
    main()
