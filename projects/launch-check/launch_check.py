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
- **Volume per trading wallet, and the raw wallet count.** Real retail does not
  average six figures. On the $LAPTOP launch of 2026-09-07 the three largest
  pools averaged $115,676, $140,779 and $178,864 per distinct wallet, on a token
  hours old.

  The wallet count is the stronger of the two. When $LAPTOP's genuine contract
  was identified on 2026-09-09, it held 42,114 distinct trading wallets, more
  than every other contract carrying the name combined, at $647 each. It ranked
  9th of 28 by volume and 1st by wallets. Ranking by volume hides the real
  token; ranking by wallets surfaces it.

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
# A pool whose reported depth is roughly its entire fully diluted valuation is
# holding the token, not money. All the supply sits on one side of the pool and
# is valued at the price that same pool quotes, so the "liquidity" is circular:
# it measures the token against itself. Real pools report reserves far below
# FDV (LAPTOP's genuine ones ran 0.01 to 0.5 of it).
#
# This replaces a threshold pair (50x median depth AND near-zero volume) that
# was added on 2026-09-08 after a Base pool reported $3.35 BILLION on $1,198 of
# volume. That rule caught one such pool on 2026-09-09 and missed two more,
# because one did 0.0015 of its depth in volume and the cutoff was 0.001. The
# totals came out at $90.8M of liquidity when the real figure was $35.5M,
# understating combined turnover by a factor of 2.6. Picking a cutoff is the
# thing this repo criticises screeners for. The ratio below is not a tuned
# threshold, it is a structural test: reserve cannot legitimately equal FDV.
RESERVE_IS_FDV_RATIO = 0.9


def get(path: str) -> dict:
    req = urllib.request.Request(f"{GT}{path}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def find_pools(ticker: str, pages: int = 5) -> list[dict]:
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
            fdv = float(a.get("fdv_usd") or 0)
            vol = float((a.get("volume_usd") or {}).get("h24") or 0)
            traders = (tx.get("buyers") or 0) + (tx.get("sellers") or 0)
            out.append({
                "name": a.get("name"), "network": net,
                "address": base.split("_", 1)[1] if "_" in base else base,
                "liquidity": liq, "fdv": fdv, "volume24h": vol,
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
                                              "fdv": 0.0,
                                              "created": p["created"], "pools": 0})
        e["liquidity"] += p["liquidity"]
        e["fdv"] = max(e["fdv"], p.get("fdv", 0.0))
        e["volume24h"] += p["volume24h"]
        e["traders24h"] += p["traders24h"]
        e["pools"] += 1
        e["created"] = min(e["created"], p["created"])
    for e in by_addr.values():
        e["turnover"] = e["volume24h"] / e["liquidity"] if e["liquidity"] else 0
        e["volumePerWallet"] = e["volume24h"] / e["traders24h"] if e["traders24h"] else 0
    # Screen out circular liquidity readings before totalling. See
    # RESERVE_IS_FDV_RATIO: depth that equals the token's own valuation is the
    # token sitting on one side of its own pool, not money you could sell into.
    excluded = {}
    for addr, e in list(by_addr.items()):
        if e["fdv"] > 0 and e["liquidity"] >= e["fdv"] * RESERVE_IS_FDV_RATIO:
            e["implausible"] = True
            e["reserveOverFdv"] = e["liquidity"] / e["fdv"]
            excluded[addr] = e

    counted = {a: e for a, e in by_addr.items() if a not in excluded}
    tot_liq = sum(e["liquidity"] for e in counted.values())
    tot_vol = sum(e["volume24h"] for e in counted.values())
    return {
        "ticker": ticker, "contracts": len(by_addr), "pools": len(pools),
        "totalLiquidity": tot_liq, "totalVolume24h": tot_vol,
        "combinedTurnover": tot_vol / tot_liq if tot_liq else 0,
        "excludedImplausible": {a: e["liquidity"] for a, e in excluded.items()},
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
        print(f"\n  {len(s['excludedImplausible'])} contract(s) excluded: reported depth is the token itself,")
        print("  not money. Reserve at or above fully diluted valuation is circular.")
        for addr, liq in s["excludedImplausible"].items():
            r = s["byContract"][addr].get("reserveOverFdv", 0)
            print(f"    {addr[:24]}… ${liq:,.0f} of \"liquidity\" = {r:.2f}x its own FDV")
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
    wal = sorted((kv for kv in s["byContract"].items() if not kv[1].get("implausible")),
                 key=lambda kv: -kv[1]["traders24h"])[:5]
    tot_tr = sum(e["traders24h"] for a, e in s["byContract"].items() if not e.get("implausible"))
    print("Most distinct trading wallets. Volume can be manufactured by a few addresses")
    print("trading with themselves; tens of thousands of wallets is harder to fake.\n")
    print(f"{'network':<11}{'wallets':>10}{'share':>8}{'per wallet':>13}{'vol 24h':>16}  contract")
    for addr, e in wal:
        sh = e["traders24h"] / tot_tr * 100 if tot_tr else 0
        print(f"{e['network']:<11}{e['traders24h']:>10,}{sh:>7.0f}%${e['volumePerWallet']:>12,.0f}"
              f"${e['volume24h']:>15,.0f}  {addr[:18]}…")

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
