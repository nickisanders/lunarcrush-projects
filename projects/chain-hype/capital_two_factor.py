#!/usr/bin/env python3
"""Fees per dollar parked, split into the two things it was hiding.

The single ratio was objected to twice in a day from opposite directions:
that it rewards bot flow, and that it rewards leverage and fast blocks. Both
are the same objection. Fees per dollar of TVL is a product:

    fees per $1,000  =  turnover  x  take rate  x  1,000

Turnover is how many times the capital moved, 30-day DEX volume over TVL.
Take rate is what the chain collected per dollar of that volume. One number
is velocity and the other is pricing, and the old chart multiplied them
together and called the result efficiency.

A scatter rather than bars because the point is two-dimensional. The dashed
diagonals are lines of equal fees per $1,000, so a chain's distance from the
origin is the old number and its position along the diagonal is how it got
there. Near and Hyperliquid sit near the same diagonal by opposite routes:
Near moves capital three times as often and charges a tenth as much.

Log scales on both axes, because turnover spans 0.3x to 24x and a linear
axis would pile nine chains into one corner.

Caveat the chart carries: turnover here is DEX volume only. DeFiLlama's
derivatives data is paywalled, so perpetuals are missing and Hyperliquid's
real turnover is far above what is plotted.

Usage: python3 capital_two_factor.py
"""

import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "out" / "usage.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
BRAND, HOT, DIM = "#1b3a6b", "#a33228", "#b9b2a4"
MIN_TVL = 100_000_000

# Where a label sits relative to its dot, for the pairs that would collide.
# (dx, dy, anchor). BSC and Arbitrum sit close enough that both needed an
# explicit side, not just a vertical offset: nudging both right rendered
# them straight through each other as "ArbBSCum".
NUDGE = {"Polygon": (0, -26, "middle"), "Hyperliquid": (0, -26, "middle"),
         "Sui": (0, 30, "middle"), "Cronos": (0, 30, "middle"),
         "BSC": (18, -12, "start"), "Arbitrum": (-18, 30, "end")}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


rows = [r for r in json.loads(SRC.read_text()) if r["tvl"] >= MIN_TVL and r["dex"] > 0]
for r in rows:
    r["turnover"] = r["dex"] / r["tvl"]
    r["take"] = r["fees"] / r["dex"]
    r["per1k"] = r["fees"] / r["tvl"] * 1000
    r["short"] = r["chain"].replace(" L1", "")

W, H = 1240, 1080
L, R, T, B = 230, 1160, 210, 820                     # plot box

xs = [math.log10(r["turnover"]) for r in rows]
ys = [math.log10(r["take"]) for r in rows]
x0, x1 = min(xs) - 0.22, max(xs) + 0.22
y0, y1 = min(ys) - 0.18, max(ys) + 0.18
px = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (R - L)
py = lambda v: B - (math.log10(v) - y0) / (y1 - y0) * (B - T)

b = [txt(60, 58, 37, INK, "The same fee revenue, reached two", 700),
     txt(60, 98, 37, INK, "completely different ways.", 700),
     txt(60, 136, 20, SUB,
         "Fees per $1,000 of TVL is turnover multiplied by take rate. "
         "Plotting them apart shows which one a chain is actually doing."),
     txt(60, 164, 20, SUB,
         "Dashed lines join chains earning the same fees per $1,000.")]

# iso-lines: take = V / (1000 * turnover)
for v, lab in ((1, "$1"), (10, "$10"), (100, "$100")):
    pts = []
    for t in (10 ** x0, 10 ** x1):
        take = v / (1000 * t)
        if y0 <= math.log10(take) <= y1:
            pts.append((px(t), py(take)))
    if len(pts) < 2:                       # clip the line to the box corners
        for take in (10 ** y0, 10 ** y1):
            t = v / (1000 * take)
            if x0 <= math.log10(t) <= x1:
                pts.append((px(t), py(take)))
    if len(pts) >= 2:
        (ax, ay), (bx, by) = pts[0], pts[1]
        b.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" '
                 f'stroke="{RULE}" stroke-width="2" stroke-dasharray="7 7"/>')
        ly = by - 10 if by - 10 > T + 16 else by + 26
        b.append(txt(bx - 8, ly, 18, DIM, f"{lab} per $1,000", 400, "end"))

b.append(f'<rect x="{L}" y="{T}" width="{R-L}" height="{B-T}" fill="none" '
         f'stroke="{RULE}" stroke-width="2"/>')

for v in (0.3, 1, 3, 10, 30):
    if x0 <= math.log10(v) <= x1:
        b.append(f'<line x1="{px(v):.0f}" y1="{B}" x2="{px(v):.0f}" y2="{B+8}" '
                 f'stroke="{RULE}" stroke-width="2"/>')
        b.append(txt(px(v), B + 32, 19, SUB, f"{v:g}x", 400, "middle", MONO))
for v in (0.002, 0.005, 0.01, 0.02):
    if y0 <= math.log10(v) <= y1:
        b.append(f'<line x1="{L-8}" y1="{py(v):.0f}" x2="{L}" y2="{py(v):.0f}" '
                 f'stroke="{RULE}" stroke-width="2"/>')
        b.append(txt(L - 16, py(v) + 7, 19, SUB, f"{v*100:g}%", 400, "end", MONO))

b.append(txt((L + R) / 2, B + 66, 21, INK,
             "Turnover: times the capital moved in 30 days", 700, "middle"))
b.append(f'<text x="{70}" y="{(T+B)/2}" font-size="21" fill="{INK}" font-weight="700" '
         f'text-anchor="middle" font-family="{FONT}" '
         f'transform="rotate(-90 70 {(T+B)/2:.0f})">Take rate: fees per dollar of volume</text>')

for r in rows:
    x, y = px(r["turnover"]), py(r["take"])
    col = BRAND if r["short"] in ("Ethereum", "Tron") else HOT
    b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="{col}"/>')
    dx, dy, anchor = NUDGE.get(r["short"], (16, 7, "start"))
    b.append(txt(x + dx, y + dy, 21, INK, r["short"], 700, anchor, MONO))

h = next(r for r in rows if r["short"] == "Hyperliquid")
n = next(r for r in rows if r["short"] == "Near")
y = B + 108
b.append(f'<rect x="60" y="{y}" width="{1180-60}" height="84" fill="#fbf7ef"/>')
b.append(f'<rect x="60" y="{y}" width="5" height="84" fill="{BRAND}"/>')
b.append(txt(86, y + 34, 22, INK,
             f"Near moves its capital {n['turnover']/h['turnover']:.1f}x as often as "
             f"Hyperliquid and charges {h['take']/n['take']:.0f}x less for it.", 700))
b.append(txt(86, y + 64, 20, SUB,
             "Velocity and pricing are different businesses. The old chart "
             "multiplied them and called the product efficiency."))

y += 112
b.append(f'<line x1="60" y1="{y}" x2="1180" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
# One line of this ran off the canvas at 19px. Two lines, and the credit
# gets its own, which is the same fix the other charts needed.
b.append(txt(60, y + 32, 19, SUB,
             "Turnover is DEX volume only. DeFiLlama's derivatives data is paywalled,"))
b.append(txt(60, y + 58, 19, SUB,
             "so perpetuals are missing and Hyperliquid sits well left of where it belongs."))
b.append(txt(1180, y + 84, 19, SUB, "measured 2026-10-20  ·  @nickisanders", 400, "end"))
H = y + 114

render("capital_two_factor", W, H, "".join(b))
