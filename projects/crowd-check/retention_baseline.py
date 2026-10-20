#!/usr/bin/env python3
"""Holder retention across seven tokens, against how concentrated arrival was.

Reads out/retention-baseline.json from proof-of-crowd-tools, measured
2026-10-18 by scanning every transfer from each contract's deployment and
joining the day each address arrived to who still holds.

The second panel used to show retention among each token's last twelve months
of arrivals, on the theory that it matched them on exposure. It did not. That
window covered 100% of $ZAMA's arrivals and 5.7% of $APE's, so for a young
token it described the whole token and for an old one it described a recent
sliver that had not had time to decay. Every old token read 39-42% for that
reason alone.

What replaces it is the thing actually worth plotting: the share of all holders
who arrived in a single month. Age is still mixed into it, because the
concentrated tokens here are also the young ones, and the footer says so.

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
ORDER = ["strk", "fet", "w", "ape", "ens", "aztec", "zama"]

W = 1200
L, R = 60, 1140

b = [txt(L, 58, 36, INK, "The more of a token's holders arrive in one", 700),
     txt(L, 96, 36, INK, "month, the fewer of them stay.", 700),
     txt(L, 132, 20, SUB,
         "Every transfer since each contract was deployed, joined to who still "
         "holds today.")]


def panel(y, title, note, key, colour_rule, full=0.5):
    """`full` is the value that fills the track. Retention tops out under 40%
    so a half-width scale reads well, but concentration reaches 61% and the
    same scale ran $ZAMA's bar off the canvas."""
    b.append(txt(L, y, 24, INK, title, 700))
    b.append(txt(L, y + 30, 19, SUB, note))
    yy = y + 62
    BW, BH = R - L - 150, 48
    for name in ORDER:
        if key not in d[name]:
            raise SystemExit(f"{name} has no '{key}' in retention-baseline.json. "
                             f"A skipped bar renders as a clean chart with a "
                             f"missing token, so this stops instead.")
        v = d[name][key]
        col = colour_rule(name)
        b.append(txt(L, yy + 40, 25, INK, "$" + name.upper(), 700, "start", MONO))
        b.append(f'<rect x="{L+150}" y="{yy+8}" width="{BW}" height="{BH}" fill="#f2efe8"/>')
        w = min(BW * v / full, BW)
        b.append(f'<rect x="{L+150}" y="{yy+8}" width="{w:.0f}" height="{BH}" fill="{col}"/>')
        # $FET at 5.4% has a bar too short to hold its own label, which clipped
        # the leading digit. Below that width the figure sits outside, in ink.
        inside = w > 130
        b.append(txt(L + 150 + w - 18 if inside else L + 150 + w + 14, yy + 40, 28,
                     "#ffffff" if inside else INK,
                     f"{v*100:.1f}%", 700, "end" if inside else "start", MONO))
        yy += BH + 14
    return yy


y = panel(190, "Retention", "Share of everyone who ever received the token and still holds it.",
          "raw", lambda n: HOT if n == "zama" else NEUTRAL)
b.append(f'<line x1="{L}" y1="{y+14}" x2="{R}" y2="{y+14}" stroke="{RULE}" stroke-width="2"/>')
y = panel(y + 50,
          "Concentration of arrival",
          "Share of all holders who first received the token in its single "
          "biggest month.",
          "concentration", lambda n: HOT if n == "zama" else BRAND, full=0.7)

z = d["zama"]["biggest_cohort"]
y += 26
b.append(f'<rect x="{L}" y="{y-26}" width="{R-L}" height="76" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y-26}" width="5" height="76" fill="{HOT}"/>')
b.append(txt(L + 26, y + 2, 22, INK,
             f"$ZAMA's largest cohort: {z['arrived']:,} addresses arrived in "
             f"{z['month']}, and {100-z['retention']*100:.0f}% are gone.", 700))
b.append(txt(L + 26, y + 30, 20, SUB,
             "It is the one token here scored manufactured on its social data alone, at 98 of 100."))

# Height follows the content. It was pinned at 1090 for four tokens, so
# adding three ran the second panel and the footer off the canvas.
y += 92
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Seven tokens, r = -0.84. The concentrated ones are also the young "
             "ones, so part of this gap is age rather than acquisition."))
b.append(txt(L, y + 58, 19, SUB, "$PEPE is still counting."))
b.append(txt(R, y + 58, 19, SUB, "measured 2026-10-19  ·  @nickisanders", 400, "end"))
H = y + 88

render("retention_baseline", W, H, "".join(b))
