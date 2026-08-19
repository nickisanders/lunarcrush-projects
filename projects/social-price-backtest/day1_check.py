#!/usr/bin/env python3
"""Does an early lead predict the rest of the move? (No. It only looks like it.)

When you publish a 3-day signal, the first question after day 1 is always
"it's green, is that a good sign?" Scored naively the answer looks emphatic:
among organic spikes, those ahead of BTC after day 1 beat BTC at day 3 about
73% of the time, against 29% for those behind. That is a 44 point spread and
it is entirely an artifact.

Day 1 sits INSIDE day 3. The 3-day return contains the 1-day return, so a coin
that is ahead early is ahead cumulatively for arithmetic reasons, not
predictive ones. The measure and the outcome share a term.

The honest test uses the non-overlapping remainder: does the day-1 lead predict
days 2 and 3 alone? It does not. The two groups land within a tenth of a point
of each other.

This is the same failure mode as the leave-one-out demeaning in
attention-cascade and the raw-level quintiles in attention-breadth: a number
that looks like a finding until you check what it shares with itself.

Usage:
    python3 day1_check.py [--bootstrap 2000]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from uprate import build_eligible

OUT_DIR = Path(__file__).resolve().parent / "out"


def remainder_excess(df: pd.DataFrame) -> pd.Series:
    """Excess return over days 2-3 only, with day 1 divided out of both legs.

    Chaining the two horizons rather than subtracting them keeps this a true
    return over the remaining window. Note both legs were winsorized at their
    own horizon before this ratio is taken, which perturbs the tails slightly;
    the result is not close enough to any threshold for that to matter.
    """
    coin = (1 + df["fwd_3d"]) / (1 + df["fwd_1d"]) - 1
    btc = (1 + df["btc_3d"]) / (1 + df["btc_1d"]) - 1
    return coin - btc


def block_bootstrap_gap(df: pd.DataFrame, col: str, ahead: pd.Series, iters: int, seed: int = 7):
    """Month-block bootstrap of the ahead-minus-behind gap in positive rate."""
    d = df.copy()
    d["ahead"] = ahead
    d["pos"] = (d[col] > 0).astype(float)
    d["block"] = d.index.to_period("M")
    blocks = d.groupby(["block", "ahead"]).agg(p=("pos", "sum"), n=("pos", "count")).unstack("ahead").fillna(0.0)
    arr = blocks.to_numpy()
    idx = {name: i for i, name in enumerate(blocks.columns)}

    def gap(sample):
        out = {}
        for grp in (True, False):
            n = sample[:, idx[("n", grp)]].sum()
            out[grp] = sample[:, idx[("p", grp)]].sum() / n if n else np.nan
        return out[True] - out[False]

    rng = np.random.default_rng(seed)
    draws = np.array([gap(arr[rng.integers(0, len(arr), len(arr))]) for _ in range(iters)])
    draws = draws[~np.isnan(draws)]
    return (
        gap(arr),
        float(np.percentile(draws, 2.5)),
        float(np.percentile(draws, 97.5)),
        float(2 * min((draws <= 0).mean(), (draws >= 0).mean())),
    )


def render_chart(rows: list[dict]) -> str:
    """Four bars: the artifact and the honest version, same events, side by side.

    Deliberately shares the y-scale across both panels so the collapse is a
    thing you see rather than a thing you read.
    """
    W, H = 1200, 810
    BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
    GREEN, RED, GREY = "#3fb950", "#f85149", "#6e7681"
    TOP, CH, BW = 250, 300, 130

    def y(v: float) -> float:
        return TOP + CH - v / 0.8 * CH

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<text x="70" y="62" font-size="36" font-weight="700" fill="{TEXT}">An early lead predicts nothing</text>',
        f'<text x="70" y="102" font-size="24" fill="{SUB}">402 organic attention spikes, split by whether they were ahead of Bitcoin after day 1</text>',
        f'<line x1="70" y1="{y(0.5):.0f}" x2="{W-70}" y2="{y(0.5):.0f}" stroke="{GRID}" stroke-width="2" stroke-dasharray="7 7"/>',
        f'<text x="{W-70}" y="{y(0.5)-14:.0f}" font-size="19" fill="{SUB}" text-anchor="end">coin flip</text>',
    ]
    panels = [(rows[0], 150, "Scored over days 1 to 3", "the number that looks like a signal"),
              (rows[1], 700, "Scored over days 2 to 3 only", "day 1 removed from the outcome")]
    for r, x0, title, note in panels:
        out += [
            f'<text x="{x0}" y="188" font-size="27" font-weight="700" fill="{TEXT}">{title}</text>',
            f'<text x="{x0}" y="220" font-size="20" fill="{SUB}">{note}</text>',
        ]
        for i, (key, lbl, colr) in enumerate([("ahead", "ahead", GREEN), ("behind", "behind", RED)]):
            v = r[key]
            bx = x0 + i * (BW + 60)
            colr = colr if abs(r["gap"]) > 0.1 else GREY
            out += [
                f'<rect x="{bx}" y="{y(v):.0f}" width="{BW}" height="{CH - (y(v) - TOP):.0f}" rx="8" fill="{colr}"/>',
                f'<text x="{bx + BW//2}" y="{y(v)-18:.0f}" font-size="34" font-weight="700" fill="{colr}" text-anchor="middle">{v:.0%}</text>',
                f'<text x="{bx + BW//2}" y="{TOP+CH+38}" font-size="21" fill="{SUB}" text-anchor="middle">{lbl} on day 1</text>',
            ]
        gap = f"{r['gap'] * 100:+.0f} pts" if abs(r["gap"]) > 0.005 else "0 pts"
        pval = "p &lt; 0.001" if r["p_two_sided"] < 0.001 else f'p = {r["p_two_sided"]:.2f}'
        out.append(
            f'<text x="{x0}" y="{TOP+CH+96}" font-size="24" font-weight="700" '
            f'fill="{GREEN if abs(r["gap"]) > 0.1 else GREY}">gap {gap} · {pval}</text>'
        )
    out += [
        f'<text x="70" y="{H-88}" font-size="23" fill="{TEXT}">Day 1 sits inside day 3, so an early lead is baked into the 3-day result before you measure it.</text>',
        f'<text x="70" y="{H-54}" font-size="21" fill="{SUB}">Take day 1 out and both groups land within a tenth of a point. The 44 point spread was arithmetic, not information.</text>',
        f'<text x="70" y="{H-22}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
        "</svg>",
    ]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--spam-split", type=float, default=0.5)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    org = build_eligible(args).query("grp == 'organic spike'").copy()
    org["rest"] = remainder_excess(org)
    ahead = org["adj_1d"] > 0

    print(f"\norganic spike events: {len(org)}  ({ahead.sum()} ahead after day 1, {(~ahead).sum()} behind)")
    print(f"unconditional +3d beats-BTC rate: {(org['adj_3d'] > 0).mean():.1%}\n")

    rows = []
    for col, label in [("adj_3d", "days 1-3 (overlapping)"), ("rest", "days 2-3 (clean)")]:
        a = (org.loc[ahead, col] > 0).mean()
        b = (org.loc[~ahead, col] > 0).mean()
        diff, lo, hi, p = block_bootstrap_gap(org, col, ahead, args.bootstrap)
        rows.append(
            {"window": label, "ahead": a, "behind": b, "gap": diff, "ci_lo": lo, "ci_hi": hi, "p_two_sided": p}
        )
        print(f"{label}")
        print(f"  ahead after day 1   {a:>6.1%}")
        print(f"  behind after day 1  {b:>6.1%}")
        print(f"  gap {diff:+.1%}  CI [{lo:+.1%}, {hi:+.1%}]  p={p:.3f}\n")

    print(f"corr(day-1 lead, days 1-3) = {np.corrcoef(org['adj_1d'], org['adj_3d'])[0, 1]:.2f}  (shares a term)")
    print(f"corr(day-1 lead, days 2-3) = {np.corrcoef(org['adj_1d'], org['rest'])[0, 1]:.2f}  (does not)")

    OUT_DIR.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_DIR / "day1.csv", index=False)
    (OUT_DIR / "day1-chart.svg").write_text(render_chart(rows))
    print("\nWrote out/day1.csv and out/day1-chart.svg")


if __name__ == "__main__":
    main()
