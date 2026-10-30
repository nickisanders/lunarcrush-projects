#!/usr/bin/env python3
"""How much of a holder count is holding less than it costs to sell.

Each row is one token. The left dot is the share of its holders whose whole
position is worth less than a swap at today's gas price, the right dot is the
same share at 20 gwei, and the bar between them is how much of the holder
count moves from "could sell" to "would lose money selling" as gas returns to
ordinary. Today is unusually cheap, so one number alone would mislead in
whichever direction it was picked.

This is the third way a holder count overstates the people inside it, after
holders who cannot pay gas at all and holders who already left and still get
counted. It is the mildest and the largest. Nobody is trapped and nothing was
done to anyone: airdrops land small and gas costs what it costs. It does mean
a retention figure is partly a map of what is not worth selling.

Reads out/sell-cost.json from proof-of-crowd-tools.

Usage: python3 sell_cost_chart.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "sell-cost.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
LINK = "#b9c4d6"
MIN_HOLDERS = 100
LEAD = "drv"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def money(v):
    if v >= 1000:
        return f"${v:,.0f}"
    if v >= 1:
        return f"${v:,.2f}"
    return f"${v:.3f}".rstrip("0").rstrip(".")


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
rows = [dict(sym=k.upper(), key=k, **v) for k, v in doc["tokens"].items()
        if v["holders"] >= MIN_HOLDERS]
if len(rows) < 5:
    raise SystemExit(f"  only {len(rows)} tokens above {MIN_HOLDERS} holders")
rows.sort(key=lambda r: -r["below_reference"])
med_live = statistics.median(r["below_live"] for r in rows)
med_ref = statistics.median(r["below_reference"] for r in rows)
lead = next((r for r in rows if r["key"] == LEAD), rows[0])

cheap, dear = doc["swap_cost_live"], doc["swap_cost_reference"]
gl, gr = doc["gas_gwei_live"], doc["gas_gwei_reference"]

W = 1240
L, R = 60, 1180
LABEL = 112
RIGHT = 152
BARW = R - L - LABEL - RIGHT
BH, GAP = 26, 6
X0 = L + LABEL

# "Most" is true of the median token at an ordinary gas price and not true
# today, so the headline says which one it means rather than leaning on the
# subhead to walk it back.
b = [txt(L, 58, 37, INK, "At ordinary gas, most of a holder count", 700),
     txt(L, 98, 37, INK, "is holding less than it costs to sell.", 700),
     txt(L, 138, 20, SUB,
         "Share of each token's holders whose entire position is worth less "
         "than one swap, at 180,000 gas."),
     txt(L, 164, 20, SUB,
         f"Gas is unusually cheap today at {gl:.2f} gwei, so the ordinary "
         f"price is shown beside it rather than instead of it.")]

y = 214
bars_top = y
marks = []
for r in rows:
    xl = X0 + BARW * r["below_live"]
    xr = X0 + BARW * r["below_reference"]
    hot = r["key"] == LEAD
    b.append(txt(L, y + BH - 7, 17, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    # The span is the finding: it is how much of the holder count changes
    # side when gas goes back to normal.
    b.append(f'<rect x="{min(xl,xr):.1f}" y="{y+BH/2-4:.0f}" '
             f'width="{abs(xr-xl):.1f}" height="8" fill="{LINK}"/>')
    b.append(f'<circle cx="{xl:.1f}" cy="{y+BH/2:.0f}" r="7" fill="{BRAND}"/>')
    b.append(f'<circle cx="{xr:.1f}" cy="{y+BH/2:.0f}" r="7" '
             f'fill="{HOT if hot else "#7a2a22"}"/>')
    marks.append(txt(xr + 14, y + BH - 7, 16, INK if hot else SUB,
                     f"{r['below_reference']*100:.0f}%", 700 if hot else 400, "start", MONO))
    b.append(txt(R, y + BH - 7, 16, SUB, money(r["median_usd"]), 400, "end", MONO))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(R, bars_top - 10, 15, SUB, "median position", 400, "end"))

for share, col, lab in ((med_live, BRAND, f"median {med_live*100:.0f}%"),
                        (med_ref, HOT, f"median {med_ref*100:.0f}%")):
    mx = X0 + BARW * share
    b.append(f'<line x1="{mx:.1f}" y1="{bars_top-6}" x2="{mx:.1f}" y2="{bars_bot+6}" '
             f'stroke="{col}" stroke-width="2" stroke-dasharray="3 4" opacity="0.5"/>')
    b.append(txt(mx + 9, bars_bot + 26, 18, col, lab, 700))
b.extend(marks)

y = bars_bot + 52
sw = (R - L) / 2
for i, (col, label) in enumerate(
        ((BRAND, f"today, {gl:.2f} gwei: a swap costs {money(cheap)}"),
         (HOT, f"at {gr:g} gwei: a swap costs {money(dear)}"))):
    x = L + i * sw
    b.append(f'<circle cx="{x+8:.0f}" cy="{y+8}" r="7" fill="{col}"/>')
    b.append(txt(x + 26, y + 14, 19, SUB, label))
y += 46

b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="112" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="112" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${lead['sym']} has the best retention in the set and the median "
             f"holder owns {money(lead['median_usd'])}.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"{lead['below_reference']*100:.0f}% of its {lead['holders']:,} "
             f"holders are below the cost of selling at {gr:g} gwei, and "
             f"{lead['over_100_usd']*100:.1f}% hold more than $100."))
b.append(txt(L + 26, y + 94, 20, SUB,
             "Nobody is trapped. Leaving costs more than what leaving returns."))
y += 152

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"A swap is modeled at {doc['swap_gas']:,} gas with ETH at "
             f"${doc['eth_usd']:,.0f}, so the dollar figures move with gas, "
             f"ether and each token's price."))
b.append(txt(L, y + 58, 19, SUB,
             "Airdrops land small by design and gas costs what it costs. This "
             "measures what is not worth selling, not anyone's intent."))
b.append(txt(L, y + 84, 19, SUB,
             f"{len(rows)} tokens with a price and a complete balance scan, "
             f"every one above {MIN_HOLDERS} holders."))
b.append(txt(R, y + 110, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 138

render("sell_cost", W, H, "".join(b))
print(f"  {len(rows)} tokens, median {med_live*100:.0f}% live and "
      f"{med_ref*100:.0f}% at {gr:g} gwei")
