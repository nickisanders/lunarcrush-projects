#!/usr/bin/env python3
"""Every tenfold more an airdrop hands a wallet costs about ten points.

The left panel is one bar per token: the points of allocation retention it
loses for every tenfold increase in what a wallet received, fitted across
that token's ten receipt groups. A rate against the log of the receipt is
the comparable version of the gap between the smallest and largest group,
which is not comparable at all: a token whose groups barely differ in size
has no room to show a difference in outcome, so its gap is small for
arithmetic reasons rather than behavioural ones.

The right panel is that objection tested. If the gap only looked bigger on
wider giveaways because the range was wider, the rate should be flat
against the range, and it is: r is -0.05 with a jackknife that sits on zero
from both sides. The rate is the same whether a token spread its
allocations across two decades or five, which also retires the idea that a
flatter giveaway decays more gently. It decays at the same rate over a
shorter distance.

Nothing measured here explains why some tokens are three times steeper than
others. Age, crowd size and the share of holders who cannot transact all
come back weak.

A token whose groups span less than a decade has no rate. Dividing a small
difference in outcome by a small difference in size is noise, and the
flattest giveaway in the set returned +96.8 points before the floor.

Reads out/receipt-deciles.json.

Usage: python3 allocation_rate.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"

W = 1240
L, R = 60, 1180


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Per-character widths read back off a render: Charter sets at about 0.415 of
# its point size and 0.53 bold. A line that will not fit says so at render
# time instead of being drawn clipped.
def fits(x, size, s, weight=400):
    width = len(str(s)) * size * (0.53 if weight >= 700 else 0.415)
    if width > R - x:
        over = int((width - (R - x)) / (size * 0.415))
        print(f"  WARNING: {size}px line runs ~{over} characters past the "
              f"margin: {str(s)[:60]}...", flush=True)


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    if anchor == "start" and font is None:
        fits(x, size, s, weight)
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>'
           f'{body}</svg>')
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('  {name}.png',i.width+'x'+i.height));"], check=True)


doc = json.loads((ROOT / "receipt-deciles.json").read_text())
st = doc["rate"]
rows = sorted((r for r in doc["per_token"] if r["rate_kept"] is not None),
              key=lambda r: r["rate_kept"])
med = st["median_kept"]
jl, jh = st["spread_vs_rate_jackknife"]
steep, gentle = rows[0], rows[-1]
# Named by rule: the two ends of the panel and the largest crowd on it, so
# the labels cannot be a selection.
biggest = max(rows, key=lambda r: r["recipients"])
NAMED = {steep["sym"], gentle["sym"], biggest["sym"]}

PW, PH, PGAP = 520, 560, 70
PX1, PX2 = L + 44, L + 44 + PW + PGAP
TOP = 300
lo = min(r["rate_kept"] for r in rows)
hi = max(0.0, max(r["rate_kept"] for r in rows))

b = [txt(L, 58, 37, INK, "Every tenfold more an airdrop gave a wallet", 700),
     txt(L, 98, 37, INK, "costs about ten points of its chances.", 700),
     txt(L, 138, 20, SUB,
         f"Left: one bar per token, the points of allocation retention lost "
         f"for each tenfold rise in what a wallet received,"),
     txt(L, 164, 20, SUB,
         f"fitted across that token's ten receipt groups. "
         f"{st['negative_kept']} of the {st['tokens']} lose ground."),
     txt(L, 190, 20, SUB,
         "Right: the same rate against how far a token spread its "
         "allocations, which is the objection that the left panel is a "
         "range effect.")]


def ry(v):
    return TOP + PH * (hi - v) / (hi - lo)


b.append(txt(PX1, TOP - 22, 17, SUB, "points of kept, per tenfold"))
zero = ry(0.0)
b.append(f'<line x1="{PX1}" y1="{zero:.0f}" x2="{PX1+PW}" y2="{zero:.0f}" '
         f'stroke="{RULE}" stroke-width="2"/>')
BW = PW / len(rows)
for i, r in enumerate(rows):
    x = PX1 + i * BW
    v = r["rate_kept"]
    y0, y1 = (ry(v), zero) if v < 0 else (zero, ry(v))
    col = HOT if r["sym"] in NAMED else BRAND
    b.append(f'<rect x="{x:.1f}" y="{min(y0,y1):.1f}" width="{BW-1.6:.1f}" '
             f'height="{abs(y1-y0):.1f}" fill="{col}"/>')
    if r["sym"] in NAMED:
        # Placed at the tip and inside the bar, these printed through their
        # own ink. A negative bar hangs below the zero line, so its tip is
        # the bottom and the label belongs under it.
        ly = ry(v) + 20 if v < 0 else ry(v) - 12
        b.append(txt(x + BW / 2, ly, 15, HOT,
                     "$" + r["sym"], 700, "middle", MONO))
my = ry(med)
b.append(f'<line x1="{PX1}" y1="{my:.0f}" x2="{PX1+PW}" y2="{my:.0f}" '
         f'stroke="{INK}" stroke-width="2" stroke-dasharray="4 5"/>')
b.append(txt(PX1 + PW, my - 10, 16, INK, f"median {med:.1f}", 700, "end"))

decs = [r["decades"] for r in rows]
dlo, dhi = min(decs), max(decs)
b.append(txt(PX2, TOP - 22, 17, SUB, "decades of allocation spanned"))
for i in range(5):
    v = lo + (hi - lo) * i / 4
    y = ry(v)
    b.append(f'<line x1="{PX2}" y1="{y:.0f}" x2="{PX2+PW}" y2="{y:.0f}" '
             f'stroke="{RULE}" stroke-width="1"/>')
    b.append(txt(PX2 - 10, y + 6, 15, SUB, f"{v:.0f}", 400, "end"))
for r in rows:
    cx = PX2 + PW * (r["decades"] - dlo) / (dhi - dlo)
    cy = ry(r["rate_kept"])
    named = r["sym"] in NAMED
    b.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{7 if named else 5}" '
             f'fill="{HOT if named else BRAND}" '
             f'opacity="{1 if named else 0.5}"/>')
    if named:
        half = len(r["sym"]) * 5 + 6
        lx = min(max(cx, PX2 + half), PX2 + PW - half)
        # Clamped below the panel caption, which the topmost dot's label
        # was printing through.
        b.append(txt(lx, max(cy - 13, TOP + 14), 15, HOT, "$" + r["sym"],
                     700, "middle", MONO))
for i in range(4):
    v = dlo + (dhi - dlo) * i / 3
    b.append(txt(PX2 + PW * i / 3, TOP + PH + 26, 15, SUB,
                 f"{v:.1f}", 400, "middle"))
b.append(txt(PX2, TOP + PH + 52, 17, SUB,
             f"r = {st['spread_vs_rate']:.2f}, jackknife {jl:.2f} to {jh:.2f}"))

y = TOP + PH + 92
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"The median token loses {abs(med):.1f} points for every "
             f"tenfold rise in what it handed a wallet.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Half the tokens sit between "
             f"{abs(st['quartiles_kept'][2]):.1f} and "
             f"{abs(st['quartiles_kept'][0]):.1f} points, and "
             f"{st['negative_kept']} of {st['tokens']} are losing ground at "
             f"all."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"On a balance above zero, the figure airdrop reports quote, "
             f"the same fit reads {st['median_holding']:.1f} points and "
             f"holds on {st['negative_holding']} of them."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"${steep['sym']} loses {abs(steep['rate_kept']):.1f} points a "
             f"decade and ${gentle['sym']} "
             f"{abs(gentle['rate_kept']):.1f}, across the same ten groups "
             f"cut the same way."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "The gap between a token's smallest and largest group is not "
             "comparable across tokens, because the groups are further apart "
             "on some"))
b.append(txt(L, y + 58, 19, SUB,
             "than others. The rate is, and it does not move with that "
             "distance, so a flatter giveaway decays just as fast over less "
             "ground."))
b.append(txt(L, y + 84, 19, SUB,
             f"Nothing measured explains the spread between tokens. Age, "
             f"crowd size and the share of holders who cannot transact all "
             f"come back weak."))
b.append(txt(L, y + 110, 19, SUB,
             f"A token whose groups span under {st['min_decades']:.0f} "
             f"decade has no rate: the flattest giveaway in the set returned "
             f"+96.8 points before that floor."))
b.append(txt(L, y + 136, 19, SUB,
             "Nothing here is priced. Why a position shrank is not visible "
             "from the chain, and nothing here says it was sold."))
b.append(txt(R, y + 164, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 196
render("allocation_rate", W, H, "".join(b))
print(f"  {st['tokens']} tokens, median {med:.2f} points per tenfold, "
      f"spread vs rate r={st['spread_vs_rate']:.3f}")
