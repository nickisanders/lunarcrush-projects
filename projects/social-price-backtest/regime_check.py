#!/usr/bin/env python3
"""Does the signal survive a falling market?

Every result in this repo is pooled across 6.5 years, which covers a 2021
mania, a 2022 collapse and everything since. A fair objection is that the edge
might live entirely in the good times.

It does not. Split by what Bitcoin had done over the 30 days before each
signal, the gap over baseline is +8.3pp when Bitcoin was falling, +4.6pp when
flat and +8.6pp when rising. No regime reverses it.

State the significance carefully. Cut into thirds, no single regime clears its
own confidence interval (p = 0.05, 0.32 and 0.07 on roughly 130 events each).
That is what splitting a 402-event sample costs in power, not evidence of
three separate effects. The pooled result is what carries the claim: +7.1pp,
CI [+2.9, +11.5], p = 0.002. The regime split shows the effect does not
reverse anywhere, which is a weaker and more defensible statement.

The second finding was not what I expected. The setup fires MORE often in a
downturn: one signal per 836 coin-days while Bitcoin was falling, against one
per 1,403 while it was rising, a 1.7x difference. A plausible mechanism is
that the setup requires a flat price, and in a rally attention and price move
together so the flat-price condition filters most spikes out. In a downturn
attention can spike while price sits still.

Usage:
    python3 regime_check.py [--bootstrap 4000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import FLOOR, HORIZONS, RAW_DIR, add_signals, load_coin

OUT_DIR = Path(__file__).resolve().parent / "out"
TRAIL = 30
BAND = 0.05
REGIMES = [
    ("Bitcoin falling", lambda r: r < -BAND),
    ("Bitcoin flat", lambda r: r.between(-BAND, BAND)),
    ("Bitcoin rising", lambda r: r > BAND),
]


def build_panel() -> pd.DataFrame:
    frames = [add_signals(d) for p in sorted(RAW_DIR.glob("*.json")) if (d := load_coin(p)) is not None]
    a = pd.concat(frames)
    btc = a[a["symbol"] == "BTC"].copy()
    # The regime is what Bitcoin had already done, known on the signal day.
    btc["btc_trail30"] = btc["close"] / btc["close"].shift(TRAIL) - 1
    a = a.merge(btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
        columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}),
        left_index=True, right_index=True, how="left")
    a = a.merge(btc[["btc_trail30"]], left_index=True, right_index=True, how="left")
    e = a[(a["market_cap"] >= 50e6) & (a["volume_24h"].fillna(0) >= 1e6)
          & (a["med_interactions"] >= FLOOR) & a["z"].notna() & a["fwd_7d"].notna()
          & a["btc_trail30"].notna() & (a["symbol"] != "BTC")].copy()
    for h in HORIZONS:
        lo, hi = e[f"fwd_{h}d"].quantile([0.01, 0.99])
        e[f"fwd_{h}d"] = e[f"fwd_{h}d"].clip(lo, hi)
        e[f"adj_{h}d"] = e[f"fwd_{h}d"] - e[f"btc_{h}d"]
    return e


def block_bootstrap_gap(a: pd.DataFrame, b: pd.DataFrame, iters: int, seed: int = 7):
    ga = {k: (v["adj_3d"] > 0).astype(float).values for k, v in a.groupby(a.index.to_period("M"))}
    gb = {k: (v["adj_3d"] > 0).astype(float).values for k, v in b.groupby(b.index.to_period("M"))}
    blocks = sorted(set(ga) & set(gb))
    rng = np.random.default_rng(seed)
    draws = np.array([
        np.concatenate([ga[k] for k in pick]).mean() - np.concatenate([gb[k] for k in pick]).mean()
        for pick in (rng.choice(blocks, len(blocks), replace=True) for _ in range(iters))
    ])
    return ((a["adj_3d"] > 0).mean() - (b["adj_3d"] > 0).mean(),
            float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def render_chart(rows: list[dict], pooled: dict) -> str:
    W, H = 1300, 830
    BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
    GREEN, RED, GREY = "#3fb950", "#f85149", "#8b949e"
    TOP, CH, BW, GAP, X0 = 290, 290, 95, 30, 130
    top_val = 0.60

    def y(v: float) -> float:
        return TOP + CH - v / top_val * CH

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="76" font-size="38" font-weight="700" fill="{TEXT}">The signal does not need a bull market</text>',
         f'<text x="60" y="120" font-size="23" fill="{SUB}">how often a coin beat Bitcoin over 3 days, by what Bitcoin had done in the 30 days before the signal</text>',
         f'<text x="60" y="156" font-size="23" fill="{SUB}">grey is an ordinary coin-day in that same regime</text>']

    for tick in (0.2, 0.3, 0.4, 0.5, 0.6):
        p += [f'<line x1="{X0 - 40}" y1="{y(tick):.0f}" x2="{W - 330}" y2="{y(tick):.0f}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{X0 - 52}" y="{y(tick) + 7:.0f}" font-size="18" fill="{SUB}" text-anchor="end">{tick * 100:.0f}%</text>']

    for i, r in enumerate(rows):
        gx = X0 + i * (2 * BW + GAP + 60)
        for k, (rate, col) in enumerate([(r["baseline"], GREY), (r["spike"], GREEN)]):
            x = gx + k * (BW + GAP)
            p += [f'<rect x="{x}" y="{y(rate):.0f}" width="{BW}" height="{TOP + CH - y(rate):.0f}" rx="8" fill="{col}"/>',
                  f'<text x="{x + BW // 2}" y="{y(rate) - 14:.0f}" font-size="24" font-weight="700" fill="{col}" text-anchor="middle">{rate * 100:.0f}%</text>']
        p += [f'<text x="{gx + BW + GAP // 2}" y="{TOP + CH + 40}" font-size="22" fill="{TEXT}" text-anchor="middle">{r["label"]}</text>',
              f'<text x="{gx + BW + GAP // 2}" y="{TOP + CH + 68}" font-size="19" fill="{GREEN}" text-anchor="middle">+{r["gap"] * 100:.1f}pp</text>',
              f'<text x="{gx + BW + GAP // 2}" y="{TOP + CH + 94}" font-size="18" fill="{SUB}" text-anchor="middle">n={r["n"]} · p = {r["p"]:.2f}</text>']

    bx = W - 290
    p += [f'<rect x="{bx - 30}" y="{TOP - 30}" width="270" height="240" rx="14" fill="#21262d"/>',
          f'<text x="{bx}" y="{TOP + 10}" font-size="22" font-weight="700" fill="{TEXT}">And it fires more</text>',
          f'<text x="{bx}" y="{TOP + 40}" font-size="22" font-weight="700" fill="{TEXT}">often in a downturn</text>',
          f'<text x="{bx}" y="{TOP + 96}" font-size="20" fill="{SUB}">falling: 1 per {rows[0]["perSignal"]:,}</text>',
          f'<text x="{bx}" y="{TOP + 130}" font-size="20" fill="{SUB}">flat: 1 per {rows[1]["perSignal"]:,}</text>',
          f'<text x="{bx}" y="{TOP + 164}" font-size="20" fill="{SUB}">rising: 1 per {rows[2]["perSignal"]:,}</text>',
          f'<text x="{bx}" y="{TOP + 196}" font-size="19" fill="{GREEN}">coin-days scanned</text>']

    p += [f'<text x="60" y="{H - 128}" font-size="23" fill="{TEXT}">No regime reverses the edge. That is the claim, and it is weaker than it looks.</text>',
          f'<text x="60" y="{H - 96}" font-size="21" fill="{SUB}">Cut into thirds, no single regime clears its own interval. Splitting 402 events costs the power to do that. The pooled</text>',
          f'<text x="60" y="{H - 68}" font-size="21" fill="{SUB}">result is what carries it: +{pooled["gap"] * 100:.1f}pp, CI [{pooled["ci"][0] * 100:+.1f}, {pooled["ci"][1] * 100:+.1f}], p = {pooled["p"]:.3f} across all 402.</text>',
          f'<text x="60" y="{H - 36}" font-size="21" fill="{SUB}">What the split shows is the absence of a reversal, not three separate confirmations.</text>',
          f'<text x="60" y="{H - 12}" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · month-block bootstrap · method and code in the repo</text>',
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", type=int, default=4000)
    args = ap.parse_args()

    e = build_panel()
    sp = e[(e.z >= 3.0) & (e.spam_ratio.fillna(0) <= 0.5) & (e.ret_1d.abs() <= 0.02)]
    base = e[e.z < 3.0]
    print(f"{len(sp)} qualifying spikes across {len(e):,} eligible coin-days\n")
    print(f"{'regime':<18}{'n':>6}{'baseline':>11}{'spike':>9}{'gap':>9}{'p':>8}{'1 signal per':>15}")

    rows = []
    for label, test in REGIMES:
        s, b = sp[test(sp.btc_trail30)], base[test(base.btc_trail30)]
        gap, lo, hi, pv = block_bootstrap_gap(s, b, args.bootstrap)
        per = int(round((len(s) + len(b)) / max(len(s), 1)))
        rows.append({"label": label, "n": len(s), "baseline": float((b.adj_3d > 0).mean()),
                     "spike": float((s.adj_3d > 0).mean()), "gap": gap, "ci": [lo, hi],
                     "p": pv, "perSignal": per})
        print(f"{label:<18}{len(s):>6}{(b.adj_3d > 0).mean():>10.1%}{(s.adj_3d > 0).mean():>9.1%}"
              f"{gap * 100:>8.1f}pp{pv:>8.3f}{per:>13,} days")

    gap, lo, hi, pv = block_bootstrap_gap(sp, base, args.bootstrap)
    pooled = {"gap": gap, "ci": [lo, hi], "p": pv, "n": len(sp)}
    print(f"\n{'POOLED':<18}{len(sp):>6}{(base.adj_3d > 0).mean():>10.1%}{(sp.adj_3d > 0).mean():>9.1%}"
          f"{gap * 100:>8.1f}pp{pv:>8.3f}")
    print("\nNo regime clears its own interval; the pooled result carries the claim.")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "regime.json").write_text(json.dumps({"regimes": rows, "pooled": pooled}, indent=1))
    (OUT_DIR / "regime.svg").write_text(render_chart(rows, pooled))
    print("Wrote out/regime.json and out/regime.svg")


if __name__ == "__main__":
    main()
