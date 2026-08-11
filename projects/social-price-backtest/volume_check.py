#!/usr/bin/env python3
"""Does trading-volume confirmation improve the organic-spike setup?

The organic watchlist fires on social evidence alone: interactions 3+ SD above
a coin's own 30-day norm, spam under 50%, price flat. It beat BTC over the
following 3 days 49.0% of the time versus 41.9% for an ordinary coin-day.

Question: among those events, does it matter whether trading volume spiked too?
"Everyone is talking AND money is moving, but price hasn't repriced yet" is a
plausible confirmation signal, and it costs nothing to test because volume_24h
is already in the cached panel.

Uses only data available at flag time: volume is compared to its own trailing
30 days ending the day BEFORE the event, so nothing here peeks ahead.

Usage:
    python3 volume_check.py [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
NUMERIC = ["time", "close", "interactions", "market_cap", "volume_24h", "spam", "posts_created"]
TRAILING = 30
HORIZON = 3


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob.get("rows") or []
    if len(rows) < TRAILING + HORIZON + 5:
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


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    li = np.log1p(df["interactions"])
    roll = li.shift(1).rolling(TRAILING)
    df["z"] = (li - roll.mean()) / roll.std()
    df["med_interactions"] = df["interactions"].shift(1).rolling(TRAILING).median()
    df["ret_1d"] = df["close"].pct_change()
    df["fwd"] = df["close"].shift(-HORIZON) / df["close"] - 1.0
    df["spam_ratio"] = (df["spam"] / df["posts_created"].clip(lower=1)).clip(0, 1)
    # Volume relative to its own trailing norm, excluding the event day itself.
    med_vol = df["volume_24h"].shift(1).rolling(TRAILING).median()
    df["vol_multiple"] = df["volume_24h"] / med_vol.replace(0, np.nan)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    panel = pd.concat(frames, ignore_index=True)

    btc = panel[panel["symbol"] == "BTC"][["date", "fwd"]].rename(columns={"fwd": "btc_fwd"})
    panel = panel.merge(btc, on="date", how="left")

    eligible = panel[
        (panel["market_cap"].fillna(0) >= 50e6)
        & (panel["volume_24h"].fillna(0) >= 1e6)
        & (panel["med_interactions"] >= 2000)
        & panel["z"].notna()
        & panel["fwd"].notna()
        & panel["btc_fwd"].notna()
        & (panel["symbol"] != "BTC")
    ].copy()
    lo, hi = eligible["fwd"].quantile([0.01, 0.99])
    eligible["fwd"] = eligible["fwd"].clip(lo, hi)
    eligible["adj"] = eligible["fwd"] - eligible["btc_fwd"]

    spike = (eligible["z"] >= 3.0) & (eligible["ret_1d"].abs() <= 0.02)
    organic = spike & (eligible["spam_ratio"].fillna(0) <= 0.5)
    events = eligible[organic & eligible["vol_multiple"].notna()].copy()
    baseline = eligible[~spike]

    print(f"eligible coin-days: {len(eligible):,}")
    print(f"organic events with volume data: {len(events):,}")
    print(f"\nbaseline hit rate (ordinary coin-day): {(baseline['adj'] > 0).mean():.3f}")
    print(f"all organic events:                   {(events['adj'] > 0).mean():.3f}  "
          f"(n={len(events)})")

    print(f"\nvolume multiple on event days: "
          + " ".join(f"p{int(q*100)}={events['vol_multiple'].quantile(q):.2f}"
                     for q in (0.25, 0.5, 0.75)))

    print("\nhit rate by volume confirmation:")
    for label, mask in [
        ("volume BELOW its norm (<1x)", events["vol_multiple"] < 1.0),
        ("volume normal (1x - 1.5x)", (events["vol_multiple"] >= 1.0) & (events["vol_multiple"] < 1.5)),
        ("volume elevated (1.5x - 3x)", (events["vol_multiple"] >= 1.5) & (events["vol_multiple"] < 3.0)),
        ("volume spiking (3x+)", events["vol_multiple"] >= 3.0),
    ]:
        sub = events[mask]
        if len(sub) < 10:
            print(f"  {label:30} n={len(sub):>4}  (too few)")
            continue
        print(f"  {label:30} n={len(sub):>4}  hit rate {(sub['adj'] > 0).mean():.3f}  "
              f"median {sub['adj'].median():+.2%}")

    # Is "volume confirmed" better than "not"? Month-cluster bootstrap, since
    # 3-day windows on daily observations overlap.
    confirmed = events[events["vol_multiple"] >= 1.5]
    unconfirmed = events[events["vol_multiple"] < 1.5]
    if len(confirmed) >= 20 and len(unconfirmed) >= 20:
        print(f"\nconfirmed (vol >= 1.5x) n={len(confirmed)} vs unconfirmed n={len(unconfirmed)}")
        events["block"] = events["date"].dt.to_period("M")
        blocks = sorted(events["block"].unique())
        by_block = {b: g for b, g in events.groupby("block")}
        rng = np.random.default_rng(7)

        def stat(s: pd.DataFrame) -> float:
            c = s[s["vol_multiple"] >= 1.5]["adj"]
            u = s[s["vol_multiple"] < 1.5]["adj"]
            if len(c) < 5 or len(u) < 5:
                return np.nan
            return (c > 0).mean() - (u > 0).mean()

        observed = stat(events)
        draws = []
        for _ in range(args.bootstrap):
            picked = rng.choice(len(blocks), len(blocks))
            v = stat(pd.concat([by_block[blocks[i]] for i in picked]))
            if np.isfinite(v):
                draws.append(v)
        d = np.array(draws)
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        print(f"hit-rate difference: {observed:+.3f}  "
              f"CI [{np.percentile(d, 2.5):+.3f}, {np.percentile(d, 97.5):+.3f}]  p={p:.4f}")


if __name__ == "__main__":
    main()
