#!/usr/bin/env python3
"""Chart: 130 coins made the top 20, 17 are still there.

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
    W, H = 1300, 850
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, f"{d['everTop']} coins have made crypto's top 20. {d['held']} are still there.", 700))
    o.append(txt(60, 112, 20, SUB,
                 "Every coin that held a top-20 seat by daily posters in any month since 2020, and where it sits now."))

    # Three big numbers.
    stats = [(f"{d['held']}", f"still top 20", GREEN), (f"{d['top50'] - d['held']}", "slipped to 21–50", AMBER),
             (f"{d['everTop'] - d['top50'] - d['past100']}", "slipped to 51–100", GREY), (f"{d['past100']}", "fell past #100", RED)]
    for i, (big, small, col) in enumerate(stats):
        x = 60 + i * 295
        o.append(f'<rect x="{x}" y="150" width="275" height="96" fill="{PANEL}" rx="6"/>')
        o.append(txt(x + 20, 202, 40, col, big, 700))
        o.append(txt(x + 100, 202, 16, SUB, small))

    # Left: biggest falls, then → now crowd.
    ly = 300
    o.append(txt(60, ly, 17, TEXT, "THE ONES YOU REMEMBER", 700))
    o.append(txt(60, ly + 22, 14, SUB, "peak seat and month · people posting a day then → now · seat now"))
    picks = [f for f in d["fallers"] if f["symbol"] in ("YFI", "SUSHI", "MANA", "BLUR", "MEME", "GMT", "SLP", "1INCH", "AGIX", "GMX", "DYM", "OCEAN")]
    picks = sorted(picks, key=lambda f: f["peakMonth"])[:11]
    for i, f in enumerate(picks):
        y = ly + 56 + i * 32
        o.append(txt(60, y, 16, TEXT, f"${f['symbol']}", 700))
        o.append(txt(150, y, 14, SUB, f"#{f['peakRank']:.0f}  {f['peakMonth']}"))
        o.append(txt(290, y, 14, TEXT, f"{f['peakContrib']:,.0f}", 700, "end"))
        o.append(txt(300, y, 14, GREY, "→"))
        o.append(txt(360, y, 14, RED, f"{f['nowContrib']:,.0f}", 700, "end"))
        o.append(txt(420, y, 14, SUB, f"#{f['nowRank']:.0f}"))
        o.append(txt(480, y, 13, GREY, f["name"][:22]))

    # Right: by the year they peaked.
    rx = 720
    o.append(txt(rx, ly, 17, TEXT, "BY THE YEAR THEY PEAKED", 700))
    o.append(txt(rx, ly + 22, 14, SUB, "of the coins that peaked that year, how many still hold a seat"))
    for i, c in enumerate(d["classes"]):
        y = ly + 56 + i * 44
        o.append(txt(rx, y + 4, 16, TEXT, c["year"], 700))
        bw = 440
        w_all = bw
        w_held = bw * c["held"] / c["n"]
        w_100 = bw * c["past100"] / c["n"]
        o.append(f'<rect x="{rx + 60}" y="{y - 12}" width="{w_all}" height="22" fill="{PANEL}" rx="3"/>')
        o.append(f'<rect x="{rx + 60}" y="{y - 12}" width="{w_held:.1f}" height="22" fill="{GREEN}" rx="3"/>')
        o.append(f'<rect x="{rx + 60 + w_all - w_100:.1f}" y="{y - 12}" width="{w_100:.1f}" height="22" fill="{RED}" rx="3"/>')
        o.append(txt(rx + 60 + bw + 12, y + 4, 14, SUB, f"{c['held']} of {c['n']}"))
    o.append(txt(rx, ly + 56 + len(d["classes"]) * 44 + 4, 13, GREY, "green: still top 20 · red: fell past #100 · grey: in between"))

    o.append(txt(60, 760, 19, TEXT,
                 "Of the 20 coins that peaked in 2021, one still holds a seat. It's DOGE.", 700))
    o.append(txt(60, 792, 15, SUB,
                 "Universe is today's top 1,000 by market cap, so a coin that fell out of it entirely is not counted. Every number here is a floor."))
    o.append(txt(60, 826, 14, GREY, "Daily active contributors, monthly median rank. Pegged assets and name collisions removed. Source: LunarCrush."))
    o.append(txt(1240, 826, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "fallen.json").read_text())
    out = HERE / "out" / "fallen.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
