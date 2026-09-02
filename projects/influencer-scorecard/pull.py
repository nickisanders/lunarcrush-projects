#!/usr/bin/env python3
"""Cache what named crypto accounts posted, and the prices to score them against.

Three steps, all resumable: anything already in data/ is skipped, so an
interrupted run costs nothing to restart.

1. Build the creator universe from the TOPIC creator lists of the largest
   coins. Deliberately not /public/creators/list/v1, which is LunarCrush's
   whole-platform ranking and returns Netflix, ESPN and Red Bull.
2. Fetch each creator's post history (about 180 posts, months to a year back).
3. Fetch daily prices for every coin those posts actually mention.

Usage:
    python3 pull.py [--coins 30] [--creators-per-coin 10]
"""

import argparse
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BASE = "https://lunarcrush.com/api4"
UA = "lunarcrush-projects-influencer-scorecard/0.1"


def load_key() -> str:
    for path in (HERE / ".env", HERE / ".." / "altrank-movers" / ".env"):
        try:
            for line in path.read_text().splitlines():
                if line.startswith("LUNARCRUSH_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
        except OSError:
            continue
    key = os.environ.get("LUNARCRUSH_API_KEY")
    if not key:
        raise SystemExit("LUNARCRUSH_API_KEY not set and no .env found")
    return key


def get(path: str, key: str, retries: int = 3):
    for attempt in range(retries):
        req = Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
        try:
            with urlopen(req, timeout=60) as r:
                body = json.loads(r.read())
            time.sleep(0.7)  # stay under 100 requests/min
            return body.get("data")
        except HTTPError as e:
            if e.code == 429:
                time.sleep(20)
                continue
            if e.code in (404, 500):
                return None
            raise
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", type=int, default=30, help="how many top coins seed the creator universe")
    ap.add_argument("--creators-per-coin", type=int, default=10)
    args = ap.parse_args()
    key = load_key()
    (DATA / "creators").mkdir(parents=True, exist_ok=True)
    (DATA / "prices").mkdir(parents=True, exist_ok=True)

    coins = get("/public/coins/list/v2?sort=market_cap_rank&limit=1000&page=0", key) or []
    (DATA / "coins.json").write_text(json.dumps(
        [{"id": c["id"], "symbol": c["symbol"], "name": c["name"], "topic": c.get("topic"),
          "market_cap": c.get("market_cap"), "rank": c.get("market_cap_rank")} for c in coins]))
    by_symbol = {c["symbol"].upper(): c for c in coins}
    print(f"{len(coins)} coins cached")

    # 1. creator universe, from the coins' own topic creator lists
    seen: dict[str, str] = {}
    for c in coins[: args.coins]:
        if not c.get("topic"):
            continue
        topic = quote(c["topic"], safe="")
        for cr in (get(f"/public/topic/{topic}/creators/v1", key) or [])[: args.creators_per_coin]:
            # Topic creator records carry no creator_network field. The
            # network is the prefix of creator_id ("twitter::1378663163...").
            name = cr.get("creator_name")
            net = str(cr.get("creator_id") or "").split("::")[0]
            # Only twitter posts carry the $TICKER convention this scores.
            if name and net == "twitter" and name not in seen:
                seen[name] = net
    print(f"{len(seen)} distinct creators across the top {args.coins} coins")

    # 2. their posts
    for i, (name, net) in enumerate(sorted(seen.items()), 1):
        out = DATA / "creators" / f"{net}__{name}.json"
        if out.exists():
            continue
        posts = get(f"/public/creator/{quote(net, safe='')}/{quote(name, safe='')}/posts/v1", key)
        if not posts:
            print(f"  [{i}/{len(seen)}] {name}: no posts")
            continue
        out.write_text(json.dumps({"creator_name": name, "network": net, "posts": posts}))
        print(f"  [{i}/{len(seen)}] {name}: {len(posts)} posts")

    # 3. prices for every coin actually mentioned, so the fetch is bounded by
    #    what the posts talk about rather than the whole market
    import re
    mentioned = set()
    for f in (DATA / "creators").glob("*.json"):
        blob = json.loads(f.read_text())
        for p in blob["posts"]:
            for t in re.findall(r"\$([A-Za-z0-9]{2,10})\b", str(p.get("post_title") or "")):
                if t.upper() in by_symbol:
                    mentioned.add(t.upper())
    print(f"\n{len(mentioned)} distinct coins mentioned; fetching prices")
    for i, sym in enumerate(sorted(mentioned), 1):
        out = DATA / "prices" / f"{sym}.json"
        if out.exists():
            continue
        rows = get(f"/public/coins/{by_symbol[sym]['id']}/time-series/v2?bucket=day&interval=1y", key)
        if not rows:
            continue
        out.write_text(json.dumps({"symbol": sym, "rows": [
            {"time": r["time"], "close": r.get("close")} for r in rows]}))
        if i % 25 == 0:
            print(f"  [{i}/{len(mentioned)}]")
    # 4. A control set: coins nobody in the sample mentioned. Without these the
    #    only available baseline is "a different coin someone else mentioned",
    #    which cannot answer whether being mentioned matters at all.
    import random
    unmentioned = [c for c in coins[:600] if c["symbol"].upper() not in mentioned]
    random.Random(7).shuffle(unmentioned)
    control = unmentioned[:150]
    (DATA / "control.json").write_text(json.dumps([c["symbol"].upper() for c in control]))
    print(f"\nfetching {len(control)} control coins that nobody mentioned")
    for i, c in enumerate(control, 1):
        out = DATA / "prices" / f"{c['symbol'].upper()}.json"
        if out.exists():
            continue
        rows = get(f"/public/coins/{c['id']}/time-series/v2?bucket=day&interval=1y", key)
        if not rows:
            continue
        out.write_text(json.dumps({"symbol": c["symbol"].upper(), "rows": [
            {"time": r["time"], "close": r.get("close")} for r in rows]}))
        if i % 25 == 0:
            print(f"  [{i}/{len(control)}]")

    # BTC is the benchmark and may not be mentioned by anyone
    if not (DATA / "prices" / "BTC.json").exists():
        rows = get(f"/public/coins/{by_symbol['BTC']['id']}/time-series/v2?bucket=day&interval=1y", key)
        (DATA / "prices" / "BTC.json").write_text(json.dumps({"symbol": "BTC", "rows": [
            {"time": r["time"], "close": r.get("close")} for r in rows]}))
    print("done")


if __name__ == "__main__":
    main()
