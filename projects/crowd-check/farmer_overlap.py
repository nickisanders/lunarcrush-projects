#!/usr/bin/env python3
"""An airdrop with no repeat collectors may have reached nobody at all.

Every wallet that ever received any of the 94 tokens in the baseline, and how
many of the 94 each one collected. 5.8 million addresses, every Transfer
event, no sampling.

The number people expect to be high is overlap, on the assumption that
airdrops are farmed by a recirculating class. Counting wallets it is low: 83%
of the addresses took exactly one. Counting airdrops it is not: the median
token had 42.8% of its recipients already holding another. Both are true and
the difference is arithmetic rather than anything about the tokens. A wallet
that collected five airdrops is one address in the first count and appears in
five tokens' percentages in the second, so the repeat collectors are counted
repeatedly in exactly the view that makes them look common.

What the two panels are for. Overlap does not predict retention: r is -0.06
and the jackknife crosses zero, which is the result after $PIEVERSE and $DRV
came back at 4.4% and 82.8% overlap with 73.5% and 72.7% retention. Against
the share of holders who cannot transact at all it reads -0.54 with a
jackknife that never comes near zero, the tightest thing in this dataset.

That is close to mechanical once stated, and it is the point. A wallet that
has never sent a transaction cannot have collected a second airdrop, so an
airdrop that reached fresh people and an airdrop that reached addresses which
have never done anything both score low. $PIEVERSE looked like the first and
96.4% of its holders cannot move anything.

The basket is 94 tokens rather than the market, so every overlap figure here
is a floor. A wallet that farmed thirty airdrops none of which are in the set
reads as a first-timer. Widening the basket can only push overlap up, which
makes the 83% the number most likely to erode and the correlation the part
that should survive.

Reads out/wallet-overlap.json and out/retention-baseline.json.

Usage: python3 farmer_overlap.py
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
MIN_ARRIVED, MIN_SAMPLED = 5000, 100

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
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    c = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    d = (sum((x - ma) ** 2 for x in a) ** 0.5) * (sum((y - mb) ** 2 for y in b) ** 0.5)
    return c / d if d else 0


def jackknife(a, b):
    """Leave one out, every time. A correlation one token can move is one
    token's finding."""
    out = [pearson([x for j, x in enumerate(a) if j != i],
                   [y for j, y in enumerate(b) if j != i]) for i in range(len(a))]
    return min(out), max(out)


ov = json.loads((ROOT / "wallet-overlap.json").read_text())
base = json.loads((ROOT / "retention-baseline.json").read_text())
per = {x["sym"]: x for x in ov["tokens"]}

rows = []
for name, d in base["tokens"].items():
    sym = name.upper()
    m = d.get("mobility") or {}
    if sym not in per or d["arrived"] < MIN_ARRIVED:
        continue
    if m.get("of_holders", 0) < MIN_SAMPLED:
        continue
    rows.append({"sym": sym, "ov": per[sym]["two_or_more"],
                 "im": m["immobile_share"], "ret": d["raw"],
                 "arr": d["arrived"]})
if len(rows) < 20:
    raise SystemExit(f"  only {len(rows)} tokens carry overlap and mobility "
                     f"above {MIN_ARRIVED:,} recipients")

X = [r["ov"] for r in rows]
r_im, (jl_im, jh_im) = pearson(X, [r["im"] for r in rows]), jackknife(X, [r["im"] for r in rows])
r_re, (jl_re, jh_re) = pearson(X, [r["ret"] for r in rows]), jackknife(X, [r["ret"] for r in rows])

hist = {int(k): v for k, v in ov["histogram"].items()}
addrs = sum(hist.values())
once = hist.get(1, 0) / addrs
med_tok = statistics.median(x["two_or_more"] for x in ov["tokens"])
most = max(rows, key=lambda r: r["ov"])
least = min(rows, key=lambda r: r["ov"])
# Taken from ov["tokens"] this could name a token that fails the filters
# below and so never appears as a labelled dot.
biggest = max(rows, key=lambda r: r["arr"])

# Named by rule rather than by eye: the two ends of the x-axis and the
# largest airdrop in the basket, so the labels cannot be a selection.
NAMED = {most["sym"], least["sym"], biggest["sym"]}

PW, PH, PGAP = 530, 400, 60
PX2 = L + PW + PGAP

