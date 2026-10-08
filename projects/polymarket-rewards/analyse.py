#!/usr/bin/env python3
"""Does reciprocal trading concentrate in the markets that pay for liquidity?

Polymarket pays makers a daily rate for resting liquidity meeting a market's
`rewardsMinSize` within its `rewardsMaxSpread`. If some share of volume exists
to collect that rather than to express a view, it should appear as pairs of
addresses trading with each other repeatedly, in both directions, concentrated
in the markets that pay.

The comparison is within-platform and within-period: paying and non-paying
markets sit on the same venue over the same days with the same mechanics, so the
incentive is the systematic difference between them. **A ratio near 1 is the
null, and the null is the result if that is what the data says.**

Two corrections that the raw numbers need, both measured rather than assumed:

- **The exchange router is not a counterparty.** `0xe1111800…` appears as the
  taker in about 35% of fills and 43% of notional. Those are the exchange's own
  matching operations; counting them as trades would make one address look like
  a hub transacting with everybody. They are excluded from pair analysis and the
  excluded amount is reported.
- **Unresolvable markets are excluded rather than assumed.** Tokens Gamma cannot
  resolve are counted as `unknown` and belong to neither arm.

**What this cannot say.** Two addresses trading reciprocally are only
self-dealing if one party controls both, and fill events do not say who controls
an address. A market maker quoting both sides against a frequent counterparty
produces reciprocity honestly. A gap between the arms is evidence the incentive
shapes trading. It is not evidence that any pair is wash trading.

Usage:
    python3 analyse.py --raw
    python3 analyse.py --raw --top 20 --json out/result.json
"""

import argparse
import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"


