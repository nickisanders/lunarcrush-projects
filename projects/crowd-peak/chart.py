#!/usr/bin/env python3
"""Chart: what happens after a coin enters crypto's top 10 conversation.

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
    W, H = 1300, 1010
    st = d["stats"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    ninety = [s for s in st if s["H"] == 90][0]
    o.append(txt(60, 74, 37, TEXT, "A coin joins crypto's top 10 conversation. Then this happens.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"{d['events']} times since 2020, a coin entered the top {d['top']} by daily posters "
                 f"with no top-{d['top']} day in the prior year."))

    # Three horizons across the full width. Bars hang below a zero line and
    # every label for a horizon lives inside that horizon's column, so a tall
    # bar cannot push text into its neighbour.
    bx, by, bh = 60, 210, 150
    col_w = 1180 / 3
    o.append(txt(bx, by - 26, 17, TEXT, "MEDIAN RETURN AGAINST BITCOIN, AFTER THE DAY IT ENTERED", 700))
    worst = min(s_["adj"] for s_ in st)
    o.append(f'<line x1="{bx}" y1="{by}" x2="{bx + 1180}" y2="{by}" stroke="{GRID}" stroke-width="2"/>')
    o.append(txt(bx - 12, by + 5, 14, SUB, "0%", 400, "end"))
    for i, s_ in enumerate(st):
        cx = bx + i * col_w + col_w / 2
        h = abs(s_["adj"]) / abs(worst) * bh
        col = RED if s_["p"] < 0.05 else GREY
        o.append(f'<rect x="{cx - 80:.1f}" y="{by}" width="160" height="{h:.1f}" fill="{col}" rx="5"/>')
        o.append(txt(cx, by + h + 44, 36, col, f"{s_['adj'] * 100:.1f}%", 700, "middle"))
        o.append(txt(cx, by + bh + 78, 17, TEXT, f"after {s_['H']} days", 700, "middle"))
        o.append(txt(cx, by + bh + 104, 14, SUB,
                     f"95% CI [{s_['lo'] * 100:+.0f}, {s_['hi'] * 100:+.0f}]   p = {s_['p']:.3f}", 400, "middle"))
        o.append(txt(cx, by + bh + 142, 24, TEXT, f"{s_['up'] * 100:.0f}%", 700, "middle"))
        o.append(txt(cx, by + bh + 166, 14, SUB, "rose", 400, "middle"))
        o.append(txt(cx + 110, by + bh + 142, 24, RED if s_["beat"] < 0.5 else GREEN,
                     f"{s_['beat'] * 100:.0f}%", 700, "middle"))
        o.append(txt(cx + 110, by + bh + 166, 14, SUB, "beat BTC", 400, "middle"))

    # Recent named cases.
    ly = 620
    o.append(txt(60, ly, 17, TEXT, "THE LAST TWELVE, 30 DAYS LATER", 700))
    rec = d["recent"]
    for i, r in enumerate(rec):
        col_i, row = divmod(i, 6)
        x = 60 + col_i * 600
        y = ly + 36 + row * 34
        c = GREEN if r["adj"] > 0 else RED
        o.append(txt(x, y, 17, TEXT, f"${r['symbol']}", 700))
        o.append(txt(x + 110, y, 15, SUB, r["date"]))
        o.append(txt(x + 300, y, 17, c, f"{r['adj'] * 100:+.0f}%", 700, "end"))
        o.append(txt(x + 400, y, 14, GREY, "vs BTC", anchor="end"))

    o.append(f'<rect x="60" y="{ly + 250}" width="1180" height="84" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, ly + 284, 19, TEXT,
                 "$ZEC is the exception. It entered in October 2025 and went on to beat Bitcoin by 220%.", 700))
    o.append(txt(84, ly + 314, 16, SUB,
                 f"The other {len(rec) - 1} of the last twelve are mostly red, and across all {d['events']} events only {ninety['beat'] * 100:.0f}% beat Bitcoin over 90 days."))

    o.append(txt(60, 980, 14, GREY,
                 "Rank by daily active contributors. Month-block bootstrap on the median. Source: LunarCrush, 2020 to 2026."))
    o.append(txt(1240, 980, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "crowd_peak.json").read_text())
    out = HERE / "out" / "crowd_peak.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
