#!/usr/bin/env python3
"""Chart: one coin's price and its seat in the conversation, month by month.

Usage: python3 chart.py out/zec.json ["optional title"]
"""

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER, ORANGE = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922", "#f7931a"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    body = esc(s)
    if weight >= 700 and " " in str(s):
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            dx = size * (0.45 if prev.endswith("%") else 0.30)
            parts.append(f'<tspan dx="{dx:.2f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def render(d: dict, title: str | None = None) -> str:
    W, H = 1300, 900
    m = [x for x in d["monthly"] if x["rank"] is not None]
    lv = d["live"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, title or f"${d['symbol']} was left for dead. It's #{lv['crowdRank']} in crypto conversation.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"{d['name']}'s price and its seat in the conversation, month by month, 2020 to today."))

    px0, px1 = 90, 1240
    n = len(m)
    def X(i): return px0 + (px1 - px0) * i / (n - 1)

    # Top: price, log scale.
    py0, py1 = 180, 420
    closes = [x["close"] for x in m] + [lv["price"]]
    lo, hi = math.log10(min(closes) * 0.8), math.log10(max(closes) * 1.2)
    def Yp(v): return py1 - (py1 - py0) * (math.log10(v) - lo) / (hi - lo)
    o.append(txt(px0, py0 - 14, 15, ORANGE, "PRICE (log scale)", 700))
    for lvl in (10, 100, 1000):
        if lo <= math.log10(lvl) <= hi:
            o.append(f'<line x1="{px0}" y1="{Yp(lvl):.1f}" x2="{px1}" y2="{Yp(lvl):.1f}" stroke="{GRID}"/>')
            o.append(txt(px0 - 8, Yp(lvl) + 5, 13, SUB, f"${lvl:,}", 400, "end"))
    path = "M" + " L".join(f"{X(i):.1f},{Yp(x['close']):.1f}" for i, x in enumerate(m))
    o.append(f'<path d="{path}" fill="none" stroke="{ORANGE}" stroke-width="3" stroke-linejoin="round"/>')
    # live point, drawn slightly past the last month
    xl = X(n - 1) + 18
    o.append(f'<line x1="{X(n - 1):.1f}" y1="{Yp(m[-1]["close"]):.1f}" x2="{xl:.1f}" y2="{Yp(lv["price"]):.1f}" stroke="{ORANGE}" stroke-width="3" stroke-dasharray="4 3"/>')
    o.append(f'<circle cx="{xl:.1f}" cy="{Yp(lv["price"]):.1f}" r="7" fill="{ORANGE}" stroke="{BG}" stroke-width="2"/>')
    o.append(txt(xl - 12, Yp(lv["price"]) - 16, 16, ORANGE, f"${lv['price']:,.0f} today", 700, "end"))
    if d.get("athIsOld"):
        ah = d["ath"]
        i_a = [x["ym"] for x in m].index(ah["ym"])
        o.append(f'<circle cx="{X(i_a):.1f}" cy="{Yp(ah["close"]):.1f}" r="7" fill="{ORANGE}" stroke="{BG}" stroke-width="2"/>')
        o.append(txt(X(i_a), Yp(ah["close"]) - 16, 15, ORANGE, f"${ah['close']:,.2f}, {ah['ym']}", 700, "middle"))
    lp = d["lowestPrice"]
    i_lo = [x["ym"] for x in m].index(lp["ym"])
    o.append(f'<circle cx="{X(i_lo):.1f}" cy="{Yp(lp["close"]):.1f}" r="7" fill="{ORANGE}" stroke="{BG}" stroke-width="2"/>')
    o.append(txt(X(i_lo), Yp(lp["close"]) + 28, 15, ORANGE, f"${lp['close']:.2f}, {lp['ym']}", 700, "middle"))

    # Bottom: crowd rank, inverted (1 at top), log scale.
    ry0, ry1 = 480, 700
    ranks = [x["rank"] for x in m] + [lv["crowdRank"]]
    rlo, rhi = 0, math.log10(max(ranks) * 1.3)
    def Yr(v): return ry0 + (ry1 - ry0) * (math.log10(max(v, 1)) - rlo) / (rhi - rlo)
    o.append(txt(px0, ry0 - 14, 15, BLUE, "SEAT IN THE CONVERSATION (rank by people posting, #1 at top)", 700))
    for lvl in (1, 10, 100):
        o.append(f'<line x1="{px0}" y1="{Yr(lvl):.1f}" x2="{px1}" y2="{Yr(lvl):.1f}" stroke="{GRID}"/>')
        o.append(txt(px0 - 8, Yr(lvl) + 5, 13, SUB, f"#{lvl}", 400, "end"))
    path = "M" + " L".join(f"{X(i):.1f},{Yr(x['rank']):.1f}" for i, x in enumerate(m))
    o.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>')
    o.append(f'<line x1="{X(n - 1):.1f}" y1="{Yr(m[-1]["rank"]):.1f}" x2="{xl:.1f}" y2="{Yr(lv["crowdRank"]):.1f}" stroke="{BLUE}" stroke-width="3" stroke-dasharray="4 3"/>')
    o.append(f'<circle cx="{xl:.1f}" cy="{Yr(lv["crowdRank"]):.1f}" r="7" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
    o.append(txt(xl - 12, Yr(lv["crowdRank"]) - 14, 16, BLUE, f"#{lv['crowdRank']} today", 700, "end"))
    wr = d["worstRank"]
    i_w = [x["ym"] for x in m].index(wr["ym"])
    o.append(f'<circle cx="{X(i_w):.1f}" cy="{Yr(wr["rank"]):.1f}" r="7" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
    if X(i_w) < px0 + 200:
        o.append(txt(X(i_w) + 14, Yr(wr["rank"]) + 6, 15, BLUE, f"#{wr['rank']:.0f}, {wr['ym']}", 700, "start"))
    else:
        o.append(txt(X(i_w) - 14, Yr(wr["rank"]) + 6, 15, BLUE, f"#{wr['rank']:.0f}, {wr['ym']}", 700, "end"))

    for i, x in enumerate(m):
        if x["ym"].endswith("-01"):
            o.append(txt(X(i), ry1 + 24, 13, SUB, x["ym"][:4], 400, "middle"))
            o.append(f'<line x1="{X(i):.1f}" y1="{ry1}" x2="{X(i):.1f}" y2="{ry1 + 6}" stroke="{GRID}"/>')

    # Stats strip.
    sy = 760
    if d.get("athIsOld"):
        ah = d["ath"]
        stats = [(f"${ah['close']:,.0f} → ${lp['close']:,.2f} → ${lv['price']:,.2f}", f"high {ah['ym'][:4]}, low {lp['ym'][:4]}, today"),
                 (f"{lv['price'] / lp['close']:.1f}x", f"from the {lp['ym']} low"),
                 (f"#{ah['rank']:.0f} → #{wr['rank']:.0f} → #{lv['crowdRank']}", "seat: at the high, at the low, today"),
                 (f"#{lv['mcapRank']}", "by market cap today")]
    else:
        stats = [(f"{lv['price'] / lp['close']:.0f}x", f"from the {lp['ym'][:4]} low"),
                 (f"#{wr['rank']:.0f} → #{lv['crowdRank']}", "seat in the conversation"),
                 (f"${lp['mcap'] / 1e9:.1f}B → ${lv['mcap'] / 1e9:.0f}B", "market cap"),
                 (f"#{lv['mcapRank']}", "by market cap today")]
    for i, (big, small) in enumerate(stats):
        x = 60 + i * 295
        o.append(f'<rect x="{x}" y="{sy}" width="275" height="70" fill="{PANEL}" rx="6"/>')
        o.append(txt(x + 16, sy + 32, 22, TEXT, big, 700))
        o.append(txt(x + 16, sy + 56, 14, SUB, small))

    o.append(txt(60, 870, 14, GREY, f"Source: LunarCrush. Monthly median rank by daily active contributors. Live as of {lv['asOf']}."))
    o.append(txt(1240, 870, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "out/zec.json")
    title = sys.argv[2] if len(sys.argv) > 2 else None
    d = json.loads(src.read_text())
    out = src.with_suffix(".svg")
    out.write_text(render(d, title))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
