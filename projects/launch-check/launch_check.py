#!/usr/bin/env python3
"""A ticker is trending. How many tokens actually carry that name?

Every celebrity or news-driven token launch produces the same situation: a
name spreads faster than any way to verify it, and a buyer searching a
screener finds several contracts that look identical. This answers two
questions in one call, using GeckoTerminal, which needs no API key:

1. How many DISTINCT contracts carry this name, and how old are they?
2. Is the volume plausible, or is it churn?

The second question is the one screeners answer badly. They rank by volume,
and volume is the easiest number on a chart to manufacture. A pool holding
$811k that reports $324M of daily volume has turned over its entire depth 400
times in a day. Healthy pools turn over a few times.

Two derived numbers do the work:

- **Turnover** = 24h volume divided by pool liquidity. Above roughly 20x,
  ask what is producing it.
- **Volume per trading wallet.** Real retail does not average six figures. On
  the $LAPTOP launch of 2026-09-07 the three largest pools averaged $115,676,
  $140,779 and $178,864 per distinct wallet, on a token hours old.

This tool cannot tell you which contract is official, and neither can a
screener. That is the finding, not a limitation to apologise for.

Usage:
    python3 launch_check.py LAPTOP
    python3 launch_check.py LAPTOP --json out/laptop.json
"""

import argparse
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = "https://api.geckoterminal.com/api/v2"
UA = "lunarcrush-projects-launch-check/0.1"
# Above this, the pool's entire depth changed hands this many times in a day.
TURNOVER_FLAG = 20
# Real retail buyers do not average this much per wallet.
PER_WALLET_FLAG = 25_000
# A pool reporting far more depth than every peer while doing almost no volume
# is a bad reading, not a market. Seen on 2026-09-08: a Base pool reported
# $3.35 BILLION of liquidity on $1,198 of daily volume, which alone dwarfed the
# real total and dragged combined turnover to zero. Excluded from the totals
# and reported separately rather than silently dropped.
IMPLAUSIBLE_LIQUIDITY_MULTIPLE = 50
IMPLAUSIBLE_VOLUME_RATIO = 0.001


