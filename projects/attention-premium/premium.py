#!/usr/bin/env python3
"""Which coins are talked about more than they are worth, and does it cost you?

LunarCrush reports two shares for every coin: social dominance (its slice of
all crypto conversation) and market dominance (its slice of all crypto market
cap). The ratio is an attention premium: how loud a coin is relative to how
big it is.

The obvious confound is size. Small coins carry a high premium by construction,
so a naive sort on the ratio is a sort on market cap wearing a disguise, and
small caps have their own return behaviour. Everything here is therefore ranked
WITHIN a market-cap decile on each day, so a $60M coin is only ever compared
against other $60M coins on that same day.

Forward returns are BTC-adjusted and winsorized at the 1st/99th percentile.
Significance comes from the same calendar-month cluster bootstrap used by the
main backtest, which respects overlapping forward windows.

Usage: python3 premium.py [--bootstrap 2000]
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

MCAP_DECILES = 10
PREMIUM_BUCKETS = 5
LABELS = ["quietest", "quiet", "middle", "loud", "loudest"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

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
    print(f"{len(all_days):,} coin-days loaded")

    btc = all_days[all_days["symbol"] == "BTC"]
    btc_fwd = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS})
    all_days = all_days.merge(btc_fwd, left_index=True, right_index=True, how="left")

    el = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & all_days["social_dominance"].notna()
        & (all_days["market_dominance"] > 0)
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()
    el["premium"] = el["social_dominance"] / el["market_dominance"]
    for h in HORIZONS:
        lo, hi = el[f"fwd_{h}d"].quantile([0.01, 0.99])
        el[f"fwd_{h}d"] = el[f"fwd_{h}d"].clip(lo, hi)
        el[f"adj_{h}d"] = el[f"fwd_{h}d"] - el[f"btc_{h}d"]
    print(f"{len(el):,} eligible coin-days, {el['symbol'].nunique()} coins")

    # Rank within a market-cap decile, on each day, so the sort is on loudness
    # rather than on size. The date index carries one row per coin per day, so
    # bucketing happens on a unique index and the dates are restored after.
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
    el = el.set_index("day")
    print(f"{len(el):,} coin-days bucketed within market-cap decile\n")

    print("Median premium (social dominance / market dominance) by bucket:")
    for lab in LABELS:
        s = el[el["group"] == lab]
        print(f"  {lab:<10} n={len(s):>8,}  median premium {s['premium'].median():>8.1f}x"
              f"   median mcap ${s['market_cap'].median()/1e6:>8,.0f}M")

    print(f"\n{'comparison':<28}{'horizon':>9}{'beats-BTC diff':>17}{'95% CI':>22}{'p':>8}")
    recs = []
    for lab in ("loudest", "loud", "quiet", "quietest"):
        r = bootstrap_diffs(el, "group", lab, "middle", args.bootstrap)
        recs.append(r)
        for _, row in r[r["metric"] == "hit_rate_adj"].iterrows():
            print(f"{lab + ' vs middle':<28}{row['horizon']:>9}{row['diff']*100:>16.1f}pp"
                  f"{f'[{row.ci_lo*100:+.1f}, {row.ci_hi*100:+.1f}]':>22}{row['p_two_sided']:>8.3f}")

    print("\nloudest vs quietest, head to head:")
    h2h = bootstrap_diffs(el, "group", "loudest", "quietest", args.bootstrap)
    for _, row in h2h[h2h["metric"] == "hit_rate_adj"].iterrows():
        print(f"  {row['horizon']}: {row['diff']*100:+.1f}pp  "
              f"[{row.ci_lo*100:+.1f}, {row.ci_hi*100:+.1f}]  p={row['p_two_sided']:.3f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "premium.json").write_text(json.dumps({
        "buckets": {lab: {"n": int((el["group"] == lab).sum()),
                          "medianPremium": float(el[el["group"] == lab]["premium"].median()),
                          "medianMcap": float(el[el["group"] == lab]["market_cap"].median()),
                          "meanAdj3d": float(el[el["group"] == lab]["adj_3d"].mean()),
                          "hitRate3d": float((el[el["group"] == lab]["adj_3d"] > 0).mean())}
                    for lab in LABELS},
        "results": pd.concat(recs).to_dict("records"),
        "headToHead": h2h.to_dict("records")}, indent=2))
    print(f"\nWrote {HERE / 'out' / 'premium.json'}")


if __name__ == "__main__":
    main()
