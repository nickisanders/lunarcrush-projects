#!/usr/bin/env python3
"""The wallets that collect every airdrop look like the most loyal holders.

Every recipient of every baseline airdrop, bucketed by how many of them that
wallet collected in total, scored two ways.

Holding anything is the retention figure every airdrop report quotes: a
balance above zero, which one token left from a full allocation will pass.
Holding a full allocation means the wallet received at least the median
receipt for that token and still holds 90% or more of it, both halves
relative to what the token handed out, so nothing moves with the price.

The two columns disagree about who the loyal holders are, and the
disagreement is the finding. Full allocations fall fourfold across the
buckets. The quoted figure does not fall at all, and the heaviest collectors
score highest on it, which is the signature of selling most of a position and
leaving the tail rather than closing the wallet.

The obvious objection is that a bridge router or a pool receives a slice of
nearly every token and never goes to zero. It is a real effect and a large
one: half the addresses at twenty or more carry code, and the most prolific
of them are routers. Removing them sharpens the finding rather than
explaining it away. The ordinary wallets in that group hold something on
42.3% of their allocations, higher than the group as a whole and higher than
any other bucket, while keeping a full allocation on 3.0% against the
one-timers' 6.4%.

What this cannot say is why. A wallet that sells most of an allocation and
keeps a sliver, a wallet that forgot, and a wallet priced out of the gas to
close the position all read the same here.

Reads out/collector-fate.json and out/heavy-split.json.

Usage: python3 collector_fate.py
"""

import json
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


doc = json.loads((ROOT / "collector-fate.json").read_text())
split = json.loads((ROOT / "heavy-split.json").read_text())
rows = doc["buckets"]
if len(rows) < 3:
    raise SystemExit(f"  only {len(rows)} buckets; the chart is a gradient")
pairs = sum(r["pairs"] for r in rows)
one, heavy = rows[0], rows[-1]
wal, con = split["rows"]["wallet"], split["rows"]["contract"]

b = [txt(L, 58, 37, INK, "The wallets that collected the most airdrops", 700),
     txt(L, 98, 37, INK, "hold a full allocation the least often.", 700),
     txt(L, 138, 20, SUB,
         f"Every recipient of every airdrop in the baseline, "
         f"{pairs:,} recipient-token pairs, grouped by how many of the"),
     txt(L, 164, 20, SUB,
         f"{doc['basket']} the wallet collected in total. Blue is a balance "
         f"above zero. Red is still holding what was handed over."),
     txt(L, 190, 20, SUB,
         f"Full means the wallet received at least the median receipt for "
         f"that token and still holds {doc['untouched']*100:.0f}% of it.")]

TOP = 0.40
GH = 300
y0 = 266
BW = (R - L) // len(rows)
b.append(txt(L, y0 - 18, 16, SUB, "share of allocations"))
for g in (0, 0.1, 0.2, 0.3, 0.4):
    gy = y0 + GH - GH * (g / TOP)
    b.append(f'<line x1="{L}" y1="{gy:.0f}" x2="{R}" y2="{gy:.0f}" '
             f'stroke="{RULE}" stroke-width="1"/>')
    b.append(txt(L - 10, gy + 5, 15, SUB, f"{g*100:.0f}%", 400, "end"))

for i, r in enumerate(rows):
    x = L + i * BW
    bw = 56
    gap = 18
    x1 = x + BW / 2 - bw - gap / 2
    x2 = x + BW / 2 + gap / 2
    h1 = GH * (r["holding"] / TOP)
    h2 = GH * (r["full"] / TOP)
    b.append(f'<rect x="{x1:.0f}" y="{y0+GH-h1:.0f}" width="{bw}" '
             f'height="{h1:.0f}" fill="{BRAND}"/>')
    b.append(f'<rect x="{x2:.0f}" y="{y0+GH-h2:.0f}" width="{bw}" '
             f'height="{h2:.0f}" fill="{HOT}"/>')
    b.append(txt(x1 + bw / 2, y0 + GH - h1 - 10, 19, BRAND,
                 f"{r['holding']*100:.1f}%", 700, "middle", MONO))
    b.append(txt(x2 + bw / 2, y0 + GH - h2 - 10, 19, HOT,
                 f"{r['full']*100:.1f}%", 700, "middle", MONO))
    b.append(txt(x + BW / 2, y0 + GH + 30, 20, INK, r["bucket"], 700, "middle"))
    b.append(txt(x + BW / 2, y0 + GH + 54, 16, SUB,
                 f"{r['pairs']:,}", 400, "middle"))

# Centred on the first group this read as a caption for that bucket alone.
b.append(txt(L, y0 + GH + 84, 17, SUB,
             "airdrops collected, and allocations counted"))

y = y0 + GH + 116
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"The quoted figure makes the heaviest collectors the most loyal "
             f"group on the chart.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"They hold something on {heavy['holding']*100:.1f}% of "
             f"allocations against {one['holding']*100:.1f}% for one-timers, "
             f"and a full allocation on {heavy['full']*100:.1f}% against "
             f"{one['full']*100:.1f}%."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"A router receives a slice of nearly every token and never goes "
             f"to zero, and {split['contracts']/(split['wallets']+split['contracts'])*100:.0f}% "
             f"of the addresses at {split['floor']}+ carry code."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"It is not the explanation. The wallets alone hold on "
             f"{wal['holding']*100:.1f}% of allocations, above the group, and "
             f"keep a full one on {wal['full']*100:.1f}%."))
y += 184

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "The unit is a recipient-token pair, so a wallet that collected "
             "thirty airdrops appears thirty times, which is the right "
             "denominator"))
b.append(txt(L, y + 58, 19, SUB,
             f"for a question about allocations rather than people. The "
             f"heaviest bucket is {split['heavy']:,} addresses seen many "
             f"times."))
b.append(txt(L, y + 84, 19, SUB,
             f"{doc['basket']} tokens carry the receipt field the full test "
             f"needs. The rest are dropped and are not a random sample: they "
             f"are the older scans."))
b.append(txt(L, y + 110, 19, SUB,
             "Nothing here is priced, and an EIP-7702 delegation counts as a "
             "wallet. Why a position was trimmed is not visible from the "
             "chain."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 166

render("collector_fate", W, H, "".join(b))
print(f"  {len(rows)} buckets, {pairs:,} pairs, full falls "
      f"{one['full']*100:.1f}% to {heavy['full']*100:.1f}%")
