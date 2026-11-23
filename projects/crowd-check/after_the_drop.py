#!/usr/bin/env python3
"""Did anyone show up after the giveaway, or was the giveaway the whole crowd?

Every bar is one token's lifetime recipients, cut three ways by when each
address first received it: before the giveaway week, inside it, and after it
was over. Sorted by the last of those, which is the only one that says
whether the token reached anyone it did not pay.

The split is three ways rather than two because a token whose giveaway came
late in its life already had a crowd, and counting those addresses as
"not from the giveaway" would read as recruitment when it is the opposite.
Seven tokens are enough of that to be a different question and are dropped
on a quarter of their crowd arriving first: $MORPHO had 86% of its holders
before its giveaway and would otherwise have sat at the bottom of the chart
looking like a token nobody joined.

Time is the obvious confound and it is a real one: against months since the
giveaway, the share arriving afterwards reads r = 0.45. It is in the footer
rather than the headline because it does not decide the order. The fourteen
tokens under two years old spread from 14% to 85% among themselves, which is
most of the chart's whole range.

Reads out/arrival-years.json and out/retention-baseline.json.

Usage: python3 after_the_drop.py
"""

import datetime
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
BEFORE_MAX = 0.25


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


doc = json.loads((ROOT / "arrival-years.json").read_text())
base = json.loads((ROOT / "retention-baseline.json").read_text())["tokens"]
rows = []
dropped = []
for r in doc["per_token"]:
    if not r["spike"]:
        continue
    t = base[r["sym"].lower()]
    n = r["recipients"]
    peak = datetime.date.fromisoformat(r["peak_day"])
    meas = datetime.date.fromisoformat(t["measured"]) if t.get("measured") \
        else datetime.date.fromisoformat(doc["measured"])
    rows.append({"sym": r["sym"], "n": n,
                 "before": r["before"]["n"] / n,
                 "week": r["giveaway"]["n"] / n,
                 "after": r["after"]["n"] / n,
                 "after_holds": r["after"]["holding"],
                 "week_holds": r["giveaway"]["holding"],
                 "since": (meas - peak).days / 30.44})
# A token with a crowd in front of its giveaway is answering a different
# question, and at the bottom of this sort it would read as one nobody
# joined rather than one that was already joined.
dropped = [r for r in rows if r["before"] >= BEFORE_MAX]
rows = [r for r in rows if r["before"] < BEFORE_MAX]
if len(rows) < 12:
    raise SystemExit(f"  only {len(rows)} tokens have a findable giveaway "
                     f"week; the chart ranks a field")
rows.sort(key=lambda r: -r["after"])
r_age = pearson([r["since"] for r in rows], [r["after"] for r in rows])

# Named by rule: the two ends of the sort, and the largest crowd on it.
top, bottom = rows[0], rows[-1]
biggest = max(rows, key=lambda r: r["n"])
young = [r for r in rows if r["since"] < 24]
# The youngest token that has already recruited past its giveaway, which is
# the one that makes the age objection answerable on the chart itself.
early = max(young, key=lambda r: r["after"]) if young else top
NAMED = {top["sym"], bottom["sym"], biggest["sym"], early["sym"]}
stalled = [r for r in rows if r["after"] < 0.25]

PX, PW = L + 104, 700
TOP, RH = 318, 25
C_N = R

b = [txt(L, 58, 37, INK, "For some tokens the airdrop is not the start", 700),
     txt(L, 98, 37, INK, "of the crowd. It is the whole of it.", 700),
     txt(L, 138, 20, SUB,
         f"Each bar is one token's lifetime recipients, split by when each "
         f"address first received it. Red is the giveaway week,"),
     txt(L, 164, 20, SUB,
         "blue is everyone who turned up after it, and the sliver at the "
         "left is anyone who was already there before it."),
     txt(L, 190, 20, SUB,
         f"The giveaway is found from the arrival data: the busiest single "
         f"day and the {doc['window']} days either side.")]

y = TOP - 28
b.append(txt(PX, y, 17, SUB, "share of everyone the token ever paid"))
b.append(txt(C_N, y, 17, SUB, "recipients", 400, "end"))

for i, r in enumerate(rows):
    yy = TOP + i * RH
    named = r["sym"] in NAMED
    b.append(txt(L, yy + 15, 15, INK if named else SUB, "$" + r["sym"],
                 700 if named else 400, "start", MONO))
    x = PX
    for share, col in ((r["before"], TRACK), (r["week"], HOT),
                       (r["after"], BRAND)):
        w = PW * share
        b.append(f'<rect x="{x:.1f}" y="{yy}" width="{w:.1f}" height="19" '
                 f'fill="{col}"/>')
        x += w
    b.append(txt(C_N, yy + 15, 15, SUB, f"{r['n']:,}", 400, "end", MONO))

y = TOP + len(rows) * RH + 16
b.append(txt(PX, y + 12, 17, SUB, "before"))
b.append(txt(PX + 110, y + 12, 17, HOT, "the giveaway week"))
b.append(txt(PX + 330, y + 12, 17, BRAND, "everyone after it"))

y += 44
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"On {len(stalled)} of these {len(rows)}, under a quarter of "
             f"the holders arrived after the giveaway.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"${bottom['sym']} is the furthest: {bottom['after']*100:.1f}% "
             f"turned up afterwards, against {bottom['week']*100:.1f}% in the "
             f"giveaway week itself."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"${top['sym']} is the other end at {top['after']*100:.1f}%, "
             f"and ${biggest['sym']}, the largest crowd here at "
             f"{biggest['n']:,}, is close behind on "
             f"{biggest['after']*100:.1f}%."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"${early['sym']} is {early['since']:.0f} months past its "
             f"giveaway and already at {early['after']*100:.1f}%, against "
             f"${bottom['sym']} at {bottom['since']:.0f} months and "
             f"{bottom['after']*100:.1f}%."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"Time is the obvious objection and it is partly right: against "
             f"months since the giveaway, the share arriving afterwards "
             f"reads r = {r_age:.2f}."))
b.append(txt(L, y + 58, 19, SUB,
             f"It does not decide the order, though: the {len(young)} tokens "
             f"under two years old spread from "
             f"{min(r['after'] for r in young)*100:.0f}% to "
             f"{max(r['after'] for r in young)*100:.0f}% among themselves."))
b.append(txt(L, y + 84, 19, SUB,
             "Arriving afterwards means buying, being sent the token, or "
             "claiming late. The chain does not separate them and this does "
             "not try to."))
b.append(txt(L, y + 110, 19, SUB,
             f"{len(rows)} tokens drawn. A giveaway needs "
             f"{doc['floor_share']*100:.0f}% of a token's arrivals to be "
             f"findable, and {len(dropped)} more are dropped for having a "
             f"crowd before it."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 170
render("after_the_drop", W, H, "".join(b))
print(f"  {len(rows)} tokens, {len(stalled)} under a quarter, "
      f"${bottom['sym']} {bottom['after']*100:.1f}% to ${top['sym']} "
      f"{top['after']*100:.1f}%, age r={r_age:.2f}")
