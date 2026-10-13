#!/usr/bin/env python3
"""The accounts that appear across the most tokens, and what they actually post.

"Does this account also post about everything else" is one of the three signals
behind a manufactured-attention verdict, and it sounds unambiguous. It is not.
One account turning up in fifty token conversations can mean two unrelated
things, and the number alone cannot tell them apart:

- **A list poster.** One post naming twenty-eight tickers puts the account
  inside dozens of conversations at once. That is somebody writing a comparison.
- **A serial poster.** Fifty separate single-token posts, each on the same
  template. That is somebody working through a catalogue.

This measures how much of each there is, by counting the distinct tickers in
every post from the accounts that reach the most tokens.

The universe is fetched fresh rather than read from a saved scan, so anyone with
a key can reproduce it. Topics are verified before use: short tickers collide
with ordinary English, and a baseline carrying conversation about sand, cake and
bats is not a baseline. A topic counts when its posts are about a token and so
are its loudest accounts, because concentration is computed from those.

Usage:
    LUNARCRUSH_API_KEY=... python3 amplifiers.py
    python3 amplifiers.py --coins 150 --top 40
"""

import argparse
import datetime as dt
import json
import os
import re
import statistics as st
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CACHE = OUT / "cache"
BASE = "https://lunarcrush.com/api4"
UA = "lunarcrush-projects/amplifier-census"
TICKER = re.compile(r"\$[A-Za-z][A-Za-z0-9]{1,6}\b")
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "BUSD",
          "USDS", "SUSDE", "USDTB", "XAUT", "PAXG", "STETH", "WSTETH", "WBTC", "WETH"}
# Too generic to identify a project by; "Protocol" matches half the market.
STOP = {"protocol", "network", "finance", "token", "coin", "chain", "labs", "the",
        "foundation", "project", "io", "ai", "dao", "exchange", "swap", "capital"}
MIN_POSTS = 25
MIN_ON_TOPIC = 0.10
MIN_TOP3_ON_TOPIC = 0.40


def get(path, attempts=6, pace=0.25):
    """None after exhaustion rather than raising: a census that dies on token 90
    should still be able to report what it has."""
    time.sleep(pace)
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {os.environ['LUNARCRUSH_API_KEY']}",
                 "User-Agent": UA})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 529) and e.code < 500:
                return None
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(min(60, 1.5 * 2 ** attempt))
    return None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def name_terms(name, symbol):
    words = re.split(r"[^A-Za-z0-9]+", str(name or "").lower())
    return [w for w in words
            if len(w) >= 4 and w not in STOP and w != str(symbol or "").lower()]


def on_topic(text, terms):
    if TICKER.search(text):
        return True
    low = text.lower()
    return any(re.search(rf"\b{re.escape(t)}\b", low) for t in terms)