def get(path: str) -> dict:
    req = urllib.request.Request(f"{GT}{path}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def find_pools(ticker: str, pages: int = 2) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        data = get(f"/search/pools?query={urllib.parse.quote(ticker)}&page={page}").get("data") or []
        if not data:
            break
        for p in data:
            a, rel = p["attributes"], p.get("relationships") or {}
            base = ((rel.get("base_token") or {}).get("data") or {}).get("id", "")
            net = ((rel.get("network") or {}).get("data") or {}).get("id") or base.split("_")[0]
            tx = (a.get("transactions") or {}).get("h24") or {}
            liq = float(a.get("reserve_in_usd") or 0)
            vol = float((a.get("volume_usd") or {}).get("h24") or 0)
            traders = (tx.get("buyers") or 0) + (tx.get("sellers") or 0)
            out.append({
                "name": a.get("name"), "network": net,
                "address": base.split("_", 1)[1] if "_" in base else base,
                "liquidity": liq, "volume24h": vol,
                "turnover": vol / liq if liq else 0,
                "traders24h": traders,
                "volumePerWallet": vol / traders if traders else 0,
                "created": str(a.get("pool_created_at"))[:10],
            })
    return out


def summarize(pools: list[dict], ticker: str) -> dict:
    # Group by contract: one token can have many pools, and counting pools
    # would overstate how many distinct things share the name.
    by_addr: dict[str, dict] = {}
    for p in pools:
        if not p["address"]:
            continue
        e = by_addr.setdefault(p["address"], {"network": p["network"], "liquidity": 0.0,
                                              "volume24h": 0.0, "traders24h": 0,
                                              "created": p["created"], "pools": 0})
        e["liquidity"] += p["liquidity"]
        e["volume24h"] += p["volume24h"]
        e["traders24h"] += p["traders24h"]
        e["pools"] += 1
        e["created"] = min(e["created"], p["created"])
    for e in by_addr.values():
        e["turnover"] = e["volume24h"] / e["liquidity"] if e["liquidity"] else 0
        e["volumePerWallet"] = e["volume24h"] / e["traders24h"] if e["traders24h"] else 0
    # Screen out implausible liquidity readings before totalling.
    liqs = sorted(e["liquidity"] for e in by_addr.values() if e["liquidity"] > 0)
    median_liq = liqs[len(liqs) // 2] if liqs else 0
    excluded = {}
    for addr, e in list(by_addr.items()):
        too_deep = median_liq > 0 and e["liquidity"] > median_liq * IMPLAUSIBLE_LIQUIDITY_MULTIPLE
        too_quiet = e["volume24h"] < e["liquidity"] * IMPLAUSIBLE_VOLUME_RATIO
        if too_deep and too_quiet:
            e["implausible"] = True
            excluded[addr] = e

    counted = {a: e for a, e in by_addr.items() if a not in excluded}
    tot_liq = sum(e["liquidity"] for e in counted.values())
    tot_vol = sum(e["volume24h"] for e in counted.values())
    return {
        "ticker": ticker, "contracts": len(by_addr), "pools": len(pools),
        "totalLiquidity": tot_liq, "totalVolume24h": tot_vol,
        "combinedTurnover": tot_vol / tot_liq if tot_liq else 0,
        "excludedImplausible": {a: e["liquidity"] for a, e in excluded.items()},
        "medianContractLiquidity": median_liq,
        "networks": sorted({e["network"] for e in by_addr.values()}),
        "created": sorted({e["created"] for e in by_addr.values()}),
        "byContract": by_addr,
    }


def report(s: dict) -> None:
    print(f"${s['ticker']}: {s['contracts']} distinct contracts across {s['pools']} pools\n")
    print(f"  networks: {', '.join(s['networks'])}")
    print(f"  pools created: {', '.join(s['created'])}")
    print(f"  combined liquidity: ${s['totalLiquidity']:,.0f}")
    print(f"  combined 24h volume: ${s['totalVolume24h']:,.0f}")
    print(f"  combined turnover: {s['combinedTurnover']:.0f}x")
    if s.get("excludedImplausible"):
        print(f"\n  {len(s['excludedImplausible'])} contract(s) excluded from the totals as implausible:")
        for addr, liq in s["excludedImplausible"].items():
            print(f"    {addr[:24]}… reported ${liq:,.0f} of liquidity on negligible volume")
        print(f"    (median contract liquidity here is ${s['medianContractLiquidity']:,.0f})")
    print()

    top = sorted((kv for kv in s["byContract"].items() if not kv[1].get("implausible")),
                 key=lambda kv: -kv[1]["volume24h"])[:8]
    print(f"{'network':<11}{'liquidity':>13}{'vol 24h':>16}{'turnover':>10}{'per wallet':>13}  contract")
    for addr, e in top:
        flag = ""
        if e["turnover"] >= TURNOVER_FLAG:
            flag += " ⚠turnover"
        if e["volumePerWallet"] >= PER_WALLET_FLAG:
            flag += " ⚠per-wallet"
        print(f"{e['network']:<11}${e['liquidity']:>12,.0f}${e['volume24h']:>15,.0f}"
              f"{e['turnover']:>9.0f}x${e['volumePerWallet']:>12,.0f}  {addr[:18]}…{flag}")

    print()
    if s["contracts"] > 1:
        print(f"{s['contracts']} different contracts carry this name. Nothing here identifies which,")
        print("if any, is official. A screener cannot tell you either.")
    flagged = [e for e in s["byContract"].values() if e["turnover"] >= TURNOVER_FLAG]
    if flagged:
        print(f"\n{len(flagged)} contracts turn their entire liquidity over more than {TURNOVER_FLAG}x a day.")
        print("Volume is the easiest number on a chart to manufacture, and it is what screeners rank by.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--json")
    args = ap.parse_args()
    s = summarize(find_pools(args.ticker), args.ticker.upper())
    report(s)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(s, indent=1))
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    import urllib.parse
    main()
