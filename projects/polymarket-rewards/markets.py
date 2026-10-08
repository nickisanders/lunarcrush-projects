#!/usr/bin/env python3
"""Resolve traded outcome tokens to their markets and reward parameters.

Two things make this harder than it looks, and both were found the hard way.

**Reward status does not survive a market closing.** Across 80 closed markets
sampled on 2026-10-07, none retained `clobRewards` or `rewardsMinSize` on either
API. Reward status is unrecoverable after the fact, so every resolution is
written as a dated snapshot and never overwritten. A fills window can only be
labelled by a snapshot taken while its markets were still open.

**Enumerating the live universe does not work.** Gamma's offset paging stops at
about 2,100 markets, far short of the live set; attributing a one-hour sample
against that enumeration left 98.6% of notional unmatched, almost all of it in
sports markets that were live and simply absent. Resolving the tokens that
actually traded, by id, is both complete and far cheaper.

`--live-snapshot` keeps the enumeration available anyway, because "how much of
the live board pays rewards" is a useful figure in its own right. It is a lower
bound on the universe, not a census, and is labelled as such.

Usage:
    python3 markets.py --from-fills out/fills-94830000-95135000.json.gz
    python3 markets.py --live-snapshot
"""

import argparse
import datetime as dt
import gzip
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
GAMMA = "https://gamma-api.polymarket.com"
# Gamma silently drops ids beyond roughly five per request: a batch of 50
# covered 18 of 50 and a batch of 5 covers all 5. Measured 2026-10-07.
BATCH = 5
UA = "polymarket-rewards/0.1 (research; github.com/nickisanders/lunarcrush-projects)"


# Gamma throttles sustained resolution: a run at full speed fell from 88%
# coverage to about 3%, returning empties rather than an error code, which is
# the failure mode that silently produces a confident wrong answer.
PACE = float(os.environ.get("GAMMA_PACE", "0.35"))


def get(url: str, attempts: int = 6) -> list | dict | None:
    time.sleep(PACE)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 529) and e.code < 500:
                return None
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(min(60, 1.5 * 2 ** attempt))
    return None


def record(m: dict) -> dict:
    rates = m.get("clobRewards") or []
    closed = bool(m.get("closed"))
    daily = 0.0
    for r in rates:
        try:
            daily += float(r.get("rewardsDailyRate") or 0)
        except (TypeError, ValueError):
            pass
    return {
        "condition_id": m.get("conditionId"),
        "slug": m.get("slug"),
        "question": m.get("question"),
        # Paid means the market carries a funded reward entry. rewardsMinSize is
        # set on unpaid markets too, so it cannot be the test.
        # A closed market has had its reward fields stripped, so False here would
        # be a guess, not a reading. Only an open market can be labelled.
        "paid": bool(rates) if not closed else None,
        "daily_rate": daily,
        "min_size": m.get("rewardsMinSize") or 0,
        "max_spread": m.get("rewardsMaxSpread") or 0,
        "maker_fee": m.get("makerBaseFee") or 0,
        "taker_fee": m.get("takerBaseFee") or 0,
        "closed": bool(m.get("closed")),
        "neg_risk": bool(m.get("negRisk")),
        "end": m.get("endDateIso"),
    }


def token_ids(m: dict) -> list[str]:
    toks = m.get("clobTokenIds")
    if isinstance(toks, str):
        try:
            toks = json.loads(toks)
        except json.JSONDecodeError:
            return []
    return [str(t) for t in (toks or [])]


def absorb(rows, markets: dict, by_token: dict) -> None:
    for m in rows or []:
        cid = m.get("conditionId")
        if not cid:
            continue
        markets[cid] = record(m)
        for tid in token_ids(m):
            by_token[tid] = {"condition_id": cid}


