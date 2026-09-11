#!/usr/bin/env python3
"""Chart: seven fixed seats, three open ones, and how long a visitor lasts.

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
    W, H = 1300, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "Crypto's top ten has three open seats.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"The ten most-discussed coins each day, {d['days']:,} days, 2020 to 2026."))

    # Ten seats.
    fx = d["fixtures"]
    seats_y, sw, sg = 170, 106, 13
    for i in range(d["topN"]):
        x = 60 + i * (sw + sg)
        if i < len(fx):
            o.append(f'<rect x="{x}" y="{seats_y}" width="{sw}" height="150" fill="{PANEL}" rx="8"/>')
            o.append(f'<rect x="{x}" y="{seats_y}" width="{sw}" height="5" fill="{BLUE}" rx="2"/>')
            o.append(txt(x + sw / 2, seats_y + 66, 24, TEXT, fx[i]["symbol"], 700, "middle"))
            o.append(txt(x + sw / 2, seats_y + 100, 17, SUB, f"{fx[i]['share'] * 100:.0f}%", 400, "middle"))
            o.append(txt(x + sw / 2, seats_y + 124, 13, GREY, "of days", 400, "middle"))
        else:
            o.append(f'<rect x="{x}" y="{seats_y}" width="{sw}" height="150" fill="none" '
                     f'stroke="{AMBER}" stroke-width="2" stroke-dasharray="7 6" rx="8"/>')
            o.append(txt(x + sw / 2, seats_y + 82, 17, AMBER, "open", 700, "middle"))
    o.append(txt(60, seats_y + 190, 17, SUB,
                 f"Seven coins hold a seat on most days. The other {d['distinctCoins'] - len(fx)} coins "
                 f"that ever made the list fight over the remaining three."))

    # Stay histogram for visitors.
    hy = 430
    o.append(txt(60, hy, 18, TEXT, "WHEN A VISITOR BREAKS IN, HOW LONG DOES IT STAY?", 700))
    o.append(txt(60, hy + 26, 16, SUB, f"{d['stints']:,} stints by non-fixtures. Bars are the share ending on that day."))
    hist = {int(k): v for k, v in d["stayHistogram"].items()}
    total = sum(hist.values())
    bx, bw, bg, bh, base = 60, 32, 6, 200, hy + 270
    mx = max(hist.values())
    for i in range(1, 32):
        v = hist.get(i, 0)
        h = v / mx * bh
        x = bx + (i - 1) * (bw + bg)
        col = RED if i == 1 else AMBER if i <= 3 else GREY
        o.append(f'<rect x="{x}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" fill="{col}" rx="3"/>')
        if i in (1, 2, 3, 7, 14, 31):
            lbl = "31+" if i == 31 else str(i)
            o.append(txt(x + bw / 2, base + 22, 14, SUB, lbl, 400, "middle"))
    o.append(f'<rect x="{bx}" y="{base}" width="{31 * (bw + bg) - bg}" height="1" fill="{GRID}"/>')
    o.append(txt(bx, base + 44, 14, GREY, "days in the top ten"))
    o.append(txt(bx + 60, base - bh + 8, 40, RED, f"{d['goneNextDay'] * 100:.0f}%", 700))
    o.append(txt(bx + 60, base - bh + 34, 16, SUB, "gone the next day"))

    # Right-side stats.
    sx = 780
    stats = [(f"{d['medianStay']:.0f} day", "median stay"),
             (f"{d['goneWithin3'] * 100:.0f}%", "gone within 3 days"),
             (f"{d['goneWithin7'] * 100:.0f}%", "gone within a week"),
             (f"{d['lastedMonth'] * 100:.1f}%", "lasted a month")]
    sy = hy + 82
    for big, small in stats:
        o.append(txt(sx, sy, 30, TEXT, big, 700))
        o.append(txt(sx + 150, sy, 16, SUB, small))
        sy += 48

    o.append(txt(60, 812, 19, TEXT,
                 "A coin trending today is, on the median, off the list tomorrow.", 700))
    o.append(txt(60, 842, 16, SUB,
                 "Name collisions and pegged assets removed before ranking. Otherwise $GIGA holds a seat on 60% of days and $S on 47%."))
    o.append(txt(60, 878, 15, GREY, "Source: LunarCrush daily history, 1,000 coins."))
    o.append(txt(1240, 878, 15, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "top_ten.json").read_text())
    out = HERE / "out" / "top_ten.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
