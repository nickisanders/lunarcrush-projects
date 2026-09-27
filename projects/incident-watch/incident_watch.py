#!/usr/bin/env python3
"""Watch for hacks, exploits and freezes being discussed, per coin.

The obvious approaches do not work:

- **Generic topics.** The bare topic "exploit" returns football and Watch Dogs
  2; "hack" is a general-English word carrying 199 million interactions a day.
  Same problem as projects/name-collision, in a different direction.
- **Security accounts.** /public/creator/twitter/:name/posts/v1 resolves, but
  on 2026-09-25 the newest post it held for a well-known investigator was 148
  hours old. Useful for history, not for a watch.
- **Attention spikes.** $ZANO fell 23% on 2026-09-25 while a post reading
  "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO AND fUSD IMMEDIATELY" circulated.
  Its contributor count that hour was 47 against a 50/hour two-day baseline,
  and its sentiment score was 88 out of 100. Every aggregate metric said
  nothing was happening.

What does work is reading the posts for coins that are already moving. This
takes coins down more than DROP in 24 hours, pulls each one's topic posts, and
surfaces any carrying security language, newest first, with links.

It reports what is being said and who said it. It does not decide whether a
claim is true, and neither should you: a post saying a project was drained is
evidence that someone said so, nothing more.

Usage:
    LUNARCRUSH_API_KEY=... python3 incident_watch.py [--drop 10] [--hours 24]
"""

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
API = "https://lunarcrush.com/api4"

# Phrases that describe an incident. Deliberately specific: "hack" alone
# matches "growth hack" and half of gaming, so the single words that survive
# are the ones with no common non-crypto use.
PATTERNS = [
    (r"\bexploit(ed|er)?\b", "exploit"), (r"\bdrain(ed|er|ing)?\b", "drained"),
    (r"\brug(ged|pull|\s?pull)\b", "rug"), (r"\bhacked?\b", "hacked"),
    (r"\bstolen\b|\bstole\b", "stolen"), (r"\bbreach(ed)?\b", "breach"),
    (r"\bvulnerab(le|ility)\b", "vulnerability"), (r"\bpostmortem\b|\bpost-mortem\b", "postmortem"),
    (r"\bpaus(ed|ing)\b|\bhalt(ed|ing)?\b|\bfroze(n)?\b", "paused or halted"),
    (r"\brollback\b|\breorg\b", "rollback"), (r"\bwithdraw(als)? (are |have been )?(dis|suspend)", "withdrawals suspended"),
    (r"\bdo not (buy|trade|deposit|interact)\b|\bcease all\b", "explicit warning"),
    (r"\bcompromis(ed|e)\b", "compromised"), (r"\binsolven(t|cy)\b", "insolvency"),
    (r"\bdepeg(ged)?\b", "depeg"),
]
# A post naming one of these is usually commentary about somebody else.
CONTEXT_NOISE = re.compile(r"\b(game|gaming|football|soccer|match|season|movie|film|goal)\b", re.I)


PROXIMITY = 100   # characters between the coin's name and the incident word
MAX_OTHERS = 1    # distinct other projects a real incident post will name

# Projects named so often in market commentary that mentioning one says
# nothing about whether the post is about them.
UBIQUITOUS = {"BITCOIN", "ETHEREUM", "SOLANA", "BNB", "CRYPTO"}


def other_projects(text: str, symbol: str, name: str, universe: dict[str, str]) -> set[str]:
    """Distinct other projects this post names.

    An incident report is about one project. Commentary is about several. The
    two $NOCK posts on 2026-09-27 name Bitget, Drift, Kelp and Aave while
    describing their losses; $ZANO's warning names only Zano and its own
    stablecoin. Counting the others separates them where proximity cannot,
    because a long post about building something called NOCK repeats the word
    beside every incident word in it.
    """
    mine = {symbol.upper(), re.sub(r"\s*\(.*?\)\s*", " ", name).strip().upper()}
    found = set()
    for sym_, nm in universe.items():
        if sym_ in mine or nm.upper() in mine or nm.upper() in UBIQUITOUS or sym_ in UBIQUITOUS:
            continue
        if re.search(rf"\${re.escape(sym_)}\b", text, re.I):
            found.add(sym_)
        elif len(nm) > 3 and re.search(rf"\b{re.escape(nm)}\b", text, re.I):
            found.add(sym_)
    return found


def coin_positions(text: str, symbol: str, name: str) -> list[int]:
    """Every character offset where this coin is named."""
    spots = [m.start() for m in re.finditer(rf"\${re.escape(symbol)}\b", text, re.I)]
    spots += [m.start() for m in re.finditer(rf"(?<![A-Za-z0-9]){re.escape(symbol)}(?![A-Za-z0-9])", text)]
    clean = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
    if clean and len(clean) > 2:
        spots += [m.start() for m in re.finditer(rf"\b{re.escape(clean)}\b", text, re.I)]
    return sorted(set(spots))


def names_the_coin(text: str, symbol: str, name: str) -> bool:
    """Does the post actually name this coin?

    The topic feed for a coin whose ticker is an ordinary word is full of
    other people's conversation. On the first run $ELF surfaced a post about
    Stable Diffusion models and $LIT one about a neighbour's motion-sensor
    light, both flagged on security wording that had nothing to do with
    either coin. Requiring the ticker with a $ prefix, the bare ticker as a
    standalone uppercase token, or the project's name removes that class
    without dropping the real ones: the $ZANO warning names both.
    """
    if re.search(rf"\${re.escape(symbol)}\b", text, re.I):
        return True
    if re.search(rf"(?<![A-Za-z0-9]){re.escape(symbol)}(?![A-Za-z0-9])", text):
        return True
    clean = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
    return bool(clean) and len(clean) > 2 and re.search(rf"\b{re.escape(clean)}\b", text, re.I) is not None


