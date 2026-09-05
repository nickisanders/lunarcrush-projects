#!/usr/bin/env python3
"""The threshold does the work. Clearing it by more does nothing.

The published setup has three thresholds: an interaction z-score of at least
3, spam under 50%, and a price flat within 2%. Coins that clear them beat
Bitcoin over 3 days 49.0% of the time against 41.9% for an ordinary coin-day,
+7.1pp at p = 0.002.

The natural next thought is that a coin clearing them by more is a better bet.
It is not. Splitting the qualifying events into quartiles, neither a larger
spike nor a cleaner conversation predicts a better outcome:

    biggest z vs smallest z:    +5.9pp, CI [-0.6, +27.5], p = 0.068
    cleanest vs dirtiest spam:  +2.0pp, CI [-18.3, +19.5], p = 0.991

Correlation between z and the 3-day excess return is +0.056, and between spam
level and the same, -0.048.

This is a design result, not a curiosity. A tool that sorts its picks
strongest-first is presenting a hierarchy the data does not support, which is
what organic-watchlist was doing until this was measured.

Usage:
    python3 threshold_check.py [--bootstrap 4000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from uprate import build_eligible

OUT_DIR = Path(__file__).resolve().parent / "out"


def block_bootstrap_gap(a: pd.DataFrame, b: pd.DataFrame, col: str, iters: int, seed: int = 7):
    ga = {k: (v[col] > 0).astype(float).values for k, v in a.groupby(a.index.to_period("M"))}
    gb = {k: (v[col] > 0).astype(float).values for k, v in b.groupby(b.index.to_period("M"))}
    blocks = sorted(set(ga) & set(gb))
    if len(blocks) < 4:
        return None
    rng = np.random.default_rng(seed)
    draws = np.array([
        np.concatenate([ga[k] for k in pick]).mean() - np.concatenate([gb[k] for k in pick]).mean()
        for pick in (rng.choice(blocks, len(blocks), replace=True) for _ in range(iters))
    ])
    return ((a[col] > 0).mean() - (b[col] > 0).mean(),
            float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def render_chart(res: dict) -> str:
    W, H = 1300, 880
    BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
    GREEN, GREY = "#3fb950", "#6e7681"
    TOP, CH, BW = 300, 280, 130
    top_val = 0.60

    def y(v: float) -> float:
        return TOP + CH - v / top_val * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">Clearing the bar works. Clearing it by more does not.</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">how often a coin beat Bitcoin over the next 3 days, {res["n"]} qualifying attention spikes</text>',
         f'<line x1="640" y1="200" x2="640" y2="{TOP + CH + 110}" stroke="{GRID}" stroke-width="2" stroke-dasharray="7 7"/>',
         f'<text x="330" y="200" font-size="25" font-weight="700" fill="{GREEN}" text-anchor="middle">Does the setup work?</text>',
         f'<text x="980" y="200" font-size="25" font-weight="700" fill="{GREY}" text-anchor="middle">Does a stronger signal work better?</text>']

    groups = [
        (200, "ordinary\\ncoin-day", res["baseline"], GREY),
        (390, "cleared the\\nthreshold", res["qualifying"], GREEN),
        (720, "smallest\\nspikes", res["smallZ"], GREY),
        (880, "biggest\\nspikes", res["bigZ"], GREY),
        (1040, "dirtiest\\nallowed", res["dirty"], GREY),
        (1180, "cleanest", res["clean"], GREY),
    ]
    for x, label, rate, col in groups:
        p += [f'<rect x="{x - BW // 2}" y="{y(rate):.0f}" width="{BW}" height="{TOP + CH - y(rate):.0f}" rx="8" fill="{col}"/>',
              f'<text x="{x}" y="{y(rate) - 16:.0f}" font-size="26" font-weight="700" fill="{col}" text-anchor="middle">{rate * 100:.1f}%</text>']
        for k, part in enumerate(label.split("\\n")):
            p.append(f'<text x="{x}" y="{TOP + CH + 40 + k * 26}" font-size="19" fill="{TEXT}" text-anchor="middle">{part}</text>')

    p += [f'<text x="330" y="{TOP + CH + 122}" font-size="22" font-weight="700" fill="{GREEN}" text-anchor="middle">+{res["thresholdGap"] * 100:.1f} points, p = {res["thresholdP"]:.3f}</text>',
          f'<text x="800" y="{TOP + CH + 122}" font-size="22" font-weight="700" fill="{GREY}" text-anchor="middle">+{res["zGap"] * 100:.1f}pp, p = {res["zP"]:.2f}</text>',
          f'<text x="1110" y="{TOP + CH + 122}" font-size="22" font-weight="700" fill="{GREY}" text-anchor="middle">+{res["spamGap"] * 100:.1f}pp, p = {res["spamP"]:.2f}</text>']

    p += [f'<text x="60" y="{H - 116}" font-size="23" fill="{TEXT}">Once a coin clears the setup, how far it cleared it predicts nothing. Correlation between spike size and the</text>',
          f'<text x="60" y="{H - 84}" font-size="23" fill="{TEXT}">3-day excess return: {res["corrZ"]:+.3f}. Between spam level and the same: {res["corrSpam"]:+.3f}.</text>',
          f'<text x="60" y="{H - 50}" font-size="21" fill="{SUB}">Which means a tool that sorts its picks strongest-first is showing a hierarchy that is not there. Mine was, until I measured this.</text>',
          f'<text x="60" y="{H - 20}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · month-block bootstrap · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=4000)
    args = ap.parse_args()

    import argparse as _a
    e = build_eligible(_a.Namespace(z=3.0, flat=0.02, mcap=50e6, min_volume=1e6, spam_split=0.5))
    base = e[e.z < 3.0]
    sp = e[(e.z >= 3.0) & (e.spam_ratio.fillna(0) <= 0.5) & (e.ret_1d.abs() <= 0.02)].copy()
    sp["zq"] = pd.qcut(sp.z, 4, labels=["small", "2", "3", "big"])
    sp["spamq"] = pd.qcut(sp.spam_ratio.fillna(0), 4, labels=["clean", "2", "3", "dirty"])

    tg, tlo, thi, tp = block_bootstrap_gap(sp, base, "adj_3d", args.bootstrap)
    zg, zlo, zhi, zp = block_bootstrap_gap(sp[sp.zq == "big"], sp[sp.zq == "small"], "adj_3d", args.bootstrap)
    sg, slo, shi, spp = block_bootstrap_gap(sp[sp.spamq == "clean"], sp[sp.spamq == "dirty"], "adj_3d", args.bootstrap)

    res = {
        "n": len(sp),
        "baseline": float((base.adj_3d > 0).mean()), "qualifying": float((sp.adj_3d > 0).mean()),
        "smallZ": float((sp[sp.zq == "small"].adj_3d > 0).mean()),
        "bigZ": float((sp[sp.zq == "big"].adj_3d > 0).mean()),
        "dirty": float((sp[sp.spamq == "dirty"].adj_3d > 0).mean()),
        "clean": float((sp[sp.spamq == "clean"].adj_3d > 0).mean()),
        "thresholdGap": tg, "thresholdCI": [tlo, thi], "thresholdP": tp,
        "zGap": zg, "zCI": [zlo, zhi], "zP": zp,
        "spamGap": sg, "spamCI": [slo, shi], "spamP": spp,
        "corrZ": float(np.corrcoef(sp.z, sp.adj_3d)[0, 1]),
        "corrSpam": float(np.corrcoef(sp.spam_ratio.fillna(0), sp.adj_3d)[0, 1]),
    }
    print(f"{res['n']} qualifying spikes\n")
    print(f"  clearing the threshold:  {res['qualifying']:.1%} vs {res['baseline']:.1%} baseline"
          f"   {tg * 100:+.1f}pp  CI [{tlo * 100:+.1f}, {thi * 100:+.1f}]  p={tp:.3f}")
    print(f"  biggest vs smallest z:   {res['bigZ']:.1%} vs {res['smallZ']:.1%}"
          f"   {zg * 100:+.1f}pp  CI [{zlo * 100:+.1f}, {zhi * 100:+.1f}]  p={zp:.3f}")
    print(f"  cleanest vs dirtiest:    {res['clean']:.1%} vs {res['dirty']:.1%}"
          f"   {sg * 100:+.1f}pp  CI [{slo * 100:+.1f}, {shi * 100:+.1f}]  p={spp:.3f}")
    print(f"\n  corr(z, 3d excess) = {res['corrZ']:+.3f}   corr(spam, 3d excess) = {res['corrSpam']:+.3f}")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "threshold.json").write_text(json.dumps(res, indent=1))
    (OUT_DIR / "threshold.svg").write_text(render_chart(res))
    print("\nWrote out/threshold.json and out/threshold.svg")


if __name__ == "__main__":
    main()
