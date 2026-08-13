#!/usr/bin/env python3
"""Attention in one tier, price in another: does the cascade exist in returns?

The lead-lag study found attention arrives across all tiers on the same day,
so there is no cascade in attention itself. The tradeable version of the myth
is different and worth testing separately: when Bitcoin's conversation spikes
today, do altcoins outperform a few days later?

Two things are measured:

  Own tier. Does a tier's attention change predict its own forward return?
  Cross tier. Does BTC (or majors) attention predict the LOWER tiers' returns,
  and specifically their return relative to BTC, which is what "alt season"
  actually means.

Multiple comparisons are the main hazard here. Five tiers against four
horizons against several lags is a lot of chances for something to look
significant. Nothing below is treated as a finding unless it survives the
month-block bootstrap AND the Bonferroni-style threshold printed at the end.

Usage:
    python3 price_effect.py [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"
NUMERIC = ["time", "close", "interactions", "market_cap", "volume_24h"]
TIERS = [("majors", 2, 10), ("large alts", 11, 50),
         ("mid alts", 51, 200), ("small alts", 201, 10_000)]
HORIZONS = (1, 3, 7)


def load_panel() -> pd.DataFrame:
    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        blob = json.loads(p.read_text())
        rows = blob.get("rows") or []
        if len(rows) < 120:
            continue
        df = pd.DataFrame(rows)
        for c in NUMERIC:
            df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
        df = df.dropna(subset=["time", "interactions", "close"])
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
        df = df.sort_values("date").drop_duplicates("date")
        df["symbol"] = blob["coin"]["symbol"]
        for h in HORIZONS:
            df[f"fwd_{h}"] = df["close"].shift(-h) / df["close"] - 1.0
        frames.append(df[["date", "symbol", "interactions", "market_cap", "volume_24h"]
                         + [f"fwd_{h}" for h in HORIZONS]])
    return pd.concat(frames, ignore_index=True).drop_duplicates(["date", "symbol"])


def build(panel: pd.DataFrame, min_mcap: float, min_vol: float):
    eligible = panel[
        (panel["market_cap"].fillna(0) >= min_mcap)
        & (panel["volume_24h"].fillna(0) >= min_vol)
        & (panel["interactions"] > 0)
    ].copy()
    eligible["rank"] = eligible.groupby("date")["market_cap"].rank(ascending=False, method="first")
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}"] = eligible[f"fwd_{h}"].clip(lo, hi)

    attn, rets = {}, {}
    btc = eligible[eligible["symbol"] == "BTC"].set_index("date")
    attn["BTC"] = btc["interactions"]
    rets["BTC"] = btc[[f"fwd_{h}" for h in HORIZONS]]
    for name, lo_r, hi_r in TIERS:
        sub = eligible[(eligible["rank"] >= lo_r) & (eligible["rank"] <= hi_r)
                       & (eligible["symbol"] != "BTC")]
        attn[name] = sub.groupby("date")["interactions"].sum()
        rets[name] = sub.groupby("date")[[f"fwd_{h}" for h in HORIZONS]].mean()

    attn_wide = pd.DataFrame(attn).dropna()
    chg = np.log(attn_wide).diff().replace([np.inf, -np.inf], np.nan).dropna()
    return chg, rets


def boot_corr(x: pd.Series, y: pd.Series, iters: int, seed: int = 7) -> tuple[float, float, float, float]:
    """Correlation with a month-block bootstrap CI and two-sided p."""
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if len(df) < 100:
        return np.nan, np.nan, np.nan, np.nan
    df["block"] = df.index.to_period("M")
    blocks = sorted(df["block"].unique())
    by_block = {b: g for b, g in df.groupby("block")}
    rng = np.random.default_rng(seed)
    observed = df["x"].corr(df["y"])
    draws = []
    for _ in range(iters):
        picked = rng.choice(len(blocks), len(blocks))
        s = pd.concat([by_block[blocks[i]] for i in picked])
        v = s["x"].corr(s["y"])
        if np.isfinite(v):
            draws.append(v)
    d = np.array(draws)
    p = 2 * min((d <= 0).mean(), (d >= 0).mean())
    return observed, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    panel = load_panel()
    chg, rets = build(panel, args.min_mcap, args.min_volume)
    tiers = ["BTC"] + [t[0] for t in TIERS]
    print(f"attention changes: {len(chg):,} days, {chg.index.min().date()} to {chg.index.max().date()}")

    tests = []

    print("\n=== 1. Does a tier's own attention predict its own return? ===")
    print(f"{'tier':14} {'horizon':>8} {'corr':>8} {'95% CI':>20} {'p':>8}")
    for t in tiers:
        for h in HORIZONS:
            r, lo, hi, p = boot_corr(chg[t], rets[t][f"fwd_{h}"], args.bootstrap)
            if np.isnan(r):
                continue
            tests.append(p)
            print(f"{t:14} {h:>7}d {r:>+8.3f} {f'[{lo:+.3f}, {hi:+.3f}]':>20} {p:>8.3f}")

    print("\n=== 2. Does BTC attention predict LOWER tiers' returns? ===")
    print("(the tradeable version of the cascade myth)")
    print(f"{'target tier':14} {'horizon':>8} {'corr':>8} {'95% CI':>20} {'p':>8}")
    for t in [x[0] for x in TIERS]:
        for h in HORIZONS:
            r, lo, hi, p = boot_corr(chg["BTC"], rets[t][f"fwd_{h}"], args.bootstrap)
            if np.isnan(r):
                continue
            tests.append(p)
            print(f"{t:14} {h:>7}d {r:>+8.3f} {f'[{lo:+.3f}, {hi:+.3f}]':>20} {p:>8.3f}")

    print("\n=== 3. Does BTC attention predict alts BEATING BTC? ===")
    print("(this is what 'alt season' actually means)")
    print(f"{'target tier':14} {'horizon':>8} {'corr':>8} {'95% CI':>20} {'p':>8}")
    for t in [x[0] for x in TIERS]:
        for h in HORIZONS:
            excess = rets[t][f"fwd_{h}"] - rets["BTC"][f"fwd_{h}"]
            r, lo, hi, p = boot_corr(chg["BTC"], excess, args.bootstrap)
            if np.isnan(r):
                continue
            tests.append(p)
            print(f"{t:14} {h:>7}d {r:>+8.3f} {f'[{lo:+.3f}, {hi:+.3f}]':>20} {p:>8.3f}")

    n = len(tests)
    thresh = 0.05 / n
    survivors = sum(1 for p in tests if p < thresh)
    print(f"\n{n} tests run. Bonferroni threshold for 5% family-wise error: p < {thresh:.4f}")
    print(f"Results below that threshold: {survivors}")
    if survivors == 0:
        print("Nothing survives correction. Any single low p-value above is expected by chance.")

    OUT_DIR.mkdir(exist_ok=True)
    print(f"\n(min |corr| that would matter here is roughly 0.05 on {len(chg):,} days)")


if __name__ == "__main__":
    main()
