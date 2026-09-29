#!/usr/bin/env python3
"""Chart: the share of the top 100 beating Bitcoin, every day since 2020.

Usage: python3 chart.py
"""

import json
from pathlib import Path

import pandas as pd

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
    s = pd.DataFrame(d["series"])
    s["date"] = pd.to_datetime(s["date"])
    n = len(s)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, f"{d['today'] * 100:.0f}% of the top 100 are beating Bitcoin.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Over the last {d['window']} days. That is the {d['percentile'] * 100:.0f}th percentile of "
                 f"{d['days']:,} days since 2020."))

    px0, px1, py0, py1 = 90, 1240, 200, 560
    def X(i): return px0 + (px1 - px0) * i / (n - 1)
    def Y(v): return py1 - (py1 - py0) * v

    for lv in (0.25, 0.5, 0.75):
        o.append(f'<line x1="{px0}" y1="{Y(lv):.1f}" x2="{px1}" y2="{Y(lv):.1f}" stroke="{GRID}"/>')
        o.append(txt(px0 - 10, Y(lv) + 5, 13, SUB, f"{lv * 100:.0f}%", 400, "end"))
    med = d["median"]
    o.append(f'<line x1="{px0}" y1="{Y(med):.1f}" x2="{px1}" y2="{Y(med):.1f}" stroke="{AMBER}" stroke-width="2" stroke-dasharray="6 5"/>')
    # The series fills the panel at every x, so the median gets a key in the
    # header rather than a label sitting on top of the data.
    o.append(f'<line x1="{px0}" y1="164" x2="{px0 + 28}" y2="164" stroke="{AMBER}" stroke-width="2" stroke-dasharray="6 5"/>')
    o.append(txt(px0 + 36, 169, 14, AMBER, f"six-year median  {med * 100:.0f}%", 700))

    path = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s["share"]))
    o.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="1.8" stroke-linejoin="round" opacity="0.9"/>')

    # Today, drawn past the end of the cached series.
    xt = px1 + 18
    o.append(f'<line x1="{X(n - 1):.1f}" y1="{Y(s["share"].iloc[-1]):.1f}" x2="{xt:.1f}" y2="{Y(d["today"]):.1f}" stroke="{GREEN}" stroke-width="3" stroke-dasharray="4 3"/>')
    o.append(f'<circle cx="{xt:.1f}" cy="{Y(d["today"]):.1f}" r="8" fill="{GREEN}" stroke="{BG}" stroke-width="2"/>')
    o.append(txt(xt - 14, Y(d["today"]) - 16, 17, GREEN, f"today  {d['today'] * 100:.0f}%", 700, "end"))

    for i, t in enumerate(s["date"]):
        if t.month == 1 and t.day == 1:
            o.append(txt(X(i), py1 + 26, 13, SUB, str(t.year), 400, "middle"))
            o.append(f'<line x1="{X(i):.1f}" y1="{py1}" x2="{X(i):.1f}" y2="{py1 + 6}" stroke="{GRID}"/>')
    o.append(txt(px0, py1 + 52, 14, GREY,
                 f"share of the top {d['topN']} by market cap whose {d['window']}-day return beat Bitcoin's"))

    # By year.
    yy = 660
    o.append(txt(60, yy, 17, TEXT, "HOW OFTEN IT GETS THIS BROAD", 700))
    o.append(txt(60, yy + 22, 14, SUB, "share of days each year with more than half the top 100 beating Bitcoin"))
    yrs = d["years"]
    bw = 1180 / len(yrs)
    for i, y in enumerate(yrs):
        x = 60 + i * bw
        h = y["above"] * 150
        o.append(f'<rect x="{x + 14:.1f}" y="{yy + 150 - h:.1f}" width="{bw - 28:.1f}" height="{h:.1f}" fill="{GREY}" rx="4"/>')
        o.append(txt(x + bw / 2, yy + 150 - h - 10, 17, TEXT, f"{y['above'] * 100:.0f}%", 700, "middle"))
        o.append(txt(x + bw / 2, yy + 176, 15, SUB, str(y["year"]), 400, "middle"))
    o.append(f'<rect x="60" y="{yy + 150}" width="1180" height="1" fill="{GRID}"/>')

    o.append(txt(60, 872, 14, GREY,
                 f"Source: LunarCrush. History to 2026-07-29 from cached daily files, today from the live API. "
                 f"Bitcoin is {d['btc30d'] * 100:+.0f}% over the window."))
    o.append(txt(1240, 872, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "altseason.json").read_text())
    out = HERE / "out" / "altseason.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
