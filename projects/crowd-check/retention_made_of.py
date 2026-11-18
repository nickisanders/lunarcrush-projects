#!/usr/bin/env python3
"""What the retention number is made of, token by token.

Every bar is the current holders of one token, split by how much of what
they received they still hold. A wallet above 90% never moved its
allocation. A wallet under 1% sold out and left a tail, and it is counted as
a retained holder by every retention figure ever quoted. The rest sold some
of it.

All three cuts are relative to what the wallet itself received, so nothing
in the split moves when the price does, which is the failure every dollar
threshold carries.

The rows are sorted by the headline retention figure, printed in the column
on the right. If that figure described the composition the red would grow or
shrink down the chart, and it does not: the two are related at r = -0.58,
which is loose enough that two tokens can post the same number and mean
opposite things.

The pair the callout names is found rather than chosen: the two tokens whose
headline retention is closest together with the widest gap in what that
retention is made of.

Reads out/retention-baseline.json.

Usage: python3 retention_made_of.py
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
MIN_ARRIVED = 5000
# The headline figure as anyone would print it. Tokens that agree to this
# many places are quoting the same number, which is the comparison the chart
# is about.
PLACES = 1

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


def pearson(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    c = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    d = (sum((x - ma) ** 2 for x in a) ** 0.5) * (sum((y - mb) ** 2 for y in b) ** 0.5)
    return c / d if d else 0.0


doc = json.loads(SRC.read_text())
rows = []
for name, d in doc["tokens"].items():
    k = (d.get("dust") or {}).get("kinds") or {}
    if "untouched_large" not in k or d["arrived"] < MIN_ARRIVED:
        continue
    rows.append({"sym": name.upper(), "arr": d["arrived"], "raw": d["raw"],
                 "held": k["untouched_large"] + k["untouched_small"],
                 "part": k["part_sold"], "gone": k["exited_leaving_dust"],
                 "holders": k.get("classified")})
if len(rows) < 20:
    raise SystemExit(f"  only {len(rows)} tokens carry the holder split; the "
                     f"chart describes a field")
rows.sort(key=lambda r: r["raw"])
r_corr = pearson([r["raw"] for r in rows], [r["gone"] for r in rows])

# Named by rule rather than by eye. Tokens whose headline retention prints
# as the same figure are grouped, and the chart names two of those groups:
# the one with the most tokens in it, and the one whose holders turn out to
# be the least alike. An earlier version matched tokens within a tolerance
# and then printed the gap between them, which came out as 1.2 points
# beside two rows a reader could see were 1.1 apart.
ties = {}
for r in rows:
    ties.setdefault(round(r["raw"] * 100, PLACES), []).append(r)
ties = {k: sorted(v, key=lambda r: r["gone"])
        for k, v in ties.items() if len(v) > 1}
if not ties:
    raise SystemExit("  no two tokens report the same headline figure; the "
                     "chart is built on that comparison")
crowd = max(ties.items(), key=lambda kv: (len(kv[1]), kv[1][-1]["gone"] - kv[1][0]["gone"]))
widest = max(ties.items(), key=lambda kv: kv[1][-1]["gone"] - kv[1][0]["gone"])
NAMED = {r["sym"] for r in crowd[1]} | {r["sym"] for r in widest[1]}

PX, PW = L + 108, 790
TOP, RH = 322, 22
C_RAW = R

b = [txt(L, 58, 37, INK, "Two tokens can report the same retention", 700),
     txt(L, 98, 37, INK, "and mean the opposite thing by it.", 700),
     txt(L, 138, 20, SUB,
         f"Every bar is one token's current holders, split by how much of "
         f"what they received they still hold. Blue never moved"),
     txt(L, 164, 20, SUB,
         "it, 90% or more. Red holds under 1%: they sold out and left a "
         "tail, and every retention figure counts them as holders."),
     txt(L, 190, 20, SUB,
         "Each cut is relative to what that wallet itself received, so "
         "nothing in the split moves when the price does.")]

y = TOP - 30
b.append(txt(PX, y, 17, SUB, "share of the token's holders"))
b.append(txt(C_RAW, y, 17, SUB, "retention", 400, "end"))

for i, r in enumerate(rows):
    yy = TOP + i * RH
    named = r["sym"] in NAMED
    b.append(txt(L, yy + 15, 15, INK if named else SUB, "$" + r["sym"],
                 700 if named else 400, "start", MONO))
    x = PX
    for share, col in ((r["held"], BRAND), (r["part"], TRACK),
                       (r["gone"], HOT)):
        w = PW * share
        b.append(f'<rect x="{x:.1f}" y="{yy}" width="{w:.1f}" height="17" '
                 f'fill="{col}"/>')
        x += w
    b.append(txt(C_RAW, yy + 15, 16, INK if named else SUB,
                 f"{r['raw']*100:.1f}%", 700 if named else 400, "end"))

y = TOP + len(rows) * RH + 14
b.append(txt(PX, y + 12, 17, SUB, "never moved it"))
b.append(txt(PX + 230, y + 12, 17, SUB, "sold some"))
b.append(txt(PX + 420, y + 12, 17, SUB, "sold out, left a tail"))

y += 44
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"{len(crowd[1])} of these tokens report retention of exactly "
             f"{crowd[0]:.1f}%.", 700))
# Joined with an "and" before the last. A bare comma list ran into the
# verb and read as one clause.
parts = [f"{r['gone']*100:.1f}% on ${r['sym']}" for r in crowd[1]]
listed = ", ".join(parts[:-1]) + " and " + parts[-1]
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Behind that one figure, {listed} hold under 1% of what they "
             f"received."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"Across the {len(rows)} tokens that share runs from "
             f"{min(r['gone'] for r in rows)*100:.1f}% to "
             f"{max(r['gone'] for r in rows)*100:.1f}%, median "
             f"{statistics.median(r['gone'] for r in rows)*100:.1f}%."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"${widest[1][0]['sym']} and ${widest[1][-1]['sym']} both "
             f"report {widest[0]:.1f}%, on "
             f"{widest[1][0]['gone']*100:.1f}% against "
             f"{widest[1][-1]['gone']*100:.1f}%. Sorted by the headline the "
             f"red does not run with it: r = {r_corr:.2f}."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "The split is of current holders, not of everyone who ever "
             "received the token, which is the denominator the headline "
             "figure uses."))
b.append(txt(L, y + 58, 19, SUB,
             "A wallet under 1% of its allocation did not necessarily sell. "
             "Sending it somewhere else and leaving the remainder looks the "
             "same from here."))
b.append(txt(L, y + 84, 19, SUB,
             f"{len(rows)} tokens above {MIN_ARRIVED:,} recipients carry the "
             f"split. The tokens named are the ones that print the same "
             f"headline figure as each other."))
b.append(txt(L, y + 110, 19, SUB,
             "Nothing here is priced. Every Transfer event since each "
             "contract's first block, netted into who holds what today."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 170
render("retention_made_of", W, H, "".join(b))
print(f"  {len(rows)} tokens, residue "
      f"{min(r['gone'] for r in rows)*100:.1f}% to "
      f"{max(r['gone'] for r in rows)*100:.1f}%, "
      f"{len(crowd[1])} tied at {crowd[0]:.1f}%, widest tie "
      f"{widest[0]:.1f}% spanning "
      f"{(widest[1][-1]['gone']-widest[1][0]['gone'])*100:.1f} points")
