#!/usr/bin/env python3
"""How much fee revenue each chain earns per dollar of capital parked on it.

Fees and TVL are both ordinary size measures and both get quoted as if they
settle which chain is biggest. Dividing one by the other asks a different
question: how hard the capital sitting there is actually working. The answer
spans two orders of magnitude, which is why "biggest chain" arguments never
resolve. The parties are each holding a real number.

Chains under $100M TVL are excluded. The ratio is unstable when the
denominator is small, and $0.3M of fees over $20M of TVL says more about the
noise than the chain.

Reads out/usage.json, written by the usage pull. All DeFiLlama: fees as a
30-day total, TVL as of the measurement date. No social data is involved,
which is the point, since the attention half of this project is retracted.

Usage: python3 capital_work.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "out" / "usage.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
MIN_TVL = 100_000_000


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


rows = [r for r in json.loads(SRC.read_text()) if r["tvl"] >= MIN_TVL]
for r in rows:
    r["per1k"] = r["fees"] / r["tvl"] * 1000
rows.sort(key=lambda r: -r["per1k"])

W = 1200
L, R = 60, 1140
# The label gutter has to clear "Hyperliquid" in 23px mono, and the bars have
# to stop short of the parked column or the longest one runs through it.
LABEL, RIGHTCOL, BH = 205, 175, 46
BW = R - L - LABEL - RIGHTCOL
top = rows[0]["per1k"]

b = [txt(L, 58, 37, INK, "Every chain holds capital. They do not", 700),
     txt(L, 98, 37, INK, "work it anywhere near as hard.", 700),
     txt(L, 136, 20, SUB,
         "Fee revenue over 30 days per $1,000 of capital parked on the chain.")]

y = 196
for r in rows:
    w = max(BW * r["per1k"] / top, 2)
    col = HOT if r["chain"] in ("Ethereum", "Tron") else BRAND
    r["short"] = r["chain"].replace(" L1", "")
    name = r["chain"].replace(" L1", "")
    b.append(txt(L, y + BH - 13, 23, INK, name, 700, "start", MONO))
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{BW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{w:.0f}" height="{BH}" fill="{col}"/>')
    # A short bar cannot hold its own figure, so below that width it sits outside.
    inside = w > 150
    b.append(txt(L + LABEL + w - 16 if inside else L + LABEL + w + 14, y + BH - 14, 26,
                 "#ffffff" if inside else INK,
                 f"${r['per1k']:,.2f}", 700, "end" if inside else "start", MONO))
    b.append(txt(R, y + BH - 14, 19, SUB,
                 f"${r['tvl']/1e9:,.1f}B parked", 400, "end"))
    y += BH + 12

y += 18
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="82" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="82" fill="{BRAND}"/>')
hi, lo = rows[0], rows[-1]
eth = next(r for r in rows if r["chain"] == "Ethereum")
sol = next(r for r in rows if r["chain"] == "Solana")
b.append(txt(L + 26, y + 34, 22, INK,
             f"{hi['short']} earns {hi['per1k']/lo['per1k']:.0f}x what {lo['short']} does from "
             f"a parked dollar. Solana earns {sol['per1k']/eth['per1k']:.0f}x Ethereum.", 700))
b.append(txt(L + 26, y + 64, 20, SUB,
             "Neither is a verdict. A trading venue and a settlement layer are "
             "different jobs."))

y += 110
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "DeFiLlama. Fees are a 30-day total, TVL is as of today. "
             "Chains under $100M TVL left out, the ratio gets noisy."))
b.append(txt(R, y + 60, 19, SUB, "measured 2026-10-20  ·  @nickisanders", 400, "end"))
H = y + 92

render("capital_work", W, H, "".join(b))
