#!/usr/bin/env python3
"""A token's retention figure is mostly about wallets that missed the giveaway.

One row per token. The left dot is the share of wallets that arrived in the
week of the giveaway and still hold 90% or more of what they received. The
right dot is the same measure for every wallet that turned up afterwards.
The column on the right is how much of the token's lifetime crowd arrived in
that week at all.

The giveaway is found rather than assumed: the busiest single day of
arrivals is the anchor and the week around it is the event. A token whose
busiest week is not a visible spike has nothing to anchor on and is dropped,
which is also what removes the bridged contracts whose giveaway happened on
another chain.

What the later group is cannot be settled from this data. It holds buyers,
late claimers and anyone who was sent the token by someone else, and all
three pass the same test. That is the point rather than a flaw in it: the
retention figure quoted for a giveaway is computed over all of them.

The rows that run the other way are kept and drawn in the other colour. They
lean toward crowds that cannot transact, which is the explanation this chart
can suggest and not the one it can prove.

Reads out/arrival-split.json.

Usage: python3 arrival_split.py
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


doc = json.loads((ROOT / "arrival-split.json").read_text())
base = json.loads((ROOT / "retention-baseline.json").read_text())["tokens"]
rows = sorted(doc["per_token"],
              key=lambda r: r["later"]["kept"] - r["event"]["kept"],
              reverse=True)
worse = [r for r in rows if r["event"]["kept"] < r["later"]["kept"]]
med_event = statistics.median(r["event"]["kept"] for r in rows)
med_later = statistics.median(r["later"]["kept"] for r in rows)
widest = rows[0]


def immobile(group):
    """Median share of a group's holders that cannot transact at all.

    Drawn from the baseline's sampled mobility rather than asserted: the
    blue rows looked like crowds that cannot sell, and the footer says how
    far that holds up instead of claiming it.
    """
    vals = [m["immobile_share"] for r in group
            if (m := (base.get(r["sym"].lower()) or {}).get("mobility"))
            and m.get("immobile_share") is not None]
    return statistics.median(vals) if vals else None


better = [r for r in rows if r not in worse]
im_worse, im_better = immobile(worse), immobile(better)

PX, PW = L + 112, 720
TOP, RH = 300, 30
C_SHARE = R


def gx(v):
    return PX + v * PW


b = [txt(L, 58, 37, INK, "The wallets that were there for the giveaway", 700),
     txt(L, 98, 37, INK, "are the ones least likely to still hold it.", 700),
     txt(L, 138, 20, SUB,
         f"Each row is a token with a visible giveaway week. Left dot: "
         f"wallets that arrived in that week and still hold "
         f"{doc['untouched']*100:.0f}% or"),
     txt(L, 164, 20, SUB,
         "more of what they received. Right dot: every wallet that turned up "
         "afterwards, measured the same way."),
     txt(L, 190, 20, SUB,
         "The retention figure quoted for a giveaway is computed across both "
         "groups at once.")]

y = TOP - 48
b.append(txt(PX, y, 17, SUB, "share of the group still holding it"))
b.append(txt(C_SHARE, y, 17, SUB, "in that week", 400, "end"))
for v in (0, 0.25, 0.5, 0.75, 1.0):
    x = gx(v)
    b.append(f'<line x1="{x:.0f}" y1="{TOP-16}" x2="{x:.0f}" '
             f'y2="{TOP + len(rows)*RH - 6}" stroke="{RULE}" '
             f'stroke-width="1"/>')
    b.append(txt(x, TOP - 24, 15, SUB, f"{v*100:.0f}%", 400, "middle"))

for i, r in enumerate(rows):
    yy = TOP + i * RH + 14
    ev, la = r["event"]["kept"], r["later"]["kept"]
    col = HOT if ev < la else BRAND
    b.append(txt(L, yy + 6, 18, INK, "$" + r["sym"], 400, "start", MONO))
    b.append(f'<line x1="{gx(min(ev,la)):.0f}" y1="{yy}" '
             f'x2="{gx(max(ev,la)):.0f}" y2="{yy}" stroke="{col}" '
             f'stroke-width="3" opacity="0.45"/>')
        # The filled dot is drawn last. Behind the hollow one it disappeared
    # entirely on the rows where the two measures almost agree, which reads
    # as a missing measurement rather than a gap of nothing.
    b.append(f'<circle cx="{gx(la):.0f}" cy="{yy}" r="7" fill="{GROUND}" '
             f'stroke="{col}" stroke-width="3"/>')
    b.append(f'<circle cx="{gx(ev):.0f}" cy="{yy}" r="7" fill="{col}"/>')
    b.append(txt(C_SHARE, yy + 6, 17, SUB,
                 f"{r['event_share']*100:.0f}%", 400, "end"))

y = TOP + len(rows) * RH + 26
b.append(txt(PX, y, 17, SUB, "filled: the giveaway week"))
b.append(txt(PX + 300, y, 17, SUB, "hollow: everyone after it"))

y += 40
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"On {len(worse)} of the {doc['tokens']}, the giveaway week "
             f"holds less often than the arrivals after it.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Median across the {doc['tokens']}: "
             f"{med_event*100:.1f}% for the giveaway week against "
             f"{med_later*100:.1f}% for everyone later."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"The week is a minority of the crowd on "
             f"{doc['event_minority']} of them, and the median token drew "
             f"{doc['median_event_share']*100:.1f}% of its lifetime "
             f"recipients in it."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"${widest['sym']} is the widest: "
             f"{widest['event']['kept']*100:.1f}% against "
             f"{widest['later']['kept']*100:.1f}%, with "
             f"{widest['event_share']*100:.0f}% of its recipients arriving "
             f"that week."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "What the later group is cannot be settled from the chain. It "
             "holds buyers, late claimers and wallets that were sent the "
             "token by"))
b.append(txt(L, y + 58, 19, SUB,
             "someone else, and all three pass the same test. The quoted "
             "retention figure counts them as retained giveaway recipients."))
b.append(txt(L, y + 84, 19, SUB,
             f"The giveaway is found rather than assumed: the busiest day of "
             f"arrivals is the anchor and the {doc['window']} days either "
             f"side are the event."))
b.append(txt(L, y + 110, 19, SUB,
             f"{doc['no_spike']} tokens above "
             f"{doc['min_recipients']:,} recipients have no week holding "
             f"{doc['floor_share']*100:.0f}% of arrivals and are dropped, "
             f"bridged contracts among them."))
if im_worse is None or im_better is None:
    raise SystemExit("  no sampled mobility on one side; the footer compares "
                     "the two groups and would be comparing nothing")
b.append(txt(L, y + 136, 19, SUB,
             f"Nothing is priced. The blue rows' holders are "
             f"{im_better*100:.1f}% immobile against {im_worse*100:.1f}%, "
             f"which suggests an explanation rather than settling one."))
b.append(txt(R, y + 164, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 196
render("arrival_split", W, H, "".join(b))
print(f"  {doc['tokens']} tokens, {len(worse)} worse in the giveaway week, "
      f"median {med_event*100:.1f}% against {med_later*100:.1f}%")
