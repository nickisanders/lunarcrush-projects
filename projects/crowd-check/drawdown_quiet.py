#!/usr/bin/env python3
"""A market fell for eight weeks. Did the airdrop crowd do anything about it?

Each line is one token's daily count of wallets that moved any of the
balance they were holding when the window opened, as a share of that same
opening crowd. The denominator is fixed, so the line is a share of one crowd
throughout rather than of a shrinking one, and a day where nobody acts reads
as nothing rather than as everyone having left.

The baseline this comes out of is snapshots: each token was scanned once,
with no history behind it, so until now nothing in it could say what a
holder did across a particular stretch of weeks. A netted balance is a sum,
which is the way in. The balance at an earlier block is the scan's balance
minus whatever moved after it, so walking one window of blocks gives both
ends and every day in between.

Contracts are dropped. A pool rebalances daily and would swamp a count it is
not part of, and on one of these two tokens 61.3% of the addresses holding
at the open have code.

The objection this chart has to answer is gas. A wallet with no ETH that has
never sent a transaction cannot sell, so its stillness is not a decision.
That share is sampled per token and taken off the headline rather than
mentioned underneath it.

Two tokens is a pilot, not a finding, and the footer says so.

Reads out/drawdown-daily.json.

Usage: python3 drawdown_quiet.py
"""

import datetime
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
def fits(x, size, s, weight=400, rt=None):
    rt = R if rt is None else rt
    width = len(str(s)) * size * (0.53 if weight >= 700 else 0.415)
    if width > rt - x:
        over = int((width - (rt - x)) / (size * 0.415))
        print(f"  WARNING: {size}px line runs ~{over} characters past the "
              f"margin: {str(s)[:60]}...", flush=True)


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None, rt=None):
    if anchor == "start" and font is None:
        fits(x, size, s, weight, rt)
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


doc = json.loads((ROOT / "drawdown-daily.json").read_text())
syms = sorted(doc, key=lambda s: -doc[s]["wallets"])
if len(syms) < 2:
    raise SystemExit(f"  only {len(syms)} token(s) measured; the chart draws "
                     f"a comparison")
days = [r["day"] for r in doc[syms[0]]["series"]]
for s in syms:
    if [r["day"] for r in doc[s]["series"]] != days:
        raise SystemExit(f"  ${s} covers different days from ${syms[0]}; two "
                         f"windows cannot share one axis")

# The chart asserts that nobody reacted, so the ceiling is the busiest single
# day any token had. If that day is quiet the whole window is.
peak = max(doc[s]["peak"]["share"] for s in syms)
TOPV = 0.02 if peak < 0.019 else (round(peak * 1.15, 3) + 0.001)
PX, PW = L + 76, R - (L + 76)
PY, PH = 258, 300
COLOR = {syms[0]: BRAND, syms[1]: HOT}


def px(i):
    return PX + i * PW / (len(days) - 1)


def py(v):
    return PY + PH - (v / TOPV) * PH


big = doc[syms[0]]
b = [txt(L, 58, 37, INK, "A market fell for eight weeks and the crowd", 700),
     txt(L, 98, 37, INK, "that was given these tokens never looked up.", 700),
     txt(L, 138, 20, SUB,
         f"Wallets that moved any of what they held, each day, as a share of "
         f"the crowd holding on {days[0]}."),
     txt(L, 166, 20, SUB,
         f"The busiest day of the whole window moved "
         f"{big['peak']['share']*100:.2f}% of ${syms[0]}'s "
         f"{big['wallets']:,} wallets."),
     txt(L, 194, 20, SUB,
         "Contracts dropped. Pools rebalance daily and are not part of the "
         "crowd being counted.")]

# Grid and the y scale, drawn first so the lines sit over it.
step = 0.005
v = 0.0
while v <= TOPV + 1e-9:
    b.append(f'<line x1="{PX}" y1="{py(v):.0f}" x2="{R}" y2="{py(v):.0f}" '
             f'stroke="{RULE if v else INK}" stroke-width="{1 if v else 2}"/>')
    b.append(txt(PX - 14, py(v) + 6, 17, SUB, f"{v*100:.1f}%", 400, "end",
                 MONO))
    v += step

