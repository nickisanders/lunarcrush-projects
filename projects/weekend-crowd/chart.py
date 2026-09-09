#!/usr/bin/env python3
"""Chart the weekend blind spot and what fixing it bought.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, GREEN, GREY, BLUE = "#f85149", "#3fb950", "#6e7681", "#58a6ff"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


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


def render(d: dict, r: dict) -> str:
    W, H = 1300, 940
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "My spike detector has a weekend blind spot.", 700))
    o.append(txt(60, 112, 20, SUB, "Fixing it was worth nothing. 450,790 coin-days, 2020 to 2026."))

    # Two panels of weekday bars.
    panels = [(60, "STANDARD Z-SCORE", "standard", "weekend deficit  -19.5%", RED),
              (700, "AFTER REMOVING THE WEEKLY CYCLE", "deseasoned", "weekend deficit  +1.3%", GREEN)]
    top = 240
    bh = 200
    mx = max(max(d["byDay"][k][s] for k in DAYS) for s in ("standard", "deseasoned"))
    for x0, head, key, note, col in panels:
        o.append(txt(x0, top - 84, 17, TEXT, head, 700))
        o.append(txt(x0, top - 58, 16, col, note, 700))
        bw, gap = 62, 16
        for i, day in enumerate(DAYS):
            v = d["byDay"][day][key]
            h = v / mx * bh
            x = x0 + i * (bw + gap)
            y = top + bh - h
            wknd = day in ("Sat", "Sun")
            fill = col if wknd else GREY
            o.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{h:.1f}" fill="{fill}" rx="3"/>')
            o.append(txt(x + bw / 2, y - 10, 15, TEXT if wknd else SUB, f"{v * 100:.2f}%",
                         700 if wknd else 400, "start" if False else "middle"))
            o.append(txt(x + bw / 2, top + bh + 26, 16, TEXT if wknd else SUB, day,
                         700 if wknd else 400, "middle"))
        o.append(f'<rect x="{x0}" y="{top + bh + 1}" width="{7 * (bw + gap) - gap}" height="1" fill="#30363d"/>')

    o.append(txt(60, top + bh + 66, 16, SUB, "Share of eligible coin-days that register a spike, by weekday."))

    # The verdict strip.
    vy = 520
    o.append(f'<rect x="60" y="{vy}" width="1180" height="212" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, vy + 40, 21, TEXT, "The fix works. It finds 12.9% more weekend events.", 700))
    o.append(txt(84, vy + 72, 18, SUB, "Then those events were scored against the same baseline as everything else:"))

    res = {(x["comparison"].split(" vs ")[0], x["horizon"]): x
           for x in r["results"] if x["metric"] == "hit_rate_adj"}
    lines = [("Events both scorers agree on", "kept", GREEN),
             ("Events only the fixed scorer finds", "recovered", RED)]
    ly = vy + 112
    for label, g, col in lines:
        row = res[(g, "+3d")]
        n = r["counts"][g]
        o.append(f'<rect x="84" y="{ly - 20}" width="8" height="28" fill="{col}" rx="2"/>')
        o.append(txt(108, ly, 18, TEXT, f"{label}  (n={n})", 700))
        sign = "+" if row["diff"] >= 0 else ""
        o.append(txt(760, ly, 20, col, f"{sign}{row['diff'] * 100:.1f}pp", 700))
        o.append(txt(880, ly, 17, SUB, f"beats BTC at +3d,  p = {row['p_two_sided']:.3f}"))
        ly += 50

    o.append(txt(60, vy + 260, 19, TEXT,
                 "The events the blind spot was hiding are the ones that were never worth having.", 700))
    o.append(txt(60, vy + 290, 18, SUB,
                 "Weekend spikes that clear the bar on their own perform like weekday spikes: -0.6pp, p = 0.95."))

    o.append(txt(60, 906, 16, GREY, "Source: LunarCrush daily history, 1,000 coins. Month-block bootstrap, 2,000 iterations."))
    o.append(txt(1240, 906, 16, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "deseason.json").read_text())
    r = json.loads((HERE / "out" / "recovered.json").read_text())
    out = HERE / "out" / "weekend.svg"
    out.write_text(render(d, r))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
