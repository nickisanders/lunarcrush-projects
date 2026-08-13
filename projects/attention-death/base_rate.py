#!/usr/bin/env python3
"""The altcoin base rate: how often does an altcoin actually beat Bitcoin?

This fell out of the attention-death study. Looking for a signal in coins whose
conversation collapses, the striking number was not the event group but the
comparison group: the typical altcoin-day bleeds badly against BTC, and the
longer the horizon the worse it gets.

Every rate here is measured per eligible coin-day on real coins ($50M+ market
cap, $1M+ volume), so it describes the experience of holding a liquid, real
altcoin picked at a random moment, not a basket of dead microcaps.

Usage:
    python3 base_rate.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"
HORIZONS = (1, 7, 30, 90, 180)
NUMERIC = ["time", "close", "market_cap", "volume_24h", "interactions"]


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob.get("rows") or []
    if len(rows) < 200:
        return None
    df = pd.DataFrame(rows)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
    df = df.dropna(subset=["time", "close"])
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["symbol"] = blob["coin"]["symbol"]
    for h in HORIZONS:
        df[f"fwd_{h}"] = df["close"].shift(-h) / df["close"] - 1.0
    return df


def main() -> None:
    frames = [d for p in sorted(RAW_DIR.glob("*.json")) if (d := load_coin(p)) is not None]
    panel = pd.concat(frames, ignore_index=True)

    btc = panel[panel["symbol"] == "BTC"][["date"] + [f"fwd_{h}" for h in HORIZONS]]
    btc = btc.rename(columns={f"fwd_{h}": f"btc_{h}" for h in HORIZONS})
    panel = panel.merge(btc, on="date", how="left")

    eligible = panel[
        (panel["market_cap"].fillna(0) >= 50e6)
        & (panel["volume_24h"].fillna(0) >= 1e6)
        & (panel["symbol"] != "BTC")
    ].copy()

    print(f"{len(eligible):,} eligible coin-days, {eligible['symbol'].nunique()} coins, "
          f"{eligible['date'].min().date()} to {eligible['date'].max().date()}")
    print("(real coins only: $50M+ market cap, $1M+ daily volume)\n")

    print(f"{'hold for':>10} {'beats BTC':>11} {'median vs BTC':>15} {'median raw':>12} {'n':>10}")
    rows = []
    for h in HORIZONS:
        sub = eligible.dropna(subset=[f"fwd_{h}", f"btc_{h}"]).copy()
        lo, hi = sub[f"fwd_{h}"].quantile([0.01, 0.99])
        sub[f"fwd_{h}"] = sub[f"fwd_{h}"].clip(lo, hi)
        adj = sub[f"fwd_{h}"] - sub[f"btc_{h}"]
        hit = (adj > 0).mean()
        rows.append({"horizon": h, "hit": hit, "median_adj": adj.median(),
                     "median_raw": sub[f"fwd_{h}"].median(), "n": len(sub)})
        label = f"{h} day" + ("s" if h > 1 else "")
        print(f"{label:>10} {hit:>11.1%} {adj.median():>+15.1%} "
              f"{sub[f'fwd_{h}'].median():>+12.1%} {len(sub):>10,}")

    # Does size protect you?
    print("\nby market cap band, 90-day horizon:")
    sub = eligible.dropna(subset=["fwd_90", "btc_90"]).copy()
    lo, hi = sub["fwd_90"].quantile([0.01, 0.99])
    sub["fwd_90"] = sub["fwd_90"].clip(lo, hi)
    sub["adj"] = sub["fwd_90"] - sub["btc_90"]
    bands = [(50e6, 250e6, "$50-250M"), (250e6, 1e9, "$250M-1B"),
             (1e9, 10e9, "$1-10B"), (1e9 * 10, np.inf, "$10B+")]
    for lo_c, hi_c, name in bands:
        b = sub[(sub["market_cap"] >= lo_c) & (sub["market_cap"] < hi_c)]
        if len(b) < 1000:
            continue
        print(f"  {name:12} beats BTC {(b['adj'] > 0).mean():>6.1%}   "
              f"median {b['adj'].median():>+7.1%}   n={len(b):>9,}")

    # Era check, since one bear market could be carrying this.
    print("\nby era, 90-day horizon:")
    sub["year"] = sub["date"].dt.year
    for era, (y0, y1) in {"2020-2022": (2020, 2022), "2023-2025": (2023, 2025),
                          "2026": (2026, 2026)}.items():
        b = sub[(sub["year"] >= y0) & (sub["year"] <= y1)]
        if len(b) < 1000:
            continue
        print(f"  {era:12} beats BTC {(b['adj'] > 0).mean():>6.1%}   "
              f"median {b['adj'].median():>+7.1%}   n={len(b):>9,}")

    OUT_DIR.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_DIR / "base_rate.csv", index=False)
    print(f"\nWrote out/base_rate.csv")


if __name__ == "__main__":
    main()
