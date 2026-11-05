#!/usr/bin/env python3
"""635,160 wallets received $EIGEN. 28,550 still hold a full allocation.

The second-largest distribution in the baseline, and the one where the gap
between the headline number and the number of people still holding anything
worth holding is widest. Three nested bars, each a strict subset of the one
above it: everyone who ever received the token, everyone who still holds any
of it, and everyone still sitting on most of a full-size allocation.

The last step is deliberately price-free. A dollar cut would be the obvious
one and $EIGEN has fallen far enough that it would do most of the work by
itself, so the bar is drawn on what a wallet holds against what a typical
recipient of this token received. The dollar figure is in the callout, where
the caveat can sit next to it rather than being implied by a bar.

"Full allocation" means the wallet received at least as much as the median
recipient and still holds at least 90% of it. A wallet that received less
than the median and never moved it is not in that bar, which is the point:
it is counted in the holder number and it never had a position.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 eigen_funnel.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
SYM = "eigen"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None, op=1.0):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="{op}" '
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


doc = json.loads(SRC.read_text())
d = doc["tokens"][SYM]
dust, k = d["dust"], d["dust"]["kinds"]
n = k["classified"]
full = round(k["untouched_large"] * n)
over100 = round(dust["usd_100_share"] * n)
under1 = round(dust["usd_under_1_share"] * n)
gone = round(k["exited_leaving_dust"] * n)

STEPS = [(d["arrived"], "ever received it", BRAND, 1.0),
         (d["kept"], "still hold any of it", BRAND, 0.55),
         (full, "still hold most of a full allocation", BRAND, 1.0)]

W = 1240
L, R = 60, 1180
BH, GAP = 96, 58
top = max(s[0] for s in STEPS)

b = [txt(L, 58, 37, INK, f"{d['arrived']:,} wallets received ${SYM.upper()}.", 700),
     txt(L, 98, 37, INK, f"{full:,} still hold a full allocation.", 700),
     txt(L, 140, 20, SUB,
         "Each bar is a strict subset of the one above it. The last one is "
         "price-free: it counts a wallet that received at least as much as"),
     txt(L, 166, 20, SUB,
         "the median recipient and has kept at least 90% of it, so a falling "
         "price cannot do the work for it.")]

y = 228
for i, (val, label, col, op) in enumerate(STEPS):
    w = (R - L) * val / top
    b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{L}" y="{y}" width="{w:.1f}" height="{BH}" fill="{col}" '
             f'fill-opacity="{op}"/>')
    # The third bar is 4.5% of the first, so a number set inside it would be
    # wider than the bar. Anything under a fifth of the width is labeled
    # outside, in ink, which also keeps the smallest figure the most legible.
    num = f"{val:,}"
    # The label trails the number at a fixed offset rather than being pinned to
    # an edge, so all three read as the same object whether the number sits
    # inside its bar or beside it.
    if w > 300:
        b.append(txt(L + 20, y + BH / 2 + 12, 33, "#ffffff", num, 700,
                     "start", MONO))
        b.append(txt(L + 20 + len(num) * 19.8 + 18, y + BH / 2 + 10, 21,
                     "#ffffff", label))
    else:
        b.append(txt(L + w + 18, y + BH / 2 + 12, 33, INK, num, 700,
                     "start", MONO))
        b.append(txt(L + w + 18 + len(num) * 19.8 + 18, y + BH / 2 + 10, 21,
                     SUB, label))
    # The first bar is the denominator, so annotating it as 100% of itself
    # says nothing.
    if i:
        b.append(txt(R, y - 10, 18, SUB,
                     f"{val / top * 100:.1f}% of everyone who received it",
                     400, "end", MONO))
    y += BH + GAP

y -= GAP - 18
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="172" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="172" fill="{HOT}"/>')
b.append(txt(L + 26, y + 40, 23, INK,
             f"The median ${SYM.upper()} holder is sitting on "
             f"{dust['median_tokens']:.1f} tokens, worth "
             f"${dust['median_usd']:.2f}.", 700))
b.append(txt(L + 26, y + 72, 23, INK,
             f"{over100:,} of the {n:,} hold more than $100 of it.", 700))
b.append(txt(L + 26, y + 104, 20, SUB,
             f"That dollar line moves with the price and ${SYM.upper()} has "
             f"fallen a long way, so read it as where the token is now rather "
             f"than"))
b.append(txt(L + 26, y + 130, 20, SUB,
             f"what anyone did. {gone:,} of these wallets sold out and left a "
             f"tail behind, which is a fact about behavior and does not move"))
b.append(txt(L + 26, y + 156, 20, SUB,
             "with the price at all."))
y += 212

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"Every transfer since the contract's first block, joined to who "
             f"holds today. {d['arrived']:,} addresses received it across "
             f"{d['age_months']} months."))
b.append(txt(L, y + 58, 19, SUB,
             f"A holder count asks whether an address has a balance. It never "
             f"asks how much, or whether the address ever chose to have it."))
b.append(txt(R, y + 84, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 112

render("eigen_funnel", W, H, "".join(b))
print(f"  arrived {d['arrived']:,}  kept {d['kept']:,}  full {full:,}")
print(f"  over $100 {over100:,}  under $1 {under1:,}  exited {gone:,}")
