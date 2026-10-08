#!/usr/bin/env python3
"""Stream Polymarket fills and aggregate them into counterparty pairs.

Every `OrderFilled` event carries the maker and the taker, which is the field
that makes any question about who trades with whom answerable at all. Fills are
aggregated as they arrive and never retained raw: a week of Polymarket is
roughly 11 million fills, and the questions here are about pairs and markets,
not individual trades.

What comes out:

- **pairs**  — per (maker, taker, segment), the fill count and notional, and
  whether the same two addresses also trade in the opposite direction.
  Reciprocity is the shape that distinguishes two parties passing inventory back
  and forth from one party providing liquidity to many.

`--raw` additionally writes every fill to a compressed log as
`maker,taker,token,usd`. Reward status is a property of the market and is only
known once the traded tokens have been resolved, which happens after streaming;
with a raw log that resolution is applied offline by `analyse.py` instead of
costing a second pass over the chain. A week is ~10M fills and compresses to a
few hundred MB, which is a good trade against several hours of re-streaming, and
it means the window can be re-analysed any number of ways for free.

`--shard i/n` splits the block range into n contiguous slices so several workers
can cover a long window at once. Each writes its own state and raw log, and
`analyse.py` reads them all.
- **tokens** — per outcome token, fill count and notional, so fills can be
  attributed to markets and joined to reward parameters by `analyse.py`.
- **sizes**  — the notional histogram, to test whether fills cluster at the
  reward programme's minimum size.

Reciprocal trading between two addresses is not by itself evidence of wash
trading: a market maker and a frequent taker produce it honestly, and two
proxies are only self-dealing if the same party controls both, which these
events cannot establish. The output is a ranking of pairs by reciprocity, not a
verdict about any of them.

Usage:
    python3 fills.py --hours 1                        # pass one: collect tokens
    python3 markets.py --from-fills out/fills-A-B.json.gz
    python3 fills.py --from-block A --to-block B \
            --token-map out/markets-latest.json       # pass two: segmented
"""

import argparse
import gzip
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
RPC = os.environ.get("POLYGON_RPC", "https://polygon-bor-rpc.publicnode.com")
UA = "polymarket-rewards/0.1 (research; github.com/nickisanders/lunarcrush-projects)"

# OrderFilled(bytes32 indexed orderHash, address indexed maker,
#             address indexed taker, uint256 makerAssetId, uint256 takerAssetId,
#             uint256 makerAmountFilled, uint256 takerAmountFilled, uint256 fee)
ORDER_FILLED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"

# Only the current router emits fills today; the two legacy exchanges were
# checked on 2026-10-07 and are dormant. They stay listed so a run over older
# history stays correct rather than silently empty.
EXCHANGES = ["0xe111180000d2663c0091e4f400237545b87b996b"]
LEGACY = ["0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",
          "0xc5d563a36ae78145c45a50134d48a1215220f80a"]

BLOCK_SECONDS = 2.0
WINDOW = 2_000       # publicnode allows 10k but times out there at this density
MIN_WINDOW = 100
USDC = 10 ** 6


def rpc(method: str, params: list, attempts: int = 6, timeout: int = 180):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, data=body,
                                 headers={"content-type": "application/json", "User-Agent": UA})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            return d.get("result") if "result" in d else None
        except urllib.error.HTTPError as e:
            if e.code == 400:        # a JSON-RPC complaint, not a transport fault
                return None
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(min(60, 1.5 * 2 ** attempt))
    return None


def state_path(frm: int, to: int, seg: bool) -> Path:
    return OUT / (f"fills-{frm}-{to}{'-seg' if seg else ''}.json.gz")


def load_segments(path: Path) -> dict:
    """token id -> 'paid' | 'unpaid', from a markets.py snapshot."""
    snap = json.loads(path.read_text())
    markets, out = snap["markets"], {}
    for tid, ref in snap["token_market"].items():
        m = markets.get(ref["condition_id"])
        if m:
            out[tid] = "paid" if m["paid"] else "unpaid"
    return out


def load(path: Path) -> dict:
    if path.exists():
        with gzip.open(path, "rt") as f:
            s = json.load(f)
        s["pairs"] = defaultdict(lambda: [0, 0.0], {k: v for k, v in s["pairs"].items()})
        s["tokens"] = defaultdict(lambda: [0, 0.0], {k: v for k, v in s["tokens"].items()})
        s["sizes"] = defaultdict(int, s["sizes"])
        s["addr"] = defaultdict(lambda: [0, 0.0], {k: v for k, v in s["addr"].items()})
        return s
    return {"cursor": None, "fills": 0, "notional": 0.0,
            "pairs": defaultdict(lambda: [0, 0.0]),
            "tokens": defaultdict(lambda: [0, 0.0]),
            "sizes": defaultdict(int),
            "addr": defaultdict(lambda: [0, 0.0])}


def save(path: Path, s: dict) -> None:
    OUT.mkdir(exist_ok=True)
    with gzip.open(path, "wt") as f:
        json.dump({"cursor": s["cursor"], "fills": s["fills"], "notional": s["notional"],
                   "pairs": dict(s["pairs"]), "tokens": dict(s["tokens"]),
                   "sizes": dict(s["sizes"]), "addr": dict(s["addr"])}, f)


