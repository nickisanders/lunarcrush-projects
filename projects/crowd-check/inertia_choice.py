#!/usr/bin/env python3
"""Holding still is usually a choice, and on one token it is not.

Every bar is the share of a token's holders sitting on exactly what they were
originally sent, split by whether they could have done otherwise. An address
with no ETH that has never sent a transaction cannot pay gas, so it cannot
sell, vote or leave. The rest had the gas and the history and chose not to.

The two are logically nested: an address that has never sent a transaction
cannot have sold anything, so every immobile holder is also an inert one. The
data agrees on all ten tokens, which is the check that the buckets are not
double counting.

They are not otherwise related. Across these tokens the correlation between
inertia and immobility is +0.74 with the outlier and -0.08 without it, so the
blue segment is doing real work that the inert figure alone cannot see.

One caveat the footer carries: inertia is read from every holder, immobility
is sampled, so the split inside each bar carries sampling error the total
does not.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 inertia_choice.py
"""

import json
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
    k = (d.get("dust") or {}).get("kinds") or {}
    m = d.get("mobility") or {}
    if "exited_leaving_dust" not in k or "immobile_share" not in m:
        continue
    if m["of_holders"] < MIN_HOLDERS:
        continue
    inert = k["untouched_small"] + k["untouched_large"]
    rows.append({"sym": name.upper(), "inert": inert,
                 "immobile": min(m["immobile_share"], inert),
                 "holders": m["of_holders"]})
if not rows:
    raise SystemExit("  no token carries both measures yet")
rows.sort(key=lambda r: -r["immobile"])

W = 1240
L, R = 60, 1180
LABEL = 200
BARW = R - L - LABEL - 150
BH = 52

b = [txt(L, 58, 37, INK, "Holding still is usually a choice.", 700),
     txt(L, 98, 37, INK, "On one token it is not a choice at all.", 700),
     txt(L, 138, 20, SUB,
         "Holders sitting on exactly what they were sent, split by whether they "
         "could have done otherwise.")]

y = 206
for r in rows:
    stuck = BARW * r["immobile"]
    free = BARW * (r["inert"] - r["immobile"])
    b.append(txt(L, y + BH - 18, 22, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{stuck:.1f}" height="{BH}" fill="{HOT}"/>')
    b.append(f'<rect x="{L+LABEL+stuck:.1f}" y="{y}" width="{free:.1f}" height="{BH}" '
             f'fill="{BRAND}"/>')
    if stuck > 95:
        b.append(txt(L + LABEL + stuck - 14, y + BH - 17, 24, "#ffffff",
                     f"{r['immobile']*100:.0f}%", 700, "end", MONO))
    if free > 95:
        b.append(txt(L + LABEL + stuck + free - 14, y + BH - 17, 24, "#ffffff",
                     f"{(r['inert']-r['immobile'])*100:.0f}%", 700, "end", MONO))
    b.append(txt(R, y + BH - 18, 19, SUB, f"{r['holders']:,} holders", 400, "end"))
    y += BH + 13

y += 18
sw = (R - L) / 2
for i, (col, label) in enumerate(
        ((HOT, "could not act: no ETH, never sent a transaction"),
         (BRAND, "could have acted and chose not to"))):
    x = L + i * sw
    b.append(f'<rect x="{x:.0f}" y="{y}" width="16" height="16" rx="3" fill="{col}"/>')
    b.append(txt(x + 26, y + 14, 19, SUB, label))
y += 52

worst, rest = rows[0], rows[1:]
gap = min(r["inert"] - r["immobile"] for r in rest)
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="88" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="88" fill="{HOT}"/>')
b.append(txt(L + 26, y + 34, 22, INK,
             f"On every token but one, at least {gap*100:.0f} points of the "
             f"holders who never moved could have.", 700))
b.append(txt(L + 26, y + 66, 20, SUB,
             f"On ${worst['sym']} the gap is "
             f"{(worst['inert']-worst['immobile'])*100:.0f} points."))
y += 128

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Inertia read from every holder. Immobility sampled per token, so the "
             "split inside each bar carries error the total does not."))
# Kept short: the attribution sits on this same line and the long
# version ran straight through it.
b.append(txt(L, y + 58, 19, SUB,
             "No transaction means no sale, so immobile is a subset of inert."))
b.append(txt(R, y + 58, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 88

render("inertia_choice", W, H, "".join(b))
