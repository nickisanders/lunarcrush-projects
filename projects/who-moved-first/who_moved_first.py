#!/usr/bin/env python3
"""When a coin pumps, did the crowd show up before the move or after it?

The backtest in projects/social-price-backtest found that an attention spike
only carries an edge when the price has not moved yet. Attention that arrives
after a move is worth nothing: same spike after a 5%+ run, 41.7% beats-BTC,
p = 0.85 against baseline. This tool takes a coin that is pumping right now
and shows which order things happened in, hour by hour.

Two series over the last 48 hours: price, and distinct accounts posting. Each
is expressed relative to its own level at the start of the window. The report
says when price first cleared +10% and +25%, and when the crowd first cleared
+50% and +100%, so the lead or lag can be read in hours.

Usage:
    LUNARCRUSH_API_KEY=... python3 who_moved_first.py AKE
"""

import argparse
import json
import os
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
API = "https://lunarcrush.com/api4"
HOURS = 48
PRICE_MARKS = (0.10, 0.25)
CROWD_MARKS = (0.50, 1.00)


def get(path: str) -> dict:
    key = os.environ["LUNARCRUSH_API_KEY"]
    req = urllib.request.Request(f"{API}{path}", headers={
        "Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def first_cross(s: pd.Series, level: float):
    hit = s[s >= level]
    return hit.index[0] if len(hit) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--hours", type=int, default=HOURS)
    ap.add_argument("--json")
    args = ap.parse_args()

    rows = get(f"/public/coins/{args.symbol}/time-series/v2?bucket=hour&interval=1w")["data"]
    df = pd.DataFrame(rows)
    df["t"] = pd.to_datetime(df["time"], unit="s")
    for c in ("close", "contributors_active", "interactions"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    # The last row is the hour in progress, so it is dropped: a partial hour
    # of contributors compared to complete hours is the same bug as a partial
    # day compared to complete days.
    df = df.dropna(subset=["close", "contributors_active"]).iloc[:-1].tail(args.hours).set_index("t")

    base_p, base_c = df["close"].iloc[0], df["contributors_active"].iloc[:6].median()
    df["price_rel"] = df["close"] / base_p - 1
    df["crowd_rel"] = df["contributors_active"] / base_c - 1
    df["inter_rel"] = df["interactions"] / df["interactions"].iloc[:6].median() - 1

    print(f"${args.symbol}, last {len(df)} complete hours "
          f"({df.index[0]:%Y-%m-%d %H:%M} to {df.index[-1]:%Y-%m-%d %H:%M} UTC)\n")
    print(f"price:  {base_p:.6g} -> {df['close'].iloc[-1]:.6g}  ({df['price_rel'].iloc[-1] * 100:+.0f}%)")
    print(f"crowd:  {base_c:.0f} -> {df['contributors_active'].iloc[-1]:.0f} accounts/hour  "
          f"({df['crowd_rel'].iloc[-1] * 100:+.0f}%)")
    print(f"peak crowd: {df['contributors_active'].max():.0f} at {df['contributors_active'].idxmax():%H:%M}")

    events = []
    for m in PRICE_MARKS:
        t = first_cross(df["price_rel"], m)
        events.append(("price", m, t))
        print(f"price first +{m * 100:.0f}%:  {t:%Y-%m-%d %H:%M}" if t is not None else f"price never reached +{m * 100:.0f}%")
    for m in CROWD_MARKS:
        t = first_cross(df["crowd_rel"], m)
        events.append(("crowd", m, t))
        print(f"crowd first +{m * 100:.0f}%:  {t:%Y-%m-%d %H:%M}" if t is not None else f"crowd never reached +{m * 100:.0f}%")

    p10 = first_cross(df["price_rel"], PRICE_MARKS[0])
    c50 = first_cross(df["crowd_rel"], CROWD_MARKS[0])
    verdict = None
    if p10 is not None and c50 is not None:
        lag = (c50 - p10).total_seconds() / 3600
        verdict = f"crowd arrived {abs(lag):.0f}h {'after' if lag > 0 else 'before'} the price move"
        print(f"\n{verdict}")

    out = Path(args.json) if args.json else HERE / "out" / f"{args.symbol.lower()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "symbol": args.symbol, "hours": len(df),
        "start": df.index[0].isoformat(), "end": df.index[-1].isoformat(),
        "basePrice": float(base_p), "baseCrowd": float(base_c),
        "series": [{"t": t.isoformat(), "close": float(r["close"]),
                    "contributors": float(r["contributors_active"]),
                    "priceRel": float(r["price_rel"]), "crowdRel": float(r["crowd_rel"])}
                   for t, r in df.iterrows()],
        "events": [{"what": w, "level": m, "t": t.isoformat() if t is not None else None}
                   for w, m, t in events],
        "verdict": verdict,
    }, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
