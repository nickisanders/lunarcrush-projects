#!/usr/bin/env python3
"""Does an attention spike mean anything once price has already moved?

The headline result requires a flat price on the spike day. That condition is
easy to read as a tidy-up detail. It is the whole finding.

This splits every genuine organic spike by what price did on the spike day and
scores each bucket the same way. A spike on a flat day shifts the 3-day
beats-BTC odds by +7.2 points. The identical spike on a day price had already
run more than 5% shifts them by nothing at all.

Which makes the practical rule the opposite of the instinct: the days when
your feed is full of coins trending are precisely the days that trending
means least, because attention that arrives after the move is a reaction to
it, not information about what happens next.

Usage:
    python3 price_context.py [--bootstrap 2000]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from uprate import build_eligible

OUT_DIR = Path(__file__).resolve().parent / "out"
EDGES = [-np.inf, -0.05, -0.02, 0.02, 0.05, np.inf]
LABELS = ["fell >5%", "fell 2-5%", "flat (<2%)", "rose 2-5%", "rose >5%"]
MIN_BUCKET = 20


def block_bootstrap(group: pd.DataFrame, base: pd.DataFrame, iters: int, seed: int = 7):
    """Month-block bootstrap of the group-minus-baseline gap in +3d hit rate.

    Both legs are resampled on the SAME month draws, so a bull month that
    flatters the group flatters its comparison too.
    """
    def blocks(df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        d["blk"] = d.index.to_period("M")
        return d.groupby("blk").agg(p=("adj_3d", lambda x: (x > 0).sum()), n=("adj_3d", "count"))

    joined = blocks(group).join(blocks(base), rsuffix="_b", how="inner").to_numpy()
    if len(joined) < 3:
        return None
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(iters):
        k = joined[rng.integers(0, len(joined), len(joined))]
        draws.append(k[:, 0].sum() / k[:, 1].sum() - k[:, 2].sum() / k[:, 3].sum())
    draws = np.array(draws)
    observed = (group["adj_3d"] > 0).mean() - (base["adj_3d"] > 0).mean()
    return (observed, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def esc(s: str) -> str:
    """Bucket labels carry < and >, which are not valid raw in SVG text."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_chart(rows: list[dict], base_rate: float) -> str:
    W, H = 1200, 800
    BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
    GREEN, GREY = "#3fb950", "#6e7681"
    TOP, CH, BW, GAP, X0 = 250, 340, 140, 44, 170
    top_val = 0.55

    def y(v: float) -> float:
        return TOP + CH - v / top_val * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="72" font-size="36" font-weight="700" fill="{TEXT}">The spike only counts before the move</text>',
         f'<text x="60" y="112" font-size="23" fill="{SUB}">1,218 genuine, low-spam attention spikes, split by what price did that same day</text>',
         f'<text x="60" y="146" font-size="23" fill="{SUB}">bars show how often the coin beat Bitcoin over the next 3 days. dashed line is an ordinary coin-day.</text>',
         f'<line x1="{X0 - 30}" y1="{y(base_rate):.0f}" x2="{W - 60}" y2="{y(base_rate):.0f}" '
         f'stroke="{GRID}" stroke-width="2" stroke-dasharray="7 7"/>',
         f'<text x="{X0 - 45}" y="{y(base_rate) + 8:.0f}" font-size="20" fill="{SUB}" text-anchor="end">'
         f'{base_rate:.0%}</text>']

    for i, r in enumerate(rows):
        x = X0 + i * (BW + GAP)
        v = r["rate"]
        color = GREEN if r["p"] < 0.05 else GREY
        p += [f'<rect x="{x}" y="{y(v):.0f}" width="{BW}" height="{TOP + CH - y(v):.0f}" rx="8" fill="{color}"/>',
              f'<text x="{x + BW // 2}" y="{y(v) - 18:.0f}" font-size="30" font-weight="700" fill="{color}" '
              f'text-anchor="middle">{v:.0%}</text>',
              f'<text x="{x + BW // 2}" y="{TOP + CH + 40}" font-size="22" fill="{TEXT}" '
              f'text-anchor="middle">{esc(r["label"])}</text>',
              f'<text x="{x + BW // 2}" y="{TOP + CH + 70}" font-size="19" fill="{SUB}" '
              f'text-anchor="middle">n={r["n"]}</text>']

    p += [f'<text x="60" y="{H - 108}" font-size="23" fill="{TEXT}">Same spike, same spam filter, same everything. The only difference is whether price had already moved.</text>',
          f'<text x="60" y="{H - 74}" font-size="21" fill="{SUB}">Only the flat-price bar is statistically distinguishable from an ordinary day (+7.2 points, p = 0.001). Grey bars are not.</text>',
          f'<text x="60" y="{H - 44}" font-size="21" fill="{SUB}">Attention that arrives after the move is a reaction to it, not information about what comes next.</text>',
          f'<text x="60" y="{H - 16}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--spam-split", type=float, default=0.5)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    e = build_eligible(args)
    base = e[e["grp"] == "baseline"]
    # Every genuine organic spike, regardless of what price did that day. The
    # published event set is only the flat-price slice of this.
    spikes = e[(e["z"] >= args.z) & (e["spam_ratio"].fillna(0) <= args.spam_split)].copy()
    spikes["bucket"] = pd.cut(spikes["ret_1d"], EDGES, labels=LABELS)

    base_rate = (base["adj_3d"] > 0).mean()
    print(f"{len(spikes):,} organic spikes | {len(base):,} baseline coin-days")
    print(f"baseline +3d beats-BTC rate: {base_rate:.1%}\n")
    print(f"{'same-day price move':<20}{'n':>6}{'beats BTC':>12}{'vs baseline':>13}{'p':>8}")

    rows = []
    for label in LABELS:
        g = spikes[spikes["bucket"] == label]
        if len(g) < MIN_BUCKET:
            print(f"{label:<20}{len(g):>6}   too few events, skipped")
            continue
        rate = (g["adj_3d"] > 0).mean()
        res = block_bootstrap(g, base, args.bootstrap)
        diff, lo, hi, pv = res if res else (rate - base_rate, np.nan, np.nan, np.nan)
        rows.append({"label": label, "n": len(g), "rate": rate, "diff": diff,
                     "ci_lo": lo, "ci_hi": hi, "p": pv})
        print(f"{label:<20}{len(g):>6}{rate:>11.1%}{diff:>12.1%}{pv:>8.3f}")

    OUT_DIR.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_DIR / "price-context.csv", index=False)
    (OUT_DIR / "price-context.svg").write_text(render_chart(rows, base_rate))
    print("\nWrote out/price-context.csv and out/price-context.svg")


if __name__ == "__main__":
    main()
