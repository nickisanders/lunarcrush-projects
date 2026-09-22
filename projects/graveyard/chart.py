#!/usr/bin/env python3
"""Chart: this week's biggest winners, against how far they fell.

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
    dead = d["dead"]
    W, H = 1300, 250 + len(dead) * 62 + 250 - 60
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "Crypto's graveyard is bidding.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"{len(dead)} of this week's 20 biggest gainers sit 80%+ below their own peak. "
                 f"They were not always nobodies."))

    y0 = 190
    o.append(txt(60, y0 - 16, 15, SUB, "COIN", 700))
    o.append(txt(380, y0 - 16, 15, SUB, "BEST SEAT IT EVER HELD IN CRYPTO CONVERSATION", 700))
    o.append(txt(880, y0 - 16, 15, SUB, "OFF PEAK", 700, "end"))
    o.append(txt(1240, y0 - 16, 15, SUB, "THIS WEEK", 700, "end"))

    # Seat bar: #1 is a full bar, #50 is a sliver. Log-ish, capped at 50.
    for i, x in enumerate(dead):
        y = y0 + i * 62
        seat = x["bestSeat"]
        w = 400 * max(0.06, 1 - (seat - 1) / 50)
        o.append(f'<rect x="60" y="{y}" width="1180" height="48" fill="{PANEL}" rx="5"/>')
        o.append(txt(80, y + 32, 22, TEXT, f"${x['symbol']}", 700))
        o.append(txt(196, y + 31, 15, GREY, x["name"][:16]))
        o.append(f'<rect x="380" y="{y + 14}" width="{w:.1f}" height="20" fill="{BLUE}" rx="4"/>')
        o.append(txt(386 + w, y + 30, 17, BLUE, f"#{seat}", 700))
        o.append(txt(880, y + 32, 19, RED, f"{x['offPeak'] * 100:.0f}%", 700, "end"))
        o.append(txt(1240, y + 32, 22, GREEN, f"+{x['pct7d']:.0f}%", 700, "end"))

    by = y0 + len(dead) * 62 + 24
    o.append(f'<rect x="60" y="{by}" width="1180" height="112" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, by + 36, 19, TEXT,
                 "ICON was the 4th most-discussed coin in all of crypto. Arbitrum was 1st. Harmony was 12th.", 700))
    o.append(txt(84, by + 70, 17, SUB,
                 "Today they are 99%, 69% and 99% below their peak market caps, and three of this week's twenty biggest gainers."))
    o.append(txt(84, by + 96, 15, GREY,
                 "Seat is a coin's best-ever rank by daily active contributors against every other coin, 2020 to now."))

    o.append(txt(60, H - 46, 19, TEXT,
                 "Last week I posted that 130 coins have made crypto's top 20 and 17 are still there. This is where some of the other 113 went.", 700))
    o.append(txt(60, H - 16, 14, GREY, f"Source: LunarCrush, {d['asOf']}. Pegged and wrapped assets excluded."))
    o.append(txt(1240, H - 16, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "graveyard.json").read_text())
    out = HERE / "out" / "graveyard.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
