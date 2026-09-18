#!/usr/bin/env python3
"""Crypto talks about pumps, not dumps.

Days when a coin rises 5%+ and days when it falls 5%+ are equally common.
The crowd does not treat them equally. A +5% day is 2.4x as likely to
trigger an attention spike as a -5% day, and a -5% day is barely more likely
to trigger one than a flat day. At +20% the ratio is 3.3x.

The measure is P(spike | price move), read off every eligible coin-day, so
it does not depend on how spikes are distributed across the year or on how
many coins are covered. A spike is the backtest's definition: interactions
3+ standard deviations above the coin's own trailing 30 days.

Usage: python3 asymmetry.py [--bootstrap 2000]
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
from analysis import FLOOR, load_coin, add_signals  # noqa: E402

Z = 3.0
MOVES = [0.05, 0.10, 0.20]
FLAT = 0.02


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    for p in sorted((BACKTEST / "data" / "raw").glob("*.json")):
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    a = pd.concat(frames)
    el = a[(a["market_cap"] >= 50e6) & (a["volume_24h"].fillna(0) >= 1e6)
           & (a["med_interactions"] >= FLOOR) & a["z"].notna() & (a["symbol"] != "BTC")].copy()
    el["spike"] = el["z"] >= Z
    print(f"{len(el):,} eligible coin-days, {int(el['spike'].sum()):,} spikes\n")

    p_flat = el[el["ret_1d"].abs() < FLAT]["spike"].mean()
    print(f"P(spike | flat, within ±{FLAT * 100:.0f}%) = {p_flat * 100:.2f}%\n")
    print(f"{'move':<10}{'days up':>10}{'days down':>11}{'P(spike|up)':>13}{'P(spike|down)':>15}{'ratio':>8}")
    rows = []
    for t in MOVES:
        up, dn = el[el["ret_1d"] >= t], el[el["ret_1d"] <= -t]
        pu, pdn = up["spike"].mean(), dn["spike"].mean()
        rows.append({"move": t, "nUp": int(len(up)), "nDown": int(len(dn)),
                     "pUp": float(pu), "pDown": float(pdn), "ratio": float(pu / pdn)})
        print(f"{t * 100:>3.0f}%{'':<6}{len(up):>10,}{len(dn):>11,}{pu * 100:>12.2f}%{pdn * 100:>14.2f}%{pu / pdn:>8.1f}x")

    # Month-block bootstrap on the 5% ratio.
    el["block"] = el.index.to_period("M")
    t = MOVES[0]
    agg = el.groupby("block").apply(lambda d: pd.Series({
        "su": d[d["ret_1d"] >= t]["spike"].sum(), "nu": (d["ret_1d"] >= t).sum(),
        "sd": d[d["ret_1d"] <= -t]["spike"].sum(), "nd": (d["ret_1d"] <= -t).sum()}),
        include_groups=False).to_numpy()
    rng = np.random.default_rng(7)
    ratios = []
    for _ in range(args.bootstrap):
        s = agg[rng.integers(0, len(agg), len(agg))].sum(0)
        ratios.append((s[0] / s[1]) / (s[2] / s[3]))
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    print(f"\nmonth-block bootstrap 95% CI on the {t * 100:.0f}% ratio: [{lo:.2f}, {hi:.2f}]")

    # Composition of spike days, for the chart.
    sp = el[el["spike"]]
    comp = {"up5": float((sp["ret_1d"] >= 0.05).mean()), "down5": float((sp["ret_1d"] <= -0.05).mean()),
            "flat": float((sp["ret_1d"].abs() < 0.05).mean())}
    base = {"up5": float((el["ret_1d"] >= 0.05).mean()), "down5": float((el["ret_1d"] <= -0.05).mean()),
            "flat": float((el["ret_1d"].abs() < 0.05).mean())}
    print(f"\nspike days: up 5%+ {comp['up5'] * 100:.0f}%, down 5%+ {comp['down5'] * 100:.0f}%, in between {comp['flat'] * 100:.0f}%")
    print(f"all days:   up 5%+ {base['up5'] * 100:.0f}%, down 5%+ {base['down5'] * 100:.0f}%, in between {base['flat'] * 100:.0f}%")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "asymmetry.json").write_text(json.dumps({
        "coinDays": int(len(el)), "spikes": int(el["spike"].sum()), "z": Z,
        "pFlat": float(p_flat), "flatBand": FLAT, "rows": rows,
        "ci5": [float(lo), float(hi)], "spikeComposition": comp, "baseComposition": base,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'asymmetry.json'}")


if __name__ == "__main__":
    main()
