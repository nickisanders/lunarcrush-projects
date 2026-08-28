#!/usr/bin/env python3
"""When attention spikes, is it more people or the same people posting more?

"Interactions are up 5x" is the headline everyone quotes. It does not say
whether a new crowd arrived or the existing one got louder, and those are
different events with the same number attached.

Applying the interaction z-score construction to unique contributors splits
every genuine spike in two. Two thirds are the same crowd getting louder: the
conversation grows without the audience growing.

Whether that distinction pays is a separate question, and the honest answer is
that it does not, at least not measurably. The beats-BTC rate is the same
either way (48.5% vs 49.3%). Crowd-grew spikes do carry a wider outcome
distribution, but the mean gap does not clear its own confidence interval, so
this ships as a description of what a spike is made of, not as a filter.

Usage:
    python3 crowd_growth.py [--contributor-z 2.0] [--bootstrap 4000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import FLOOR, HORIZONS, RAW_DIR, TRAILING, add_signals, load_coin

OUT_DIR = Path(__file__).resolve().parent / "out"
QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]


def build_panel() -> pd.DataFrame:
    """The backtest panel, plus a contributor z-score built exactly like the
    interaction one so the two are directly comparable."""
    frames = []
    for path in sorted(RAW_DIR.glob("*.json")):
        df = load_coin(path)
        if df is None:
            continue
        d = add_signals(df)
        lc = np.log1p(d["contributors_active"].fillna(0))
        mean = lc.rolling(TRAILING).mean().shift(1)
        sd = lc.rolling(TRAILING).std().shift(1)
        d["cz"] = (lc - mean) / sd.replace(0, np.nan)
        frames.append(d)
    all_days = pd.concat(frames)

    btc = all_days[all_days["symbol"] == "BTC"]
    all_days = all_days.merge(
        btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
            columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}
        ),
        left_index=True, right_index=True, how="left",
    )
    e = all_days[
        (all_days["market_cap"] >= 50e6)
        & (all_days["volume_24h"].fillna(0) >= 1e6)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna() & all_days["cz"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()
    for h in HORIZONS:
        lo, hi = e[f"fwd_{h}d"].quantile([0.01, 0.99])
        e[f"fwd_{h}d"] = e[f"fwd_{h}d"].clip(lo, hi)
        e[f"adj_{h}d"] = e[f"fwd_{h}d"] - e[f"btc_{h}d"]
    return e


def block_bootstrap_mean(a: pd.DataFrame, b: pd.DataFrame, iters: int, seed: int = 7):
    """Month-block bootstrap of the difference in mean +3d adjusted return."""
    def blocks(df):
        d = df.copy()
        d["blk"] = d.index.to_period("M")
        return d.groupby("blk")["adj_3d"].agg(["sum", "count"])

    j = blocks(a).join(blocks(b), rsuffix="_b", how="inner").to_numpy()
    if len(j) < 3:
        return None
    rng = np.random.default_rng(seed)
    draws = np.array([
        (lambda k: k[:, 0].sum() / k[:, 1].sum() - k[:, 2].sum() / k[:, 3].sum())(
            j[rng.integers(0, len(j), len(j))]
        )
        for _ in range(iters)
    ])
    observed = a["adj_3d"].mean() - b["adj_3d"].mean()
    return (observed, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def render_chart(groups: dict, stats: dict) -> str:
    """Composition on the left, outcome spread on the right.

    The right panel is p10-to-p90 with a median tick rather than a bar, because
    the finding is that the middles are identical and the tails are not. A bar
    chart of means would show a difference the significance test does not
    support.
    """
    W, H = 1300, 700
    BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
    BLUE, GREY = "#58a6ff", "#8b949e"
    same, grew = groups["same"], groups["grew"]

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="74" font-size="36" font-weight="700" fill="{TEXT}">Most hype is not new people</text>',
         f'<text x="60" y="116" font-size="23" fill="{SUB}">{stats["spikes"]} genuine, low-spam attention spikes on coins whose price had not moved</text>']

    # Left: composition.
    bx, by, bw, bh = 60, 200, 480, 74
    share = stats["shareSameCrowd"]
    p += [
        f'<text x="{bx}" y="{by - 22}" font-size="24" fill="{TEXT}" font-weight="700">What the spike was made of</text>',
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{BLUE}"/>',
        f'<rect x="{bx + bw * share:.0f}" y="{by}" width="{bw * (1 - share):.0f}" height="{bh}" rx="10" fill="{TRACK}"/>',
        f'<text x="{bx + 20}" y="{by + 48}" font-size="30" font-weight="800" fill="#0d1117">{share * 100:.0f}%</text>',
        f'<text x="{bx}" y="{by + bh + 44}" font-size="23" fill="{BLUE}" font-weight="700">the same crowd, posting more</text>',
        f'<text x="{bx}" y="{by + bh + 78}" font-size="23" fill="{SUB}">{(1 - share) * 100:.0f}% had an actual influx of new contributors</text>',
        f'<text x="{bx}" y="{by + bh + 132}" font-size="22" fill="{TEXT}">On a normal day the median coin gets {stats["normalPerContributor"]:,} interactions</text>',
        f'<text x="{bx}" y="{by + bh + 164}" font-size="22" fill="{TEXT}">per active contributor. On a spike day: {stats["spikePerContributor"]:,}.</text>',
        f'<text x="{bx}" y="{by + bh + 196}" font-size="22" fill="{SUB}">Same people. Roughly five times the noise each.</text>',
    ]

    # Right: outcome ranges.
    rx, ry, rw = 700, 250, 520
    lo_v, hi_v = -0.10, 0.10
    def xv(v: float) -> float:
        return rx + (v - lo_v) / (hi_v - lo_v) * rw
    p += [f'<text x="{rx}" y="{ry - 72}" font-size="24" fill="{TEXT}" font-weight="700">Did it matter for price?</text>',
          f'<text x="{rx}" y="{ry - 42}" font-size="21" fill="{SUB}">return vs Bitcoin over the next 3 days, p10 to p90</text>']
    for tick in (-0.10, -0.05, 0, 0.05, 0.10):
        p += [f'<line x1="{xv(tick):.0f}" y1="{ry - 16}" x2="{xv(tick):.0f}" y2="{ry + 196}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{xv(tick):.0f}" y="{ry + 226}" font-size="19" fill="{SUB}" text-anchor="middle">{tick * 100:+.0f}%</text>']
    for i, (label, g, col) in enumerate([("crowd grew", grew, BLUE), ("same crowd, louder", same, GREY)]):
        y = ry + 40 + i * 104
        p += [
            f'<text x="{rx}" y="{y - 26}" font-size="22" fill="{col}" font-weight="700">{label} (n={g["n"]})</text>',
            f'<line x1="{xv(g["p10"]):.0f}" y1="{y + 16}" x2="{xv(g["p90"]):.0f}" y2="{y + 16}" stroke="{col}" stroke-width="16" stroke-linecap="round" opacity="0.5"/>',
            f'<line x1="{xv(g["p50"]):.0f}" y1="{y - 2}" x2="{xv(g["p50"]):.0f}" y2="{y + 34}" stroke="{col}" stroke-width="4"/>',
            f'<text x="{xv(g["p90"]):.0f}" y="{y - 4}" font-size="19" fill="{col}" text-anchor="middle">{g["p90"] * 100:+.1f}%</text>',
        ]
    p += [
        f'<text x="60" y="{H - 108}" font-size="23" fill="{TEXT}">Both beat Bitcoin about equally often ({stats["grewRate"] * 100:.1f}% vs {stats["sameRate"] * 100:.1f}%). The medians are identical.</text>',
        f'<text x="60" y="{H - 74}" font-size="21" fill="{SUB}">A growing crowd widens the tails, but the gap in mean return is {stats["gap"] * 100:+.1f}pp with a CI of [{stats["ci"][0] * 100:+.1f}, {stats["ci"][1] * 100:+.1f}], p = {stats["p"]:.2f}.</text>',
        f'<text x="60" y="{H - 44}" font-size="21" fill="{SUB}">So this is a description of what a spike is made of, not a filter I would trade on.</text>',
        f'<text x="60" y="{H - 16}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
        "</svg>",
    ]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contributor-z", type=float, default=2.0)
    ap.add_argument("--bootstrap", type=int, default=4000)
    args = ap.parse_args()

    e = build_panel()
    normal = e[e.z < 3.0]
    normal = normal[normal.contributors_active > 0]
    per_normal = (normal.interactions / normal.contributors_active).median()

    sp = e[(e.z >= 3.0) & (e.spam_ratio.fillna(0) <= 0.5) & (e.ret_1d.abs() <= 0.02)].copy()
    sp["kind"] = np.where(sp.cz >= args.contributor_z, "crowd grew", "same crowd, louder")
    grew = sp[sp.kind == "crowd grew"]
    same = sp[sp.kind == "same crowd, louder"]
    per_spike = (sp.interactions / sp.contributors_active.replace(0, np.nan)).median()

    print(f"{len(sp)} organic flat-price spikes\n")
    print(f"the same crowd, louder: {len(same)} ({len(same)/len(sp):.0%})")
    print(f"an actual influx:       {len(grew)} ({len(grew)/len(sp):.0%})\n")
    print(f"interactions per active contributor: {per_normal:,.0f} on a normal day, "
          f"{per_spike:,.0f} on a spike day\n")
    print(f"{'kind':<22}{'n':>6}{'beats BTC':>12}{'p10':>9}{'median':>9}{'p90':>9}")
    groups = {}
    for key, label, g in [("grew", "crowd grew", grew), ("same", "same crowd, louder", same)]:
        q = g.adj_3d.quantile(QUANTILES)
        groups[key] = {"n": len(g), "p10": float(q[0.1]), "p50": float(q[0.5]), "p90": float(q[0.9])}
        print(f"{label:<22}{len(g):>6}{(g.adj_3d > 0).mean():>11.1%}"
              f"{q[0.1]*100:>8.1f}%{q[0.5]*100:>8.1f}%{q[0.9]*100:>8.1f}%")

    res = block_bootstrap_mean(grew, same, args.bootstrap)
    diff, lo, hi, pv = res
    print(f"\nmean-return gap: {diff*100:+.2f}pp  CI [{lo*100:+.2f}, {hi*100:+.2f}]  p={pv:.3f}")
    print("Not significant, so the split describes spikes rather than filtering them.")

    stats = {
        "spikes": len(sp), "shareSameCrowd": len(same) / len(sp),
        "grewRate": float((grew.adj_3d > 0).mean()), "sameRate": float((same.adj_3d > 0).mean()),
        "normalPerContributor": int(round(per_normal)), "spikePerContributor": int(round(per_spike)),
        "gap": diff, "ci": [lo, hi], "p": pv, "contributorZ": args.contributor_z,
    }
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "crowd-growth.json").write_text(json.dumps({"stats": stats, "groups": groups}, indent=1))
    (OUT_DIR / "crowd-growth.svg").write_text(render_chart(groups, stats))
    print("\nWrote out/crowd-growth.json and out/crowd-growth.svg")


if __name__ == "__main__":
    main()