def bucket(usd: float) -> str:
    """Log-ish buckets, with the boundaries that matter for reward minimums
    (commonly 100 and 200 USDC) falling on their own edges."""
    for hi in (1, 5, 10, 25, 50, 100, 200, 500, 1_000, 5_000, 25_000):
        if usd < hi:
            return f"<{hi}"
    return ">=25000"


def fold(logs: list, s: dict, seg_of: dict | None, raw=None) -> None:
    for lg in logs:
        t = lg["topics"]
        if len(t) < 4:
            continue
        maker, taker = "0x" + t[2][-40:], "0x" + t[3][-40:]
        d = lg["data"][2:]
        if len(d) < 4 * 64:
            continue
        maker_asset = int(d[0:64], 16)
        taker_asset = int(d[64:128], 16)
        maker_amt = int(d[128:192], 16)
        taker_amt = int(d[192:256], 16)
        # Exactly one side is the collateral (asset id 0); that side carries the
        # USDC notional and the other names the outcome token being traded.
        if maker_asset == 0:
            usd, token = maker_amt / USDC, str(taker_asset)
        elif taker_asset == 0:
            usd, token = taker_amt / USDC, str(maker_asset)
        else:
            continue                 # token-for-token, not priced in collateral
        s["fills"] += 1
        s["notional"] += usd
        seg = (seg_of.get(token, "unknown") if seg_of is not None else "all")
        key = f"{maker}|{taker}|{seg}"
        p = s["pairs"][key]; p[0] += 1; p[1] += usd
        tk = s["tokens"][token]; tk[0] += 1; tk[1] += usd
        s["sizes"][bucket(usd)] += 1
        for a in (maker, taker):
            r = s["addr"][a]; r[0] += 1; r[1] += usd
        if raw is not None:
            raw.write(f"{maker},{taker},{token},{usd:.6f}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--days", type=float, help="look back this many days from the head")
    g.add_argument("--hours", type=float, help="look back this many hours from the head")
    ap.add_argument("--from-block", type=int)
    ap.add_argument("--to-block", type=int)
    ap.add_argument("--max-requests", type=int, default=0, help="stop after N (resumable)")
    ap.add_argument("--token-map", type=Path,
                    help="a markets.py snapshot; splits pairs into paid/unpaid")
    ap.add_argument("--raw", action="store_true",
                    help="also log every fill, so segmentation needs no second pass")
    ap.add_argument("--shard", help="i/n: cover only slice i of n over the range")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    head = args.to_block or int(rpc("eth_blockNumber", []), 16)
    if args.from_block:
        start = args.from_block
    else:
        span = (args.days or 0) * 86400 + (args.hours or 1) * 3600
        start = head - int(span / BLOCK_SECONDS)

    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        span = (head - start) // n
        lo = start + span * (i - 1)
        start, head = lo, (lo + span - 1 if i < n else head)
        print(f"  shard {i}/{n}: blocks {start:,}-{head:,}")

    seg_of = load_segments(args.token_map) if args.token_map else None
    if seg_of is not None:
        print(f"  segmenting against {len(seg_of):,} resolved tokens")
    path = state_path(start, head, seg_of is not None)
    s = load(path)
    raw = gzip.open(OUT / f"raw-{start}-{head}.csv.gz", "at") if args.raw else None
    cursor = s["cursor"] or start
    window, reqs, t0 = WINDOW, 0, time.time()

    while cursor <= head:
        if args.max_requests and reqs >= args.max_requests:
            print("  stopped at the request limit; re-run to resume")
            break
        upper = min(cursor + window - 1, head)
        logs = rpc("eth_getLogs", [{"address": EXCHANGES + LEGACY,
                                    "topics": [ORDER_FILLED],
                                    "fromBlock": hex(cursor), "toBlock": hex(upper)}])
        if logs is None:
            if window > MIN_WINDOW:
                window = max(MIN_WINDOW, window // 2)
                continue
            print(f"  no answer at block {cursor:,}; state saved, re-run to resume")
            s["cursor"] = cursor; save(path, s)
            raise SystemExit(1)

        fold(logs, s, seg_of, raw)
        cursor = s["cursor"] = upper + 1
        reqs += 1
        if len(logs) < 15_000 and window < WINDOW:
            window = min(WINDOW, window * 2)
        if reqs % 20 == 0:
            save(path, s)
        done = (cursor - start) / max(head - start, 1)
        rate = (cursor - start) / max(time.time() - t0, 1)
        print(f"  {done*100:5.1f}%  block {cursor:,}  {s['fills']:>10,} fills  "
              f"{len(s['pairs']):>9,} pairs  {len(s['addr']):>8,} addrs  "
              f"${s['notional']/1e6:>8,.1f}M  eta {(head-cursor)/max(rate,1)/60:5.1f}m", flush=True)

    save(path, s)
    if raw is not None:
        raw.close()
    print(f"\n  {s['fills']:,} fills, ${s['notional']:,.0f} notional")
    print(f"  {len(s['pairs']):,} counterparty pairs, {len(s['addr']):,} addresses")
    print(f"  wrote {path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
