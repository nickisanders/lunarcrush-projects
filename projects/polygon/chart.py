#!/usr/bin/env python3
"""Chart Polygon's rank in crypto conversation, with peers.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER, PURPLE = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922", "#a371f7"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
LAUNCH = {"ARB": "2023H1", "OP": "2022H1", "SUI": "2023H1", "APT": "2022H2", "AVAX": "2020H2"}


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


def render(d: dict) -> str:
    W, H = 1300, 1040
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 72, 38, TEXT, "Polygon held a top-20 seat for four years.", 700))
    o.append(txt(60, 110, 20, SUB,
                 f"Rank among ~1,000 coins by daily active contributors. July 2026: #{d['latestRank']:.0f}."))

    # Main line: monthly rank, inverted (1 at top), log-ish scale via sqrt for readability.
    mon = d["monthly"]
    px0, px1, py0, py1 = 90, 1240, 160, 560
    import math
    def yof(r): return py0 + (math.sqrt(r) - 1) / (math.sqrt(130) - 1) * (py1 - py0)
    n = len(mon)
    def xof(i): return px0 + i / (n - 1) * (px1 - px0)
    # top-20 band
    o.append(f'<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{yof(20) - py0:.1f}" fill="{PANEL}" rx="4"/>')
    o.append(txt(px1 - 10, yof(20) - 8, 13, GREY, "top 20", anchor="end"))
    for r in (1, 5, 10, 20, 50, 100):
        y = yof(r)
        o.append(f'<line x1="{px0}" y1="{y:.1f}" x2="{px1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(txt(px0 - 10, y + 5, 13, SUB, f"#{r}", anchor="end"))
    # year ticks
    for i, m in enumerate(mon):
        if m["month"].endswith("-01"):
            x = xof(i)
            o.append(f'<line x1="{x:.1f}" y1="{py1}" x2="{x:.1f}" y2="{py1 + 6}" stroke="{GRID}"/>')
            o.append(txt(x, py1 + 24, 13, SUB, m["month"][:4], anchor="middle"))
    pts = " ".join(f"{xof(i):.1f},{yof(min(m['rank'], 130)):.1f}" for i, m in enumerate(mon))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linejoin="round"/>')
    # annotations
    def ann(month, label, dy=-14, col=SUB):
        for i, m in enumerate(mon):
            if m["month"] == month:
                x, y = xof(i), yof(min(m["rank"], 130))
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}"/>')
                o.append(txt(x, y + dy, 14, col, label, 700, "middle"))
    ann(d["bestMonth"], f"#{d['bestRank']:.0f}, May 2021", -14, GREEN)
    ann("2023-12", "2,777 contributors a day", -14, GREEN)
    ann("2024-09", "MATIC becomes POL", 28, AMBER)
    ann(d["latestMonth"], f"#{d['latestRank']:.0f}", -14, RED)

    # Peer strip.
    sy = 640
    o.append(txt(60, sy, 18, TEXT, "SAME MEASURE, PEER CHAINS: PLACES LOST SINCE EARLY 2024", 700))
    o.append(txt(60, sy + 24, 15, SUB, "median rank, first half of 2024 to latest. Positive means it fell down the list."))
    mv = d["moves"]
    order = sorted(mv, key=lambda c: -mv[c]["change"])
    bx, bw, gap, base = 60, 118, 26, sy + 200
    mx = max(abs(v["change"]) for v in mv.values())
    scale = 110 / mx
    o.append(f'<line x1="{bx}" y1="{base}" x2="{bx + len(order) * (bw + gap) - gap}" y2="{base}" stroke="{GRID}"/>')
    l2 = {"Polygon", "ARB", "OP"}
    for i, c in enumerate(order):
        v = mv[c]["change"]
        x = bx + i * (bw + gap)
        h = abs(v) * scale
        col = RED if v > 30 else GREY if v > -5 else GREEN
        if c in l2: col = RED
        y = base - h if v > 0 else base
        o.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{col}" rx="3"/>')
        # Labels for falling chains sit above the bar; for flat or rising ones
        # the bar is tiny, so the label sits above the baseline instead.
        ly = (y - 8) if v > 0 else (base - 10)
        o.append(txt(x + bw / 2, ly, 16, col, f"{v:+.0f}", 700, "middle"))
        o.append(txt(x + bw / 2, base + 44, 15, TEXT, c, 700, "middle"))
        o.append(txt(x + bw / 2, base + 66, 13, SUB, f"#{mv[c]['from']:.0f} → #{mv[c]['to']:.0f}", 400, "middle"))

    o.append(txt(60, 946, 19, TEXT,
                 "Every Ethereum scaling chain fell. Solana and BNB held their seats. Sui rose.", 700))
    o.append(txt(60, 978, 15, SUB,
                 "MATIC and POL summed. Ranked by daily active contributors, which is stable across LunarCrush's 2023 counting change. "
                 "Pegged assets and name collisions removed."))
    o.append(txt(60, 1010, 14, GREY, "Source: LunarCrush. Peer ranks before each token's launch are omitted."))
    o.append(txt(1240, 1010, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "polygon.json").read_text())
    out = HERE / "out" / "polygon.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
