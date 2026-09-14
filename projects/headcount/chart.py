#!/usr/bin/env python3
"""Chart: how many people are actually posting about each coin.

Usage: python3 chart.py
"""

import json
import math
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


def render(d: dict) -> str:
    W, H = 1300, 916
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, f"The median coin has {d['median']:.0f} people talking about it.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Distinct accounts posting about each coin per day, {d['coins']} coins, {d['start']} to {d['end']}."))

    # Ladder by market-cap rank band, log-scaled bars.
    ly = 180
    o.append(txt(60, ly, 18, TEXT, "PEOPLE A DAY, BY MARKET-CAP RANK", 700))
    o.append(txt(60, ly + 24, 15, SUB, "median coin in each band"))
    mx = math.log10(max(b["contrib"] for b in d["bands"]) * 1.2)
    bw = 1180 - 260
    for i, b in enumerate(d["bands"]):
        y = ly + 60 + i * 52
        w = bw * math.log10(max(b["contrib"], 1)) / mx
        col = ORANGE if b["lo"] == 1 else BLUE if b["lo"] <= 50 else GREY if b["lo"] <= 250 else RED
        o.append(txt(60, y + 24, 17, TEXT, f"#{b['lo']} to {b['hi']}", 700))
        o.append(f'<rect x="260" y="{y}" width="{w:.1f}" height="36" fill="{col}" rx="4"/>')
        o.append(txt(260 + w + 14, y + 25, 18, TEXT, f"{b['contrib']:,.0f}", 700))
    o.append(txt(60, ly + 60 + 6 * 52 + 10, 14, GREY, "bars on a log scale, or the bottom four would not be visible"))

    # Right: the distribution.
    rx = 800
    stats = [(f"{d['belowThreshold']['10'] * 100:.0f}%", "of coins have fewer than 10"),
             (f"{d['belowThreshold']['50'] * 100:.0f}%", "have fewer than 50"),
             (f"{d['belowThreshold']['100'] * 100:.0f}%", "have fewer than 100")]
    # (placed under ladder instead to avoid crowding)

    sy = 596
    o.append(f'<rect x="60" y="{sy}" width="560" height="150" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, sy + 34, 15, SUB, "HOW MANY COINS HAVE A CROWD AT ALL", 700))
    for i, (big, small) in enumerate(stats):
        o.append(txt(84, sy + 76 + i * 34, 24, RED if i == 0 else TEXT, big, 700))
        o.append(txt(170, sy + 76 + i * 34, 16, SUB, small + " people a day"))

    qb = d["quietBigCaps"][:5]
    o.append(f'<rect x="680" y="{sy}" width="560" height="150" fill="{PANEL}" rx="6"/>')
    o.append(txt(704, sy + 34, 15, SUB, "BIG COINS, TINY CROWDS", 700))
    for i, q in enumerate(qb):
        y = sy + 62 + i * 21
        o.append(txt(704, y, 15, TEXT, f"${q['symbol']}", 700))
        o.append(txt(790, y, 15, SUB, f"#{q['rank']} by market cap, ${q['mcap'] / 1e9:.1f}B"))
        o.append(txt(1216, y, 15, AMBER, f"{q['contrib']:.0f} people a day", 700, "end"))

    o.append(txt(60, 796, 19, TEXT,
                 f"To be in the top 100 coins by crowd, you need {d['rankCutoffs']['100']:.0f} people a day. The top 10 needs {d['rankCutoffs']['10']:,.0f}.", 700))
    o.append(txt(60, 830, 16, SUB,
                 "Pegged, wrapped and yield-bearing tokens excluded: nobody discusses a wrapper. What is left is projects with a real ticker and almost no crowd."))
    o.append(txt(60, 882, 15, GREY, "Source: LunarCrush daily history."))
    o.append(txt(1240, 882, 15, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "headcount.json").read_text())
    out = HERE / "out" / "headcount.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
