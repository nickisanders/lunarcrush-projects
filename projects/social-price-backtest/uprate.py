#!/usr/bin/env python3
"""Is the organic-spike signal directional, or only relative to Bitcoin?

The headline result is a BTC-adjusted hit rate: organic spikes beat Bitcoin
over the next 3 days 49.0% of the time against a 41.9% baseline. That is a
statement about relative strength, and it is easy for a reader (or the person
writing the post) to hear it as "the price goes up."

Those are different claims and they need separate tests. This script runs the
same events through the same cluster bootstrap, but scores each one on whether
the price simply rose, with no Bitcoin subtracted. If the setup is directional,
the up-rate gap should look like the beats-BTC gap. If it is purely relative,
the up-rate gap should collapse toward zero.

It collapses. Reporting the beats-BTC number without this one invites the
directional reading, so this check exists to keep the claim honest.

Usage:
    python3 uprate.py [--bootstrap 2000] [--z 3.0] [--flat 0.02] [--spam-split 0.5]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import FLOOR, HORIZONS, RAW_DIR, add_signals, load_coin

OUT_DIR = Path(__file__).resolve().parent / "out"
QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]


# --- chart ---------------------------------------------------------------
# Same visual grammar as out/crypto-vs-stocks.svg: effect sizes as 95%
# confidence intervals against a dashed "no effect" line. The whole point of
# the finding is that one interval clears zero and the other straddles it,
# which is a thing you can see rather than a thing you have to be told.

W, H = 1200, 700
PLOT_X0, PLOT_X1 = 340, 1140
DOMAIN = (-5.0, 12.5)
BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
GREEN, GREY = "#3fb950", "#6e7681"


def _x(pts: float) -> float:
    lo, hi = DOMAIN
    return PLOT_X0 + (pts - lo) / (hi - lo) * (PLOT_X1 - PLOT_X0)


def render_chart(boot: pd.DataFrame, n_organic: int, horizon: str = "+3d") -> str:
    """Effect-size chart for the two competing readings of the same events."""
    rows = []
    for metric, label, note, color in [
        ("beats_btc_rate", "Beats Bitcoin", "49.0% vs 41.8%", GREEN),
        ("up_rate", "Price simply rose", "47.8% vs 46.3%", GREY),
    ]:
        r = boot[(boot["horizon"] == horizon) & (boot["metric"] == metric)].iloc[0]
        rows.append((label, note, color, r["diff"] * 100, r["ci_lo"] * 100, r["ci_hi"] * 100, r["p_two_sided"]))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<text x="70" y="62" font-size="36" font-weight="700" fill="{TEXT}">The same {n_organic} events, scored two ways</text>',
        f'<text x="70" y="102" font-size="24" fill="{SUB}">how much an organic attention spike shifts the odds over the next 3 days</text>',
        f'<line x1="{_x(0):.0f}" y1="180" x2="{_x(0):.0f}" y2="520" stroke="{GRID}" stroke-width="2" stroke-dasharray="7 7"/>',
        f'<text x="{_x(0):.0f}" y="168" font-size="20" fill="{SUB}" text-anchor="middle">no effect</text>',
    ]
    for i, (label, note, color, diff, lo, hi, p) in enumerate(rows):
        y = 250 + i * 170
        out += [
            f'<text x="70" y="{y + 6}" font-size="32" font-weight="700" fill="{TEXT}">{label}</text>',
            f'<text x="70" y="{y + 40}" font-size="20" fill="{SUB}">{note}</text>',
            f'<line x1="{_x(lo):.0f}" y1="{y}" x2="{_x(hi):.0f}" y2="{y}" stroke="{color}" '
            f'stroke-width="7" stroke-linecap="round" opacity="0.45"/>',
            f'<circle cx="{_x(diff):.0f}" cy="{y}" r="15" fill="{color}"/>',
            f'<text x="{_x(diff):.0f}" y="{y - 34}" font-size="30" font-weight="700" fill="{color}" '
            f'text-anchor="middle">{diff:+.1f}</text>',
            f'<text x="{_x(hi):.0f}" y="{y + 46}" font-size="20" fill="{SUB}" text-anchor="middle">p = {p:.3f}</text>',
        ]
    for tick in (-5, 0, 5, 10):
        out.append(
            f'<text x="{_x(tick):.0f}" y="560" font-size="20" fill="{SUB}" text-anchor="middle">{tick:+d} pts</text>'
        )
    out += [
        f'<text x="70" y="616" font-size="23" fill="{TEXT}">An organic spike stops a coin bleeding against Bitcoin. It does not make the price rise.</text>',
        f'<text x="70" y="650" font-size="21" fill="{SUB}">Bars are 95% confidence intervals from the same month-block bootstrap draws.</text>',
        f'<text x="70" y="680" font-size="19" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
        "</svg>",
    ]
    return "\n".join(out)


def block_bootstrap_rates(
    df: pd.DataFrame, target: str, baseline: str, cols: dict[str, str], iters: int, seed: int = 7
) -> dict[str, tuple[float, float, float, float]]:
    """Cluster bootstrap (calendar-month blocks) of target-minus-baseline
    differences in the share of events where each column is positive.

    Blocks are resampled once and reused for every column, so the up-rate and
    beats-BTC gaps come from the same draws and are directly comparable.
    Returns {label: (observed diff, ci_lo, ci_hi, p_two_sided)}.
    """
    sub = df[df["grp"].isin([target, baseline])].copy()
    sub["block"] = sub.index.to_period("M")

    aggs = {}
    for label, col in cols.items():
        sub[f"pos_{label}"] = (sub[col] > 0).astype(float)
        aggs[f"p_{label}"] = (f"pos_{label}", "sum")
        aggs[f"n_{label}"] = (f"pos_{label}", "count")
    blocks = sub.groupby(["block", "grp"]).agg(**aggs).unstack("grp").fillna(0.0)
    arr = blocks.to_numpy()
    idx = {name: i for i, name in enumerate(blocks.columns)}

    def diffs(sample: np.ndarray) -> dict[str, float]:
        out = {}
        for label in cols:
            rates = {}
            for grp in (target, baseline):
                n = sample[:, idx[(f"n_{label}", grp)]].sum()
                rates[grp] = sample[:, idx[(f"p_{label}", grp)]].sum() / n if n else np.nan
            out[label] = rates[target] - rates[baseline]
        return out

    observed = diffs(arr)
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {label: [] for label in cols}
    for _ in range(iters):
        for label, v in diffs(arr[rng.integers(0, len(arr), len(arr))]).items():
            draws[label].append(v)

    result = {}
    for label, d in draws.items():
        d = np.array(d)
        result[label] = (
            observed[label],
            float(np.percentile(d, 2.5)),
            float(np.percentile(d, 97.5)),
            float(2 * min((d <= 0).mean(), (d >= 0).mean())),
        )
    return result


def build_eligible(args: argparse.Namespace) -> pd.DataFrame:
    """Same universe, winsorization and grouping as analysis.py, so the event
    set here is identical to the one behind the headline number."""
    frames = []
    files = sorted(RAW_DIR.glob("*.json"))
    print(f"Loading {len(files)} coins...")
    for p in files:
        df = load_coin(p)
        if df is not None:
            frames.append(add_signals(df))
    all_days = pd.concat(frames)

    btc = all_days[all_days["symbol"] == "BTC"]
    if btc.empty:
        raise SystemExit("BTC missing from raw data; cannot compute adjusted returns")
    all_days = all_days.merge(
        btc[[f"fwd_{h}d" for h in HORIZONS]].rename(
            columns={f"fwd_{h}d": f"btc_{h}d" for h in HORIZONS}
        ),
        left_index=True,
        right_index=True,
        how="left",
    )

    eligible = all_days[
        (all_days["market_cap"] >= args.mcap)
        & (all_days["volume_24h"].fillna(0) >= args.min_volume)
        & (all_days["med_interactions"] >= FLOOR)
        & all_days["z"].notna()
        & all_days["fwd_7d"].notna()
        & (all_days["symbol"] != "BTC")
    ].copy()
    for h in HORIZONS:
        lo, hi = eligible[f"fwd_{h}d"].quantile([0.01, 0.99])
        eligible[f"fwd_{h}d"] = eligible[f"fwd_{h}d"].clip(lo, hi)
        eligible[f"adj_{h}d"] = eligible[f"fwd_{h}d"] - eligible[f"btc_{h}d"]

    spike = (eligible["z"] >= args.z) & (eligible["ret_1d"].abs() <= args.flat)
    organic = spike & (eligible["spam_ratio"].fillna(0) <= args.spam_split)
    eligible["grp"] = np.select(
        [organic, spike & ~organic], ["organic spike", "spam spike"], default="baseline"
    )
    return eligible


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--spam-split", type=float, default=0.5)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    eligible = build_eligible(args)
    counts = eligible["grp"].value_counts()
    print(
        f"eligible coin-days: {len(eligible):,} | organic spikes: "
        f"{counts.get('organic spike', 0):,} | spam spikes: {counts.get('spam spike', 0):,}\n"
    )

    rows = []
    for h in HORIZONS:
        for name, g in eligible.groupby("grp"):
            rows.append(
                {
                    "horizon": f"+{h}d",
                    "group": name,
                    "n": len(g),
                    "up_rate": (g[f"fwd_{h}d"] > 0).mean(),
                    "beats_btc_rate": (g[f"adj_{h}d"] > 0).mean(),
                    "median_raw": g[f"fwd_{h}d"].median(),
                    "mean_raw": g[f"fwd_{h}d"].mean(),
                }
            )
    table = pd.DataFrame(rows)

    print(f"{'horizon':<9}{'group':<15}{'n':>9}{'up-rate':>10}{'beats BTC':>11}{'median':>9}")
    for _, r in table.iterrows():
        print(
            f"{r['horizon']:<9}{r['group']:<15}{r['n']:>9,}{r['up_rate']:>9.1%}"
            f"{r['beats_btc_rate']:>11.1%}{r['median_raw']:>9.2%}"
        )

    print(f"\nCluster bootstrap ({args.bootstrap} iters, calendar-month blocks),")
    print("organic spike minus baseline. Both metrics share the same draws.\n")
    boot_rows = []
    for h in HORIZONS:
        res = block_bootstrap_rates(
            eligible,
            "organic spike",
            "baseline",
            {"up_rate": f"fwd_{h}d", "beats_btc_rate": f"adj_{h}d"},
            args.bootstrap,
        )
        for metric, (diff, lo, hi, p) in res.items():
            boot_rows.append(
                {
                    "horizon": f"+{h}d",
                    "metric": metric,
                    "diff": diff,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "p_two_sided": p,
                }
            )
            print(
                f"  +{h}d {metric:<15} {diff:+6.1%}  CI [{lo:+.1%}, {hi:+.1%}]  p={p:.3f}"
            )

    org = eligible[eligible["grp"] == "organic spike"]
    print("\norganic spike, +3d raw return distribution:")
    for q in QUANTILES:
        print(f"  p{int(q * 100):<3} {org['fwd_3d'].quantile(q):>8.1%}")

    OUT_DIR.mkdir(exist_ok=True)
    table.to_csv(OUT_DIR / "uprate.csv", index=False)
    boot = pd.DataFrame(boot_rows)
    boot.to_csv(OUT_DIR / "uprate-bootstrap.csv", index=False)
    (OUT_DIR / "uprate-chart.svg").write_text(render_chart(boot, len(org)))
    print("\nWrote out/uprate.csv, out/uprate-bootstrap.csv and out/uprate-chart.svg")
    print(
        "Rasterize with sharp:\n"
        '  node -e "require(\'../hype-detector/node_modules/sharp\')'
        "('out/uprate-chart.svg',{density:144}).png().toFile('out/uprate-chart.png')\""
    )


if __name__ == "__main__":
    main()
