#!/usr/bin/env python3
"""Which chains are used, and which are only talked about.

Two measures, deliberately chosen.

**Usage is fees paid over 30 days**, from DeFiLlama. Fees are what someone
actually handed over for blockspace, which is harder to inflate than
transaction counts (cheap on purpose for many chains), active addresses
(airdrop farming) or TVL (capital parked, not used). DEX volume and TVL are
collected alongside it so the choice can be argued with.

**Attention is interactions on posts that are verifiably about the chain.**
This is the part that needs care, because chain names collide with ordinary
language worse than token tickers do. `avalanche` returns snow videos, `base`
is a common word, `tron` is a film, `sonic` is a hedgehog, `near` returns an
obituary. Counting a topic's raw posts would rank chains by how ordinary their
name is.

A ticker test alone does not fix it either: it reads 13% on `ethereum` and 5%
on `solana`, because those communities write the chain's name and not its
cashtag, while a trading-heavy community writes `$SEI` constantly. That would
rank chains by cashtag habit.

So one filter is applied identically to every chain. A post counts when it
names the chain or its ticker AND carries a crypto term from a fixed
vocabulary. Attention is then the interactions on the posts that survive.

What this cannot say: it is one snapshot rather than a long window, it reads
English-language social data, and a chain whose users talk elsewhere will look
quiet here. BSC is the obvious case to be careful with.

Usage: python3 chain_hype.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LLAMA = "https://api.llama.fi"
LC = "https://lunarcrush.com/api4/public"

# One vocabulary for every chain. A post has to name the chain and sound like
# crypto, or `base` alone sweeps in every other meaning of the word.
CRYPTO = re.compile(
    r"\$[a-z]{2,6}\b|defi|blockchain|onchain|on-chain|crypto|wallet|token|"
    r"stablecoin|liquidity|tvl|validator|staking|staked|gas fee|mainnet|"
    r"testnet|airdrop|dex|bridge|rollup|layer ?2|l2\b|smart contract", re.I)

# chain, DeFiLlama slug, LunarCrush topic, pattern that names the chain.
# The topic is the one that survived verification, not the obvious guess:
# `avax` over `avalanche`, `polygon-ecosystem-token` over `polygon`.
CHAINS = [
    ("Ethereum", "ethereum", "ethereum", r"ethereum|\$eth\b"),
    ("Solana", "solana", "solana", r"solana|\$sol\b"),
    ("Base", "base", "base-chain", r"\bbase\b"),
    ("BSC", "bsc", "$bnb", r"\bbnb\b|binance smart|\$bnb\b"),
    ("Arbitrum", "arbitrum", "arbitrum", r"arbitrum|\$arb\b"),
    ("Avalanche", "avalanche", "avax", r"avalanche|\$avax\b"),
    ("Polygon", "polygon", "polygon-ecosystem-token", r"polygon|\$pol\b|\$matic\b"),
    ("Optimism", "optimism", "optimism", r"optimism|\$op\b"),
    ("Tron", "tron", "tron", r"\btron\b|\$trx\b"),
    ("Sui", "sui", "$sui", r"\bsui\b|\$sui\b"),
    ("Aptos", "aptos", "aptos", r"aptos|\$apt\b"),
    ("Sei", "sei", "sei-network", r"\bsei\b|\$sei\b"),
    ("Hyperliquid L1", "hyperliquid-l1", "hyperliquid", r"hyperliquid|\$hype\b"),
    ("Near", "near", "$near", r"near protocol|\$near\b"),
]


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "chain-hype/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=90))


def usage() -> dict:
    tvl = {c["name"]: c.get("tvl") or 0 for c in get(f"{LLAMA}/v2/chains")}
    out = {}
    for name, slug, _, _ in CHAINS:
        row = {"tvl": tvl.get(name, 0)}
        for kind, key in (("fees", "fees30d"), ("dexs", "dex30d")):
            try:
                d = get(f"{LLAMA}/overview/{kind}/{slug}"
                        "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
                row[key] = d.get("total30d") or 0
            except Exception:
                row[key] = 0
            time.sleep(0.4)
        out[name] = row
    return out


def attention(key: str) -> dict:
    head = {"Authorization": f"Bearer {key}", "User-Agent": "chain-hype/1.0"}
    out = {}
    for name, _, topic, pat in CHAINS:
        try:
            posts = get(f"{LC}/topic/{urllib.parse.quote(topic)}/posts/v1", head).get("data") or []
        except Exception:
            posts = []
        names = re.compile(pat, re.I)
        text = lambda x: (x.get("post_title") or "") + " " + (x.get("post_description") or "")
        hits = [x for x in posts if names.search(text(x)) and CRYPTO.search(text(x))]
        out[name] = {"topic": topic, "posts": len(posts), "on_topic": len(hits),
                     "interactions": sum(x.get("interactions_total") or 0 for x in hits)}
        time.sleep(0.3)
    return out


def main() -> None:
    import os
    key = os.environ["LUNARCRUSH_API_KEY"]
    use, att = usage(), attention(key)
    rows = []
    for name, *_ in CHAINS:
        u, a = use.get(name), att.get(name)
        if not u or not a:
            continue
        rows.append({"chain": name, **u, **a})
    ti = sum(r["interactions"] for r in rows) or 1
    tf = sum(r["fees30d"] for r in rows) or 1
    for r in rows:
        r["att_share"] = r["interactions"] / ti
        r["fee_share"] = r["fees30d"] / tf
        r["ratio"] = r["att_share"] / r["fee_share"] if r["fee_share"] else None
    rows.sort(key=lambda r: -(r["ratio"] or 0))

    print(f"  {'chain':16}{'attention':>11}{'fees':>9}{'ratio':>8}")
    for r in rows:
        print(f"  {r['chain']:16}{r['att_share']*100:>10.1f}%{r['fee_share']*100:>8.1f}%"
              f"{r['ratio']:>8.1f}")
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(rows, open(HERE / "out" / "chain-hype.json", "w"), indent=1)
    print(f"\n  wrote out/chain-hype.json")


if __name__ == "__main__":
    main()
