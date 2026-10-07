#!/usr/bin/env python3
"""Two common "manufactured attention" signals are partly measuring market cap.

Creator concentration and cross-token account overlap both look like evidence
about a community. Across a population they also track how large the token is,
in opposite directions, for reasons that have nothing to do with manipulation:

- **Cross-token overlap rises with size.** An account that posts about twenty
  tokens posts about the big ones by definition, so the largest tokens inherit
  those accounts whether or not anyone is paying them.
- **Creator concentration falls with size.** A token with forty people talking
  about it will always have its loudest three owning more of the conversation
  than a token with four thousand.

Neither gradient is a finding about either token. Ranking a $150M token against
a $3B one on either number compares the wrong things, and any percentile built
over a mixed-size population inherits the problem.

This measures the size of the effect so it can be corrected for rather than
argued about. The correction is to rank within size bands, which `--bands` does.

Usage:
    LUNARCRUSH_API_KEY=... python3 size_bias.py
    python3 size_bias.py --coins 200 --bands 4
"""

import argparse
import datetime as dt
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://lunarcrush.com/api4"
# Cloudflare fronts this API and rejects the default Python-urllib signature
# with a 403 that reads exactly like throttling. Always send a User-Agent.
UA = "lunarcrush-projects/size-bias"
MIN_POSTS = 25          # below this the signals are noise rather than measurement
SPREAD_ACROSS = 3       # other tokens before an account counts as spread thin
TOP_CREATORS = 3


def get(path: str) -> list | dict:
    key = os.environ.get("LUNARCRUSH_API_KEY")
    if not key:
        raise SystemExit("LUNARCRUSH_API_KEY is not set.")
    req = urllib.request.Request(f"{BASE}{path}",
                                 headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["data"]
        except (urllib.error.HTTPError, OSError):
            time.sleep(2 * 2 ** attempt)
    return []


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def posts_for(topic: str, cache: Path, pace: float) -> list[dict] | None:
    """Cached: the population gets fetched once and reused across reruns."""
    f = cache / f"{topic}.json"
    if f.exists():
        return json.loads(f.read_text())
    rows = get(f"/public/topic/{topic}/posts/v1")
    if not isinstance(rows, list):
        return None
    cache.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows))
    time.sleep(pace)
    return rows


def concentration(posts: list[dict]) -> float | None:
    by = defaultdict(float)
    for p in posts:
        if p.get("creator_id"):
            by[p["creator_id"]] += p.get("interactions_total") or 0
    total = sum(by.values())
    if not total:
        return None
    return sum(sorted(by.values(), reverse=True)[:TOP_CREATORS]) / total


def overlap(posts: list[dict], topic: str, seen: dict) -> float | None:
    by = defaultdict(float)
    for p in posts:
        if p.get("creator_id"):
            by[p["creator_id"]] += p.get("interactions_total") or 0
    total = sum(by.values())
    if not total:
        return None
    spread = sum(v for c, v in by.items() if len(seen[c] - {topic}) >= SPREAD_ACROSS)
    return spread / total


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation without scipy, which this repo does not depend on."""
    rx = {v: i for i, v in enumerate(sorted(xs))}
    ry = {v: i for i, v in enumerate(sorted(ys))}
    a = [rx[v] for v in xs]
    b = [ry[v] for v in ys]
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--coins", type=int, default=200, help="top N by market cap to consider")
    ap.add_argument("--bands", type=int, default=3, help="size bands to split into")
    ap.add_argument("--pace", type=float, default=0.5)
    a = ap.parse_args()

    coins = [c for c in get(f"/public/coins/list/v2?limit={a.coins}")
             if c.get("market_cap")]
    print(f"  {len(coins)} coins with a market cap\n")

    cache = HERE / "out" / "cache"
    universe, missing = {}, 0
    for i, c in enumerate(coins, 1):
        topic = None
        for cand in (slug(c.get("name")), (c.get("symbol") or "").lower()):
            rows = posts_for(cand, cache, a.pace) if cand else None
            if rows and len(rows) >= MIN_POSTS:
                topic = cand
                break
        if not topic:
            missing += 1
            continue
        universe[topic] = {"symbol": c["symbol"], "name": c.get("name"),
                           "mcap": float(c["market_cap"]), "posts": rows}
        print(f"\r  fetched {i}/{len(coins)}, usable {len(universe)}", end="", flush=True)
    print(f"\n  {len(universe)} usable, {missing} without enough conversation\n")

    # Every token is every other token's basket, which is what makes the
    # overlap figure comparable across the population at all.
    seen = defaultdict(set)
    for topic, v in universe.items():
        for p in v["posts"]:
            if p.get("creator_id"):
                seen[p["creator_id"]].add(topic)

    rows = []
    for topic, v in universe.items():
        rows.append({"topic": topic, "symbol": v["symbol"], "mcap": v["mcap"],
                     "posts": len(v["posts"]),
                     "concentration": concentration(v["posts"]),
                     "overlap": overlap(v["posts"], topic, seen)})
    rows = [r for r in rows if r["concentration"] is not None and r["overlap"] is not None]
    rows.sort(key=lambda r: -r["mcap"])

    size = len(rows) // a.bands
    bands = []
    for i in range(a.bands):
        grp = rows[i * size:(i + 1) * size] if i < a.bands - 1 else rows[i * size:]
        bands.append({
            "label": f"band {i+1}" if a.bands != 3 else ["largest", "middle", "smallest"][i],
            "n": len(grp),
            "median_mcap": statistics.median(r["mcap"] for r in grp),
            "median_concentration": statistics.median(r["concentration"] for r in grp),
            "median_overlap": statistics.median(r["overlap"] for r in grp),
        })

    caps = [r["mcap"] for r in rows]
    out = {
        "asOf": dt.date.today().isoformat(),
        "n": len(rows),
        "bands": bands,
        "spearman": {
            "overlap_vs_mcap": round(spearman(caps, [r["overlap"] for r in rows]), 3),
            "concentration_vs_mcap": round(spearman(caps, [r["concentration"] for r in rows]), 3),
        },
        "coins": rows,
    }
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "size_bias.json").write_text(json.dumps(out, indent=2))

    print(f"  {'band':<10}{'median mcap':>14}{'concentration':>16}{'cross-token':>14}{'n':>5}")
    for b in bands:
        print(f"  {b['label']:<10}{b['median_mcap']/1e6:>13,.0f}M"
              f"{b['median_concentration']:>16.0%}{b['median_overlap']:>14.0%}{b['n']:>5}")
    print(f"\n  rank correlation with market cap")
    print(f"    cross-token overlap      {out['spearman']['overlap_vs_mcap']:>+6.2f}")
    print(f"    creator concentration    {out['spearman']['concentration_vs_mcap']:>+6.2f}")
    print(f"\n  Wrote out/size_bias.json")


if __name__ == "__main__":
    main()
