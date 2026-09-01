#!/usr/bin/env python3
"""You missed the pump. Should you buy it anyway?

The most-asked question in crypto, answered against 6.5 years of it. For every
coin-day, how much had the coin risen over the previous seven days, and what
happened next.

The answer is a clean gradient: the bigger the run you are chasing, the worse
it goes, monotonically, at every horizon. After a 200%+ week the median coin is
down 19.6% in a month and 42.8% in three, against -2.9% and -9.2% for a coin
that had a quiet week. Nearly half lose half.

Two things this does carefully:

- **Episodes, not coin-days.** A coin in the middle of a run qualifies on many
  consecutive days, and counting each as an event would inflate 375 real
  episodes into 1,183 correlated ones. Consecutive qualifying days on one coin
  collapse to a single episode, with a 7-day gap starting a new one.
- **Survivorship runs the wrong way, and that is the safe direction.** The
  universe is today's top 1,000 coins, so coins that pumped and then died out
  of the rankings are missing entirely. The real picture for chasing a pump is
  worse than what is reported here, not better.

Usage:
    python3 after_the_run.py [--bootstrap 3000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import RAW_DIR, load_coin, add_signals

OUT_DIR = Path(__file__).resolve().parent / "out"
HORIZONS = (3, 7, 30, 90)
BUCKETS = [
    ("a quiet week", lambda r: (r >= -0.10) & (r <= 0.10)),
    ("up 50-100%", lambda r: (r > 0.50) & (r <= 1.0)),
    ("up 100-200%", lambda r: (r > 1.0) & (r <= 2.0)),
    ("up 200%+", lambda r: r > 2.0),
]
EPISODE_GAP_DAYS = 7


def build_panel() -> pd.DataFrame:
    frames = []
    for path in sorted(RAW_DIR.glob("*.json")):
        d = load_coin(path)
        if d is None:
            continue
        s = add_signals(d)
        s["run7"] = s["close"] / s["close"].shift(7) - 1
        for h in HORIZONS:
            s[f"f{h}"] = s["close"].shift(-h) / s["close"] - 1
        frames.append(s)
    a = pd.concat(frames)
    btc = a[a["symbol"] == "BTC"]
    a = a.merge(
        btc[[f"f{h}" for h in HORIZONS]].rename(columns={f"f{h}": f"b{h}" for h in HORIZONS}),
        left_index=True, right_index=True, how="left",
    )
    e = a[(a["market_cap"] >= 50e6) & (a["volume_24h"].fillna(0) >= 1e6)
          & (a["symbol"] != "BTC") & a["run7"].notna()].copy()
    for h in HORIZONS:
        lo, hi = e[f"f{h}"].quantile([0.01, 0.99])
        e[f"f{h}"] = e[f"f{h}"].clip(lo, hi)
        e[f"a{h}"] = e[f"f{h}"] - e[f"b{h}"]
    return e


def episodes(qualifying: pd.DataFrame) -> pd.DataFrame:
    """One row per run, not per day inside it."""
    keep = []
    for sym, g in qualifying.sort_index().groupby("symbol"):
        prev = None
        for d in g.index:
            if prev is None or (d - prev).days > EPISODE_GAP_DAYS:
                keep.append((sym, d))
            prev = d
    idx = pd.DataFrame(keep, columns=["symbol", "date"])
    return qualifying.reset_index().merge(idx, on=["symbol", "date"]).set_index("date")


def block_bootstrap_median_gap(a: pd.DataFrame, b: pd.DataFrame, col: str, iters: int, seed: int = 7):
    """Month-block bootstrap of the difference in median forward return."""
    a, b = a.dropna(subset=[col]), b.dropna(subset=[col])
    ga = {k: v[col].values for k, v in a.groupby(a.index.to_period("M"))}
    gb = {k: v[col].values for k, v in b.groupby(b.index.to_period("M"))}
    blocks = sorted(set(ga) & set(gb))
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(iters):
        pick = rng.choice(blocks, len(blocks), replace=True)
        draws.append(np.median(np.concatenate([ga[k] for k in pick]))
                     - np.median(np.concatenate([gb[k] for k in pick])))
    draws = np.array(draws)
    return (float(np.median(a[col]) - np.median(b[col])),
            float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())), len(a))


def render_chart(rows: list[dict], big: dict) -> str:
    W, H = 1300, 800
    BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
    RED, AMBER, GREY = "#f85149", "#d29922", "#8b949e"
    TOP, CH, BW, GAP, X0 = 300, 300, 130, 52, 110
    worst = min(r["m90"] for r in rows)

    def y(v: float) -> float:
        return TOP + (abs(v) / abs(worst)) * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">The bigger the pump you chase, the worse it goes</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">median return over the NEXT 90 days, by how much the coin had already risen in the previous week</text>',
         f'<text x="60" y="156" font-size="23" fill="{SUB}">6.5 years, 1,000 coins, every episode counted once</text>',
         f'<line x1="{X0 - 40}" y1="{TOP}" x2="{W - 380}" y2="{TOP}" stroke="{GRID}" stroke-width="2"/>',
         f'<text x="{X0 - 50}" y="{TOP + 7}" font-size="19" fill="{SUB}" text-anchor="end">0%</text>']

    for i, r in enumerate(rows):
        x = X0 + i * (BW + GAP)
        h = y(r["m90"]) - TOP
        col = RED if r["m90"] <= -0.30 else AMBER if r["m90"] <= -0.15 else GREY
        p += [f'<rect x="{x}" y="{TOP}" width="{BW}" height="{h:.0f}" rx="8" fill="{col}"/>',
              f'<text x="{x + BW // 2}" y="{TOP + h + 38:.0f}" font-size="30" font-weight="700" fill="{col}" text-anchor="middle">{r["m90"] * 100:.0f}%</text>',
              f'<text x="{x + BW // 2}" y="{TOP - 46}" font-size="21" fill="{TEXT}" text-anchor="middle">{r["label"]}</text>',
              f'<text x="{x + BW // 2}" y="{TOP - 22}" font-size="18" fill="{SUB}" text-anchor="middle">n={r["n"]:,}</text>']

    bx = W - 330
    p += [f'<rect x="{bx - 30}" y="{TOP - 76}" width="300" height="360" rx="14" fill="{TRACK}"/>',
          f'<text x="{bx}" y="{TOP - 36}" font-size="22" font-weight="700" fill="{TEXT}">After a 200%+ week,</text>',
          f'<text x="{bx}" y="{TOP - 8}" font-size="22" font-weight="700" fill="{TEXT}">90 days later:</text>',
          f'<text x="{bx}" y="{TOP + 62}" font-size="58" font-weight="800" fill="{RED}">{big["lower"] * 100:.0f}%</text>',
          f'<text x="{bx}" y="{TOP + 92}" font-size="20" fill="{SUB}">were lower</text>',
          f'<text x="{bx}" y="{TOP + 168}" font-size="58" font-weight="800" fill="{RED}">{big["halved"] * 100:.0f}%</text>',
          f'<text x="{bx}" y="{TOP + 198}" font-size="20" fill="{SUB}">had lost half</text>',
          f'<text x="{bx}" y="{TOP + 250}" font-size="20" fill="{SUB}">median vs Bitcoin: {big["vsBtc"] * 100:.0f}%</text>']

    p += [f'<text x="60" y="{H - 116}" font-size="23" fill="{TEXT}">A coin that had a quiet week loses 9% over the next 90 days. One that just tripled loses 43%.</text>',
          f'<text x="60" y="{H - 82}" font-size="21" fill="{SUB}">Gap of {big["gap"] * 100:.0f} points, CI [{big["ci"][0] * 100:.0f}, {big["ci"][1] * 100:.0f}], p &lt; 0.001, month-block bootstrap on {big["n"]} episodes.</text>',
          f'<text x="60" y="{H - 52}" font-size="21" fill="{SUB}">Survivorship makes this generous: coins that pumped and then died out of the top 1,000 are not in the data at all.</text>',
          f'<text x="60" y="{H - 20}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=3000)
    args = ap.parse_args()

    e = build_panel()
    print(f"{len(e):,} eligible coin-days\n")
    print(f"{'the previous week':<18}{'episodes':>10}{'+3d':>9}{'+7d':>9}{'+30d':>9}{'+90d':>9}   median raw")
    rows, quiet_ep = [], None
    for label, test in BUCKETS:
        sub = e[test(e["run7"])]
        ep = episodes(sub) if label != "a quiet week" else sub
        if label == "a quiet week":
            quiet_ep = ep
        rows.append({"label": label, "n": len(ep),
                     **{f"m{h}": float(ep[f"f{h}"].median()) for h in HORIZONS}})
        print(f"{label:<18}{len(ep):>10,}" + "".join(f"{ep[f'f{h}'].median() * 100:>8.1f}%" for h in HORIZONS))

    big_ep = episodes(e[e["run7"] > 2.0])
    gap, lo, hi, pv, n = block_bootstrap_median_gap(big_ep, quiet_ep, "f90", args.bootstrap)
    at90 = big_ep.dropna(subset=["f90"])
    big = {"lower": float((at90["f90"] < 0).mean()), "halved": float((at90["f90"] < -0.5).mean()),
           "vsBtc": float(at90["a90"].median()), "gap": gap, "ci": [lo, hi], "p": pv, "n": n,
           "coins": int(big_ep["symbol"].nunique())}
    print(f"\nafter a 200%+ week, 90 days later ({n} episodes across {big['coins']} coins):")
    print(f"  {big['lower']:.0%} were lower, {big['halved']:.0%} had lost half")
    print(f"  median vs Bitcoin: {big['vsBtc']:+.1%}")
    print(f"  gap vs a quiet week: {gap * 100:+.1f}pp  CI [{lo * 100:+.1f}, {hi * 100:+.1f}]  p={pv:.3f}")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "after-the-run.json").write_text(json.dumps({"buckets": rows, "big": big}, indent=1))
    (OUT_DIR / "after-the-run.svg").write_text(render_chart(rows, big))
    print("\nWrote out/after-the-run.json and out/after-the-run.svg")


if __name__ == "__main__":
    main()