def posts_for(topic, ttl):
    """Cached, because a re-run should cost nothing and the verification pass
    reads the same posts the census does."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{urllib.parse.quote(topic, safe='')}.json"
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return json.loads(path.read_text())
    d = get(f"/public/topic/{urllib.parse.quote(topic)}/posts/v1")
    if d is None:
        return None
    rows = d.get("data") or []
    path.write_text(json.dumps(rows))
    return rows


def verify(symbol, name, ttl):
    """Most specific candidate first: a colliding ticker is usually fixed by a
    longer name, and $TICKER beats the bare symbol."""
    terms = name_terms(name, symbol)
    for cand in dict.fromkeys([slug(name), f"${str(symbol).lower()}", str(symbol).lower()]):
        if not cand:
            continue
        rows = posts_for(cand, ttl)
        if not rows:
            continue
        texts = [(r.get("creator_id") or r.get("creator_name"),
                  r.get("post_title") or "", r.get("interactions_24h") or 0)
                 for r in rows]
        texts = [t for t in texts if t[1].strip()]
        if len(rows) < MIN_POSTS or not texts:
            continue
        share = sum(1 for _, s, _ in texts if on_topic(s, terms)) / len(texts)
        agg = defaultdict(lambda: [0, 0])
        for cid, s, i in texts:
            a = agg[cid]
            a[0] += i
            if on_topic(s, terms):
                a[1] += i
        top3 = sorted(agg.values(), key=lambda v: -v[0])[:3]
        top_on = sum(v[1] for v in top3) / max(sum(v[0] for v in top3), 1)
        if share >= MIN_ON_TOPIC and top_on >= MIN_TOP3_ON_TOPIC:
            return cand, rows
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coins", type=int, default=200, help="universe size by market cap")
    ap.add_argument("--top", type=int, default=40, help="how many amplifiers to profile")
    ap.add_argument("--ttl", type=int, default=6 * 3600)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    coins = (get("/public/coins/list/v2?limit=1000") or {}).get("data") or []
    coins = [c for c in coins
             if str(c.get("symbol", "")).upper() not in PEGGED
             and float(c.get("market_cap") or 0) > 0][:a.coins]
    print(f"  universe: {len(coins)} coins")

    topics, dropped = {}, 0
    for i, c in enumerate(coins, 1):
        chosen, rows = verify(c.get("symbol"), c.get("name"), a.ttl)
        if chosen:
            topics[chosen] = rows
        else:
            dropped += 1
        if i % 25 == 0 or i == len(coins):
            print(f"  verified {i}/{len(coins)}  kept {len(topics)}  dropped {dropped}",
                  flush=True)
    print(f"\n  {len(topics)} verified topics, {dropped} rejected")

    reach = defaultdict(set)
    posts_by = defaultdict(list)
    for topic, rows in topics.items():
        for r in rows:
            cid = r.get("creator_id") or r.get("creator_name")
            text = (r.get("post_title") or "").strip()
            if not cid or not text:
                continue
            reach[cid].add(topic)
            posts_by[cid].append(text)

    multi = {c: t for c, t in reach.items() if len(t) >= 2}
    ranked = sorted(reach.items(), key=lambda kv: -len(kv[1]))[:a.top]

    buckets, profiles, total = Counter(), [], 0
    for cid, t in ranked:
        counts = [len(set(TICKER.findall(p))) for p in posts_by[cid]]
        if not counts:
            continue
        total += len(counts)
        for n in counts:
            buckets["1" if n <= 1 else "2" if n == 2 else "3-7" if n <= 7 else "8+"] += 1
        profiles.append({
            "topics": len(t), "posts": len(counts),
            "median_tickers": st.median(counts),
            # A post naming three or more tokens reaches them all at once, which
            # is a different act from writing about one.
            "list_share": round(sum(1 for n in counts if n >= 3) / len(counts), 3),
        })

    result = {
        "captured": dt.datetime.now(dt.timezone.utc).isoformat(),
        "universe": len(coins), "verified_topics": len(topics), "rejected": dropped,
        "accounts_in_2_plus": len(multi),
        "max_topics": len(ranked[0][1]) if ranked else 0,
        "median_topics_multi": st.median([len(t) for t in multi.values()]) if multi else 0,
        "profiled": len(profiles), "posts": total,
        "buckets": {k: buckets[k] for k in ("1", "2", "3-7", "8+")},
        "profiles": profiles,
    }
    (OUT / "amplifiers.json").write_text(json.dumps(result, indent=2))

    print(f"\n  accounts in 2+ topics: {result['accounts_in_2_plus']:,}")
    print(f"  most topics reached by one account: {result['max_topics']}")
    print(f"  median for accounts in 2+: {result['median_topics_multi']:.0f}")
    print(f"\n  across {total:,} posts from the top {len(profiles)} accounts:")
    for k in ("1", "2", "3-7", "8+"):
        print(f"    names {k:<4} {buckets[k]:>5}  {buckets[k]/max(total,1)*100:5.1f}%")
    print(f"\n  wrote {(OUT/'amplifiers.json').relative_to(HERE)}")


if __name__ == "__main__":
    main()