def segments(path: Path) -> tuple[dict, dict]:
    snap = json.loads(path.read_text())
    markets, seg = snap["markets"], {}
    for tid, ref in snap["token_market"].items():
        m = markets.get(ref["condition_id"])
        if m:
            seg[tid] = "paid" if m["paid"] else "unpaid"
    return seg, markets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", action="store_true", help="read out/raw-*.csv.gz")
    ap.add_argument("--markets", type=Path, default=OUT / "markets-latest.json")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    seg_of, markets = segments(args.markets)
    paths = sorted(OUT.glob("raw-*.csv.gz"))
    if not paths:
        raise SystemExit("No out/raw-*.csv.gz. Run fills.py --raw first.")
    print(f"  reading {len(paths)} raw log(s); {len(seg_of):,} tokens resolved")

    pairs = defaultdict(lambda: [0, 0.0])
    seg_total = defaultdict(float)
    sizes = defaultdict(int)
    fills = router = 0
    notional = router_usd = 0.0

    for p in paths:
        with gzip.open(p, "rt") as f:
            for line in f:
                try:
                    m, t, tok, u = line.rstrip().split(",")
                    usd = float(u)
                except ValueError:
                    continue
                fills += 1
                notional += usd
                seg = seg_of.get(tok, "unknown")
                seg_total[seg] += usd
                for hi in (1, 5, 10, 25, 50, 100, 200, 500, 1_000, 5_000, 25_000):
                    if usd < hi:
                        sizes[f"<{hi}|{seg}"] += 1
                        break
                else:
                    sizes[f">=25000|{seg}"] += 1
                if m == EXCHANGE or t == EXCHANGE:
                    router += 1
                    router_usd += usd
                    continue
                e = pairs[f"{m}|{t}|{seg}"]
                e[0] += 1
                e[1] += usd
        print(f"    {p.name}: {fills:,} fills so far", flush=True)

    print(f"\n  fills          {fills:,}   (${notional:,.0f} notional)")
    print(f"  router legs    {router:,} (${router_usd:,.0f}, "
          f"{router_usd/max(notional,1)*100:.1f}%) excluded from pair analysis")
    print(f"  trader pairs   {len(pairs):,}")
    print(f"  markets        {len(markets):,} resolved, "
          f"{sum(1 for m in markets.values() if m['paid']):,} paying rewards")

    print("\n  notional by reward status:")
    for s in ("paid", "unpaid", "unknown"):
        v = seg_total.get(s, 0.0)
        print(f"    {s:8} ${v:>16,.0f}   {v/max(notional,1)*100:5.1f}%")

    # --- reciprocity -------------------------------------------------------
    tot = defaultdict(float)
    recip = defaultdict(float)
    rows = defaultdict(list)
    for key, (n, usd) in pairs.items():
        a, b, seg = key.split("|")
        tot[seg] += usd
        back = pairs.get(f"{b}|{a}|{seg}")
        if back:
            recip[seg] += usd
            if a < b:
                rows[seg].append((usd + back[1], n + back[0], a, b,
                                  min(usd, back[1]) / max(usd, back[1], 1e-9)))

    print("\n  RECIPROCAL SHARE OF TRADER-TO-TRADER NOTIONAL")
    print(f"    {'segment':9} {'notional':>18} {'reciprocal':>18} {'share':>8}  pairs")
    for s in ("paid", "unpaid", "unknown"):
        if s not in tot:
            continue
        print(f"    {s:9} ${tot[s]:>17,.0f} ${recip[s]:>17,.0f} "
              f"{recip[s]/max(tot[s],1)*100:7.2f}%  {len(rows[s]):,}")
    if tot.get("paid") and tot.get("unpaid"):
        pr = recip["paid"] / tot["paid"]
        ur = recip["unpaid"] / max(tot["unpaid"], 1)
        ratio = pr / max(ur, 1e-12)
        print(f"\n    paid runs {ratio:.2f}x the unpaid reciprocal share")
        verdict = ("no effect — the incentive does not shape who trades with whom"
                   if 0.8 <= ratio <= 1.25 else
                   "higher in paid markets" if ratio > 1.25 else
                   "lower in paid markets")
        print(f"    reading: {verdict}")

    for s in ("paid", "unpaid"):
        if not rows.get(s):
            continue
        print(f"\n  top {args.top} reciprocal pairs, {s} markets "
              f"(balance = smaller/larger side; 1.00 is perfectly even):")
        for usd, n, a, b, bal in sorted(rows[s], reverse=True)[:args.top]:
            print(f"    ${usd:>13,.0f}  {n:>8,} fills  balance {bal:4.2f}  "
                  f"{a[:14]}..  {b[:14]}..")

    # --- size clustering against the reward minimum ------------------------
    mins = [m["min_size"] for m in markets.values() if m["paid"] and m["min_size"]]
    print("\n  fill size distribution, paid vs unpaid (% of that arm's fills):")
    order = ["<1", "<5", "<10", "<25", "<50", "<100", "<200", "<500",
             "<1000", "<5000", "<25000", ">=25000"]
    tp = sum(v for k, v in sizes.items() if k.endswith("|paid")) or 1
    tu = sum(v for k, v in sizes.items() if k.endswith("|unpaid")) or 1
    print(f"    {'bucket':>9} {'paid':>8} {'unpaid':>8}")
    for b in order:
        pv, uv = sizes.get(f"{b}|paid", 0), sizes.get(f"{b}|unpaid", 0)
        if pv or uv:
            print(f"    {b:>9} {pv/tp*100:7.2f}% {uv/tu*100:7.2f}%")
    if mins:
        print(f"    reward minimum across paying markets: median "
              f"{statistics.median(mins):,.0f}, range {min(mins):,.0f}-{max(mins):,.0f}")

    if args.json:
        args.json.write_text(json.dumps({
            "fills": fills, "notional": notional,
            "router_excluded_usd": router_usd,
            "notional_by_segment": dict(seg_total),
            "pair_notional": dict(tot), "reciprocal_notional": dict(recip),
            "sizes": dict(sizes),
        }, indent=2))
        print(f"\n  wrote {args.json}")


if __name__ == "__main__":
    main()
