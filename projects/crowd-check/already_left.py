#!/usr/bin/env python3
"""A holder count includes the people who already left.

Every bar is one token's current holder count, split by how much of everything
each wallet ever received is still sitting there. Below one percent the wallet
is done: it sold or moved out and left a tail behind, and a tail is a balance,
so the count still counts it. Across 21 tokens the median is 20.9% of holders
in that state, which is one in five.

This is the same blind spot as the mobility chart approached from the other
end. That one found holders who never had the option to leave. This one finds
holders who already took it. A holder count asks whether an address has a
balance and never asks whether anyone chose to have it.

Three things the chart has to be careful about. Leaving is not always selling,
because a wallet can move to another wallet the same person owns. The cut is
relative, so a tail of a very large position can still be real money. And only
21 of the 40 tokens in the baseline carry this measure at all, because the
older scans did not record how much each wallet originally received, which is
why $PIEVERSE and $H sit near the bottom here and are not comparable.

None of this is anyone cheating. Dust is what ordinary exits leave behind.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 already_left.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
MIN_HOLDERS = 100


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
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


doc = json.loads(SRC.read_text())
rows = []
for name, d in doc["tokens"].items():
    k = ((d.get("dust") or {}).get("kinds") or {})
    if "exited_leaving_dust" not in k:
        continue
    n = k.get("classified") or 0
    if n < MIN_HOLDERS:
        continue
    gone = k["exited_leaving_dust"]
    rows.append({"sym": name.upper(), "gone": gone, "holders": n,
                 "left": round(gone * n), "stay": n - round(gone * n),
                 "ret": d["raw"]})
if len(rows) < 5:
    raise SystemExit(f"  only {len(rows)} tokens carry the receipt split")
rows.sort(key=lambda r: -r["gone"])
med = statistics.median(r["gone"] for r in rows)
top = rows[0]
# The example worth naming is the one where the gap is large in people, not
# the one with the highest share: a 57% share of 2,113 holders moves fewer
# wallets than a 46% share of 10,474.
lead = max(rows, key=lambda r: r["left"])

W = 1240
L, R = 60, 1180
LABEL = 112
RIGHT = 206
BARW = R - L - LABEL - RIGHT
BH, GAP = 34, 8
X0 = L + LABEL

b = [txt(L, 58, 37, INK, "A holder count includes", 700),
     txt(L, 98, 37, INK, "the people who already left.", 700),
     txt(L, 138, 20, SUB,
         "Each bar is one token's current holders, split by how much of "
         "everything they ever received is still there."),
     txt(L, 164, 20, SUB,
         "Under one percent means that wallet sold or moved out and left a "
         "tail. A tail is a balance, so the count still counts it.")]

y = 216
bars_top = y
marks = []                      # drawn after the median rule, never under it
for r in rows:
    w_gone = BARW * r["gone"]
    b.append(txt(L, y + BH - 11, 17, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{BRAND}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{w_gone:.1f}" height="{BH}" fill="{HOT}"/>')
    # Under one percent, a whole number reads as zero and $PIEVERSE's 239
    # finished wallets disappear into a "0%".
    pct = (f"{r['gone']*100:.1f}%" if r["gone"] < 0.095
           else f"{r['gone']*100:.0f}%")
    if w_gone > 72:
        marks.append(txt(X0 + w_gone - 11, y + BH - 11, 17, "#ffffff",
                         pct, 700, "end", MONO))
    else:
        marks.append(txt(X0 + w_gone + 10, y + BH - 11, 17, "#ffffff",
                         pct, 700, "start", MONO))
    # Reported count, then what is left once the finished wallets come out.
    b.append(txt(R, y + BH - 11, 16, SUB,
                 f"{r['holders']:,}  →  {r['stay']:,}", 400, "end", MONO))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(R, bars_top - 10, 15, SUB, "reported  →  still in", 400, "end"))

mx = X0 + BARW * med
b.append(f'<line x1="{mx:.1f}" y1="{bars_top-6}" x2="{mx:.1f}" y2="{bars_bot+6}" '
         f'stroke="{GROUND}" stroke-width="2" stroke-dasharray="3 4" opacity="0.8"/>')
b.append(txt(mx + 9, bars_bot + 26, 18, INK, f"median {med*100:.1f}%", 700))
b.extend(marks)

y = bars_bot + 52
sw = (R - L) / 2
for i, (col, label) in enumerate(
        ((HOT, "already left: holds under 1% of everything it received"),
         (BRAND, "still holding more than a tail"))):
    x = L + i * sw
    b.append(f'<rect x="{x:.0f}" y="{y}" width="16" height="16" rx="3" fill="{col}"/>')
    b.append(txt(x + 26, y + 14, 19, SUB, label))
y += 46

b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="86" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="86" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${lead['sym']} reports {lead['holders']:,} holders. About "
             f"{lead['stay']:,} of them still hold more than a tail.", 700))
b.append(txt(L + 26, y + 66, 20, SUB,
             f"Its retention reads {lead['ret']*100:.1f}%, and {lead['left']:,} "
             f"of the wallets inside that number are already finished."))
y += 126

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Leaving is not always selling, since a wallet can move to another "
             "wallet the same person owns."))
b.append(txt(L, y + 58, 19, SUB,
             "The cut is relative, so a tail of a very large position can still "
             "be real money. Dust is what ordinary exits leave behind."))
b.append(txt(L, y + 84, 19, SUB,
             f"{len(rows)} of {len(doc['tokens'])} tokens record what each wallet "
             f"was originally sent, which is what this measure needs."))
b.append(txt(R, y + 110, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 138

render("already_left", W, H, "".join(b))
print(f"  {len(rows)} tokens, median {med*100:.1f}%, "
      f"lead ${lead['sym']} {lead['left']:,} of {lead['holders']:,} gone")
