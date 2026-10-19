#!/usr/bin/env python3
"""Two privacy airdrops of near-identical size, one month, two outcomes.

$AZTEC distributed to 21,479 addresses in February 2026 and $ZAMA to 21,762,
within 300 of each other. Same month, same market, same size of giveaway, so
the retention gap that follows is not age, conditions or cohort size.

The top panel exists to show the two cohorts are the same. The one below it
shows they are not. The kicker is that Aztec's airdrop crowd held on better
than Zama's non-airdrop crowd, which rules out Aztec simply having drawn fewer
farmers.

Reads out/aztec-zama.json from proof-of-crowd-tools (cohort_split.py).

Usage: python3 airdrop_split.py
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/aztec-zama.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"

COL = {"aztec": BRAND, "zama": HOT}
ORDER = ["aztec", "zama"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


d = json.loads(SRC.read_text())["tokens"]

W = 1200
L, R = 60, 1140
LABEL = 150                      # gutter for the $TICKER
BW, BH = R - L - LABEL, 52       # bar track width and height

b = [txt(L, 58, 37, INK, "Two privacy airdrops, same month,", 700),
     txt(L, 98, 37, INK, "same size, and nothing else alike.", 700),
     txt(L, 136, 20, SUB,
         "Every transfer since each contract was deployed, joined to who holds today.")]


def bars(y, title, note, pick, denom, fmt):
    """One panel. `pick` returns the value, `denom` the full-bar value."""
    b.append(txt(L, y, 25, INK, title, 700))
    b.append(txt(L, y + 30, 19, SUB, note))
    yy = y + 58
    for name in ORDER:
        v = pick(d[name])
        w = max(BW * v / denom, 1)
        b.append(txt(L, yy + BH - 14, 25, INK, "$" + name.upper(), 700, "start", MONO))
        b.append(f'<rect x="{L+LABEL}" y="{yy}" width="{BW}" height="{BH}" fill="{TRACK}"/>')
        b.append(f'<rect x="{L+LABEL}" y="{yy}" width="{w:.0f}" height="{BH}" fill="{COL[name]}"/>')
        # Keep the figure inside its own bar unless the bar is too short to hold it.
        inside = w > 190
        b.append(txt(L + LABEL + w - 18 if inside else L + LABEL + w + 14,
                     yy + BH - 15, 29, "#ffffff" if inside else INK,
                     fmt(v), 700, "end" if inside else "start", MONO))
        yy += BH + 14
    return yy


top = max(d[n]["distribution"]["arrived"] for n in ORDER)
y = bars(196, "February 2026: addresses that received the airdrop",
         "Within 300 addresses of each other, which is what makes the rest comparable.",
         lambda t: t["distribution"]["arrived"], top, lambda v: f"{v:,.0f}")

b.append(f'<line x1="{L}" y1="{y+16}" x2="{R}" y2="{y+16}" stroke="{RULE}" stroke-width="2"/>')

y = bars(y + 56, "Of those same addresses, who still holds",
         "Eight months later. Same month, same market, same size of giveaway.",
         lambda t: t["distribution"]["retention"], 0.5, lambda v: f"{v*100:.1f}%")

az, za = d["aztec"], d["zama"]
y += 24
b.append(f'<rect x="{L}" y="{y-26}" width="{R-L}" height="86" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y-26}" width="5" height="86" fill="{BRAND}"/>')
b.append(txt(L + 26, y + 4, 23, INK,
             f"Aztec's airdrop crowd ({az['distribution']['retention']*100:.1f}%) held on better than "
             f"Zama's non-airdrop crowd ({za['after']['retention']*100:.1f}%).", 700))
b.append(txt(L + 26, y + 34, 20, SUB,
             "Which rules out the easy explanation, that Aztec just drew fewer farmers."))

# The caveat and the credit each get their own line. Sharing one put them on
# top of each other, since the caveat is a sentence and not a label.
y += 92
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
w = az["worst_month"]
month = datetime.strptime(w["month"], "%Y-%m").strftime("%B %Y")
b.append(txt(L, y + 32, 19, SUB,
             f"Aztec has its own hole: {w['arrived']:,} addresses arrived in {month} and "
             f"{w['retention']*100:.1f}% remain, {w['share']*100:.0f}% of all holders ever."))
b.append(txt(R, y + 62, 19, SUB, "measured 2026-10-19  ·  @nickisanders", 400, "end"))
H = y + 92

render("airdrop_split", W, H, "".join(b))
