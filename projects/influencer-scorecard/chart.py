#!/usr/bin/env python3
"""Chart the scorecard's headline: mentioned vs unmentioned, at every horizon.

Runs the comparison at 3, 7 and 30 days and writes out/scorecard-chart.svg.

Usage: python3 chart.py
"""

import json
from pathlib import Path

import pandas as pd

from scorecard import (HORIZONS, block_bootstrap_rate_gap, extract_events,
                       load_prices, matched_baseline, score_events)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
RED, GREY, GREEN = "#f85149", "#6e7681", "#3fb950"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def render(results: list[dict], creators: int, events: int) -> str:
    W, H = 1300, 850
    TOP, CH, BW, GAP, X0 = 290, 300, 110, 40, 150
    top_val = 0.50

    def y(v: float) -> float:
        return TOP + CH - v / top_val * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">Getting mentioned by a big account is worth nothing</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">how often a coin beat Bitcoin after {creators} named crypto accounts posted about it, against coins nobody mentioned</text>',
         f'<text x="60" y="156" font-size="23" fill="{SUB}">{events:,} distinct mentions, months of post history, every mention counted once per creator per day</text>']

    for tick in (0.1, 0.2, 0.3, 0.4, 0.5):
        p += [f'<line x1="{X0 - 40}" y1="{y(tick):.0f}" x2="{W - 300}" y2="{y(tick):.0f}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{X0 - 52}" y="{y(tick) + 7:.0f}" font-size="18" fill="{SUB}" text-anchor="end">{tick * 100:.0f}%</text>']

    for i, r in enumerate(results):
        gx = X0 + i * (2 * BW + GAP + 90)
        for k, (label, rate, col) in enumerate([("mentioned", r["mentioned"], RED),
                                                ("nobody mentioned", r["control"], GREY)]):
            x = gx + k * (BW + GAP)
            p += [f'<rect x="{x}" y="{y(rate):.0f}" width="{BW}" height="{TOP + CH - y(rate):.0f}" rx="8" fill="{col}"/>',
                  f'<text x="{x + BW // 2}" y="{y(rate) - 16:.0f}" font-size="27" font-weight="700" fill="{col}" text-anchor="middle">{rate * 100:.0f}%</text>']
        p += [f'<text x="{gx + BW + GAP // 2}" y="{TOP + CH + 42}" font-size="24" fill="{TEXT}" text-anchor="middle">{r["horizon"]} days</text>',
              f'<text x="{gx + BW + GAP // 2}" y="{TOP + CH + 74}" font-size="19" fill="{SUB}" text-anchor="middle">gap {r["gap"] * 100:+.1f}pp · p = {r["p"]:.2f}</text>']

    # Legend runs horizontally above the plot. On the right it sat on top of
    # the 30-day bars.
    p += [f'<rect x="{X0 - 40}" y="{TOP - 62}" width="16" height="16" rx="4" fill="{RED}"/>',
          f'<text x="{X0 - 16}" y="{TOP - 48}" font-size="21" fill="{TEXT}">a coin they mentioned</text>',
          f'<rect x="{X0 + 240}" y="{TOP - 62}" width="16" height="16" rx="4" fill="{GREY}"/>',
          f'<text x="{X0 + 264}" y="{TOP - 48}" font-size="21" fill="{TEXT}">a coin nobody mentioned</text>']

    p += [f'<text x="60" y="{H - 150}" font-size="23" fill="{TEXT}">A coin a big account talked about did not beat Bitcoin more often than a coin nobody talked about.</text>',
          f'<text x="60" y="{H - 116}" font-size="21" fill="{SUB}">Only the 3-day gap clears its own confidence interval, and it runs against the mentioned coins.</text>',
          f'<text x="60" y="{H - 82}" font-size="21" fill="{SUB}">Mentioned coins do carry a better median ({results[1]["median_m"] * 100:+.1f}% vs {results[1]["median_c"] * 100:+.1f}% at 7 days), which is a liquidity difference: coins people discuss are larger,</text>',
          f'<text x="60" y="{H - 54}" font-size="21" fill="{SUB}">so their outcomes are less dispersed in both tails. Fewer big winners as well as fewer big losers.</text>',
          f'<text x="60" y="{H - 20}" font-size="19" fill="{SUB}">A mention is not a recommendation, and this cannot show causation. Data: LunarCrush · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    coins = json.loads((HERE / "data" / "coins.json").read_text())
    symbols = {c["symbol"].upper() for c in coins}
    prices = load_prices()
    events = extract_events(symbols)
    scored = score_events(events, prices)

    results = []
    for h in HORIZONS:
        col = f"a{h}"
        d = scored.dropna(subset=[col])
        base, base_dates = matched_baseline(prices, d, h)
        gap, lo, hi, pv = block_bootstrap_rate_gap(d[col], d["date"], base, base_dates)
        results.append({"horizon": h, "mentioned": float((d[col] > 0).mean()),
                        "control": float((base > 0).mean()), "gap": gap, "ci": [lo, hi], "p": pv,
                        "median_m": float(d[col].median()), "median_c": float(base.median()),
                        "n": len(d)})
        print(f"{h:>3}d  mentioned {(d[col] > 0).mean():.1%}  control {(base > 0).mean():.1%}  "
              f"gap {gap * 100:+.1f}pp  p={pv:.3f}  n={len(d):,}")

    OUT.mkdir(exist_ok=True)
    (OUT / "scorecard-summary.json").write_text(json.dumps(results, indent=1))
    (OUT / "scorecard-chart.svg").write_text(
        render(results, events.creator.nunique(), len(scored)))
    print("\nWrote out/scorecard-summary.json and out/scorecard-chart.svg")


if __name__ == "__main__":
    main()
