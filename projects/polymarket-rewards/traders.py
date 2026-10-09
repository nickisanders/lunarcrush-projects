#!/usr/bin/env python3
"""Who actually trades on Polymarket, from the raw fill log.

A venue's headline user count says nothing about who moves the money. This
splits a week of fills by address and reports the concentration alongside the
median, because the gap between them is the finding: the typical address is
risking pocket change while a few hundred run inventory across thousands of
markets at once.

The exchange router is excluded. It is the counterparty on roughly half of all
fill notional, and those are mints rather than trades, so counting it would make
one address look like most of the venue.

Maker share and market breadth are reported for the largest addresses because
they are what distinguishes a whale from a market maker, and the difference
decides what the concentration figure means. An address taking tens of thousands
of fills across thousands of questions is not expressing a view.

Usage:
    python3 traders.py            # reads out/raw-*.csv.gz
"""

import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"


def main() -> None:
    paths = sorted(OUT.glob("raw-*.csv.gz"))
    if not paths:
        raise SystemExit("No out/raw-*.csv.gz. Run fills.py --raw first.")

    vol = defaultdict(float)
    fills = defaultdict(int)
    made = defaultdict(float)
    took = defaultdict(float)
    toks = defaultdict(set)
    total = 0.0
    n = 0

    for p in paths:
        with gzip.open(p, "rt") as f:
            for line in f:
                try:
                    m, t, tok, u = line.rstrip().split(",")
                    usd = float(u)
                except ValueError:
                    continue
                if m == EXCHANGE or t == EXCHANGE:
                    continue
                n += 1
                total += usd
                vol[m] += usd; vol[t] += usd
                fills[m] += 1; fills[t] += 1
                made[m] += usd; took[t] += usd
                toks[m].add(tok); toks[t].add(tok)
        print(f"  read {p.name}", flush=True)

    ranked = sorted(vol.items(), key=lambda kv: -kv[1])
    vals = [v for _, v in ranked]
    cuts = {}
    for k in (10, 100, 1000, 5000):
        cuts[k] = sum(vals[:k]) / max(sum(vals), 1)

    top = []
    for a, v in ranked[:10]:
        top.append({"address": a, "volume": round(v, 2), "fills": fills[a],
                    "tokens": len(toks[a]),
                    "maker_share": round(made[a] / max(made[a] + took[a], 1), 3)})

    out = {
        "fills": n, "notional": round(total, 2), "addresses": len(vals),
        "median_volume": round(statistics.median(vals), 2),
        "median_fills": statistics.median(sorted(fills.values())),
        "concentration": {str(k): round(v, 4) for k, v in cuts.items()},
        "over": {str(t): sum(1 for v in vals if v >= t) for t in (100, 1000, 10000)},
        "top10": top,
    }
    (OUT / "traders.json").write_text(json.dumps(out, indent=2))
    print(f"\n  {n:,} fills, ${total:,.0f}, {len(vals):,} addresses")
    print(f"  median address ${out['median_volume']:,.2f} across "
          f"{out['median_fills']:,.0f} fills")
    for k, v in cuts.items():
        print(f"  top {k:>5,}: {v*100:5.1f}% of volume")
    print(f"  wrote {(OUT/'traders.json').relative_to(HERE)}")


if __name__ == "__main__":
    main()
