#!/usr/bin/env python3
"""Hourly-resolution decay: do spam-heavy spikes die differently within a day?

Daily buckets can't see the difference between a botnet stopping within hours
and real interest tapering across a day. This measures decay shape at hourly
resolution for the windows pulled by pull_hourly.py.

Per spike:
  - hourly baseline: median hourly interactions over the 48h before spike day
  - peak: max hour within the spike day; height = peak - baseline
  - hourly half-life: hours after the peak until interactions first fall to
    baseline + 50% of height (capped at 168h)
  - burst share: top-3 hours' share of spike-day interactions
  - cliff6: mean height retention over the 6 hours after the peak
  - retention at +24h and +48h from the peak

Usage:
    python3 hourly_analysis.py [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
HOURLY_DIR = PROJECT_DIR / "data" / "hourly"
OUT_DIR = PROJECT_DIR / "out"
DAY = 86400


def measure(path: Path) -> dict | None:
    blob = json.loads(path.read_text())
    rows = blob["rows"]
    if len(rows) < 200:
        return None
    t0 = blob["spike_ts"]
    times = np.array([r["time"] for r in rows])
    inter = np.array([pd.to_numeric(r.get("interactions"), errors="coerce") for r in rows], dtype=float)
    ok = np.isfinite(inter)
    times, inter = times[ok], inter[ok]

    pre = inter[(times >= t0 - 2 * DAY) & (times < t0)]
    day = (times >= t0) & (times < t0 + DAY)
    if len(pre) < 24 or day.sum() < 20:
        return None
    baseline = float(np.median(pre))
    day_idx = np.where(day)[0]
    peak_pos = day_idx[np.argmax(inter[day_idx])]
    peak = inter[peak_pos]
    height = peak - baseline
    if height <= 0 or baseline < 0:
        return None

    after = inter[peak_pos + 1 :]
    half_life = None
    for h, v in enumerate(after[:168], start=1):
        if v <= baseline + 0.5 * height:
            half_life = h
            break

    day_vals = np.sort(inter[day_idx])[::-1]
    burst_share = float(day_vals[:3].sum() / max(1.0, day_vals.sum()))

    def retention(hours: int) -> float | None:
        pos = peak_pos + hours
        if pos >= len(inter):
            return None
        return float(max(0.0, (inter[pos] - baseline) / height))

    cliff = after[:6]
    return {
        "symbol": blob["symbol"],
        "date": pd.to_datetime(t0, unit="s"),
        "group": blob["group"],
        "spam_ratio": blob["spam_ratio"],
        "half_life_h": half_life,
        "censored": half_life is None,
        "burst_share": burst_share,
        "cliff6": float(np.clip((cliff - baseline) / height, 0, None).mean()) if len(cliff) == 6 else None,
        "ret_24h": retention(24),
        "ret_48h": retention(48),
    }


def cluster_bootstrap_diff(df: pd.DataFrame, col: str, iters: int, seed: int = 7) -> dict:
    df = df[df[col].notna()].copy()
    df["block"] = df["date"].dt.to_period("M")
    blocks = sorted(df["block"].unique())
    rng = np.random.default_rng(seed)

    def stat(sample: pd.DataFrame) -> float:
        return (
            sample.loc[sample["group"] == "organic", col].median()
            - sample.loc[sample["group"] == "spam", col].median()
        )

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
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    files = sorted(HOURLY_DIR.glob("*.json"))
    print(f"Measuring {len(files)} hourly spike windows...")
    rows = [m for p in files if (m := measure(p)) is not None]
    df = pd.DataFrame(rows)
    print(f"{len(df):,} usable ({(df['group'] == 'organic').sum():,} organic, "
          f"{(df['group'] == 'spam').sum():,} spam)")

    summary = []
    for group, g in df.groupby("group"):
        summary.append(
            {
                "group": group,
                "n": len(g),
                "median_half_life_h": g.loc[~g["censored"], "half_life_h"].median(),
                "pct_dead_in_6h": (g["half_life_h"] <= 6).fillna(False).mean(),
                "pct_dead_in_12h": (g["half_life_h"] <= 12).fillna(False).mean(),
                "median_burst_share": g["burst_share"].median(),
                "median_cliff6": g["cliff6"].median(),
                "median_ret_24h": g["ret_24h"].median(),
                "median_ret_48h": g["ret_48h"].median(),
            }
        )
    out = pd.DataFrame(summary)
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUT_DIR / "hourly_spikes.csv", index=False)
    out.to_csv(OUT_DIR / "hourly_summary.csv", index=False)

    pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
    print("\n=== Hourly decay by group ===")
    print(out.to_string(index=False))

    if args.bootstrap > 0 and df["group"].nunique() == 2:
        print(f"\n=== Month-cluster bootstrap ({args.bootstrap} draws): organic minus spam ===")
        for col in ["half_life_h", "burst_share", "cliff6", "ret_24h"]:
            r = cluster_bootstrap_diff(df, col, args.bootstrap)
            print(
                f"median {col}: diff {r['diff']:+.3f}  CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
                f"  p={r['p_two_sided']:.4f}"
            )

    print("\nWrote out/hourly_spikes.csv, out/hourly_summary.csv")


if __name__ == "__main__":
    main()
