#!/usr/bin/env python3
"""Does the attention floor rise between spikes, or does the crowd round-trip?

Spikes are easy to see and nearly useless on their own. projects/attention-death
found crypto attention dies fast whatever its source, so a tall bar says almost
nothing about whether anyone stayed. The signature that separates adoption from
a campaign is what happens on the ordinary days afterwards: genuine arrivals
leave a durably higher floor, and a campaign leaves a crater once the budget
stops.

So this measures the quiet days and throws the spikes away. Every day at or
above 2x the coin's own 30-day median is excluded, and what remains is compared
across three windows. A floor that climbs while spikes come and go is a crowd
that is accumulating rather than cycling.

Two things it deliberately does not do. It makes no claim about who is behind
any spike, since the same pattern is compatible with coordinated promotion, a
news cycle and a genuinely growing community. And it is not a buy signal:
projects/social-price-backtest found organic attention only shifts the odds
while the price has not moved yet, so a rising floor next to a price that has
already run is a description, not an edge.

Usage: LUNARCRUSH_API_KEY=... python3 floor.py FET [--spike-multiple 2.0]
"""

import argparse
import datetime as dt
import json
import os
import statistics
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://lunarcrush.com/api4"
# Cloudflare sits in front of this API and rejects the default Python-urllib
# signature with a 403 that reads exactly like throttling. Always send one.
UA = "lunarcrush-projects/attention-floor"


def get(path: str) -> list[dict]:
    key = os.environ.get("LUNARCRUSH_API_KEY")
    if not key:
        raise SystemExit("LUNARCRUSH_API_KEY is not set.")
    req = urllib.request.Request(f"{BASE}{path}",
                                 headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]


def day(row: dict) -> str:
    return dt.datetime.fromtimestamp(row["time"], dt.timezone.utc).strftime("%Y-%m-%d")


def window(rows: list[dict], spike: float, label: str) -> dict | None:
    """The floor of a stretch, measured on its quiet days only."""
    quiet = [r for r in rows if r["interactions"] < spike]
    if not quiet:
        return None
    return {
        "label": label,
        "days": len(quiet),
        "spike_days": len(rows) - len(quiet),
        "interactions": statistics.median(r["interactions"] for r in quiet),
        "people": statistics.median(r["contributors_active"] for r in quiet),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    ap.add_argument("--spike-multiple", type=float, default=2.0)
    a = ap.parse_args()

    rows = get(f"/public/coins/{a.symbol}/time-series/v2?bucket=day&interval=3m")
    # The last row is today and still accumulating. Dropping it is the
    # partial-day bias that has bitten three projects in this repo.
    rows = [r for r in rows[:-1]
            if r.get("interactions") and r.get("contributors_active")]
    if len(rows) < 90:
        raise SystemExit(f"Only {len(rows)} usable days for {a.symbol}; need 90.")

    base = statistics.median(r["interactions"] for r in rows[-31:-1])
    threshold = base * a.spike_multiple
    spikes = [{"day": day(r), "interactions": r["interactions"],
               "people": r["contributors_active"], "close": r["close"],
               "multiple": round(r["interactions"] / base, 2)}
              for r in rows[-21:] if r["interactions"] >= threshold]

    windows = [w for w in (window(rows[-90:-42], threshold, "90 to 42 days ago"),
                           window(rows[-42:-21], threshold, "42 to 21 days ago"),
                           window(rows[-21:], threshold, "the last 21 days")) if w]

    out = {
        "symbol": a.symbol.upper(),
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "baseline_30d": base,
        "spike_threshold": threshold,
        "spikes_21d": spikes,
        "windows": windows,
        "recent": [{"day": day(r), "interactions": r["interactions"],
                    "people": r["contributors_active"], "close": r["close"]}
                   for r in rows[-21:]],
        "price_90d_change": rows[-1]["close"] / rows[-90]["close"] - 1,
    }
    if len(windows) >= 2:
        out["floor_lift"] = windows[-1]["interactions"] / windows[0]["interactions"]
        out["people_lift"] = windows[-1]["people"] / windows[0]["people"]

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "floor.json").write_text(json.dumps(out, indent=1))

    print(f"{out['symbol']}  30-day baseline {base:,.0f} interactions "
          f"(spike at {threshold:,.0f})\n")
    print(f"  {len(spikes)} spike days in the last 21:")
    for s in spikes:
        print(f"    {s['day']}  {s['interactions']:>10,.0f}  {s['multiple']:>4.1f}x  "
              f"{s['people']:>5,.0f} people  ${s['close']:.4f}")
    print(f"\n  floor on quiet days only:")
    for w in windows:
        print(f"    {w['label']:<20}{w['interactions']:>11,.0f} interactions"
              f"{w['people']:>7,.0f} people   ({w['days']} quiet, {w['spike_days']} spiking)")
    if "floor_lift" in out:
        print(f"\n  floor is {out['floor_lift']:.2f}x where it was, "
              f"with {out['people_lift']:.2f}x the people")
    print(f"  price over 90 days: {out['price_90d_change']:+.0%}")
    print(f"\nWrote out/floor.json")


if __name__ == "__main__":
    main()
