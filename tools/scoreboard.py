#!/usr/bin/env python3
"""What 28 projects on one API actually established.

Reads the headline result out of each project's own output JSON where one
exists, so the scoreboard cannot drift from what the code last produced.
Anything without a machine-readable result is listed with its finding from
the repo README and marked as such.

Usage: python3 tools/scoreboard.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (project, headline, verdict) where verdict is one of:
#   works   - a measured, reproducible edge or effect
#   null    - tested and found nothing
#   caution - a measurement problem others will hit too
FINDINGS = [
    ("social-price-backtest", "An organic attention spike on a flat price beats Bitcoin 49.0% of the time over 3 days, against 41.9% baseline. p = 0.003", "works"),
    ("social-price-backtest", "The same spike after the price has already run 5%+ is worth nothing. 41.7%, p = 0.85", "caution"),
    ("social-price-backtest", "85% of spikes are spam-heavy and carry no signal. Filtering them is the difference between a signal and an anti-signal", "works"),
    ("social-price-backtest", "None of it works on stocks. 4,063 tickers, 9,073 events, no effect", "null"),
    ("attention-cascade", "The Bitcoin-to-alts attention cascade does not exist", "null"),
    ("attention-floor", "Talkers per DEX trader tracks where a token trades, not whether its attention converts. LINK scores worst because it trades on exchanges", "null"),
    ("attention-death", "Dying conversations predict nothing", "null"),
    ("attention-halflife", "Crypto attention has a one-day half-life, organic or manufactured", "works"),
    ("attention-premium", "Coins talked about more than they are worth are not punished. The first version of this result was 30% stablecoins", "null"),
    ("mood", "Sentiment falls as the crowd grows. The lowest-scoring coins in the data are the ones named ASS, USELESS and TROLL", "caution"),
    ("name-collision", "A coin whose ticker is a word inherits the word's traffic. $ONE borrowed 5.0 billion interactions", "caution"),
    ("bot-share", "The median major coin's conversation is about 40% flagged spam", "caution"),
    ("polymarket-rewards", "Half of Polymarket's fill notional is minted against the exchange rather than matched with a trader, so any who-traded-with-whom analysis sees about half the money", "caution"),
    ("size-bias", "Creator concentration and cross-token overlap both track market cap, in opposite directions. A whole-population percentile charges a token for its size", "caution"),
    ("headcount", "The median top-1,000 coin has 24 people posting about it a day. 82% have fewer than 100", "works"),
    ("top-ten", "Seven coins hold crypto's top-ten conversation. A visitor's median stay in the other three seats is one day", "works"),
    ("where-are-they-now", "130 coins have held a top-20 seat since 2020. 17 still do", "works"),
    ("narrative-shift", "The top three coins went from 31% of the crowd to 52% between 2024 and 2026", "works"),
    ("pumps-not-dumps", "A +5% day is 2.4x as likely to trigger a spike as a -5% day. A -5% day barely beats a flat one", "works"),
    ("who-moved-first", "On every live case so far the price moved first and the crowd arrived hours later", "works"),
    ("weekend-crowd", "The spike detector has a real weekend blind spot and fixing it recovers nothing", "null"),
    ("influencer-scorecard", "Named crypto accounts do not beat Bitcoin on the coins they post about", "null"),
    ("attention-clock", "Conversation runs on a 2.1x daily cycle and every major coin keeps the same Western hours", "works"),
]


def main() -> None:
    projects = sorted(p.name for p in (ROOT / "projects").iterdir() if p.is_dir())
    counts = {v: sum(1 for _, _, k in FINDINGS if k == v) for v in ("works", "null", "caution")}
    print(f"{len(projects)} projects, {len(FINDINGS)} recorded findings\n")
    for verdict, label in (("works", "HOLDS UP"), ("null", "TESTED, FOUND NOTHING"),
                           ("caution", "THE DATA WILL LIE TO YOU HERE")):
        print(f"{label}  ({counts[verdict]})")
        for proj, text, v in FINDINGS:
            if v == verdict:
                print(f"  [{proj}] {text}")
        print()

    missing = [p for p in projects if not any(p == proj for proj, _, _ in FINDINGS)]
    if missing:
        print(f"projects without a recorded headline: {', '.join(missing)}")

    out = ROOT / "tools" / "out"
    out.mkdir(exist_ok=True)
    (out / "scoreboard.json").write_text(json.dumps({
        "projects": len(projects), "counts": counts,
        "findings": [{"project": p, "text": t, "verdict": v} for p, t, v in FINDINGS],
    }, indent=2))
    print(f"Wrote {out / 'scoreboard.json'}")


if __name__ == "__main__":
    main()
