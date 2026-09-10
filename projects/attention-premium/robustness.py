#!/usr/bin/env python3
"""Does the attention-premium result survive being attacked?

Four checks:
  1. Era split. The finding should hold before and after 2023, which is both a
     market-regime boundary and the point where LunarCrush changed how some
     social fields are counted.
  2. Concentration. Drop the 20 symbols contributing the most coin-days, in
     case a handful of coins carry the whole result.
  3. Size. Run it inside the largest and smallest market-cap halves separately.
  4. Volume floor. Raise it 10x, in case this is an illiquidity premium.

Usage: python3 robustness.py [--bootstrap 1000]
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
from analysis import HORIZONS, load_coin, bootstrap_diffs  # noqa: E402
from premium import MCAP_DECILES, PREMIUM_BUCKETS, LABELS  # noqa: E402


def build(mcap_floor: float, vol_floor: float) -> pd.DataFrame:
    frames = []
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is None:
            continue
        for col in ("social_dominance", "market_dominance"):
            if col not in df.columns:
                df[col] = np.nan
            df[col] = pd.to_numeric(df[col], errors="coerce")
        for h in HORIZONS:
            df[f"fwd_{h}d"] = df["close"].shift(-h) / df["close"] - 1
        frames.append(df)
    all_days = pd.concat(frames)
    btc = all_days[all_days["symbol"] == "BTC"]
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS})
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")
    el = all_days[
        (all_days["market_cap"] >= mcap_floor)
        & (all_days["volume_24h"].fillna(0) >= vol_floor)
        & all_days["social_dominance"].notna()
        & (all_days["market_dominance"] > 0)
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")].copy()
    el["premium"] = el["social_dominance"] / el["market_dominance"]
    for h in HORIZONS:
        lo, hi = el[f"fwd_{h}d"].quantile([0.01, 0.99])
        el[f"fwd_{h}d"] = el[f"fwd_{h}d"].clip(lo, hi)
        el[f"adj_{h}d"] = el[f"fwd_{h}d"] - el[f"btc_{h}d"]
    return el


def bucketize(el: pd.DataFrame) -> pd.DataFrame:
    el = el.copy()
    el["day"] = el.index
    el = el.reset_index(drop=True)
    el["mcap_decile"] = el.groupby("day")["market_cap"].transform(
        lambda s: pd.qcut(s.rank(method="first"), MCAP_DECILES, labels=False, duplicates="drop")
        if len(s) >= MCAP_DECILES * 2 else np.nan)
    el = el.dropna(subset=["mcap_decile"])

    def bucket(s: pd.Series) -> pd.Series:
        if len(s) < PREMIUM_BUCKETS * 2:
            return pd.Series(np.nan, index=s.index, dtype=object)
        return pd.qcut(s.rank(method="first"), PREMIUM_BUCKETS, labels=LABELS).astype(object)

    el["group"] = el.groupby(["day", "mcap_decile"])["premium"].transform(bucket)
    el = el.dropna(subset=["group"])
    el["group"] = el["group"].astype(str)
    return el.set_index("day")


def spread(el: pd.DataFrame, label: str, iters: int, out: list) -> None:
    if len(el) < 5000:
        print(f"{label:<34}  too few rows ({len(el):,})")
        return
    r = bootstrap_diffs(el, "group", "quietest", "loudest", iters)
    row = r[(r["metric"] == "hit_rate_adj") & (r["horizon"] == "+7d")].iloc[0]
    print(f"{label:<34}{len(el):>10,}{row['diff']*100:>11.1f}pp"
          f"{f'[{row.ci_lo*100:+.1f}, {row.ci_hi*100:+.1f}]':>20}{row['p_two_sided']:>8.3f}")
    out.append({"check": label, "n": int(len(el)), "diff": float(row["diff"]),
                "ci_lo": float(row.ci_lo), "ci_hi": float(row.ci_hi),
                "p": float(row["p_two_sided"])})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=1000)
    args = ap.parse_args()

    base = bucketize(build(50e6, 1e6))
    print("quietest minus loudest, beats-BTC rate at +7d\n")
    print(f"{'check':<34}{'coin-days':>10}{'diff':>13}{'95% CI':>20}{'p':>8}")
    out = []
    spread(base, "all data (headline)", args.bootstrap, out)

    spread(base[base.index < "2023-01-01"], "era: 2020-2022", args.bootstrap, out)
    spread(base[base.index >= "2023-01-01"], "era: 2023-2026", args.bootstrap, out)

    top20 = base["symbol"].value_counts().head(20).index
    spread(base[~base["symbol"].isin(top20)], "drop 20 most-present symbols", args.bootstrap, out)

    med = base["market_cap"].median()
    spread(base[base["market_cap"] >= med], "larger half by market cap", args.bootstrap, out)
    spread(base[base["market_cap"] < med], "smaller half by market cap", args.bootstrap, out)

    spread(bucketize(build(50e6, 1e7)), "volume floor raised 10x", args.bootstrap, out)

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "robustness.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {HERE / 'out' / 'robustness.json'}")


if __name__ == "__main__":
    main()
