#!/usr/bin/env python3
"""Ten coins are up big. Which ones have a real crowd behind them?

The question every pump raises and a price screen cannot answer. This takes
the week's biggest gainers and reports four things per coin, none of which is
a verdict on anyone's honesty:

- **Crowd now vs a month ago.** Did people arrive, or is the same group louder?
  projects/crowd-growth found 67% of spikes are the second one.
- **Interactions per person.** A crowd of 60 producing 1,000 reactions each is
  a different object from 2,800 producing 1,000 each.
- **Spam lift, not spam share.** The absolute share is close to useless: it
  runs chronically high for some tokens and LunarCrush's own counting changed
  in 2023, so `spam` can exceed `posts_created`. What carries information is
  the ratio against the coin's own 30-day norm. Above roughly 1.4x is a fresh
  wave; a high share at ~1.0x is a noisy neighbourhood, not a new campaign.
- **Whether the crowd shrank.** A price up with fewer people talking is the
  single most interesting pattern on the list.

This is the screen, not the audit. It says where to look, and it never claims
to know who is behind anything: amplification patterns are compatible with
bots, coordinated advocacy, and unusually tight real communities alike.

Usage: LUNARCRUSH_API_KEY=... python3 crowd_check.py [--top 10]
"""

import argparse
import datetime as dt
import json
import os
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
API = "https://lunarcrush.com/api4"
MIN_MCAP, MIN_VOL = 50e6, 1e6
FRESH_WAVE = 1.4      # spam this many times the coin's own norm reads as a fresh wave
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}


def get(path: str, tries: int = 3) -> dict:
    key = os.environ["LUNARCRUSH_API_KEY"]
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{API}{path}", headers={
                "Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                return {}
            time.sleep(3)


def read(r: dict) -> str:
    """One line describing the pattern, never the cause."""
    if r["growth"] is not None and r["growth"] < 0:
        return "price up, fewer people talking"
    if r["spamLift"] is not None and r["spamLift"] >= FRESH_WAVE:
        return "fresh spam wave against its own norm"
    if r["growth"] is not None and r["growth"] > 1.0:
        return "crowd more than doubled"
    return "crowd grew with the price"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    L["nm"] = L["name"].astype(str)
    for c in ("market_cap", "percent_change_7d", "volume_24h", "interactions_24h"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    L = L.sort_values("market_cap", ascending=False).drop_duplicates("symbol")
    f = L[(L["market_cap"] > MIN_MCAP) & (L["volume_24h"] > MIN_VOL)
          & (L["symbol"].str.len() >= 2) & ~L["symbol"].isin(PEGGED)]
    movers = f.nlargest(args.top, "percent_change_7d")

    rows = []
    for _, r in movers.iterrows():
        d = get(f"/public/coins/{r['symbol']}/time-series/v2?bucket=day&interval=3m")
        data = (d or {}).get("data") or []
        if len(data) < 40:
            continue
        h = pd.DataFrame(data)
        for c in ("contributors_active", "interactions", "posts_created", "spam"):
            h[c] = pd.to_numeric(h.get(c), errors="coerce")
        h = h.iloc[:-1]        # the final row is today, still accumulating
        week, prior = h.iloc[-7:], h.iloc[-37:-7]
        now, base = week["contributors_active"].median(), prior["contributors_active"].median()
        spam_now = week["spam"].sum() / max(week["posts_created"].sum(), 1)
        spam_base = prior["spam"].sum() / max(prior["posts_created"].sum(), 1)
        rows.append({
            "symbol": r["symbol"], "name": r["nm"], "pct7d": float(r["percent_change_7d"]),
            "mcap": float(r["market_cap"]), "crowdNow": float(now), "crowdBase": float(base),
            "growth": float(now / base - 1) if base else None,
            "perPerson": float(week["interactions"].sum() / max(week["contributors_active"].sum(), 1)),
            "spamNow": float(spam_now), "spamLift": float(spam_now / spam_base) if spam_base else None,
        })
        time.sleep(0.2)

    for r in rows:
        r["read"] = read(r)
    d = pd.DataFrame(rows)

    print(f"The week's {len(d)} biggest gainers over $50M\n")
    print(f"{'coin':<9}{'7d':>7}{'people/day':>12}{'a month ago':>13}{'change':>9}{'per person':>12}{'spam lift':>11}  read")
    for _, r in d.iterrows():
        g = f"{r['growth'] * 100:+.0f}%" if r["growth"] is not None else "n/a"
        sl = f"{r['spamLift']:.2f}x" if r["spamLift"] is not None else "n/a"
        print(f"{r['symbol']:<9}{r['pct7d']:>+6.0f}%{r['crowdNow']:>12,.0f}{r['crowdBase']:>13,.0f}"
              f"{g:>9}{r['perPerson']:>12,.0f}{sl:>11}  {r['read']}")

    shrank = d[d["growth"] < 0]
    fresh = d[d["spamLift"] >= FRESH_WAVE]
    print(f"\ncrowd shrank while the price rose: {len(shrank)}"
          f"{' (' + ', '.join(shrank['symbol']) + ')' if len(shrank) else ''}")
    print(f"spam at {FRESH_WAVE}x its own norm or more: {len(fresh)}"
          f"{' (' + ', '.join(fresh['symbol']) + ')' if len(fresh) else ''}")
    print(f"median interactions per person: {d['perPerson'].median():,.0f}")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "crowd_check.json").write_text(json.dumps({
        "asOf": dt.date.today().isoformat(), "freshWave": FRESH_WAVE,
        "medianPerPerson": float(d["perPerson"].median()),
        "shrank": list(shrank["symbol"]), "fresh": list(fresh["symbol"]),
        "coins": rows,
    }, indent=2))
    print(f"\nWrote {HERE / 'out' / 'crowd_check.json'}")


if __name__ == "__main__":
    main()
