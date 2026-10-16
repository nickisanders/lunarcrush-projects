#!/usr/bin/env python3
"""Who the biggest Polymarket addresses actually are, from out/traders.json.

Breadth against maker share separates a bet from a business. An address quoting
thousands of outcomes at a high maker share is running inventory; one holding a
position in sixty is expressing a view. Plotting the two axes puts them in
different corners of the chart, which is the whole finding.

The x axis counts outcome tokens rather than markets. Every Polymarket binary
market has exactly two, YES and NO, and the Oct 15 reward snapshot shares no
token ids with the Oct 2-7 fills, so there is no way to collapse legs into
questions here. Outcomes is what the number counts, so outcomes is what it says.

Usage: python3 furniture.py
"""

import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
NEUTRAL, BRAND, HOT = "#8d8578", "#1b3a6b", "#a33228"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


d = json.loads((HERE / "out" / "traders.json").read_text())
TOP = d["top10"]

W, H = 1200, 960
L, R = 60, 1140

b = [txt(L, 58, 36, INK, "The median Polymarket trader bet $92.", 700),
     txt(L, 96, 36, INK, "The biggest one did not really bet at all.", 700),
     txt(L, 132, 20, SUB,
         f"Every fill on chain, 2 to 7 October, mint legs removed. "
         f"${d['notional']/1e6:.0f}M between {d['addresses']:,} addresses.")]

# Concentration, stated before the scatter so the scatter is about the top of
# a distribution the reader already has a size for.
y = 186
cards = [(f"{d['median_volume']:.0f}", "median address,\nover 10 fills"),
         ("76%", "of volume from the\ntop 1,000 addresses"),
         (f"{d['over']['10000']:,}", "addresses cleared\n$10,000 all week")]
cw = (R - L) / 3
for i, (big, small) in enumerate(cards):
    x = L + i * cw
    b.append(txt(x, y + 16, 50, INK, "$" + big if i == 0 else big, 700, "start", MONO))
    for j, ln in enumerate(small.split("\n")):
        b.append(txt(x, y + 52 + j * 26, 19, SUB, ln))
b.append(f'<line x1="{L}" y1="{y+118}" x2="{R}" y2="{y+118}" stroke="{RULE}" stroke-width="2"/>')

# The scatter. Log x because breadth spans 62 to 11,680 and a linear axis would
# stack every market maker on the right edge.
AX, AY, AW, AH = L + 70, 360, R - L - 110, 360
b.append(txt(L, AY - 24, 23, INK, "The ten largest addresses, by what they traded and how", 700))
b.append(f'<line x1="{AX}" y1="{AY+AH}" x2="{AX+AW}" y2="{AY+AH}" stroke="{RULE}" stroke-width="2"/>')
b.append(f'<line x1="{AX}" y1="{AY}" x2="{AX}" y2="{AY+AH}" stroke="{RULE}" stroke-width="2"/>')

LO, HI = math.log10(40), math.log10(16000)
px = lambda n: AX + AW * (math.log10(max(n, 40)) - LO) / (HI - LO)
py = lambda m: AY + AH * (1 - m)

for n in (100, 1000, 10000):
    b.append(f'<line x1="{px(n):.0f}" y1="{AY}" x2="{px(n):.0f}" y2="{AY+AH}" stroke="{RULE}" stroke-width="1"/>')
    b.append(txt(px(n), AY + AH + 30, 19, SUB, f"{n:,}", 400, "middle", MONO))
for m, lab in ((0, "0%"), (0.5, "50%"), (1.0, "100%")):
    b.append(txt(AX - 14, py(m) + 7, 19, SUB, lab, 400, "end", MONO))
b.append(txt(AX + AW / 2, AY + AH + 68, 20, SUB, "outcomes traded (log scale)", 400, "middle"))
b.append(f'<text x="{L+16}" y="{AY+AH/2}" font-size="20" fill="{SUB}" font-family="{FONT}" '
         f'text-anchor="middle" transform="rotate(-90 {L+16} {AY+AH/2})">maker share</text>')

for t in TOP:
    wide = t["tokens"] >= 500
    col = NEUTRAL if wide else HOT
    r = 9 + 16 * (t["volume"] / max(x["volume"] for x in TOP)) ** 0.5
    b.append(f'<circle cx="{px(t["tokens"]):.1f}" cy="{py(t["maker_share"]):.1f}" r="{r:.1f}" '
             f'fill="{col}" fill-opacity="{0.45 if wide else 0.9}"/>')

big = max(TOP, key=lambda t: t["volume"])
b.append(txt(px(big["tokens"]), py(big["maker_share"]) - 34, 19, INK,
             f"${big['volume']/1e6:.0f}M, {big['tokens']:,} outcomes", 700, "middle"))
taker = min(TOP, key=lambda t: t["maker_share"])
b.append(txt(px(taker["tokens"]) - 24, py(taker["maker_share"]) - 22, 19, INK,
             f"{taker['fills']:,} fills, 0% maker", 700, "end"))
for t in sorted(TOP, key=lambda t: t["tokens"])[:2]:
    b.append(txt(px(t["tokens"]), py(t["maker_share"]) - 30, 19, HOT,
                 f"${t['volume']/1e6:.1f}M in {t['tokens']}", 700, "middle"))

LY = AY + AH + 124
b.append(f'<circle cx="{L+8}" cy="{LY-7}" r="8" fill="{HOT}"/>')
b.append(txt(L + 26, LY, 19, INK, "a position you could explain out loud"))
b.append(f'<circle cx="{L+470}" cy="{LY-7}" r="8" fill="{NEUTRAL}" fill-opacity="0.45"/>')
b.append(txt(L + 488, LY, 19, SUB, "quoting the board, or a bot hitting it"))

y = H - 54
b.append(f'<line x1="{L}" y1="{y-40}" x2="{R}" y2="{y-40}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y, 27, INK, "You are mostly trading with the furniture.", 700))
b.append(txt(R, y, 17, SUB, "@nickisanders", 400, "end"))

render("furniture", W, H, "".join(b))
