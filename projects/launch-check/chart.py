#!/usr/bin/env python3
"""Chart a launch check. Reads the JSON written by launch_check.py.

Usage: python3 chart.py out/laptop.json
"""

import json
import sys
from pathlib import Path

BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, ORANGE, GREY = "#f85149", "#f7931a", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def money(n: float) -> str:
    if n >= 1e9: return f"${n / 1e9:.2f}B"
    if n >= 1e6: return f"${n / 1e6:.1f}M"
    if n >= 1e3: return f"${n / 1e3:.0f}k"
    return f"${n:,.0f}"


def render(s: dict) -> str:
    W, H = 1300, 920
    top = sorted(s["byContract"].items(), key=lambda kv: -kv[1]["volume24h"])[:5]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         txt(60, 78, 38, TEXT, f"${s['ticker']} is trending. There are {s['contracts']} of them.", 700),
         txt(60, 122, 23, SUB, f"every distinct contract carrying this ticker, across {', '.join(s['networks'][:6])}"),
         txt(60, 158, 23, SUB, "nothing in the data identifies which, if any, is official")]

    # headline panels
    cards = [(60, str(s["contracts"]), "separate contracts", "share this name", RED),
             (470, money(s["totalLiquidity"]), "total liquidity", "across all of them", GREY),
             (880, money(s["totalVolume24h"]), "reported 24h volume", f"{s['combinedTurnover']:.0f}x the liquidity", ORANGE)]
    for x, big, lab, sub, col in cards:
        p += [f'<rect x="{x}" y="205" width="360" height="180" rx="14" fill="{PANEL}"/>',
              txt(x + 30, 300, 62, col, big, 800),
              txt(x + 30, 336, 22, TEXT, lab, 700),
              txt(x + 30, 364, 19, SUB, sub)]

    p += [txt(60, 450, 25, TEXT, "The five busiest, and what their volume implies", 700),
          txt(60, 484, 20, SUB, "turnover is 24h volume divided by pool depth. healthy pools turn over a few times a day.")]
    p += [txt(60, 530, 19, SUB, "chain"), txt(210, 530, 19, SUB, "liquidity"),
          txt(390, 530, 19, SUB, "24h volume"), txt(600, 530, 19, SUB, "turnover"),
          txt(760, 530, 19, SUB, "volume per trading wallet")]
    for i, (addr, e) in enumerate(top):
        y = 570 + i * 40
        col = RED if e["turnover"] >= 20 else TEXT
        p += [txt(60, y, 20, TEXT, e["network"]),
              txt(210, y, 20, TEXT, money(e["liquidity"])),
              txt(390, y, 20, TEXT, money(e["volume24h"])),
              txt(600, y, 20, col, f"{e['turnover']:.0f}x", 700),
              txt(760, y, 20, col, f"${e['volumePerWallet']:,.0f}", 700)]

    p += [txt(60, H - 96, 23, TEXT, "Volume is the easiest number on a chart to manufacture, and it is what screeners rank by.", 700),
          txt(60, H - 62, 21, SUB, "Real retail does not average six figures per wallet on a token hours old."),
          txt(60, H - 34, 21, SUB, "This cannot tell you which contract is official. Neither can a screener. That is the point."),
          txt(60, H - 8, 18, SUB, "Data: GeckoTerminal · no API key required · method and code in the repo"),
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "out/laptop.json")
    s = json.loads(src.read_text())
    out = src.with_suffix(".svg")
    out.write_text(render(s))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
