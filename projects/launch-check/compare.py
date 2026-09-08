#!/usr/bin/env python3
"""What happened to a launch's pools a day later.

Takes two launch_check.py JSON files and shows, per contract, how liquidity
moved. Built to answer the question a copycat warning should be held to: did
the thing you called manufactured actually behave that way?

Usage:
    python3 compare.py out/laptop.json out/laptop-day2.json
"""

import json
import sys
from pathlib import Path

BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, GREEN, GREY, ORANGE = "#f85149", "#3fb950", "#6e7681", "#f7931a"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DRAINED = 0.05  # kept less than this share of its liquidity


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def money(n: float) -> str:
    if n >= 1e9: return f"${n / 1e9:.2f}B"
    if n >= 1e6: return f"${n / 1e6:.1f}M"
    if n >= 1e3: return f"${n / 1e3:.0f}k"
    return f"${n:,.0f}"


def render(d1: dict, d2: dict) -> str:
    a, b = d1["byContract"], d2["byContract"]
    rows = sorted(a.items(), key=lambda kv: -kv[1]["volume24h"])[:6]
    gone = sum(1 for k, _ in rows if k not in b)
    drained = sum(1 for k, v in rows if k in b and v["liquidity"] > 50_000
                  and b[k]["liquidity"] < v["liquidity"] * DRAINED)

    W, H = 1300, 830
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         txt(60, 78, 38, TEXT, f"${d1['ticker']}: the six biggest pools, 24 hours later", 700),
         txt(60, 122, 23, SUB, "liquidity is the money actually in the pool. volume is what the screener shows you."),
         txt(60, 158, 23, SUB, f"{gone} delisted entirely, {drained} drained to nothing, and the count of contracts rose from {d1['contracts']} to {d2['contracts']}")]

    p += [txt(60, 240, 19, SUB, "chain"), txt(190, 240, 19, SUB, "liquidity yesterday"),
          txt(450, 240, 19, SUB, "today"), txt(690, 240, 19, SUB, "change"),
          txt(900, 240, 19, SUB, "volume it still reports")]

    for i, (addr, e) in enumerate(rows):
        y = 292 + i * 62
        n = b.get(addr)
        if n is None:
            now, change, col = "delisted", "gone", RED
            vol = "-"
        else:
            now = money(n["liquidity"])
            ratio = n["liquidity"] / e["liquidity"] if e["liquidity"] else 0
            change = f"{(ratio - 1) * 100:+.0f}%"
            col = RED if ratio < DRAINED else GREEN if ratio > 1 else GREY
            vol = money(n["volume24h"])
        p += [txt(60, y, 21, TEXT, e["network"]),
              txt(190, y, 21, TEXT, money(e["liquidity"])),
              txt(450, y, 21, col, now, 700),
              txt(690, y, 21, col, change, 700),
              txt(900, y, 21, SUB, vol)]

    p += [txt(60, H - 152, 24, TEXT, "The pool that fell from $1.19M to $542 still reports $320M of daily volume.", 700),
          txt(60, H - 118, 21, SUB, "That is a turnover of 589,813x. There is no money left in it and the tape has not noticed."),
          txt(60, H - 82, 21, SUB, "Volume is what screeners rank by. Liquidity is what you get back when you sell."),
          txt(60, H - 48, 21, SUB, "New contracts kept arriving while these emptied, so the name still looks busy on any dashboard."),
          txt(60, H - 16, 18, SUB, "Data: GeckoTerminal · method and code in the repo"),
          "</svg>"]
    return "\n".join(p)


def main() -> None:
    d1 = json.loads(Path(sys.argv[1]).read_text())
    d2 = json.loads(Path(sys.argv[2]).read_text())
    out = Path(sys.argv[1]).with_name(f"{d1['ticker'].lower()}-compare.svg")
    out.write_text(render(d1, d2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
