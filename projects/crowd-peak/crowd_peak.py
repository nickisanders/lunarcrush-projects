#!/usr/bin/env python3
"""A coin crashes into crypto's top 10 conversation. What happens next?

$QNT went from #90 in April to #4 today. The natural question is whether that
has ever meant anything, so this finds every time a coin entered the top N by
daily active contributors for the first time in a year, and measures what the
price did afterwards.

Returns are reported two ways and the gap between them is the finding:
absolute, which is what it feels like, and Bitcoin-adjusted, which is what it
is worth. Significance from the same calendar-month cluster bootstrap the rest
of the repo uses.

Usage: python3 crowd_peak.py [--top 10]
"""

import argparse
import datetime as dt
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
HORIZONS = (7, 30, 90)
LOOKBACK = 365      # no day in the top N in the prior year
MIN_HISTORY = 200   # the coin needs this much history before it counts
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def load() -> tuple[dict, dict]:
    px, day = {}, defaultdict(list)
    for f in glob.glob(str(RAW / "*.json")):
        d = json.load(open(f))
        s = d["coin"]["symbol"]
        if s in PEGGED or len(s) < 2:
            continue
        rows = []
        for r in d["rows"]:
            t = dt.datetime.fromtimestamp(r["time"], dt.UTC).date()
            c, mc = r.get("contributors_active") or 0, r.get("market_cap") or 0
            rows.append((t, r.get("close")))
            if c > 0 and mc > 0:
                day[t].append((s, c))
        df = pd.DataFrame(rows, columns=["date", "close"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        px[s] = df.dropna(subset=["close"]).set_index("date")
    rank = defaultdict(dict)
    for t, rows in day.items():
        rows.sort(key=lambda x: -x[1])
        for i, (s, _) in enumerate(rows, 1):
            rank[s][t] = i
    return px, rank


def block_bootstrap(vals: pd.Series, blocks: pd.Series, iters: int = 2000, seed: int = 7) -> tuple:
    """Median of vals, resampled by calendar-month block."""
    g = {b: vals[blocks == b].to_numpy() for b in blocks.unique()}
    keys = list(g)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(iters):
        pick = np.concatenate([g[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        out.append(np.median(pick))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), \
        float(2 * min((np.array(out) <= 0).mean(), (np.array(out) >= 0).mean()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    TOP = args.top

    px, rank = load()
    btc = px["BTC"]
    events = []
    for s, rk in rank.items():
        if s == "BTC":
            continue
        ds = sorted(rk)
        for i, t in enumerate(ds):
            if rk[t] > TOP:
                continue
            prior = [rk[d] for d in ds[max(0, i - LOOKBACK):i]]
            if len(prior) < MIN_HISTORY or (prior and min(prior) <= TOP):
                continue
            events.append((s, t))

    rows = []
    for s, t in events:
        p = px[s]
        if t not in p.index or t not in btc.index:
            continue
        after = [d for d in p.index if d >= t]
        for H in HORIZONS:
            fut = [d for d in after if d >= t + dt.timedelta(days=H)]
            if not fut or fut[0] not in btc.index:
                continue
            d1 = fut[0]
            r = p.loc[d1, "close"] / p.loc[t, "close"] - 1
            b = btc.loc[d1, "close"] / btc.loc[t, "close"] - 1
            rows.append({"symbol": s, "date": t, "H": H, "ret": r, "adj": r - b})
    df = pd.DataFrame(rows)
    df["block"] = [f"{d.year}-{d.month:02d}" for d in df["date"]]

    print(f"{len(events)} first entries into the top {TOP} by crowd, no top-{TOP} day in the prior year\n")
    print(f"{'horizon':>8}{'n':>5}{'median':>10}{'vs BTC':>10}{'95% CI on vs BTC':>22}{'p':>8}{'up':>7}{'beat':>7}")
    stats = []
    for H in HORIZONS:
        g = df[df["H"] == H]
        lo, hi, p = block_bootstrap(g["adj"], g["block"])
        stats.append({"H": H, "n": int(len(g)), "ret": float(g["ret"].median()),
                      "adj": float(g["adj"].median()), "lo": lo, "hi": hi, "p": p,
                      "up": float((g["ret"] > 0).mean()), "beat": float((g["adj"] > 0).mean())})
        print(f"{H:>7}d{len(g):>5}{g['ret'].median() * 100:>9.1f}%{g['adj'].median() * 100:>9.1f}%"
              f"{f'[{lo * 100:+.1f}, {hi * 100:+.1f}]':>22}{p:>8.3f}{(g['ret'] > 0).mean() * 100:>6.0f}%{(g['adj'] > 0).mean() * 100:>6.0f}%")

    recent = df[df["H"] == 30].sort_values("date").tail(12)
    print("\nMost recent entries, 30 days later")
    for _, r in recent.iterrows():
        print(f"  {r['symbol']:<8}{r['date']}   {r['ret'] * 100:>+6.0f}%   vs BTC {r['adj'] * 100:>+6.0f}%")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "crowd_peak.json").write_text(json.dumps({
        "top": TOP, "events": int(len(events)), "stats": stats,
        "recent": [{"symbol": r["symbol"], "date": r["date"].isoformat(),
                    "ret": float(r["ret"]), "adj": float(r["adj"])} for _, r in recent.iterrows()],
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'crowd_peak.json'}")


if __name__ == "__main__":
    main()
