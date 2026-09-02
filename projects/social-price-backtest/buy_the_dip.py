#!/usr/bin/env python3
"""Chasing a pump is reliably bad. Is buying the crash reliably good?

The mirror of after_the_run.py, and the answer is not the mirror image.

No. The dip side has no clean gradient, and the one bucket that IS significant
runs the wrong way for dip buyers.

Buying a modest 10-30% dip returns a median -20.4% over 90 days against -9.2%
for a quiet week: a gap of -11.2 points at p < 0.001. That is measurably worse
than doing nothing, and it is the most common dip by far.

The deeper buckets are not distinguishable from a quiet week at all (50-70%:
+3.6%, p = 0.69). So the deep crash is the only case here that is not clearly
bad, and "not clearly bad" is all the data supports.

What separates the crash from the pump is the median, not the spread. Both are
wide. After a 200%+ pump the median is -43% and 45% lose another half; after a
50%+ crash the median is -2% and 21% do. The pump is a reliable loss. The crash
is a coin flip on a wide distribution.

A note on the mean. It reads +19.5%, and that number is not usable: forward
returns are winsorized at the 1st and 99th percentile, so the largest outcomes
are all exactly the clip value and the mean is partly an artifact of where the
clip sits. Medians and percentiles are reported instead.

Usage:
    python3 buy_the_dip.py [--bootstrap 3000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from after_the_run import block_bootstrap_median_gap, build_panel, episodes

OUT_DIR = Path(__file__).resolve().parent / "out"
QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]
BUCKETS = [
    ("fell 70%+", lambda r: r <= -0.70),
    ("fell 50-70%", lambda r: (r > -0.70) & (r <= -0.50)),
    ("fell 30-50%", lambda r: (r > -0.50) & (r <= -0.30)),
    ("fell 10-30%", lambda r: (r > -0.30) & (r <= -0.10)),
]


def render_chart(crash: dict, pump: dict, quiet: dict) -> str:
    """Two outcome ranges against the ordinary case.

    Ranges rather than bars, because both buckets are wide and the medians sit
    in very different places. A bar chart of medians would hide how much of
    each distribution lies on the other side of zero.
    """
    W, H = 1300, 830
    BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
    RED, BLUE, GREY = "#f85149", "#58a6ff", "#8b949e"
    L, R, TOP, ROW = 300, 110, 300, 140
    PW = W - L - R
    lo_v, hi_v = -1.0, 2.1

    def x(v: float) -> float:
        return L + (v - lo_v) / (hi_v - lo_v) * PW

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">Chasing a pump is a loss. Buying a crash is a lottery.</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">what the next 90 days looked like, 10th to 90th percentile, with the median marked</text>',
         f'<text x="60" y="156" font-size="23" fill="{SUB}">every episode counted once, 6.5 years, 1,000 coins</text>']

    for tick in (-1.0, -0.5, 0, 0.5, 1.0, 1.5, 2.0):
        p += [f'<line x1="{x(tick):.0f}" y1="{TOP - 40}" x2="{x(tick):.0f}" y2="{TOP + 2 * ROW + 40}" '
              f'stroke="{GRID}" stroke-width="{2 if tick == 0 else 1}"/>',
              f'<text x="{x(tick):.0f}" y="{TOP + 2 * ROW + 76}" font-size="19" fill="{SUB}" text-anchor="middle">{tick * 100:+.0f}%</text>']

    for i, (label, g, col, note) in enumerate([
        ("after a 50%+ crash", crash, BLUE, f'{crash["doubled"] * 100:.0f}% at least doubled · {crash["halved"] * 100:.0f}% lost another half'),
        ("after a 200%+ pump", pump, RED, f'{pump["halved"] * 100:.0f}% lost another half · only {pump["doubled"] * 100:.0f}% doubled'),
    ]):
        y = TOP + i * ROW
        p += [f'<text x="{L - 24}" y="{y + 2}" font-size="24" font-weight="700" fill="{col}" text-anchor="end">{label}</text>',
              f'<text x="{L - 24}" y="{y + 28}" font-size="18" fill="{SUB}" text-anchor="end">n={g["n"]}</text>',
              f'<line x1="{x(g["p10"]):.0f}" y1="{y}" x2="{x(g["p90"]):.0f}" y2="{y}" stroke="{col}" stroke-width="20" stroke-linecap="round" opacity="0.45"/>',
              f'<line x1="{x(g["p50"]):.0f}" y1="{y - 20}" x2="{x(g["p50"]):.0f}" y2="{y + 20}" stroke="{col}" stroke-width="5"/>',
              f'<text x="{x(g["p50"]):.0f}" y="{y - 32}" font-size="20" font-weight="700" fill="{col}" text-anchor="middle">{g["p50"] * 100:+.0f}%</text>',
              # Under the bar, not beside it: at +200% the range reaches the
              # right margin and a trailing note would run off the canvas.
              f'<text x="{L}" y="{y + 48}" font-size="19" fill="{SUB}">{note}</text>']

    y = TOP + 2 * ROW
    p += [f'<text x="{L - 24}" y="{y + 6}" font-size="22" fill="{GREY}" text-anchor="end">after a quiet week</text>',
          f'<line x1="{x(quiet["p10"]):.0f}" y1="{y}" x2="{x(quiet["p90"]):.0f}" y2="{y}" stroke="{GREY}" stroke-width="20" stroke-linecap="round" opacity="0.3"/>',
          f'<line x1="{x(quiet["p50"]):.0f}" y1="{y - 20}" x2="{x(quiet["p50"]):.0f}" y2="{y + 20}" stroke="{GREY}" stroke-width="5"/>',
          f'<text x="{x(quiet["p50"]):.0f}" y="{y - 32}" font-size="20" fill="{GREY}" text-anchor="middle">{quiet["p50"] * 100:+.0f}%</text>']

    p += [f'<text x="60" y="{H - 116}" font-size="23" fill="{TEXT}">Both are wide. What differs is where the middle sits: a pump median of {pump["p50"]*100:.0f}% against a crash median of {crash["p50"]*100:.0f}%.</text>',
          f'<text x="60" y="{H - 82}" font-size="21" fill="{SUB}">A 50%+ crash is not distinguishable from a quiet week (p = 0.69). A modest 10-30% dip measurably IS, and it is worse (p &lt; 0.001).</text>',
          f'<text x="60" y="{H - 52}" font-size="21" fill="{SUB}">So the deep crash is the only case here that is not clearly bad, and a coin flip is all the data supports.</text>',
          f'<text x="60" y="{H - 20}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def describe(ep: pd.DataFrame) -> dict:
    d = ep.dropna(subset=["f90"])
    q = d["f90"].quantile(QUANTILES)
    return {"n": len(d), "p10": float(q[0.1]), "p25": float(q[0.25]), "p50": float(q[0.5]),
            "p75": float(q[0.75]), "p90": float(q[0.9]),
            "doubled": float((d["f90"] > 1.0).mean()), "halved": float((d["f90"] < -0.5).mean())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=3000)
    args = ap.parse_args()

    e = build_panel()
    quiet = e[(e["run7"] >= -0.10) & (e["run7"] <= 0.10)]
    print(f"{len(e):,} eligible coin-days\n")
    print("Does buying the dip work? Each bucket against a quiet week.\n")
    print(f"{'last week':<14}{'episodes':>10}{'median +90d':>14}{'vs quiet':>11}{'p':>8}")
    rows = []
    for label, test in BUCKETS:
        ep = episodes(e[test(e["run7"])])
        gap, lo, hi, pv, n = block_bootstrap_median_gap(ep, quiet, "f90", args.bootstrap)
        rows.append({"label": label, "n": n, "median": float(ep["f90"].median()),
                     "gap": gap, "ci": [lo, hi], "p": pv})
        print(f"{label:<14}{n:>10,}{ep['f90'].median() * 100:>13.1f}%{gap * 100:>10.1f}%{pv:>8.3f}")
    sig = [r for r in rows if r["p"] < 0.05]
    if sig:
        print("\nSignificant: " + ", ".join(
            f"{r['label']} ({r['gap']*100:+.1f}pp, p={r['p']:.3f})" for r in sig))
        print("The only dip result that clears its own interval is that SMALL dips do worse")
        print("than a quiet week. Deeper crashes are indistinguishable from doing nothing.")

    crash = describe(episodes(e[e["run7"] <= -0.50]))
    pump = describe(episodes(e[e["run7"] > 2.0]))
    q = describe(quiet)
    print(f"\n{'':<22}{'p10':>9}{'median':>9}{'p90':>9}{'doubled':>10}{'halved':>9}")
    for name, g in [("after a 50%+ crash", crash), ("after a 200%+ pump", pump), ("after a quiet week", q)]:
        print(f"{name:<22}{g['p10']*100:>8.0f}%{g['p50']*100:>8.0f}%{g['p90']*100:>8.0f}%"
              f"{g['doubled']*100:>9.0f}%{g['halved']*100:>8.0f}%")
    print(f"\ncrash spread: {(crash['p90'] - crash['p10']) * 100:.0f} points. "
          f"pump spread: {(pump['p90'] - pump['p10']) * 100:.0f} points.")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "buy-the-dip.json").write_text(json.dumps(
        {"buckets": rows, "crash": crash, "pump": pump, "quiet": q}, indent=1))
    (OUT_DIR / "buy-the-dip.svg").write_text(render_chart(crash, pump, q))
    print("\nWrote out/buy-the-dip.json and out/buy-the-dip.svg")


if __name__ == "__main__":
    main()
