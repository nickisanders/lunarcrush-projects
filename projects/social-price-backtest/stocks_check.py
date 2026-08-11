#!/usr/bin/env python3
"""Out-of-sample test: does the organic-spike setup work on stocks?

The crypto backtest found that organic attention spikes on flat-price days
beat BTC over the next 3 days 49.0% of the time versus 41.9% for an ordinary
coin-day. Equities are a genuinely independent test: different participants,
different market structure, different data.

Three things differ from the crypto version and are handled explicitly:

  Weekends. Stock prices carry forward Sat/Sun, so those days show a 0% move
  and would sail through a "price is flat" filter for free. Weekdays only.

  Spam denominator. The stocks feed has no posts_created, so the spam share is
  computed against posts_active. That is a different denominator than crypto's,
  so the threshold is not strictly comparable; it is internally consistent.

  Benchmark. There is no BTC. Excess return is measured against the
  equal-weighted mean forward return of all eligible stocks that day.

Usage:
    python3 stocks_check.py [--min-interactions 500] [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "stocks"
TRAILING = 30
HORIZON = 3
NUMERIC = ["time", "close", "interactions", "market_cap", "spam", "posts_active"]


def load_stock(path: Path) -> pd.DataFrame | None:
    blob = json.loads(path.read_text())
    rows = blob.get("rows") or []
    if len(rows) < TRAILING + HORIZON + 20:
        return None
    df = pd.DataFrame(rows)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
    df = df.dropna(subset=["time", "interactions", "close"])
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
    # Trading days only: weekend rows carry the Friday close, so a weekend
    # would register as a free "flat price" day and manufacture fake events.
    df = df[df["date"].dt.dayofweek < 5]
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if len(df) < TRAILING + HORIZON + 10:
        return None
    df["symbol"] = blob["stock"]["symbol"]
    return df


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    li = np.log1p(df["interactions"])
    roll = li.shift(1).rolling(TRAILING)
    df["z"] = (li - roll.mean()) / roll.std()
    df["med_interactions"] = df["interactions"].shift(1).rolling(TRAILING).median()
    df["ret_1d"] = df["close"].pct_change()
    df["fwd"] = df["close"].shift(-HORIZON) / df["close"] - 1.0
    df["spam_ratio"] = (df["spam"] / df["posts_active"].clip(lower=1)).clip(0, 1)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-interactions", type=float, default=500)
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--flat", type=float, default=0.02)
    ap.add_argument("--spam-max", type=float, default=0.5)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        df = load_stock(p)
        if df is not None:
            frames.append(add_signals(df))
    if not frames:
        raise SystemExit("No usable stock history. Run pull_stocks.py first.")
    panel = pd.concat(frames, ignore_index=True)
    print(f"panel: {len(panel):,} stock-days, {panel['symbol'].nunique()} stocks, "
          f"{panel['date'].min().date()} to {panel['date'].max().date()}")

    eligible = panel[
        (panel["med_interactions"] >= args.min_interactions)
        & panel["z"].notna()
        & panel["fwd"].notna()
    ].copy()
    lo, hi = eligible["fwd"].quantile([0.01, 0.99])
    eligible["fwd"] = eligible["fwd"].clip(lo, hi)

    # Benchmark: the average eligible stock that day.
    market = eligible.groupby("date")["fwd"].transform("mean")
    eligible["adj"] = eligible["fwd"] - market

    has_spam = eligible["spam_ratio"].notna()
    print(f"eligible stock-days: {len(eligible):,} ({has_spam.mean():.0%} have spam data)")

    spike = (eligible["z"] >= args.z) & (eligible["ret_1d"].abs() <= args.flat)
    organic = spike & has_spam & (eligible["spam_ratio"] <= args.spam_max)
    spammy = spike & has_spam & (eligible["spam_ratio"] > args.spam_max)

    baseline = eligible[~spike]
    events = eligible[organic]
    spam_events = eligible[spammy]

    print(f"\n{'group':28} {'n':>6} {'hit rate':>9} {'median excess':>14}")
    for label, g in [
        ("ordinary stock-day", baseline),
        ("organic attention spike", events),
        ("spam-heavy spike", spam_events),
    ]:
        if len(g) == 0:
            print(f"{label:28} {0:>6}")
            continue
        print(f"{label:28} {len(g):>6} {(g['adj'] > 0).mean():>9.3f} {g['adj'].median():>+14.2%}")

    # The interesting question the large-cap-only universe cannot answer: does
    # the effect appear in the retail-driven corner of equities, where there is
    # little analyst coverage and attention may actually lead price the way it
    # does in crypto?
    labelled = pd.concat([events.assign(grp="event"), baseline.assign(grp="base")])
    labelled = labelled[labelled["market_cap"].notna() & (labelled["market_cap"] > 0)]
    if len(labelled) > 1000:
        bands = [(0, 2e9, "small (<$2B)"), (2e9, 10e9, "mid ($2-10B)"),
                 (10e9, 100e9, "large ($10-100B)"), (100e9, np.inf, "mega (>$100B)")]
        print(f"\n{'market cap band':22} {'events':>7} {'event hit':>10} {'base hit':>9} {'diff':>8}")
        for lo_c, hi_c, name in bands:
            sub = labelled[(labelled["market_cap"] >= lo_c) & (labelled["market_cap"] < hi_c)]
            ev = sub[sub["grp"] == "event"]["adj"]
            ba = sub[sub["grp"] == "base"]["adj"]
            if len(ev) < 25 or len(ba) < 500:
                print(f"{name:22} {len(ev):>7}  (too few)")
                continue
            e_hit, b_hit = (ev > 0).mean(), (ba > 0).mean()
            print(f"{name:22} {len(ev):>7} {e_hit:>10.3f} {b_hit:>9.3f} {e_hit - b_hit:>+8.3f}")

    if len(events) < 20:
        print("\nToo few organic events to test. Try a lower --min-interactions.")
        return

    # Month-cluster bootstrap: 3-day windows on daily rows overlap.
    pool = pd.concat([events.assign(grp="event"), baseline.assign(grp="base")])
    pool["block"] = pool["date"].dt.to_period("M")
    blocks = sorted(pool["block"].unique())
    by_block = {b: g for b, g in pool.groupby("block")}
    rng = np.random.default_rng(7)

    def stat(s: pd.DataFrame) -> float:
        e = s[s["grp"] == "event"]["adj"]
        b = s[s["grp"] == "base"]["adj"]
        if len(e) < 5 or len(b) < 50:
            return np.nan
        return (e > 0).mean() - (b > 0).mean()

    observed = stat(pool)
    draws = []
    for _ in range(args.bootstrap):
        picked = rng.choice(len(blocks), len(blocks))
        v = stat(pd.concat([by_block[blocks[i]] for i in picked]))
        if np.isfinite(v):
            draws.append(v)
    d = np.array(draws)
    p = 2 * min((d <= 0).mean(), (d >= 0).mean())
    print(f"\norganic minus ordinary hit rate: {observed:+.3f}  "
          f"CI [{np.percentile(d, 2.5):+.3f}, {np.percentile(d, 97.5):+.3f}]  p={p:.4f}")
    print(f"(crypto, for comparison: +0.072, p=0.003)")


if __name__ == "__main__":
    main()