b = [txt(L, 58, 37, INK, "How many of an airdrop's recipients had", 700),
     txt(L, 98, 37, INK, "collected others says nothing about retention.", 700),
     txt(L, 138, 20, SUB,
         f"Every wallet that received any of {ov['basket']} airdrops, and how "
         f"many of them it took. {addrs:,} addresses, no sampling."),
     txt(L, 164, 20, SUB,
         f"Each dot is one token. Across on both panels is the share of its "
         f"recipients who also received another of the {ov['basket']}.")]


def panel(x0, y0, ys, lab, color, r, jl, jh):
    p = [f'<rect x="{x0}" y="{y0}" width="{PW}" height="{PH}" fill="{TRACK}"/>']
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        gy = y0 + PH - PH * g
        p.append(f'<line x1="{x0}" y1="{gy:.0f}" x2="{x0+PW}" y2="{gy:.0f}" '
                 f'stroke="{GROUND}" stroke-width="2"/>')
        p.append(txt(x0 - 8, gy + 5, 15, SUB, f"{g*ys*100:.0f}%", 400, "end"))
    for d in rows:
        cx = x0 + PW * (d["ov"] / 0.9)
        cy = y0 + PH - PH * (d[lab] / ys)
        named = d["sym"] in NAMED
        p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{6 if named else 4.5}" '
                 f'fill="{HOT if named else color}" '
                 f'opacity="{1 if named else 0.55}"/>')
        if named:
            # Beside the dot these ran off the panel at one end and printed
            # through neighbouring dots in the crowded band at the other.
            # Above and centred, clamped to the panel, does both jobs.
            half = len(d["sym"]) * 5 + 6
            lx = min(max(cx, x0 + half), x0 + PW - half)
            p.append(txt(lx, cy - 13, 15, HOT, "$" + d["sym"], 700,
                         "middle", MONO))
    p.append(txt(x0, y0 + PH + 26, 20, INK,
                 f"r = {r:+.2f}", 700))
    p.append(txt(x0 + 90, y0 + PH + 26, 18, SUB,
                 f"jackknife {jl:+.2f} to {jh:+.2f}"))
    return p


b.append(txt(L, 214, 21, INK, "Share of holders who cannot transact at all",
             700))
b += panel(L, 240, 1.0, "im", BRAND, r_im, jl_im, jh_im)
b.append(txt(PX2, 214, 21, INK, "Share of recipients still holding", 700))
b += panel(PX2, 240, 0.8, "ret", BRAND, r_re, jl_re, jh_re)

for x0 in (L, PX2):
    for g in (0, 0.45, 0.9):
        b.append(txt(x0 + PW * (g / 0.9), 240 + PH + 50, 15, SUB,
                     f"{g*100:.0f}%", 400, "middle"))

y = 240 + PH + 76
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"A wallet that has never sent a transaction cannot have "
             f"collected a second airdrop.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"So an airdrop that reached fresh people and one that reached "
             f"addresses which have never done anything both score low on the "
             f"left."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"${least['sym']} looked like the first. "
             f"{least['im']*100:.1f}% of its holders cannot move anything, "
             f"and it retains {least['ret']*100:.1f}% against "
             f"${most['sym']}'s {most['ret']*100:.1f}%."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"${most['sym']} sits at {most['ov']*100:.1f}% overlap and "
             f"${least['sym']} at {least['ov']*100:.1f}%, on airdrops of "
             f"{most['arr']:,} and {least['arr']:,} recipients."))
y += 184

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"By wallet, {once*100:.0f}% of the {addrs:,} addresses took "
             f"exactly one of the {ov['basket']}. By token, the median "
             f"airdrop had {med_tok*100:.1f}% repeat collectors."))
b.append(txt(L, y + 58, 19, SUB,
             "Both are true. A wallet that collected five is one address in "
             "the first count and sits in five tokens' percentages in the "
             "second."))
b.append(txt(L, y + 84, 19, SUB,
             f"The basket is {ov['basket']} tokens and not the market, so "
             f"every figure here is a floor: a wallet that farmed elsewhere "
             f"reads as a first-timer."))
b.append(txt(L, y + 110, 19, SUB,
             f"{len(rows)} tokens carry both measures above "
             f"{MIN_ARRIVED:,} recipients. Immobility is sampled at 250 "
             f"addresses per token."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {ov['measured']}  ·  @nickisanders", 400, "end"))
H = y + 166

render("farmer_overlap", W, H, "".join(b))
print(f"  {len(rows)} tokens, overlap vs immobile r={r_im:+.3f} "
      f"({jl_im:+.3f} to {jh_im:+.3f}), vs retention r={r_re:+.3f} "
      f"({jl_re:+.3f} to {jh_re:+.3f})")
