#!/usr/bin/env python3
"""The same contracts ranked two ways: by volume, and by distinct wallets.

Screeners rank by volume. On $LAPTOP's launch day that put the genuine contract
9th out of 42. Ranking the identical set by how many distinct wallets traded it
put the genuine contract 1st, six times clear of the next.

Usage: python3 rank_chart.py out/laptop-day3-wide.json <real-contract-address>
"""

import json
import sys
from pathlib import Path

BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, GREEN, GREY = "#f85149", "#3fb950", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    body = esc(s)
    if weight >= 700 and " " in str(s):
        # librsvg loses the inter-word space at bold weights.
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            dx = size * (0.45 if prev.endswith("%") else 0.30)
            parts.append(f'<tspan dx="{dx:.2f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def money(n: float) -> str:
    if n >= 1e9: return f"${n / 1e9:.2f}B"
    if n >= 1e6: return f"${n / 1e6:.1f}M"
    if n >= 1e3: return f"${n / 1e3:.0f}k"
    return f"${n:,.0f}"


def render(s: dict, real: str) -> str:
    bc = {k: v for k, v in s["byContract"].items() if not v.get("implausible")}
    byv = sorted(bc.items(), key=lambda kv: -kv[1]["volume24h"])
    byw = sorted(bc.items(), key=lambda kv: -kv[1]["traders24h"])
    rv = [k for k, _ in byv].index(real) + 1
    rw = [k for k, _ in byw].index(real) + 1
    n = len(bc)

    W, H = 1300, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 76, 39, TEXT, "Same contracts. Two rankings.", 700))
    o.append(txt(60, 114, 20, SUB,
                 f"${s['ticker']} on its announced launch day. The genuine contract "
                 f"ranked {rv}th of {n} by volume, 1st by wallets."))

    cols = [(60, "RANKED BY 24H VOLUME", "what every screener shows you", byv,
             lambda e: money(e["volume24h"]), lambda e: f"{e['traders24h']:,} wallets"),
            (680, "RANKED BY DISTINCT WALLETS", "how many people actually traded it", byw,
             lambda e: f"{e['traders24h']:,}", lambda e: money(e["volume24h"]) + " vol")]

    for x, head, sub, rows, main, side in cols:
        o.append(txt(x, 176, 18, TEXT, head, 700))
        o.append(txt(x, 202, 16, SUB, sub))
        y = 236
        for i, (addr, e) in enumerate(rows[:9], 1):
            is_real = addr == real
            bar = GREEN if is_real else GREY
            o.append(f'<rect x="{x}" y="{y}" width="560" height="46" fill="{PANEL}" rx="4"/>')
            if is_real:
                o.append(f'<rect x="{x}" y="{y}" width="560" height="46" fill="#0e2f1c" rx="4"/>')
                o.append(f'<rect x="{x}" y="{y}" width="4" height="46" fill="{bar}" rx="2"/>')
            o.append(txt(x + 20, y + 30, 17, GREEN if is_real else GREY, f"{i}", 700))
            o.append(txt(x + 48, y + 30, 16, TEXT if is_real else SUB,
                         (addr[:14] + "…"), 700 if is_real else 400))
            o.append(txt(x + 400, y + 30, 16, TEXT if is_real else SUB, main(e), 700 if is_real else 400, "end"))
            o.append(txt(x + 545, y + 30, 14, GREY, side(e), anchor="end"))
            y += 52

    o.append(f'<rect x="60" y="736" width="1180" height="86" fill={chr(34)}{PANEL}{chr(34)} rx="6"/>')
    o.append(txt(84, 770, 18, TEXT,
                 "A few addresses can trade a token with themselves all day. Tens of thousands of wallets is harder.", 700))
    o.append(txt(84, 798, 17, SUB,
                 "The genuine contract holds 42% of every wallet trading this name, at $552 each, on 2.5% of the volume."))

    o.append(txt(60, 866, 16, GREY,
                 "Source: GeckoTerminal, 2026-09-09. Contract identity supplied by its publisher, not derived onchain."))
    o.append(txt(1240, 866, 16, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = Path(sys.argv[1])
    real = sys.argv[2].lower()
    out = src.parent / "laptop-ranks.svg"
    out.write_text(render(json.loads(src.read_text()), real))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
