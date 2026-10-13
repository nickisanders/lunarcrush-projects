#!/usr/bin/env python3
"""Chart: spam share follows the working week, and the event did not move it.

Reads out/spam_baseline.json, so the figure always matches the last run.

Usage: python3 chart.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, TRACK, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#161b22"
RED, GREEN, BLUE, GREY, AMBER = "#f85149", "#3fb950", "#58a6ff", "#6e7681", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, monospace"
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Tall enough for the event panels plus the two closing lines. At 820 the
# verdict and the footer were drawn on top of the panels.
W, H = 1200, 960


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{body}</text>')


def main() -> None:
    d = json.loads((HERE / "out" / "spam_baseline.json").read_text())
    base = d["baseline"]

    b = [txt(60, 60, 36, TEXT, "Spam share keeps office hours", 700),
         txt(60, 94, 20, SUB,
             f"Median share of posts labelled spam, by weekday, across {d['coins']} "
             f"coins over {d['days']} days")]

    TOP, COLW, BASEY, HMAX = 150, 140, 470, 250
    shares = [base[k]["median_share"] for k in DOW if k in base]
    lo, hi = min(shares) * 0.92, max(shares) * 1.02
    for i, k in enumerate(DOW):
        if k not in base:
            continue
        v = base[k]["median_share"]
        x = 110 + i * COLW
        h = HMAX * (v - lo) / max(hi - lo, 1e-9)
        col = AMBER if k in ("Sat", "Sun") else GREY
        b.append(f'<rect x="{x}" y="{BASEY-h:.0f}" width="{COLW-46}" height="{h:.0f}" '
                 f'rx="4" fill="{col}"/>')
        b.append(txt(x + (COLW-46)/2, BASEY - h - 16, 23, col, f"{v*100:.1f}%", 700, "middle", MONO))
        b.append(txt(x + (COLW-46)/2, BASEY + 30, 20, SUB, k, 400, "middle"))
    b.append(f'<rect x="100" y="{BASEY}" width="1000" height="1.5" fill="{TRACK}"/>')

    y = BASEY + 70
    b.append(f'<rect x="60" y="{y}" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, y + 44, 25, TEXT,
                 f"Weekends run {d['weekend_gap_points']:+.1f} points above the working week.",
                 700))
    b.append(txt(60, y + 78, 20, SUB,
                 "Real people post less at the weekend. Automated posting does not care "
                 "what day it is,"))
    b.append(txt(60, y + 104, 20, SUB, "so its share of the total rises."))

    ev = d.get("event")
    if ev:
        yy = y + 150
        b.append(txt(60, yy, 23, TEXT,
                     f"Tested against {ev['date']}, each day versus its own weekday:", 700))
        for i, t in enumerate(ev["days"]):
            x = 60 + i * 215
            col = GREEN if t["change_pct"] < 0 else RED
            b.append(f'<rect x="{x}" y="{yy+22}" width="195" height="86" rx="6" fill="{PANEL}"/>')
            b.append(txt(x + 16, yy + 50, 18, SUB, f"{t['day'][5:]}  {t['dow']}"))
            b.append(txt(x + 16, yy + 88, 28, col, f"{t['change_pct']:+.1f}%", 700, "start", MONO))
        b.append(txt(60, yy + 148, 23, TEXT,
                     f"{ev['days_below']} of {len(ev['days'])} days below baseline, "
                     f"median {ev['median_change_pct']:+.1f}%.", 700))
        b.append(txt(60, yy + 180, 20, RED,
                     "No drop. A real one would put most days below the line, not one.", 700))

    b.append(txt(60, H - 22, 16, SUB, "Source: LunarCrush"))
    b.append(txt(1140, H - 22, 16, SUB,
                 "github.com/nickisanders/lunarcrush-projects", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    (HERE / "out" / "spam_baseline.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/spam_baseline.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/spam_baseline.png')"
        f".then(i=>console.log('out/spam_baseline.png',i.width+'x'+i.height));"], check=True)


if __name__ == "__main__":
    main()
