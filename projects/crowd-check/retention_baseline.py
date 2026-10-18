#!/usr/bin/env python3
"""Holder retention across five tokens, with contract age controlled for.

Reads out/retention-baseline.json from proof-of-crowd-tools, measured
2026-10-18 by scanning every transfer from each contract's deployment and
joining the day each address arrived to who still holds.

Two panels because the second is the one that means something. A raw retention
figure is not comparable across tokens: an older contract has had longer to
lose people, so $FET at 2,196 days and $ZAMA at 273 are not being asked the
same question. Matching cohorts on exposure asks it properly, and the gap that
survives that is the finding.

Usage: python3 retention_baseline.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
NEUTRAL, BRAND, HOT = "#8d8578", "#1b3a6b", "#a33228"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


d = json.loads(SRC.read_text())["tokens"]
ORDER = ["strk", "w", "ape", "zama"]

W, H = 1200, 1090
L, R = 60, 1140

b = [txt(L, 58, 36, INK, "Three tokens keep about 40% of everyone who", 700),
     txt(L, 96, 36, INK, "ever held them. One keeps 17%.", 700),
     txt(L, 132, 20, SUB,
         "Every transfer since each contract was deployed, joined to who still "
         "holds today.")]


def panel(y, title, note, key, colour_rule):
    b.append(txt(L, y, 24, INK, title, 700))
    b.append(txt(L, y + 30, 19, SUB, note))
    yy = y + 62
    BW, BH = R - L - 150, 48
    for name in ORDER:
        v = d[name].get(key)
        if v is None:
            continue
        col = colour_rule(name)
        b.append(txt(L, yy + 40, 25, INK, "$" + name.upper(), 700, "start", MONO))
        b.append(f'<rect x="{L+150}" y="{yy+8}" width="{BW}" height="{BH}" fill="#f2efe8"/>')
        b.append(f'<rect x="{L+150}" y="{yy+8}" width="{BW*v/0.5:.0f}" height="{BH}" fill="{col}"/>')
        b.append(txt(L + 150 + BW * v / 0.5 - 18, yy + 40, 28, "#ffffff",
                     f"{v*100:.1f}%", 700, "end", MONO))
        yy += BH + 14
    return yy


y = panel(190, "Raw retention", "Not comparable: an older contract has had longer to lose people.",
          "raw", lambda n: NEUTRAL)
b.append(f'<line x1="{L}" y1="{y+14}" x2="{R}" y2="{y+14}" stroke="{RULE}" stroke-width="2"/>')
y = panel(y + 50,
          "Matched on exposure",
          "Only those who arrived in each token's last twelve months, so every "
          "group has had the same time to leave.",
          "cohort", lambda n: HOT if n == "zama" else BRAND)

z = d["zama"]["biggest_cohort"]
y += 26
b.append(f'<rect x="{L}" y="{y-26}" width="{R-L}" height="76" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y-26}" width="5" height="76" fill="{HOT}"/>')
b.append(txt(L + 26, y + 2, 22, INK,
             f"$ZAMA's largest cohort: {z['arrived']:,} addresses arrived in "
             f"{z['month']}, and {100-z['retention']*100:.0f}% are gone.", 700))
b.append(txt(L + 26, y + 30, 20, SUB,
             "It is the one token here scored manufactured on its social data alone, at 98 of 100."))

y = H - 52
b.append(f'<line x1="{L}" y1="{y-36}" x2="{R}" y2="{y-36}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y, 19, SUB, "Four tokens is not a baseline yet. $FET and $PEPE are still counting."))
b.append(txt(R, y, 19, SUB, "measured 2026-10-18  ·  @nickisanders", 400, "end"))

render("retention_baseline", W, H, "".join(b))
