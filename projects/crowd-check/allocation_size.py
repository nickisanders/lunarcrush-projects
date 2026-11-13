#!/usr/bin/env python3
"""The more an airdrop gave a wallet, the less of it the wallet still holds.

Each line is one airdrop. Its recipients are sorted by what they received
and cut into ten equal groups, so every point on a line is a set of wallets
handed a different amount of the same token on the same day as the wallets
beside it. The height is the share of that group still holding 90% or more
of what it was given.

Nothing is priced and nothing is compared across tokens. Both the groups and
the test are defined against the token's own giveaway, which is what makes
the ten points comparable and what keeps the whole chart still when the
market moves.

The gradient has two obvious readings besides the one in the headline and
both are tested rather than argued. A small position may be held because
selling it costs more than it is worth, so the same slope is computed over
the top half alone, where that reading is hardest to sustain. The largest
receivers may be pools and treasuries, which move tokens because that is
what they are for, so both ends of the distribution are sampled and asked
for code.

Whether a line falls is read off all ten groups rather than off its two
ends. The first version compared the bottom group with the top one, which
called $PIEVERSE the single exception because its bottom group sits at 12.8%
against 98.3% for the one above it, while the line itself falls from the
second group onward like every other. Two airdrops fail the slope test and are
drawn dark: each has a high smallest group, a flat middle and a rise through
the larger groups.

Reads out/receipt-deciles.json and out/decile-code.json.

Usage: python3 allocation_size.py
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
code = json.loads((ROOT / "decile-code.json").read_text())
rows = doc["per_token"]
G = doc["groups"]
med = doc["median"]

# Named by rule rather than by eye: every airdrop that does not fall across
# its ten groups, and the steepest fall in the set.
odd = sorted((r for r in rows if r["slope"] >= 0), key=lambda r: -r["slope"])
if not 1 <= len(odd) <= 3:
    raise SystemExit(f"  {len(odd)} airdrops do not fall; the chart labels "
                     f"them individually and has room for three")
falling = len(rows) - len(odd)
steep = max(rows, key=lambda r: r["bottom"] - r["top"])
spread = sorted(r["groups"][-1]["received"] / r["groups"][0]["received"]
                for r in rows if r["groups"][0]["received"] > 0)

PX, PY, PW, PH = L + 54, 252, 866, 432


def gx(i):
    return PX + i * PW / (G - 1)


def gy(v):
    return PY + PH - v * PH


b = [txt(L, 58, 37, INK, "The more an airdrop handed a wallet,", 700),
     txt(L, 98, 37, INK, "the less of it that wallet still holds.", 700),
     txt(L, 138, 20, SUB,
         f"Each line is one of {doc['tokens']} airdrops. Its recipients are "
         f"sorted by what they received and cut into ten equal groups, "
         f"smallest first."),
     txt(L, 164, 20, SUB,
         f"The height is the share of a group still holding "
         f"{doc['untouched']*100:.0f}% or more of what it was given."),
     txt(L, 190, 20, SUB,
         f"The median airdrop handed its largest tenth "
         f"{statistics.median(spread):,.0f} times what it handed its "
         f"smallest. Nothing in the chart is priced.")]

for v in range(0, 101, 20):
    y = gy(v / 100)
    b.append(f'<line x1="{PX}" y1="{y:.0f}" x2="{PX+PW}" y2="{y:.0f}" '
             f'stroke="{RULE}" stroke-width="1"/>')
    b.append(txt(PX - 14, y + 6, 16, SUB, f"{v}%", 400, "end"))
b.append(txt(PX - 46, PY - 16, 17, SUB, "share of the group still holding it"))

for r in rows:
    if r in odd:
        continue
    d = " ".join(f"{'M' if i == 0 else 'L'}{gx(i):.0f} {gy(g['kept']):.0f}"
                 for i, g in enumerate(r["groups"]))
    b.append(f'<path d="{d}" fill="none" stroke="{RULE}" stroke-width="1.6"/>')

for key, color, width, dash in (("holding", BRAND, 3, "7 5"),
                                ("kept", HOT, 4.5, None)):
    d = " ".join(f"{'M' if i == 0 else 'L'}{gx(i):.0f} {gy(m[key]):.0f}"
                 for i, m in enumerate(med))
    b.append(f'<path d="{d}" fill="none" stroke="{color}" '
             f'stroke-width="{width}"'
             + (f' stroke-dasharray="{dash}"' if dash else "") + '/>')
    for i, m in enumerate(med):
        b.append(f'<circle cx="{gx(i):.0f}" cy="{gy(m[key]):.0f}" r="4.5" '
                 f'fill="{color}"/>')

for r in odd:
    d = " ".join(f"{'M' if i == 0 else 'L'}{gx(i):.0f} {gy(g['kept']):.0f}"
                 for i, g in enumerate(r["groups"]))
    b.append(f'<path d="{d}" fill="none" stroke="{SUB}" stroke-width="2.6"/>')

# At the right edge the three lines end close enough to overprint each other,
# so each label is pushed off its neighbour rather than sitting on its line.
ends = sorted([(gy(med[-1]["kept"]), HOT, "median kept", 700),
               (gy(med[-1]["holding"]), BRAND, "median balance above zero", 400)]
              + [(gy(r["groups"][-1]["kept"]), SUB, f"${r['sym']}", 700)
                 for r in odd])
placed = []
for y, color, label, weight in ends:
    while placed and y - placed[-1] < 26:
        y = placed[-1] + 26
    placed.append(y)
    b.append(txt(PX + PW + 14, y + 6, 17, color, label, weight))

for i in range(G):
    b.append(txt(gx(i), PY + PH + 30, 17, SUB, str(i + 1), 400, "middle"))
b.append(txt(PX, PY + PH + 58, 17, SUB, "smallest tenth"))
b.append(txt(PX + PW, PY + PH + 58, 17, SUB, "largest tenth", 400, "end"))

y = PY + PH + 92
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"{falling} of the {doc['tokens']} run downhill across all ten "
             f"groups.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Median across airdrops, the smallest tenth still holds "
             f"{med[0]['kept']*100:.1f}% of what it received and the largest "
             f"tenth {med[-1]['kept']*100:.1f}%."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"A small position may be held because selling costs more than "
             f"it is worth. Over the top half alone "
             f"{doc['falling_top_half']} of {doc['tokens']} still fall."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"The largest group is not simply contracts: "
             f"{code['ends']['top']['share']*100:.1f}% of a sample there "
             f"carry code against "
             f"{code['ends']['bottom']['share']*100:.1f}% at the bottom."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
# Spelled from the count rather than printed as a digit, which read as a
# footnote marker in a sentence that has no footnotes.
COUNT = ("no", "one", "two", "three")
b.append(txt(L, y + 32, 19, SUB,
             f"${steep['sym']} falls furthest, from "
             f"{steep['bottom']*100:.1f}% to {steep['top']*100:.1f}%. The "
             f"{COUNT[len(odd)]} drawn dark do not fall, each with a high "
             f"smallest group, a flat middle"))
b.append(txt(L, y + 58, 19, SUB,
             "and a rise through the larger groups, so the order of their "
             "ten carries no single direction."))
b.append(txt(L, y + 84, 19, SUB,
             f"{doc['tokens']} airdrops above {doc['floor']:,} recipients "
             f"carry the receipt field this needs. Groups and test are "
             f"both defined against the token's own giveaway."))
b.append(txt(L, y + 110, 19, SUB,
             f"The dashed line is the retention figure airdrop reports "
             f"quote, falling {med[0]['holding']/med[-1]['holding']:.1f}x "
             f"against the solid line's "
             f"{med[0]['kept']/med[-1]['kept']:.1f}x."))
b.append(txt(L, y + 136, 19, SUB,
             "An EIP-7702 delegation counts as a wallet. Why a position was "
             "trimmed is not visible from the chain, and nothing here says "
             "it was sold."))
b.append(txt(R, y + 164, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 196
render("allocation_size", W, H, "".join(b))
print(f"  {doc['tokens']} airdrops, median kept {med[0]['kept']*100:.1f}% to "
      f"{med[-1]['kept']*100:.1f}%, {falling} falling, "
      f"{' '.join('$' + r['sym'] for r in odd)} flat")
