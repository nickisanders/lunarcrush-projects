#!/usr/bin/env python3
"""Two reasons a wallet holds dust, and why one number cannot tell them apart.

A small balance has two completely different histories behind it. Someone was
handed an airdrop and never touched it, or someone bought a real position and
sold out of it, leaving a tail. The first wallet never showed up. The second
showed up and left. Every residue measure built so far reports them as one.

Separating them needs what each address ever received, not only what it holds
now. A wallet still sitting on most of what it was sent has never traded; one
holding a fraction of a percent of it sold out.

The two tokens here retain 46.6% and 7.3% of everyone who ever held them, a
sixfold gap, and land within a point of each other on the share that sold out
to a tail. Two tokens is not a pattern and the footer says so.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 residue_split.py
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
MID, GREY = "#4a6fa5", "#9a948a"

# Order matters: the two that a plain residue number folds together sit next
# to each other, so the eye reads them as the one block they used to be.
SEGMENTS = [("exited_leaving_dust", HOT, "sold out, left a tail"),
            ("untouched_small", BRAND, "handed a little, never moved it"),
            ("untouched_large", MID, "handed a lot, never moved it"),
            ("part_sold", GREY, "sold part of a position")]


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
    if "exited_leaving_dust" not in k:
        continue
    rows.append({"name": name.upper(), "ret": d["raw"], "held": d["kept"],
                 "arrived": d["arrived"], "k": k})
rows.sort(key=lambda r: -r["ret"])
if not rows:
    raise SystemExit("  no token carries the split yet")

W = 1240
L, R = 60, 1180
LABEL = 290
BARW = R - L - LABEL
BH = 92

b = [txt(L, 58, 37, INK, "A token can keep three quarters of its holders", 700),
     txt(L, 98, 37, INK, "and have almost none who ever traded.", 700),
     txt(L, 138, 20, SUB,
         "Everyone still holding, split by what they were originally sent against "
         "what they have left. Sorted by retention.")]

y = 196
for r in rows:
    b.append(txt(L, y + 34, 25, INK, f"kept {r['ret']*100:.1f}%", 700, "start", MONO))
    b.append(txt(L, y + 62, 18, SUB, f"{r['held']:,} of {r['arrived']:,}"))
    x = L + LABEL
    b.append(f'<rect x="{x}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    for key, col, _ in SEGMENTS:
        share = r["k"][key]
        w = BARW * share
        b.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{BH}" fill="{col}"/>')
        if w > 74:
            b.append(txt(x + w / 2, y + BH / 2 + 9, 25, "#ffffff",
                         f"{share*100:.1f}%", 700, "middle", MONO))
        x += w
    y += BH + 26

# Computed, not written for a fixed number of tokens. An earlier version
# hardcoded a two-token comparison and kept asserting it after the third and
# fourth arrived and destroyed it.
top = rows[0]
inert = top["k"]["untouched_small"] + top["k"]["untouched_large"]
ex = [r["k"]["exited_leaving_dust"] for r in rows]
y += 8
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="92" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="92" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 22, INK,
             f"The top token kept {top['ret']*100:.1f}% of its holders. "
             f"{inert*100:.1f}% of them have never moved what they were sent.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Across {len(rows)} tokens the share that sold out to a tail runs from "
             f"{min(ex)*100:.1f}% to {max(ex)*100:.1f}%, so nothing here is a rule yet."))
y += 122

sw = (R - L) / len(SEGMENTS)
for i, (_, col, label) in enumerate(SEGMENTS):
    x = L + i * sw
    b.append(f'<rect x="{x:.0f}" y="{y}" width="15" height="15" rx="3" fill="{col}"/>')
    b.append(txt(x + 24, y + 13, 18, SUB, label))
y += 44

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"{len(rows)} tokens is not a pattern. The rest of the set is being "
             "rescanned to capture what each address was originally sent."))
b.append(txt(L, y + 58, 19, SUB,
             "Price free: every cut is relative to what the wallet itself received."))
b.append(txt(R, y + 58, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 88

render("residue_split", W, H, "".join(b))
