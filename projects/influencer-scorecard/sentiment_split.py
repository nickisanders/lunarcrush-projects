#!/usr/bin/env python3
"""Does it matter whether the post was bullish or bearish?

Yesterday's result was that being mentioned by a big account does not help.
The obvious objection is that a mention is not a recommendation: `lookonchain`
reporting a whale dump and a caller shouting "next 10x" both register as a
mention of the same ticker, so mixing them could be hiding a real signal in
the bullish half.

It is not. Splitting the mentions by the post's own sentiment score changes
nothing. The most bullish quarter beat Bitcoin 37.4% of the time over 7 days
against 38.5% for the most bearish quarter: a gap of -1.2 points at p = 0.59,
with the bands not even ordered. Correlation between a post's sentiment and
the coin's 7-day excess return is -0.001.

Two handling notes that matter:

- **A third of posts score exactly 3.00.** On a 1-5 scale that is the neutral
  midpoint and it lands on 2,433 of 7,053 mentions, which is far too many to
  be a measurement. Treated as unscored and excluded rather than filed as
  neutral opinion.
- **The remaining spread is narrow.** Even after excluding the default, the
  5th to 95th percentile runs about 2.8 to 3.4 on a 1-5 scale. This tests
  relative stance within a tight band, not bulls against bears.

Usage:
    python3 sentiment_split.py [--horizon 7]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
NEUTRAL_DEFAULT = 3.00
BANDS = ["most bearish", "2", "3", "most bullish"]
BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
RED, GREEN, GREY = "#f85149", "#3fb950", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def block_bootstrap_gap(a: pd.DataFrame, b: pd.DataFrame, col: str,
                        iters: int = 3000, seed: int = 7):
    """Month-block bootstrap of the gap in beats-BTC rate."""
    ga = {k: (v[col] > 0).astype(float).values for k, v in a.groupby(a.date.dt.to_period("M"))}
    gb = {k: (v[col] > 0).astype(float).values for k, v in b.groupby(b.date.dt.to_period("M"))}
    blocks = sorted(set(ga) & set(gb))
    rng = np.random.default_rng(seed)
    draws = np.array([
        np.concatenate([ga[k] for k in pick]).mean() - np.concatenate([gb[k] for k in pick]).mean()
        for pick in (rng.choice(blocks, len(blocks), replace=True) for _ in range(iters))
    ])
    return ((a[col] > 0).mean() - (b[col] > 0).mean(),
            float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def render_chart(rows: list[dict], gap: dict, corr: float, horizon: int, dropped: int) -> str:
    W, H = 1300, 880
    TOP, CH, BW, GAP, X0 = 300, 300, 150, 70, 170
    top_val = 0.50

    def y(v: float) -> float:
        return TOP + CH - v / top_val * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">Bullish posts did no better than bearish ones</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">how often the coin beat Bitcoin over {horizon} days, by how bullish the post itself was</text>',
         f'<text x="60" y="156" font-size="23" fill="{SUB}">{sum(r["n"] for r in rows):,} mentions by named crypto accounts, split into quarters by the post\'s own sentiment score</text>']

    for tick in (0.1, 0.2, 0.3, 0.4, 0.5):
        p += [f'<line x1="{X0 - 40}" y1="{y(tick):.0f}" x2="{W - 90}" y2="{y(tick):.0f}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{X0 - 52}" y="{y(tick) + 7:.0f}" font-size="18" fill="{SUB}" text-anchor="end">{tick * 100:.0f}%</text>']

    for i, r in enumerate(rows):
        x = X0 + i * (BW + GAP)
        col = RED if r["label"] == "most bearish" else GREEN if r["label"] == "most bullish" else GREY
        p += [f'<rect x="{x}" y="{y(r["rate"]):.0f}" width="{BW}" height="{TOP + CH - y(r["rate"]):.0f}" rx="8" fill="{col}"/>',
              f'<text x="{x + BW // 2}" y="{y(r["rate"]) - 16:.0f}" font-size="30" font-weight="700" fill="{col}" text-anchor="middle">{r["rate"] * 100:.1f}%</text>',
              f'<text x="{x + BW // 2}" y="{TOP + CH + 42}" font-size="22" fill="{TEXT}" text-anchor="middle">{r["label"]}</text>',
              f'<text x="{x + BW // 2}" y="{TOP + CH + 70}" font-size="18" fill="{SUB}" text-anchor="middle">n={r["n"]:,} · {r["range"]}</text>']

    p += [f'<text x="60" y="{H - 148}" font-size="24" fill="{TEXT}" font-weight="700">Most bullish minus most bearish: {gap["gap"] * 100:+.1f} points, p = {gap["p"]:.2f}. The bands are not even in order.</text>',
          f'<text x="60" y="{H - 112}" font-size="21" fill="{SUB}">Correlation between a post\'s sentiment and the coin\'s {horizon}-day excess return: {corr:+.3f}.</text>',
          f'<text x="60" y="{H - 80}" font-size="21" fill="{SUB}">So the null is not an artifact of mixing whale-dump reports with bullish calls. Stance makes no difference either.</text>',
          f'<text x="60" y="{H - 48}" font-size="20" fill="{SUB}">{dropped:,} posts scoring exactly 3.00 were excluded: on a 1-5 scale that is the neutral midpoint and far too common to be a measurement.</text>',
          f'<text x="60" y="{H - 18}" font-size="19" fill="{SUB}">Data: LunarCrush · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=7, choices=(3, 7, 30))
    args = ap.parse_args()
    col = f"a{args.horizon}"

    d = pd.read_csv(OUT / "events.csv")
    d["sentiment"] = pd.to_numeric(d["sentiment"], errors="coerce")
    d["date"] = pd.to_datetime(d["date"])
    default = d["sentiment"].eq(NEUTRAL_DEFAULT)
    print(f"{default.sum():,} of {len(d):,} posts score exactly {NEUTRAL_DEFAULT:.2f} "
          f"({default.mean():.0%}); treated as unscored\n")

    scored = d[~default].dropna(subset=[col]).copy()
    scored["band"] = pd.qcut(scored["sentiment"], 4, labels=BANDS)
    print(f"{len(scored):,} mentions with a real sentiment score and a {args.horizon}d outcome\n")
    print(f"{'band':<16}{'n':>7}{'range':>14}{'beats BTC':>12}{'median':>10}")
    rows = []
    for b, g in scored.groupby("band", observed=True):
        rng = f"{g.sentiment.min():.2f}-{g.sentiment.max():.2f}"
        rows.append({"label": str(b), "n": len(g), "range": rng,
                     "rate": float((g[col] > 0).mean()), "median": float(g[col].median())})
        print(f"{str(b):<16}{len(g):>7,}{rng:>14}{(g[col] > 0).mean():>11.1%}{g[col].median() * 100:>9.2f}%")

    bull, bear = scored[scored.band == "most bullish"], scored[scored.band == "most bearish"]
    g, lo, hi, pv = block_bootstrap_gap(bull, bear, col)
    corr = float(np.corrcoef(scored["sentiment"], scored[col])[0, 1])
    print(f"\nmost bullish minus most bearish: {g * 100:+.1f}pp  CI [{lo * 100:+.1f}, {hi * 100:+.1f}]  p={pv:.3f}")
    print(f"corr(sentiment, {args.horizon}d excess) = {corr:+.3f}")

    gap = {"gap": g, "ci": [lo, hi], "p": pv}
    OUT.mkdir(exist_ok=True)
    (OUT / "sentiment-split.json").write_text(json.dumps(
        {"bands": rows, "gap": gap, "corr": corr, "horizon": args.horizon,
         "excludedDefault": int(default.sum())}, indent=1))
    (OUT / "sentiment-split.svg").write_text(
        render_chart(rows, gap, corr, args.horizon, int(default.sum())))
    print("\nWrote out/sentiment-split.json and out/sentiment-split.svg")


if __name__ == "__main__":
    main()
