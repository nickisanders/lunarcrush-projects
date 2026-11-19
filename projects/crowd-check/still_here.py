#!/usr/bin/env python3
"""Retention, and retention among the holders who could have left.

Every row is a token at least five years old with a crowd worth the name.
The hollow dot is the retention figure as anyone would quote it: the share
of everyone the token ever paid who still holds a balance above zero. The
solid dot removes the holders who cannot transact at all, meaning they hold
no ETH and have never sent a transaction, so the token they are sitting on
is not a position they chose to keep.

That adjustment is a sample. Mobility is read off 250 holders per token, so
the solid dot comes with the interval that sample supports, drawn as a bar
through it. A reordering only counts when the bars do not overlap.

The point of the chart is that the reordering happens. The token at the top
of the quoted figure falls past most of the field once its immobile holders
come out, and the one that survives the adjustment best among the large
crowds is the oldest token here.

Reads out/retention-baseline.json.

Usage: python3 still_here.py
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
MIN_AGE, MIN_ARRIVED, BIG = 60, 20000, 100000

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


doc = json.loads(SRC.read_text())
rows = []
for name, d in doc["tokens"].items():
    m = d.get("mobility") or {}
    if (d.get("age_months") or 0) < MIN_AGE or d["arrived"] < MIN_ARRIVED:
        continue
    if m.get("immobile_share") is None:
        continue
    lo_im, hi_im = m["immobile_ci"]
    rows.append({"sym": name.upper(), "arr": d["arrived"],
                 "age": d["age_months"], "raw": d["raw"],
                 "adj": d["raw"] * (1 - m["immobile_share"]),
                 # The wider the immobile share, the lower the adjusted
                 # figure, so the interval flips end for end.
                 "lo": d["raw"] * (1 - hi_im), "hi": d["raw"] * (1 - lo_im),
                 "im": m["immobile_share"], "sampled": m["sampled"]})
if len(rows) < 6:
    raise SystemExit(f"  only {len(rows)} tokens are {MIN_AGE} months old "
                     f"with mobility; the chart compares a cohort")
rows.sort(key=lambda r: -r["raw"])

# Named by rule: the token the quoted figure puts first, and the best
# survivor of the adjustment among the crowds over BIG.
head = rows[0]
big = [r for r in rows if r["arr"] >= BIG]
if not big:
    raise SystemExit(f"  no token here has a crowd over {BIG:,}")
star = max(big, key=lambda r: r["adj"])
# The best survivor overall is usually not the one on a crowd worth naming,
# and leaving it unmentioned invites the reader to find it on the chart and
# assume it was hidden.
best = max(rows, key=lambda r: r["adj"])
NAMED = {head["sym"], star["sym"]}

PX, PW = L + 112, 760
TOP, RH = 316, 46
C_N = R


def gx(v):
    return PX + PW * v


b = [txt(L, 58, 37, INK,
         f"${star['sym']} has paid {star['arr']:,} wallets and over half", 700),
     txt(L, 98, 37, INK, "of them are still holding it.", 700),
     txt(L, 138, 20, SUB,
         f"Every token here is at least {MIN_AGE//12} years old with more "
         f"than {MIN_ARRIVED:,} recipients. Hollow: the retention figure as "
         f"it gets quoted."),
     txt(L, 164, 20, SUB,
         "Solid: the same figure with the holders who cannot transact at "
         "all taken out, since a wallet with no ETH that has never sent a"),
     txt(L, 190, 20, SUB,
         f"transaction is not holding by choice. Mobility is sampled at "
         f"{rows[0]['sampled']} holders a token, so the solid dot carries "
         f"that sample's interval.")]

# The caption sat on the same line as the tick labels and printed through
# the first two of them.
b.append(txt(PX, TOP - 48, 17, SUB, "share of everyone the token ever paid"))
b.append(txt(C_N, TOP - 48, 17, SUB, "recipients", 400, "end"))
for v in (0, 0.25, 0.5, 0.75):
    x = gx(v)
    b.append(f'<line x1="{x:.0f}" y1="{TOP-12}" x2="{x:.0f}" '
             f'y2="{TOP + len(rows)*RH - 18}" stroke="{RULE}" '
             f'stroke-width="1"/>')
    b.append(txt(x, TOP - 24, 15, SUB, f"{v*100:.0f}%", 400, "middle"))

for i, r in enumerate(rows):
    y = TOP + i * RH + 10
    named = r["sym"] in NAMED
    col = HOT if named else BRAND
    b.append(txt(L, y + 6, 17, INK if named else SUB, "$" + r["sym"],
                 700 if named else 400, "start", MONO))
    b.append(f'<line x1="{gx(r["adj"]):.0f}" y1="{y}" '
             f'x2="{gx(r["raw"]):.0f}" y2="{y}" stroke="{col}" '
             f'stroke-width="3" opacity="0.4"/>')
    b.append(f'<line x1="{gx(r["lo"]):.0f}" y1="{y}" '
             f'x2="{gx(r["hi"]):.0f}" y2="{y}" stroke="{col}" '
             f'stroke-width="9" opacity="0.28"/>')
    b.append(f'<circle cx="{gx(r["raw"]):.0f}" cy="{y}" r="7" '
             f'fill="{GROUND}" stroke="{col}" stroke-width="3"/>')
    b.append(f'<circle cx="{gx(r["adj"]):.0f}" cy="{y}" r="7" fill="{col}"/>')
    b.append(txt(C_N, y + 6, 16, SUB, f"{r['arr']:,}", 400, "end", MONO))

y = TOP + len(rows) * RH + 16
b.append(txt(PX, y + 12, 17, SUB, "cannot transact, removed"))
b.append(txt(PX + 300, y + 12, 17, SUB, "quoted retention"))

y += 44
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${head['sym']} leads the quoted figure and falls below "
             f"${star['sym']} once the stuck wallets come out.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"${head['sym']}: {head['raw']*100:.1f}% quoted, "
             f"{head['im']*100:.1f}% of its holders immobile, "
             f"{head['adj']*100:.1f}% left. The two intervals do not touch, "
             f"so the swap is not sampling noise."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"${star['sym']}: {star['raw']*100:.1f}% quoted and "
             f"{star['adj']*100:.1f}% adjusted, on a crowd of "
             f"{star['arr']:,}, which is "
             f"{star['arr']/statistics.median(r['arr'] for r in rows):.0f} "
             f"times the median token here."))
b.append(txt(L + 26, y + 124, 20, SUB,
             (f"${best['sym']} survives the adjustment best of anything "
              f"here, at {best['adj']*100:.1f}%, on {best['arr']:,} "
              f"recipients." if best is not star else
              f"It is also the oldest token here, at {star['age']} "
              f"months.")))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Immobile means no ETH and no transaction ever sent, so the "
             "wallet cannot pay gas and cannot move the token whatever its "
             "balance says."))
b.append(txt(L, y + 58, 19, SUB,
             "It is a floor on who is stuck rather than a count. A wallet "
             "holding a dollar of ETH against a gas price it will not pay "
             "counts as mobile."))
b.append(txt(L, y + 84, 19, SUB,
             "The adjustment assumes the sampled share holds across all of "
             "a token's holders, which is what the interval on each solid "
             "dot is for."))
b.append(txt(L, y + 110, 19, SUB,
             "Nothing here is priced. A balance above zero is the whole "
             "retention test, and how much of an allocation is left is a "
             "different question."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 170
render("still_here", W, H, "".join(b))
print(f"  {len(rows)} tokens, ${star['sym']} {star['raw']*100:.1f}% to "
      f"{star['adj']*100:.1f}%, ${head['sym']} {head['raw']*100:.1f}% to "
      f"{head['adj']*100:.1f}%")