def resolve(tokens: list[str]) -> tuple[dict, dict]:
    """Batch first, then retry anything still missing one id at a time.

    A token resolving alone but not in a batch is the normal case here, not an
    error, so the singles pass is what makes coverage complete rather than a
    fallback for failures."""
    markets, by_token = {}, {}
    for i in range(0, len(tokens), BATCH):
        chunk = tokens[i:i + BATCH]
        q = "&".join(f"clob_token_ids={t}" for t in chunk)
        # Gamma's default excludes closed markets, and over any multi-day window
        # most volume sits in markets that have since closed, so both states have
        # to be asked for. A closed market still resolves its name and condition
        # id; what it no longer carries is its reward status.
        absorb(get(f"{GAMMA}/markets?{q}"), markets, by_token)
        absorb(get(f"{GAMMA}/markets?{q}&closed=true"), markets, by_token)
        done = min(i + BATCH, len(tokens))
        if (i // BATCH) % 100 == 0 or done == len(tokens):
            hit = sum(1 for t in tokens[:done] if t in by_token)
            print(f"  batched  {done:>7,}/{len(tokens):,}  {len(markets):>6,} markets  "
                  f"{hit/max(done,1)*100:5.1f}% covered", flush=True)

    missing = [t for t in tokens if t not in by_token]
    print(f"  retrying {len(missing):,} unmatched tokens individually")
    for n, t in enumerate(missing, 1):
        absorb(get(f"{GAMMA}/markets?clob_token_ids={t}"), markets, by_token)
        if t not in by_token:
            absorb(get(f"{GAMMA}/markets?clob_token_ids={t}&closed=true"), markets, by_token)
        if n % 200 == 0 or n == len(missing):
            hit = sum(1 for x in tokens if x in by_token)
            print(f"  singles  {n:>7,}/{len(missing):,}  {len(markets):>6,} markets  "
                  f"{hit/len(tokens)*100:5.1f}% covered", flush=True)

    unresolved = [t for t in tokens if t not in by_token]
    if unresolved:
        print(f"  {len(unresolved):,} tokens have no market on Gamma and stay unattributed")
    return markets, by_token


def live_snapshot() -> tuple[dict, dict]:
    markets, by_token, seen, offset = {}, {}, set(), 0
    while offset < 6000:
        rows = get(f"{GAMMA}/markets?limit=100&closed=false&offset={offset}")
        if not isinstance(rows, list) or not rows:
            break
        fresh = 0
        for m in rows:
            if m.get("id") in seen:
                continue
            seen.add(m.get("id")); fresh += 1
            cid = m.get("conditionId")
            markets[cid] = record(m)
            for tid in token_ids(m):
                by_token[tid] = {"condition_id": cid}
        if fresh == 0:
            break
        offset += 100
    return markets, by_token


def write(markets: dict, by_token: dict, tag: str) -> None:
    OUT.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc)
    snap = {"captured": stamp.isoformat(), "source": tag,
            "markets": markets, "token_market": by_token}
    # Dated copies live in out/history/ alongside the latest run, matching the
    # rest of the repo. Reward status cannot be read back later, so a snapshot
    # not kept on the day is a window that can never be labelled.
    hist = OUT / "history"
    hist.mkdir(parents=True, exist_ok=True)
    path = hist / f"markets-{tag}-{stamp:%Y-%m-%dT%H%M}.json"
    path.write_text(json.dumps(snap))
    (OUT / "markets-latest.json").write_text(json.dumps(snap))
    paid = sum(1 for v in markets.values() if v["paid"])
    budget = sum(v["daily_rate"] for v in markets.values())
    print(f"\n  {len(markets):,} markets, {paid:,} paying rewards "
          f"({paid/max(len(markets),1)*100:.1f}%), {len(by_token):,} tokens")
    print(f"  advertised reward budget across them: {budget:,.0f}/day")
    print(f"  wrote {path.relative_to(HERE)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-fills", type=Path, nargs="+",
                    help="resolve the tokens these files traded")
    ap.add_argument("--top-tokens", type=int, default=0,
                    help="resolve only the N largest by notional (0 = all)")
    ap.add_argument("--live-snapshot", action="store_true")
    args = ap.parse_args()

    if args.from_fills:
        merged: dict[str, float] = {}
        for path in args.from_fills:
            with gzip.open(path, "rt") as f:
                for t, (_n, usd) in json.load(f)["tokens"].items():
                    merged[t] = merged.get(t, 0.0) + usd
        tokens = sorted(merged, key=lambda t: -merged[t])
        total = sum(merged.values())
        if args.top_tokens:
            tokens = tokens[:args.top_tokens]
            covered = sum(merged[t] for t in tokens)
            print(f"  {len(merged):,} tokens traded; resolving the top {len(tokens):,}, "
                  f"which carry {covered/max(total,1)*100:.1f}% of notional")
            print("  the remainder stay unattributed and are excluded from both arms")
        else:
            print(f"  {len(tokens):,} distinct tokens traded")
        write(*resolve(tokens), tag="traded")
    elif args.live_snapshot:
        write(*live_snapshot(), tag="live")
    else:
        ap.error("pass --from-fills or --live-snapshot")


if __name__ == "__main__":
    main()
