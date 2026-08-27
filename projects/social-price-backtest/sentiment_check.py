#!/usr/bin/env python3
"""Does crypto sentiment ever say anything other than "bullish"?

Sentiment is the most quoted number in crypto social data and the least
examined. Two questions, both answerable from the backtest cache:

1. What does it actually read? Across 449,640 coin-days it is net positive
   97.6% of the time, with a median of 86 out of 100. The monthly median has
   never left the 77-94 band in six and a half years, and it did not leave it
   during the COVID crash, the LUNA collapse or the failure of FTX.

2. Does it predict anything? No. Sorted into quintiles, the beats-BTC rate
   over the next 3 days runs 41.0% to 42.4%, a gap of 1.4 points that does not
   clear its own confidence interval. Correlation with forward BTC-adjusted
   return is +0.005.

An indicator that reads the same in a bull market and a bankruptcy is not
measuring the market. It is measuring the fact that people who post about a
coin tend to like it.

Usage:
    python3 sentiment_check.py [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import RAW_DIR, load_coin
from uprate import build_eligible

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
MIN_MONTH_DAYS = 200

# Events worth marking on the timeline, because they are the strongest possible
# test of whether the indicator responds to anything at all.
EVENTS = [
    ("2020-03", "COVID crash"),
    ("2022-05", "LUNA collapse"),
    ("2022-11", "FTX collapse"),
]


def block_bootstrap(hi: pd.DataFrame, lo: pd.DataFrame, iters: int, seed: int = 7):
    """Month-block bootstrap of the top-minus-bottom quintile gap in hit rate."""
    def blocks(df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        d["blk"] = d.index.to_period("M")
        return d.groupby("blk").agg(p=("adj_3d", lambda x: (x > 0).sum()), n=("adj_3d", "count"))

    j = blocks(hi).join(blocks(lo), rsuffix="_l", how="inner").to_numpy()
    rng = np.random.default_rng(seed)
    draws = np.array([
        (lambda k: k[:, 0].sum() / k[:, 1].sum() - k[:, 2].sum() / k[:, 3].sum())(
            j[rng.integers(0, len(j), len(j))]
        )
        for _ in range(iters)
    ])
    observed = (hi["adj_3d"] > 0).mean() - (lo["adj_3d"] > 0).mean()
    return (observed, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def euphoria_test(e: pd.DataFrame) -> dict:
    """Does a high-sentiment month precede a bad one? ("Everyone was bullish
    right before the rug.")

    The anecdote has something to it: three of the five worst months in the
    data followed a month whose sentiment sat at the 71st percentile. The
    systematic version does not survive. High-sentiment months are followed by
    a losing month LESS often than low-sentiment ones, which is the opposite of
    the folk theory, and the correlation with next month's return is +0.14.

    Both readings are consistent with the simpler explanation: sentiment is
    high before crashes because sentiment is high before everything.
    """
    m = e.groupby("ym").agg(sent=("sentiment", "median"), ret=("ret_1d", "median"),
                            n=("sentiment", "size"))
    m = m[m.n >= MIN_MONTH_DAYS].copy()
    m["next_ret"] = m["ret"].shift(-1)
    m = m.dropna(subset=["next_ret"])
    hi = m[m.sent >= m.sent.quantile(0.75)]
    lo = m[m.sent <= m.sent.quantile(0.25)]
    return {
        "months": len(m),
        "corrNextMonth": float(np.corrcoef(m.sent, m.next_ret)[0, 1]),
        "highThenNegative": float((hi.next_ret < 0).mean()),
        "lowThenNegative": float((lo.next_ret < 0).mean()),
        "baseRateNegative": float((m.next_ret < 0).mean()),
        "nHigh": len(hi), "nLow": len(lo),
    }


def render_chart(monthly: pd.DataFrame, stats: dict) -> str:
    """Bitcoin's price above, sentiment below, on a shared timeline.

    The point is the contrast between the two shapes, so they share an x-axis
    and the sentiment panel keeps a full 0-100 y-range. Rescaling it to its own
    77-94 band would manufacture drama the data does not contain.
    """
    W, H = 1300, 1040
    L, R = 110, 60
    PW = W - L - R
    TOP_Y, TOP_H = 236, 270
    BOT_Y, BOT_H = 640, 200
    BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
    ORANGE, GREEN, RED = "#f7931a", "#3fb950", "#f85149"

    n = len(monthly)
    def x(i: float) -> float:
        return L + (i / max(n - 1, 1)) * PW
    prices = monthly["btc"].to_numpy()
    lo_p, hi_p = np.log10(prices.min()), np.log10(prices.max())
    def yp(v: float) -> float:
        return TOP_Y + TOP_H - (np.log10(v) - lo_p) / (hi_p - lo_p) * TOP_H
    def ys(v: float) -> float:
        return BOT_Y + BOT_H - (v / 100) * BOT_H

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family=\"system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif\">",
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="60" y="72" font-size="36" font-weight="700" fill="{TEXT}">Crypto sentiment has said the same thing for six years</text>',
         f'<text x="60" y="114" font-size="23" fill="{SUB}">Bitcoin above, the median sentiment score across every major coin below, same months</text>',
         f'<text x="60" y="150" font-size="23" fill="{SUB}">sentiment is shown on its full 0-100 range, because that is the range it claims to use</text>']

    months = list(monthly.index.astype(str))
    # Event rules first, so both series draw over them.
    for k, (period, label) in enumerate(EVENTS):
        if period not in months:
            continue
        i = months.index(period)
        # Stagger consecutive labels: LUNA and FTX are six months apart and
        # their captions are wider than the gap between them.
        ly = 200 - (k % 2) * 32
        p += [
            f'<line x1="{x(i):.0f}" y1="{ly + 10}" x2="{x(i):.0f}" y2="{BOT_Y + BOT_H}" stroke="{RED}" stroke-width="2" stroke-dasharray="5 6" opacity="0.7"/>',
            f'<text x="{x(i):.0f}" y="{ly}" font-size="19" fill="{RED}" text-anchor="middle">{label}</text>',
        ]

    pts = " ".join(f"{x(i):.1f},{yp(v):.1f}" for i, v in enumerate(prices))
    p += [f'<polyline points="{pts}" fill="none" stroke="{ORANGE}" stroke-width="3"/>',
          f'<text x="{L}" y="{TOP_Y + 26}" font-size="21" fill="{ORANGE}" font-weight="700">Bitcoin price (log)</text>']

    for v in (0, 50, 100):
        p += [f'<line x1="{L}" y1="{ys(v):.0f}" x2="{L + PW}" y2="{ys(v):.0f}" stroke="{GRID}" stroke-width="1"/>',
              f'<text x="{L - 14}" y="{ys(v) + 7:.0f}" font-size="19" fill="{SUB}" text-anchor="end">{v}</text>']
    p.append(f'<text x="{L - 14}" y="{ys(50) - 12:.0f}" font-size="17" fill="{SUB}" text-anchor="end">neutral</text>')
    spts = " ".join(f"{x(i):.1f},{ys(v):.1f}" for i, v in enumerate(monthly["sentiment"]))
    p += [f'<polyline points="{spts}" fill="none" stroke="{GREEN}" stroke-width="3"/>',
          f'<text x="{L + PW}" y="{BOT_Y - 14}" font-size="21" fill="{GREEN}" font-weight="700" text-anchor="end">Sentiment, 0 to 100</text>']

    # Event readings sit BELOW the line: above it they collide with the 100 rule.
    for period, label in EVENTS:
        if period not in months:
            continue
        i = months.index(period)
        v = monthly["sentiment"].iloc[i]
        p.append(f'<text x="{x(i):.0f}" y="{ys(v) + 34:.0f}" font-size="22" font-weight="700" fill="{RED}" text-anchor="middle">{v:.0f}</text>')

    for i, period in enumerate(months):
        if period.endswith("-01"):
            p.append(f'<text x="{x(i):.0f}" y="{BOT_Y + BOT_H + 36}" font-size="19" fill="{SUB}" text-anchor="middle">{period[:4]}</text>')

    p += [
        f'<text x="60" y="{H - 100}" font-size="23" fill="{TEXT}">Net positive on {stats["shareAbove50"]*100:.1f}% of all {stats["coinDays"]:,} coin-days. The monthly median has never left the {stats["monthlyMin"]:.0f} to {stats["monthlyMax"]:.0f} band.</text>',
        f'<text x="60" y="{H - 66}" font-size="21" fill="{SUB}">It also predicts nothing: sorted into quintiles, the 3-day beats-BTC rate runs {stats["lowestRate"]*100:.1f}% to {stats["highestRate"]*100:.1f}% (gap p = {stats["p"]:.2f}).</text>',
        f'<text x="60" y="{H - 36}" font-size="21" fill="{SUB}">An indicator that reads 86 during a bankruptcy is measuring who posts about a coin, not what the market thinks of it.</text>',
        f'<text x="60" y="{H - 10}" font-size="18" fill="{SUB}">Data: LunarCrush · 2020 to 2026 · method and code in the repo</text>',
        "</svg>",
    ]
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

    e = build_eligible(args).dropna(subset=["sentiment", "adj_3d"]).copy()
    s = e["sentiment"]
    print(f"{len(e):,} coin-days\n")
    print("what sentiment reads:")
    for q in (5, 25, 50, 75, 95):
        print(f"  p{q:<3} {np.percentile(s, q):.0f}")
    for t in (50, 70, 85):
        print(f"  share of coin-days above {t}: {(s > t).mean():.1%}")

    e["ym"] = e.index.to_period("M")
    monthly = e.groupby("ym").agg(sentiment=("sentiment", "median"), n=("sentiment", "size"))
    monthly = monthly[monthly.n >= MIN_MONTH_DAYS]
    # BTC's own price is excluded from `eligible` (it is the benchmark), so
    # load it separately for the timeline.
    btc_monthly = None
    for path in sorted(RAW_DIR.glob("*.json")):
        # Read the header only; loading all 1,000 coins again to find one is
        # wasteful and some frames come back empty after cleaning.
        if json.loads(path.read_text())["coin"]["symbol"] != "BTC":
            continue
        df = load_coin(path)
        if df is None or df.empty:
            break
        btc_monthly = df.groupby(df.index.to_period("M"))["close"].last()
        break
    if btc_monthly is None:
        raise SystemExit("BTC not found in the raw cache")
    monthly = monthly.join(btc_monthly.rename("btc"), how="inner").dropna()

    print(f"\nmonthly median sentiment across {len(monthly)} months: "
          f"{monthly.sentiment.min():.0f} to {monthly.sentiment.max():.0f}")
    print("\nduring the worst events in the data:")
    for period, label in EVENTS:
        if period in monthly.index.astype(str).tolist():
            row = monthly.loc[pd.Period(period)]
            print(f"  {label:<16} {period}: sentiment {row.sentiment:.0f}")

    e["q"] = pd.qcut(s.rank(method="first"), 5, labels=["lowest", "2", "3", "4", "highest"])
    print(f"\n{'quintile':<12}{'n':>9}{'range':>12}{'+3d beats BTC':>16}")
    rates = {}
    for q, g in e.groupby("q", observed=True):
        rate = (g["adj_3d"] > 0).mean()
        rates[str(q)] = rate
        print(f"{str(q):<12}{len(g):>9,}{f'{g.sentiment.min():.0f}-{g.sentiment.max():.0f}':>12}{rate:>15.1%}")
    diff, lo, hi, pv = block_bootstrap(e[e.q == "highest"], e[e.q == "lowest"], args.bootstrap)
    print(f"\nhighest minus lowest: {diff:+.1%}  CI [{lo:+.1%}, {hi:+.1%}]  p={pv:.3f}")
    print(f"corr(sentiment, +3d BTC-adjusted return) = {np.corrcoef(s, e['adj_3d'])[0, 1]:+.3f}")

    euphoria = euphoria_test(e)
    print("\n\"everyone was bullish right before the rug\" - tested:")
    print(f"  high-sentiment months followed by a losing month: {euphoria['highThenNegative']:.0%} (n={euphoria['nHigh']})")
    print(f"  low-sentiment  months followed by a losing month: {euphoria['lowThenNegative']:.0%} (n={euphoria['nLow']})")
    print(f"  base rate across all {euphoria['months']} months: {euphoria['baseRateNegative']:.0%}")
    print(f"  corr(this month's sentiment, next month's return) = {euphoria['corrNextMonth']:+.2f}")
    print("  so the folk theory runs backwards here, on a small sample. Sentiment is")
    print("  high before crashes because it is high before everything.")

    stats = {
        "coinDays": len(e), "euphoria": euphoria, "shareAbove50": float((s > 50).mean()),
        "median": float(s.median()), "monthlyMin": float(monthly.sentiment.min()),
        "monthlyMax": float(monthly.sentiment.max()),
        "lowestRate": rates["lowest"], "highestRate": rates["highest"],
        "gap": diff, "ci": [lo, hi], "p": pv,
    }
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "sentiment.json").write_text(json.dumps({"stats": stats,
        "monthly": {str(k): float(v) for k, v in monthly.sentiment.items()}}, indent=1))
    (OUT_DIR / "sentiment-chart.svg").write_text(render_chart(monthly, stats))
    print("\nWrote out/sentiment.json and out/sentiment-chart.svg")


if __name__ == "__main__":
    main()
