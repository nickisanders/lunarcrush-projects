#!/usr/bin/env python3
"""Who pays for blockspace on each chain, and how few of them there are.

Fees per dollar of TVL rewards a chain with heavy automated flow, which was a
fair objection to the previous chart. This is the answer: every block on eight
chains for 24 hours, the distinct addresses that sent a transaction, and the
share of transactions coming from the busiest 1% of them.

Two panels because neither number works alone. The wallet count alone misses
that an operator can run a thousand addresses. The concentration alone misses
that Hyperliquid's is spread across 19,821 wallets while Ethereum's is spread
across 511,663.

Sorted by concentration rather than by wallet count, because the finding is
that Ethereum sits alone at the bottom and everything else clusters.

Reads out/payers.json from proof-of-crowd-tools (payers.py).

Usage: python3 payer_spread.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/payers.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"


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


rows = json.loads(SRC.read_text())
rows.sort(key=lambda r: -r["top1pct_tx_share"])
for r in rows:
    r["short"] = r["chain"].replace(" L1", "")

W = 1240
L, R = 60, 1180
LABEL = 185
GAP = 46
COLW = (R - L - LABEL - GAP) / 2          # two panels side by side
BH = 46

# "A handful of addresses" was the first headline and it overstates: 1% of
# BSC's 2.2M senders is 22,000 wallets, which is not a handful. The share is
# the thing measured, so the share is what the headline claims.
b = [txt(L, 58, 37, INK, "On seven of eight chains, 1% of senders", 700),
     txt(L, 98, 37, INK, "carry two thirds of the transactions.", 700),
     txt(L, 136, 20, SUB,
         "Every block over 24 hours. Distinct senders, and the share of "
         "transactions from the busiest 1% of them.")]

y0 = 206
b.append(txt(L + LABEL, y0 - 14, 21, INK, "Transactions from the top 1%", 700))
b.append(txt(L + LABEL + COLW + GAP, y0 - 14, 21, INK, "Distinct senders in the day", 700))

maxsend = max(r["senders"] for r in rows)
y = y0 + 14
for r in rows:
    col = BRAND if r["chain"] == "Ethereum" else HOT
    b.append(txt(L, y + BH - 14, 23, INK, r["short"], 700, "start", MONO))

    # left: concentration, full track is 100%
    w = COLW * r["top1pct_tx_share"]
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{COLW:.0f}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{L+LABEL}" y="{y}" width="{w:.0f}" height="{BH}" fill="{col}"/>')
    b.append(txt(L + LABEL + w - 14, y + BH - 15, 24, "#ffffff",
                 f"{r['top1pct_tx_share']*100:.1f}%", 700, "end", MONO))

    # right: senders, full track is the largest
    x2 = L + LABEL + COLW + GAP
    w2 = max(COLW * r["senders"] / maxsend, 2)
    b.append(f'<rect x="{x2}" y="{y}" width="{COLW:.0f}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{x2}" y="{y}" width="{w2:.0f}" height="{BH}" fill="{col}"/>')
    inside = w2 > 160
    b.append(txt(x2 + w2 - 14 if inside else x2 + w2 + 12, y + BH - 15, 23,
                 "#ffffff" if inside else INK,
                 f"{r['senders']:,}", 700, "end" if inside else "start", MONO))
    y += BH + 12

eth = next(r for r in rows if r["chain"] == "Ethereum")
hyp = next(r for r in rows if r["chain"] == "Hyperliquid L1")
y += 22
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="86" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="86" fill="{BRAND}"/>')
b.append(txt(L + 26, y + 34, 22, INK,
             f"Ethereum is the only one where paying for blockspace is something "
             f"a broad set of people do.", 700))
b.append(txt(L + 26, y + 64, 20, SUB,
             f"Hyperliquid earns the most per wallet at ${hyp['fee_per_sender']:,.0f}, "
             f"from {hyp['senders']:,} of them. Ethereum has "
             f"{eth['senders']/hyp['senders']:.0f}x as many."))

y += 114
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Distinct senders is not quite distinct payers: a relayer pays gas for "
             "many users, which compresses the count where they are used."))
b.append(txt(L, y + 58, 19, SUB,
             "Every block in the window, not a sample. Distinct addresses do not "
             "extrapolate."))
b.append(txt(R, y + 58, 19, SUB, "measured 2026-10-20  ·  @nickisanders", 400, "end"))
H = y + 88

render("payer_spread", W, H, "".join(b))
