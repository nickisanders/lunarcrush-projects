#!/usr/bin/env python3
"""Chart: the 2021 bags against the memecoins, this week.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922"
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
    W, H = 1300, 940
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "Your 2021 bags are beating the memecoins.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"This week, {d['universe']} coins over $50M. The market median was {d['market']:+.1f}%."))

    # Two cohort cards.
    co = d["cohorts"]
    cards = [("THE 2021 BAGS", co["old"], GREEN, "peaked 2021 or earlier, still 50%+ below it"),
             ("THE MEMECOINS", co["meme"], RED, "LunarCrush's own meme category")]
    for i, (label, c, col, note) in enumerate(cards):
        x = 60 + i * 600
        o.append(f'<rect x="{x}" y="170" width="580" height="150" fill="{PANEL}" rx="8"/>')
        o.append(txt(x + 24, 206, 16, SUB, label, 700))
        o.append(txt(x + 24, 262, 46, col, f"{c['median7d']:+.1f}%", 700))
        o.append(txt(x + 200, 254, 17, TEXT, "median this week"))
        o.append(txt(x + 200, 280, 15, SUB, f"{c['n']} coins  ·  {c['beat'] * 100:.0f}% beat the market"))
        o.append(txt(x + 24, 302, 14, GREY, note))

    # Named lists.
    ly = 380
    o.append(txt(60, ly, 17, GREEN, "BEST OF THE BAGS", 700))
    o.append(txt(60, ly + 22, 14, SUB, "and how far below their own 2021 peak they still sit"))
    for i, r in enumerate(d["topOld"][:9]):
        y = ly + 58 + i * 40
        o.append(txt(60, y, 19, TEXT, f"${r['symbol']}", 700))
        o.append(txt(160, y, 15, GREY, r["name"][:16]))
        o.append(txt(400, y, 19, GREEN, f"+{r['pct7d']:.0f}%", 700, "end"))
        o.append(txt(520, y, 15, SUB, f"{r['offPeak'] * 100:.0f}% off peak", anchor="end"))

    o.append(txt(680, ly, 17, RED, "WORST OF THE MEMES", 700))
    o.append(txt(680, ly + 22, 14, SUB, "same week, same market"))
    for i, r in enumerate(d["worstMeme"][:6]):
        y = ly + 58 + i * 40
        o.append(txt(680, y, 19, TEXT, f"${r['symbol']}", 700))
        o.append(txt(800, y, 15, GREY, r["name"][:18]))
        o.append(txt(1100, y, 19, RED, f"{r['pct7d']:.0f}%", 700, "end"))
        o.append(txt(1240, y, 15, SUB, f"${r['mcap'] / 1e6:,.0f}M", anchor="end"))

    if d.get("qnt"):
        q = d["qnt"]
        qy = ly + 58 + 6 * 40 + 20
        o.append(f'<rect x="680" y="{qy}" width="560" height="96" fill={chr(34)}{PANEL}{chr(34)} rx="8"/>')
        o.append(txt(704, qy + 34, 16, AMBER, "AND ONE THAT GRADUATED", 700))
        o.append(txt(704, qy + 68, 17, TEXT,
                     f"$QNT is {q['pct7d']:+.0f}% this week and only {abs(q['offPeak']) * 100:.0f}% off its {q['peakYear']} peak.", 700))

    o.append(txt(60, 852, 19, TEXT,
                 "63% of the bags beat the market this week. 28% of the memecoins did.", 700))
    o.append(txt(60, 886, 15, SUB,
                 "Both cohorts are defined from data, not picked: peak year and drawdown come from six years of daily history."))
    o.append(txt(60, 918, 14, GREY, f"Source: LunarCrush, {d['asOf']}. One week is one week."))
    o.append(txt(1240, 918, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "old_bags.json").read_text())
    out = HERE / "out" / "old_bags.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