kx = R
for s_ in reversed(syms):
    b.append(txt(kx, PY - 22, 19, COLOR[s_], f"${s_}", 700, "end"))
    kx -= (len(s_) + 1) * 19 * 0.53 + 12
    b.append(f'<line x1="{kx-24:.0f}" y1="{PY-28}" x2="{kx:.0f}" '
             f'y2="{PY-28}" stroke="{COLOR[s_]}" stroke-width="2.5"/>')
    kx -= 60

for i, d in enumerate(days):
    # The last day is always labelled, so a tick that would crowd it is not.
    if (i % 7 or len(days) - 1 - i < 6) and i != len(days) - 1:
        continue
    lab = datetime.date.fromisoformat(d).strftime("%b %-d")
    b.append(f'<line x1="{px(i):.0f}" y1="{PY+PH}" x2="{px(i):.0f}" '
             f'y2="{PY+PH+7}" stroke="{SUB}" stroke-width="1"/>')
    b.append(txt(px(i), PY + PH + 30, 17, SUB, lab, 400,
                 "end" if i == len(days) - 1 else "middle", MONO))

for s in syms:
    pts = " ".join(f"{px(i):.1f},{py(r['share']):.1f}"
                   for i, r in enumerate(doc[s]["series"]))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{COLOR[s]}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
# Each token's own median, as a flat reference the eye can hold the line
# against. A trend is the claim here, so the level has to be visible.
for s in syms:
    m = doc[s]["median_share"]
    b.append(f'<line x1="{PX}" y1="{py(m):.1f}" x2="{R}" y2="{py(m):.1f}" '
             f'stroke="{COLOR[s]}" stroke-width="1" stroke-dasharray="2 5" '
             f'opacity="0.55"/>')

y = PY + PH + 76
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="162" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="162" fill="{HOT}"/>')
b.append(txt(L + 26, y + 40, 24, INK,
             "Holding still is only conviction if selling was possible.",
             700))
for i, s in enumerate(syms):
    d = doc[s]
    lo, hi = d["chose_ci"]
    b.append(txt(L + 26, y + 74 + i * 28, 20, SUB,
                 f"${s}: {d['inert_share']*100:.1f}% never touched it. "
                 f"{d['immobile_share']*100:.1f}% of those cannot pay gas, "
                 f"leaving {d['chose_share']*100:.1f}% "
                 f"[{lo*100:.0f}–{hi*100:.0f}] that could have acted and "
                 f"did not.", 400, "start", None, R - 26))
b.append(txt(L + 26, y + 74 + len(syms) * 28, 20, SUB,
             "Immobile means a wallet that has never sent a transaction and "
             "holds no ETH now, sampled 250 per token.", 400, "start", None,
             R - 26))

y += 198
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
notes = [
    f"${syms[0]} thinned as the fall went on: {big['first_half']*100:.2f}% of "
    f"the crowd acted on the average day of the first half, "
    f"{big['second_half']*100:.2f}% in the second.",
    f"${syms[1]} did not move either way, holding "
    f"{doc[syms[1]]['first_half']*100:.2f}% against "
    f"{doc[syms[1]]['second_half']*100:.2f}%, so the thinning is one token's "
    f"and not a pattern yet.",
    "Dashed lines are each token's median day. Moving means any change in "
    "the balance, so being sent more counts alongside selling.",
    f"Two tokens over {len(days)} days, which is a pilot and not a finding. "
    f"The method reads any token in the baseline from one window scan.",
]
for i, n in enumerate(notes):
    b.append(txt(L, y + 32 + i * 26, 19, SUB, n))
b.append(txt(R, y + 32 + len(notes) * 26, 19, SUB,
             f"measured {days[-1]}  ·  @nickisanders", 400, "end"))

H = y + 64 + len(notes) * 26
render("drawdown_quiet", W, H, "".join(b))
print(f"  {len(syms)} tokens, peak {peak*100:.2f}%, "
      + ", ".join(f"${s} chose {doc[s]['chose_share']*100:.1f}%" for s in syms))
