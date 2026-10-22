#!/usr/bin/env python3
"""What a holder count is actually counting.

Every project quotes a holder number and none of them say what those holders
hold. Reading the balance of every holder of eight tokens and bucketing by
what the position is worth, $BLUR's 51,179 holders come down to 1,240 above
$100, and two thirds of them hold less than a dollar.

Two panels, because the share above $100 is the finding and the dust share is
the thing that makes it concrete. Sorted by the share above $100, which puts
the ranking on the measure the headline claims.

The dollar thresholds move with price, so a token that has fallen hard shows
more dust for that reason alone. The footer says so rather than leaving it to
be discovered.

Reads out/*-wallets.json from proof-of-crowd-tools.

Usage: python3 dust.py
"""

import glob
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


rows = []
for p in sorted(glob.glob(str(SRC / "*-wallets.json"))):
    d = json.loads(Path(p).read_text())
    h = d.get("holders_headline") or 0
    if not h:
        continue
    buckets = d.get("buckets") or {}
    key = [k for k in buckets if "under" in k]
    rows.append({"sym": d["symbol"], "holders": h,
                 "dust": buckets[key[0]] if key else 0,
                 "big": d.get("with_100_usd") or 0})
for r in rows:
    r["dust_s"] = r["dust"] / r["holders"]
    r["big_s"] = r["big"] / r["holders"]
rows.sort(key=lambda r: -r["big_s"])

W = 1240
L, R = 60, 1180
LABEL, GAP, RIGHTCOL = 150, 54, 150
COLW = (R - L - LABEL - GAP - RIGHTCOL) / 2
BH = 50

# "Almost all of it is dust" was the first headline and it overstates: $STRK
# is 14.8% dust and $AZTEC 9.1%. What is true of every token here is that a
# minority of holders hold a position worth $100, topping out at 37.9%.
b = [txt(L, 58, 37, INK, "Every project quotes a holder count.", 700),
     txt(L, 98, 37, INK, "In none of these do most holders hold $100.", 700),
     txt(L, 136, 20, SUB,
         "The balance of every holder of eight tokens, bucketed by what the "
         "position is actually worth.")]

y0 = 206
b.append(txt(L + LABEL, y0 - 14, 21, INK, "Holders with $100 or more", 700))
b.append(txt(L + LABEL + COLW + GAP, y0 - 14, 21, INK, "Holders with under $1", 700))

y = y0 + 14
for r in rows:
    col = HOT if r["sym"] in ("BLUR", "APE") else BRAND
    b.append(txt(L, y + BH - 15, 24, INK, "$" + r["sym"], 700, "start", MONO))
    for i, (share, shade) in enumerate(((r["big_s"], col), (r["dust_s"], col))):
        x = L + LABEL + i * (COLW + GAP)
        w = max(COLW * share, 2)
        b.append(f'<rect x="{x:.0f}" y="{y}" width="{COLW:.0f}" height="{BH}" fill="{TRACK}"/>')
        b.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{BH}" fill="{shade}"/>')
        inside = w > 110
        b.append(txt(x + w - 14 if inside else x + w + 12, y + BH - 16, 24,
                     "#ffffff" if inside else INK, f"{share*100:.1f}%", 700,
                     "end" if inside else "start", MONO))
    b.append(txt(R, y + BH - 16, 19, SUB, f"{r['holders']:,} holders", 400, "end"))
    y += BH + 12

blur = next(r for r in rows if r["sym"] == "BLUR")
y += 22
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="86" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="86" fill="{HOT}"/>')
b.append(txt(L + 26, y + 34, 22, INK,
             f"$BLUR has {blur['holders']:,} holders. {blur['big']:,} of them hold "
             f"more than $100.", 700))
b.append(txt(L + 26, y + 64, 20, SUB,
             "A holder count treats a wallet with eleven cents exactly like one "
             "with eleven thousand dollars."))

y += 114
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Dollar thresholds move with price, so a token that has fallen hard shows "
             "more dust for that reason alone."))
b.append(txt(L, y + 58, 19, SUB,
             "Balances read off the chain for every holder, not a sample."))
b.append(txt(R, y + 58, 19, SUB, "measured 2026-10-22  ·  @nickisanders", 400, "end"))
H = y + 88

render("dust", W, H, "".join(b))