def get(path: str, tries: int = 3) -> dict:
    key = os.environ["LUNARCRUSH_API_KEY"]
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{API}{path}", headers={
                "Authorization": f"Bearer {key}", "User-Agent": "lunarcrush-projects/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                return {"__err": str(e)}
            time.sleep(2)


def flags(text: str, symbol: str, name: str, universe: dict[str, str] | None = None) -> list[str]:
    """Incident wording that sits next to this coin's name.

    Proximity is what separates a warning from an essay. $ZANO's real warning
    reads "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO", twenty characters
    apart. On 2026-09-27 $NOCK surfaced two posts about a hackathon project of
    that name whose author then listed other people's incidents: 683 and 2,434
    characters long, naming the coin once at the top and reaching "hacks",
    "drained" and "breach" more than a hundred characters later, about Drift,
    Kelp and Bitget. Both name the coin and both carry the wording. Only the
    distance between the two tells them apart.
    """
    spots = coin_positions(text, symbol, name)
    if not spots:
        return []
    if universe:
        others = other_projects(text, symbol, name, universe)
        if len(others) > MAX_OTHERS:
            return []
    hits = []
    for pat, label in PATTERNS:
        for m in re.finditer(pat, text, re.I):
            if min(abs(m.start() - s_) for s_ in spots) <= PROXIMITY:
                hits.append(label)
                break
    return [] if CONTEXT_NOISE.search(text) and len(hits) < 2 else hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", type=float, default=10.0, help="minimum 24h fall, percent")
    ap.add_argument("--hours", type=float, default=24.0, help="only posts this fresh")
    ap.add_argument("--min-mcap", type=float, default=20e6)
    ap.add_argument("--max-coins", type=int, default=25)
    args = ap.parse_args()

    L = pd.DataFrame(get("/public/coins/list/v2?limit=1000")["data"])
    for c in ("market_cap", "percent_change_24h", "volume_24h", "price"):
        L[c] = pd.to_numeric(L.get(c), errors="coerce")
    # LunarCrush lists 12 tickers twice under different ids (KMNO appears as
    # both "Kamino" and "Kamino Finance"). Keep the larger listing per symbol.
    L = L.sort_values("market_cap", ascending=False).drop_duplicates("symbol", keep="first")
    fallers = L[(L["market_cap"] >= args.min_mcap) & (L["volume_24h"] > 5e5)
                & (L["percent_change_24h"] <= -args.drop)
                & (L["symbol"].str.len() >= 2)].nsmallest(args.max_coins, "percent_change_24h")
    print(f"{len(fallers)} coins down {args.drop:.0f}%+ in 24h, over ${args.min_mcap / 1e6:.0f}M\n")

    universe = {str(x["symbol"]).upper(): str(x["name"]) for _, x in L.iterrows()
                if isinstance(x.get("symbol"), str) and len(str(x["symbol"])) >= 3}
    cutoff = time.time() - args.hours * 3600
    found = []
    for _, r in fallers.iterrows():
        sym = r["symbol"]
        d = get(f"/public/topic/{urllib.parse.quote(sym.lower(), safe='')}/posts/v1")
        posts = [] if "__err" in d else (d.get("data") or [])
        hits = []
        for p in posts:
            if (p.get("post_created") or 0) < cutoff:
                continue
            text = f"{p.get('post_title') or ''} {p.get('post_description') or ''}"
            f = flags(text, sym, str(r["name"]), universe)
            if f:
                hits.append({"flags": f, "age_h": (time.time() - p["post_created"]) / 3600,
                             "interactions": p.get("interactions_24h") or 0,
                             "creator": p.get("creator_display_name") or p.get("creator_name"),
                             "text": " ".join(text.split())[:240], "link": p.get("post_link")})
        status = f"{len(hits)} flagged" if hits else ("no posts" if not posts else "clean")
        print(f"  {sym:<10}{r['percent_change_24h']:>+7.1f}%  ${r['market_cap'] / 1e6:>7,.0f}M  {len(posts):>3} posts  {status}")
        if hits:
            hits.sort(key=lambda h: h["age_h"])
            found.append({"symbol": sym, "name": str(r["name"]), "pct24h": float(r["percent_change_24h"]),
                          "mcap": float(r["market_cap"]), "posts": len(posts), "hits": hits})
        time.sleep(0.2)

    print()
    if not found:
        print("Nothing flagged. That is the normal state.")
    for f in found:
        print(f"=== ${f['symbol']} ({f['name']}) {f['pct24h']:+.1f}% in 24h, ${f['mcap'] / 1e6:,.0f}M ===")
        for h in f["hits"][:5]:
            print(f"  [{h['age_h']:>4.1f}h ago] {', '.join(h['flags'])}  ({h['interactions']:,} interactions)")
            print(f"    {h['creator']}: {h['text'][:190]}")
            if h["link"]:
                print(f"    {h['link']}")
        print()

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "incidents.json").write_text(json.dumps({
        "asOf": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "drop": args.drop, "hours": args.hours,
        "scanned": int(len(fallers)), "flagged": found,
    }, indent=2))
    print(f"Wrote {HERE / 'out' / 'incidents.json'}")


if __name__ == "__main__":
    main()
