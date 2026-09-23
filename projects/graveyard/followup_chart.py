#!/usr/bin/env python3
"""Chart: the day after the graveyard post.

Usage: python3 followup_chart.py
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
    rows = d["rows"]
    W, H = 1300, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "I posted these nine yesterday. Here's the day after.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Median {d['medianNext']:+.1f}% against a market at {d['marketMedian']:+.1f}%. "
                 f"The bigger the run had been, the harder it fell."))

    # Scatter: run size (log x) vs next-day return (y).
    import math
    px0, px1, py0, py1 = 110, 780, 190, 560
    runs = [r["run"] for r in rows]
    nxt = [r["next"] for r in rows]
    lx, hx = math.log10(min(runs) * 0.85), math.log10(max(runs) * 1.2)
    ly, hy = min(nxt + [d["marketMedian"]]) - 5, max(nxt) + 6
    def X(v): return px0 + (px1 - px0) * (math.log10(v) - lx) / (hx - lx)
    def Y(v): return py1 - (py1 - py0) * (v - ly) / (hy - ly)
    o.append(txt(px0, py0 - 22, 16, TEXT, "THE WEEK'S RUN, AGAINST WHAT IT DID NEXT", 700))
    o.append(f'<line x1="{px0}" y1="{Y(0):.1f}" x2="{px1}" y2="{Y(0):.1f}" stroke="{GRID}" stroke-width="2"/>')
    o.append(txt(px0 - 10, Y(0) + 5, 13, SUB, "0%", 400, "end"))
    for lv in (-20, -10, 10):
        if ly <= lv <= hy:
            o.append(f'<line x1="{px0}" y1="{Y(lv):.1f}" x2="{px1}" y2="{Y(lv):.1f}" stroke="{GRID}" stroke-dasharray="3 4"/>')
            o.append(txt(px0 - 10, Y(lv) + 5, 13, SUB, f"{lv}%", 400, "end"))
    for lv in (60, 100, 200, 500):
        if lx <= math.log10(lv) <= hx:
            o.append(txt(X(lv), py1 + 26, 13, SUB, f"+{lv}%", 400, "middle"))
    o.append(txt(px0, py1 + 52, 14, GREY, "the 7-day run when I posted, log scale →"))
    # Two points can land within a label's height of each other; nudge the
    # later one so the two names do not print on top of one another.
    placed: list[tuple[float, float]] = []
    for r in rows:
        x, y = X(r["run"]), Y(r["next"])
        col = GREEN if r["next"] > 0 else RED
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{col}" stroke="{BG}" stroke-width="2"/>')
        side = "end" if x > px1 - 90 else "start"
        dx = -16 if side == "end" else 16
        ly_ = y + 6
        while any(abs(ly_ - py) < 20 and abs(x - pxx) < 110 for pxx, py in placed):
            ly_ += 21
        placed.append((x, ly_))
        if abs(ly_ - (y + 6)) > 1:
            o.append(f'<line x1="{x + dx * 0.55:.1f}" y1="{y:.1f}" x2="{x + dx * 0.9:.1f}" y2="{ly_ - 5:.1f}" stroke="{col}" stroke-width="1.5"/>')
        o.append(txt(x + dx, ly_, 15, TEXT, f"${r['symbol']}", 700, side))

    # Right: the split.
    rx = 850
    o.append(txt(rx, py0 - 22, 16, TEXT, "SPLIT BY SIZE OF THE RUN", 700))
    parts = [(f"runs over +{d['bigRunThreshold']:.0f}%", d["bigRunMedian"], RED, "AURORA, ONE, SYN"),
             ("the other six", d["smallRunMedian"], GREY, "MINA, PHA, AR, ICX, ZETA, AIOZ"),
             ("the market", d["marketMedian"], BLUE, "every coin over $50M")]
    for i, (lab, v, col, note) in enumerate(parts):
        y = py0 + 20 + i * 110
        o.append(txt(rx, y, 16, SUB, lab, 700))
        o.append(txt(rx, y + 46, 40, col, f"{v:+.1f}%", 700))
        o.append(txt(rx, y + 72, 14, GREY, note))

    # Backtest strip.
    by = 630
    o.append(f'<rect x="60" y="{by}" width="1180" height="160" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, by + 34, 15, SUB, "AND THE PART I ALREADY KNEW: 90-DAY MEDIAN RETURN AFTER A WEEK LIKE THAT", 700))
    bs = d["buckets"]
    for i, b in enumerate(bs):
        x = 84 + i * 292
        col = GREY if i == 0 else AMBER if i == 1 else RED
        o.append(txt(x, by + 78, 30, col, f"{b['m90'] * 100:.0f}%", 700))
        o.append(txt(x, by + 106, 15, TEXT, b["label"]))
        o.append(txt(x, by + 128, 13, GREY, f"n = {b.get('n'):,}"))

    o.append(txt(60, 838, 19, TEXT,
                 "Six of the nine fell. The three that had run hardest fell the hardest.", 700))
    o.append(txt(60, 872, 14, GREY,
                 f"Source: LunarCrush, posted {d['postedOn']}, checked {d['asOf']}. Nine coins is a small sample and one day is a short window."))
    o.append(txt(1240, 872, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "followup.json").read_text())
    out = HERE / "out" / "followup.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
