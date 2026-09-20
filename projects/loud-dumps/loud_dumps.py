#!/usr/bin/env python3
"""A dump people talk about keeps falling. A dump nobody mentions recovers.

projects/pumps-not-dumps found that a 10% drop triggers an attention spike
only 2.2% of the time. This asks what happens next in that 2.2%.

Every eligible coin-day where the price fell DROP or more is split by whether
the day also carried an attention spike (interactions 3+ standard deviations
above the coin's own trailing 30 days). Forward returns are BTC-adjusted and
winsorized, significance from the calendar-month cluster bootstrap in the
main backtest.

The same split is run on pumps for contrast. Loudness makes almost no
difference to what follows a pump. It makes a large difference to what
follows a dump.

Usage: python3 loud_dumps.py [--drop 0.10] [--bootstrap 2000]
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
from analysis import HORIZONS, FLOOR, load_coin, add_signals, bootstrap_diffs  # noqa: E402

Z = 3.0


def build() -> pd.DataFrame:
    frames = []
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    a = pd.concat(frames)
    btc = a[a["symbol"] == "BTC"]
    bf = btc[[f"fwd_{h}d" for h in HORIZONS]].rename(columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS})
    a = a.merge(bf, left_index=True, right_index=True, how="left")
    el = a[(a["market_cap"] >= 50e6) & (a["volume_24h"].fillna(0) >= 1e6)
           & (a["med_interactions"] >= FLOOR) & a["z"].notna() & a["fwd_7d"].notna()
           & (a["symbol"] != "BTC")].copy()
    for h in HORIZONS:
        lo, hi = el[f"fwd_{h}d"].quantile([0.01, 0.99])
        el[f"fwd_{h}d"] = el[f"fwd_{h}d"].clip(lo, hi)
        el[f"adj_{h}d"] = el[f"fwd_{h}d"] - el[f"btc_{h}d"]
    el["spike"] = el["z"] >= Z
    return el


def split(el: pd.DataFrame, mask, loud: str, quiet: str, iters: int) -> dict:
    d = el[mask].copy()
    d["group"] = np.where(d["spike"], loud, quiet)
    res = {"n": {loud: int(d["spike"].sum()), quiet: int((~d["spike"]).sum())}, "hit": {}, "diff": []}
    for g in (loud, quiet):
        s = d[d["group"] == g]
        res["hit"][g] = {f"+{h}d": float((s[f"adj_{h}d"] > 0).mean()) for h in HORIZONS}
        res["hit"][g]["median7d"] = float(s["adj_7d"].median())
    r = bootstrap_diffs(d, "group", loud, quiet, iters)
    for _, row in r[r["metric"] == "hit_rate_adj"].iterrows():
        res["diff"].append({"horizon": row["horizon"], "diff": float(row["diff"]),
                            "lo": float(row["ci_lo"]), "hi": float(row["ci_hi"]), "p": float(row["p_two_sided"])})
    return res


def show(label: str, r: dict, loud: str, quiet: str) -> None:
    print(f"\n=== {label}: {loud} n={r['n'][loud]:,}   {quiet} n={r['n'][quiet]:,} ===")
    for g in (loud, quiet):
        h = r["hit"][g]
        print(f"  {g:<12} beats BTC  +1d {h['+1d'] * 100:.1f}%   +3d {h['+3d'] * 100:.1f}%   +7d {h['+7d'] * 100:.1f}%"
              f"   median adj +7d {h['median7d'] * 100:+.1f}%")
    for x in r["diff"]:
        print(f"  {loud} minus {quiet} {x['horizon']}: {x['diff'] * 100:+.1f}pp  [{x['lo'] * 100:+.1f}, {x['hi'] * 100:+.1f}]  p={x['p']:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", type=float, default=0.10)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    el = build()
    print(f"{len(el):,} eligible coin-days")

    T = args.drop
    dumps = split(el, el["ret_1d"] <= -T, "loud_dump", "quiet_dump", args.bootstrap)
    show(f"dumps of {T * 100:.0f}%+", dumps, "loud_dump", "quiet_dump")
    pumps = split(el, el["ret_1d"] >= T, "loud_pump", "quiet_pump", args.bootstrap)
    show(f"pumps of {T * 100:.0f}%+", pumps, "loud_pump", "quiet_pump")

    # Robustness on the dump result.
    print("\n=== ROBUSTNESS, loud minus quiet dump, beats-BTC at +3d ===")
    checks = []
    for lab, m in (("5% dumps", el["ret_1d"] <= -0.05), ("20% dumps", el["ret_1d"] <= -0.20),
                   ("2020-2022", (el["ret_1d"] <= -T) & (el.index < "2023-01-01")),
                   ("2023-2026", (el["ret_1d"] <= -T) & (el.index >= "2023-01-01")),
                   ("organic spikes only (spam<=50%)", (el["ret_1d"] <= -T) & ((el["spam_ratio"] <= 0.5) | ~el["spike"])),
                   ("larger half by mcap", (el["ret_1d"] <= -T) & (el["market_cap"] >= el["market_cap"].median())),
                   ("smaller half by mcap", (el["ret_1d"] <= -T) & (el["market_cap"] < el["market_cap"].median()))):
        r = split(el, m, "loud", "quiet", max(500, args.bootstrap // 2))
        x = [d for d in r["diff"] if d["horizon"] == "+3d"][0]
        checks.append({"check": lab, "nLoud": r["n"]["loud"], "nQuiet": r["n"]["quiet"], **x})
        print(f"  {lab:<32} loud n={r['n']['loud']:>4,}  {x['diff'] * 100:+.1f}pp  [{x['lo'] * 100:+.1f}, {x['hi'] * 100:+.1f}]  p={x['p']:.3f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "loud_dumps.json").write_text(json.dumps({
        "coinDays": int(len(el)), "drop": T, "dumps": dumps, "pumps": pumps, "robustness": checks,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'loud_dumps.json'}")


if __name__ == "__main__":
    main()
