#!/usr/bin/env python3
"""Chart: sentiment falls as the crowd grows.

Usage: python3 chart.py
"""

import json
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
    W, H = 1300, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "The more people talk about a coin, the less they like it.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Median daily sentiment score by crowd size. {d['coins']} coins, {d['start']} to {d['end']}."))

    # Bands as bars, sentiment 60-90 range.
    bx, by, bw, bh = 60, 200, 720, 300
    lo_s, hi_s = 68, 88
    bands = d["bands"]
    n = len(bands)
    slot = bw / n
    o.append(txt(bx, by - 30, 17, TEXT, "SENTIMENT BY HOW MANY PEOPLE POST A DAY", 700))
    for lv in (70, 75, 80, 85):
        y = by + bh - (lv - lo_s) / (hi_s - lo_s) * bh
        o.append(f'<line x1="{bx}" y1="{y:.1f}" x2="{bx + bw}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(txt(bx - 10, y + 5, 13, SUB, str(lv), 400, "end"))
    for i, b in enumerate(bands):
        x = bx + i * slot + 12
        w = slot - 24
        h = (b["sent"] - lo_s) / (hi_s - lo_s) * bh
        col = GREEN if b["sent"] >= 82 else AMBER if b["sent"] >= 78 else RED
        o.append(f'<rect x="{x:.1f}" y="{by + bh - h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{col}" rx="5"/>')
        o.append(txt(x + w / 2, by + bh - h - 12, 22, TEXT, f"{b['sent']:.0f}", 700, "middle"))
        lab = f"{b['lo']:,}+" if b["hi"] >= 10**9 else f"{b['lo']}–{b['hi']:,}"
        o.append(txt(x + w / 2, by + bh + 24, 14, TEXT, lab, 700, "middle"))
        o.append(txt(x + w / 2, by + bh + 44, 12, GREY, ", ".join(b["examples"][:3]), 400, "middle"))
    o.append(txt(bx, by + bh + 74, 14, SUB, "people posting per day →"))
    o.append(txt(bx, by + bh + 100, 15, SUB,
                 f"Spearman {d['spearman']:+.2f}, 95% CI [{d['ci'][0]:+.2f}, {d['ci'][1]:+.2f}]. "
                 f"Within a single coin, day to day, the direction holds for {d['withinCoinNegShare'] * 100:.0f}% of coins."))

    # Right: top 10 ladder.
    rx = 840
    o.append(txt(rx, by - 30, 17, TEXT, "THE TOP TEN BY MARKET CAP", 700))
    o.append(txt(rx, by - 8, 13, SUB, "least liked first"))
    for i, t in enumerate(d["top10"]):
        y = by + 30 + i * 44
        col = RED if t["sent"] < 75 else AMBER if t["sent"] < 82 else GREEN
        o.append(txt(rx, y, 18, TEXT, f"${t['symbol']}", 700))
        o.append(txt(rx + 110, y, 22, col, f"{t['sent']:.0f}", 700))
        o.append(txt(rx + 170, y, 14, SUB, f"{t['contrib']:,.0f} people a day"))
    o.append(txt(rx, by + 30 + len(d["top10"]) * 44 + 6, 14, GREY, "stablecoins and wrappers excluded"))

    # Bottom: the ticker-reading caveat.
    cy = 690
    o.append(f'<rect x="60" y="{cy}" width="1180" height="118" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, cy + 34, 16, SUB, "ONE THING THE SCORE CANNOT DO", 700))
    low = [x for x in d["lowest"] if x["symbol"] in ("ASS", "USELESS", "TROLL", "CLASH")]
    o.append(txt(84, cy + 66, 17, TEXT,
                 "The lowest-scoring coins in the data are " + ", ".join(f"${x['symbol']} ({x['sent']:.0f})" for x in low) + ".", 700))
    o.append(txt(84, cy + 94, 16, SUB,
                 "Those are their names. The model reads the ticker and cannot tell a coin called USELESS from a coin people think is useless."))

    o.append(txt(60, 852, 19, TEXT, "A small crowd is holders. A big crowd includes everyone who disagrees with them.", 700))
    o.append(txt(60, 882, 14, GREY, f"Source: LunarCrush daily sentiment, coins with ≥45 days of ≥20 posters in the window."))
    o.append(txt(1240, 882, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "mood.json").read_text())
    out = HERE / "out" / "mood.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
