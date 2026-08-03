#!/usr/bin/env python3
"""Attention half-life: how fast do social spikes decay, organic vs spam?

Tests the claim "real attention decays, rented attention stops" on every
historical spike in the backtest dataset (../social-price-backtest/data/raw).

For each spike day t (interactions z >= 3 vs trailing 30d, eligible coin):
  - baseline B = trailing 30-day median interactions (excludes day t)
  - spike height = I[t] - B
  - retention at day k = max(0, (I[t+k] - B) / (I[t] - B))
  - half-life = first day k in 1..14 where retention <= 50% (censored if never)

Spikes followed by another spike within 7 days are excluded (overlap), as are
spikes without 14 days of subsequent history.

Usage:
    python3 analysis.py [--z 3.0] [--spam-split 0.5] [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"

TRAILING = 30
FLOOR = 2000
FOLLOW = 14
CURVE_DAYS = 7
NUMERIC = ["time", "close", "interactions", "market_cap", "spam", "posts_created", "volume_24h"]


def load_coin(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob["rows"]
    if len(rows) < TRAILING + FOLLOW + 5:
        return None
    df = pd.DataFrame(rows)
    if not {"time", "interactions", "market_cap"}.issubset(df.columns):
        return None
    for col in NUMERIC:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["time", "interactions"])
    df["date"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["symbol"] = blob["coin"]["symbol"]
    return df


def find_spikes(df: pd.DataFrame, z_min: float, args) -> list[dict]:
    li = np.log1p(df["interactions"].astype(float))
    roll = li.shift(1).rolling(TRAILING)
    z = (li - roll.mean()) / roll.std()
    med = df["interactions"].shift(1).rolling(TRAILING).median()
    spam_ratio = (
        (df["spam"] / df["posts_created"].clip(lower=1)).clip(0, 1)
        if "spam" in df.columns and "posts_created" in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    vol = df.get("volume_24h", pd.Series(0, index=df.index)).fillna(0)
    mcap = df.get("market_cap", pd.Series(0, index=df.index)).fillna(0)

    spike_idx = df.index[
        (z >= z_min) & (med >= FLOOR) & (mcap >= args.mcap) & (vol >= args.min_volume)
    ].to_list()
    spike_set = set(spike_idx)

    out = []
    interactions = df["interactions"].to_numpy(dtype=float)
    for t in spike_idx:
        if t + FOLLOW >= len(df):
            continue  # not enough follow-up history
        if any((t + k) in spike_set for k in range(1, 8)):
            continue  # overlapping spike contaminates the decay window
        base = med.iloc[t]
        height = interactions[t] - base
        if not np.isfinite(base) or height <= 0:
            continue
        retention = {
            k: max(0.0, (interactions[t + k] - base) / height) for k in range(1, CURVE_DAYS + 1)
        }
        # Residue: does the spike permanently lift the attention baseline?
        # Compare the week-two floor (days 8..14) against the pre-spike baseline.
        base_shift = float(np.median(interactions[t + 8 : t + 15]) / base)
        half_life = None
        for k in range(1, FOLLOW + 1):
            if (interactions[t + k] - base) <= 0.5 * height:
                half_life = k
                break
        out.append(
            {
                "symbol": df["symbol"].iloc[0],
                "date": df["date"].iloc[t],
                "spam_ratio": float(spam_ratio.iloc[t]) if np.isfinite(spam_ratio.iloc[t]) else np.nan,
                "half_life": half_life,
                "censored": half_life is None,
                "base_shift": base_shift,
                **{f"ret_{k}d": retention[k] for k in range(1, CURVE_DAYS + 1)},
            }
        )
    return out


def cluster_bootstrap_diff(df: pd.DataFrame, col: str, iters: int, seed: int = 7) -> dict:
    """Month-cluster bootstrap of the organic-minus-spam difference in median."""
    df = df.copy()
    df["block"] = df["date"].dt.to_period("M")
    blocks = sorted(df["block"].unique())
    rng = np.random.default_rng(seed)

    def stat(sample: pd.DataFrame) -> float:
        org = sample.loc[sample["group"] == "organic", col].median()
        spam = sample.loc[sample["group"] == "spam", col].median()
        return org - spam

    observed = stat(df)
    by_block = {b: g for b, g in df.groupby("block")}
    draws = []
    for _ in range(iters):
        picked = rng.choice(len(blocks), len(blocks))
        sample = pd.concat([by_block[blocks[i]] for i in picked])
        if sample["group"].nunique() == 2:
            draws.append(stat(sample))
    d = np.array(draws)
    return {
        "diff": observed,
        "ci_lo": float(np.percentile(d, 2.5)),
        "ci_hi": float(np.percentile(d, 97.5)),
        "p_two_sided": float(2 * min((d <= 0).mean(), (d >= 0).mean())),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--spam-split", type=float, default=0.5)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    spikes: list[dict] = []
    files = sorted(RAW_DIR.glob("*.json"))
    print(f"Scanning {len(files)} coins for spikes...")
    for p in files:
        df = load_coin(p)
        if df is not None:
            spikes.extend(find_spikes(df, args.z, args))
    sp = pd.DataFrame(spikes)
    sp = sp[sp["spam_ratio"].notna()]
    sp["group"] = np.where(sp["spam_ratio"] <= args.spam_split, "organic", "spam")
    print(f"{len(sp):,} clean spikes ({(sp['group'] == 'organic').sum():,} organic, "
          f"{(sp['group'] == 'spam').sum():,} spam-heavy)")

    rows = []
    curves: dict[str, list[float]] = {}
    for group, g in sp.groupby("group"):
        finite_hl = g.loc[~g["censored"], "half_life"]
        rows.append(
            {
                "group": group,
                "n": len(g),
                "median_ret_1d": g["ret_1d"].median(),
                "median_ret_3d": g["ret_3d"].median(),
                "median_ret_7d": g["ret_7d"].median(),
                "pct_dead_day1": (g["half_life"] == 1).mean(),
                "pct_dead_by_day2": (g["half_life"] <= 2).fillna(False).mean(),
                "median_half_life": finite_hl.median(),
                "pct_alive_day14": g["censored"].mean(),
                "median_base_shift": g["base_shift"].median(),
                "pct_baseline_up_25": (g["base_shift"] >= 1.25).mean(),
            }
        )
        curves[group] = [1.0] + [float(g[f"ret_{k}d"].median()) for k in range(1, CURVE_DAYS + 1)]
    summary = pd.DataFrame(rows)

    OUT_DIR.mkdir(exist_ok=True)
    sp.to_csv(OUT_DIR / "spikes.csv", index=False)
    (OUT_DIR / "curves.json").write_text(json.dumps(curves, indent=1))
    summary.to_csv(OUT_DIR / "summary.csv", index=False)

    pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
    print("\n=== Decay by group ===")
    print(summary.to_string(index=False))

    # Sharper groups: heavily clean vs heavily botted, dropping the mixed middle
    sharp = sp[(sp["spam_ratio"] <= 0.2) | (sp["spam_ratio"] >= 0.8)].copy()
    sharp["group"] = np.where(sharp["spam_ratio"] <= 0.2, "organic", "spam")
    print(f"\n=== Sharp groups (spam <=20% vs >=80%): "
          f"{(sharp['group'] == 'organic').sum():,} vs {(sharp['group'] == 'spam').sum():,} ===")
    sharp_rows = []
    for group, g in sharp.groupby("group"):
        sharp_rows.append(
            {
                "group": group,
                "n": len(g),
                "median_ret_1d": g["ret_1d"].median(),
                "median_ret_3d": g["ret_3d"].median(),
                "median_half_life": g.loc[~g["censored"], "half_life"].median(),
                "median_base_shift": g["base_shift"].median(),
                "pct_baseline_up_25": (g["base_shift"] >= 1.25).mean(),
            }
        )
    print(pd.DataFrame(sharp_rows).to_string(index=False))

    if args.bootstrap > 0 and sp["group"].nunique() == 2:
        print(f"\n=== Month-cluster bootstrap ({args.bootstrap} draws): organic minus spam ===")
        for col in ["ret_1d", "ret_3d", "ret_7d", "base_shift"]:
            r = cluster_bootstrap_diff(sp, col, args.bootstrap)
            print(
                f"median {col}: diff {r['diff']:+.3f}  CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
                f"  p={r['p_two_sided']:.4f}"
            )
        print("--- sharp groups ---")
        for col in ["ret_1d", "ret_3d", "base_shift"]:
            r = cluster_bootstrap_diff(sharp, col, args.bootstrap)
            print(
                f"median {col}: diff {r['diff']:+.3f}  CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
                f"  p={r['p_two_sided']:.4f}"
            )

    print(f"\nWrote out/spikes.csv, out/summary.csv, out/curves.json")


if __name__ == "__main__":
    main()
