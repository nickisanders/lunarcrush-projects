#!/usr/bin/env python3
"""The attention-premium result, with pegged and wrapped assets removed.

The first cut of this finding was an artifact. Ranking coins by social
dominance over market dominance puts stablecoins and wrapped assets in the
quietest bucket by construction: nobody discusses USDT or WBETH, because the
conversation about a wrapper belongs to the thing it wraps. Those assets then
"beat Bitcoin" on the BTC-adjusted measure every day Bitcoin falls, which is
not a finding about attention.

In the contaminated quietest bucket, 26.5% of coin-days moved less than 0.5%,
against 8.7% in the loudest.

Two exclusions, both applied before any ranking:

  - **Pegged**, detected by behaviour rather than by a hand-kept list: a coin
    whose median absolute daily return across its history is under 1%.
  - **Wrapped and liquid-staked**, by name, because their price is another
    asset's price and their conversation is another asset's conversation.

Usage: python3 clean.py [--bootstrap 2000]
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
from robustness import bucketize  # noqa: E402

PEGGED_MEDIAN_MOVE = 0.01
WRAPPED = {"WBTC", "WETH", "WBNB", "WMATIC", "WAVAX", "WSTETH", "STETH", "CBETH",
           "RETH", "WBETH", "MSOL", "JITOSOL", "BSOL", "SOLVBTC", "LBTC", "CBBTC",
           "WEETH", "EZETH", "RSETH", "SFRXETH", "FRXETH", "ANKRETH", "OSETH",
           "SWETH", "STSOL", "JUPSOL", "INFSOL", "BNSOL", "WBETH", "METH", "STBTC"}


def build_clean(mcap_floor=50e6, vol_floor=1e6) -> tuple[pd.DataFrame, dict]:
    frames, dropped_peg = [], []
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is None:
            continue
        if df.empty:
            continue
        sym = str(df["symbol"].iloc[0])
        ret = df["close"].pct_change()
        med_move = ret.abs().median()
        if sym in WRAPPED:
            continue
        if pd.notna(med_move) and med_move < PEGGED_MEDIAN_MOVE:
            dropped_peg.append((sym, float(med_move)))
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
    return el, {"peggedDropped": sorted(s for s, _ in dropped_peg)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    el, meta = build_clean()
    el = bucketize(el)
    print(f"{len(el):,} coin-days after removing pegged and wrapped assets")
    print(f"dropped as pegged ({len(meta['peggedDropped'])}): "
          f"{', '.join(meta['peggedDropped'][:18])}\n")

    print("bucket composition check:")
    for lab in ("quietest", "loudest"):
        s = el[el["group"] == lab]
        print(f"  {lab:<9} n={len(s):>7,}  median |1d| {s['fwd_1d'].abs().median()*100:>5.2f}%"
              f"   flat days {(s['fwd_1d'].abs()<0.005).mean()*100:>5.1f}%"
              f"   median mcap ${s['market_cap'].median()/1e6:>6,.0f}M")
        print(f"            top: {', '.join(s['symbol'].value_counts().head(10).index)}")

    print(f"\n{'comparison':<28}{'horizon':>9}{'beats-BTC diff':>17}{'95% CI':>22}{'p':>8}")
    recs = []
    for lab in ("loudest", "loud", "quiet", "quietest"):
        r = bootstrap_diffs(el, "group", lab, "middle", args.bootstrap)
        recs.append(r)
        for _, row in r[r["metric"] == "hit_rate_adj"].iterrows():
            print(f"{lab + ' vs middle':<28}{row['horizon']:>9}{row['diff']*100:>16.1f}pp"
                  f"{f'[{row.ci_lo*100:+.1f}, {row.ci_hi*100:+.1f}]':>22}{row['p_two_sided']:>8.3f}")

    print("\nquietest minus loudest, head to head:")
    h2h = bootstrap_diffs(el, "group", "quietest", "loudest", args.bootstrap)
    for _, row in h2h[h2h["metric"] == "hit_rate_adj"].iterrows():
        print(f"  {row['horizon']}: {row['diff']*100:+.1f}pp  "
              f"[{row.ci_lo*100:+.1f}, {row.ci_hi*100:+.1f}]  p={row['p_two_sided']:.3f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "clean.json").write_text(json.dumps({
        "n": int(len(el)), "peggedDropped": meta["peggedDropped"],
        "buckets": {lab: {"n": int((el["group"] == lab).sum()),
                          "medianPremium": float(el[el["group"] == lab]["premium"].median()),
                          "medianMcap": float(el[el["group"] == lab]["market_cap"].median()),
                          "flatDays": float((el[el["group"] == lab]["fwd_1d"].abs() < 0.005).mean()),
                          "hitRate7d": float((el[el["group"] == lab]["adj_7d"] > 0).mean())}
                    for lab in LABELS},
        "results": pd.concat(recs).to_dict("records"),
        "headToHead": h2h.to_dict("records")}, indent=2))
    print(f"\nWrote {HERE / 'out' / 'clean.json'}")


if __name__ == "__main__":
    main()
