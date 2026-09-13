#!/usr/bin/env python3
"""Where did the attention go? Crypto's conversation by narrative, 2024 to 2026.

projects/polygon found every Ethereum scaling chain lost its seat in crypto's
top-20 conversation between early 2024 and mid 2026. This asks what took the
seats: which narratives' share of the crowd rose, and which fell.

Method: for each day, every coin's active contributors are counted toward
each narrative tag it carries, then divided by the day's total across all
coins. A coin tagged both layer-1 and defi counts toward both, so shares do
not sum to 100%; each is read as "share of the crowd touching a coin tagged
X". Tags are LunarCrush's current categories, applied retroactively, which
is fine for a 2024-to-2026 comparison since these narratives all existed by
2024.

Same universe hygiene as projects/top-ten: pegged assets removed, per-day
name collisions removed, single-character tickers dropped. Contributors, not
interactions, for the reason given in projects/polygon.

Usage: python3 shift.py   (reads tags.json, a symbol-to-categories map from coins/list/v2)
"""

import datetime as dt
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "social-price-backtest" / "data" / "raw"
TAGS_SRC = HERE / "tags.json"  # symbol -> comma-separated categories, from coins/list/v2
COLLISION_X = 100
NARRATIVES = {
    "layer-2": "Layer 2s", "layer-1": "Layer 1s", "meme": "Memecoins",
    "ai": "AI", "ai-agents": "AI agents", "defi": "DeFi", "gaming": "Gaming",
    "nft": "NFT", "depin": "DePIN", "real-world-assets": "RWA",
    "privacy": "Privacy", "zk": "ZK", "exchange-tokens": "Exchange tokens",
    "pump-fun": "pump.fun", "perpetuals": "Perps", "bitcoin-ecosystem": "Bitcoin ecosystem",
}
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE", "BUSD",
          "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG", "WBTC", "WETH",
          "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC", "FRAX",
          "CRVUSD", "GUSD", "LUSD", "USDP", "EURC", "MSOL", "CBETH", "WBETH"}
THEN, NOW = ("2024-01", "2024-03"), ("2026-05", "2026-07")


def main() -> None:
    tags = {sym: {t.strip() for t in cats.split(",") if t.strip()}
            for sym, cats in json.loads(TAGS_SRC.read_text()).items()}

    day = defaultdict(list)
    for f in sorted(glob.glob(str(RAW / "*.json"))):
        d = json.load(open(f))
        sym = d["coin"]["symbol"]
        if sym in PEGGED or len(sym) < 2:
            continue
        for r in d["rows"]:
            c, it, mc = r.get("contributors_active") or 0, r.get("interactions") or 0, r.get("market_cap") or 0
            if c > 0 and mc > 0:
                day[dt.datetime.fromtimestamp(r["time"], dt.UTC).date()].append((sym, c, it / mc))

    rows = []
    for dd in sorted(day):
        med = np.median([x[2] for x in day[dd]])
        clean = [(s, c) for s, c, ratio in day[dd] if ratio <= med * COLLISION_X]
        total = sum(c for _, c in clean)
        if total == 0:
            continue
        share = defaultdict(float)
        for s, c in clean:
            for t in tags.get(s, ()):
                if t in NARRATIVES:
                    share[t] += c
        by_coin = {s: c for s, c in clean}
        ranked = sorted(clean, key=lambda x: -x[1])
        rows.append({"date": pd.Timestamp(dd), **{t: share[t] / total for t in NARRATIVES},
                     "_btc": by_coin.get("BTC", 0) / total, "_eth": by_coin.get("ETH", 0) / total,
                     "_sol": by_coin.get("SOL", 0) / total,
                     "_top3": sum(c for _, c in ranked[:3]) / total,
                     "_top10": sum(c for _, c in ranked[:10]) / total,
                     "_total": total, "_ncoins": len(clean)})
    df = pd.DataFrame(rows).set_index("date")
    m = df.resample("ME").mean()
    m.index = m.index.strftime("%Y-%m")

    then = m.loc[THEN[0]:THEN[1]].mean()
    now = m.loc[NOW[0]:NOW[1]].mean()
    out = pd.DataFrame({"then": then, "now": now}).loc[list(NARRATIVES)]
    out["change_pp"] = (out["now"] - out["then"]) * 100
    out["change_rel"] = out["now"] / out["then"] - 1
    out = out.sort_values("change_pp")

    print(f"Share of daily active contributors touching a coin tagged X\n"
          f"then = {THEN[0]} to {THEN[1]}, now = {NOW[0]} to {NOW[1]}\n")
    print(f"{'narrative':<20}{'then':>8}{'now':>8}{'change':>10}{'relative':>10}")
    for t, r in out.iterrows():
        print(f"{NARRATIVES[t]:<20}{r['then'] * 100:>7.1f}%{r['now'] * 100:>7.1f}%"
              f"{r['change_pp']:>+9.1f}pp{r['change_rel'] * 100:>+9.0f}%")

    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "shift.json").write_text(json.dumps({
        "then": list(THEN), "now": list(NOW),
        "narratives": [{"tag": t, "label": NARRATIVES[t], "then": float(r["then"]),
                        "now": float(r["now"]), "changePp": float(r["change_pp"]),
                        "changeRel": float(r["change_rel"])} for t, r in out.iterrows()],
        "monthly": {t: {k: float(v) for k, v in m[t].items()} for t in NARRATIVES},
    }, indent=2))
    conc = pd.DataFrame({"then": then, "now": now}).loc[["_btc", "_eth", "_sol", "_top3", "_top10", "_total", "_ncoins"]]
    print(f"\nCONCENTRATION: share of all daily contributors")
    for k, lab in (("_btc", "BTC"), ("_eth", "ETH"), ("_sol", "SOL"), ("_top3", "top 3 coins"), ("_top10", "top 10 coins")):
        print(f"  {lab:<14}{conc.loc[k, 'then'] * 100:>6.1f}%  ->{conc.loc[k, 'now'] * 100:>6.1f}%   {(conc.loc[k, 'now'] - conc.loc[k, 'then']) * 100:>+5.1f}pp")
    print(f"  {'outside top 10':<14}{(1 - conc.loc['_top10', 'then']) * 100:>6.1f}%  ->{(1 - conc.loc['_top10', 'now']) * 100:>6.1f}%")
    print(f"  total contributors/day: {conc.loc['_total', 'then']:,.0f} -> {conc.loc['_total', 'now']:,.0f}  "
          f"({conc.loc['_total', 'now'] / conc.loc['_total', 'then'] * 100 - 100:+.0f}%)   "
          f"coins tracked: {conc.loc['_ncoins', 'then']:.0f} -> {conc.loc['_ncoins', 'now']:.0f}")
    payload = json.loads((HERE / "out" / "shift.json").read_text())
    payload["concentration"] = {k.lstrip("_"): {"then": float(conc.loc[k, "then"]), "now": float(conc.loc[k, "now"])} for k in conc.index}
    payload["top3Monthly"] = {k: float(v) for k, v in m["_top3"].items()}
    payload["top10Monthly"] = {k: float(v) for k, v in m["_top10"].items()}
    (HERE / "out" / "shift.json").write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {HERE / 'out' / 'shift.json'}")


if __name__ == "__main__":
    main()
