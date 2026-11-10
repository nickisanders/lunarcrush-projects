#!/usr/bin/env python3
"""Retention counts a balance. Far fewer people still hold what they got.

Every retention figure in this repo, and every one quoted anywhere else, is
the share of recipients whose balance is not zero. One token left out of a
10,000-token airdrop counts the same as the whole allocation, which makes the
number a measure of not having bothered as much as a measure of staying.

The inner bar is the price-free alternative. A wallet counts only if it
received at least the typical allocation and still holds 90% or more of it.
Both halves of that test are relative to what this token handed out, so
nothing here moves when the price does, which is the failure mode of every
dollar cut. A token that has fallen 90% shows more dust without a single
holder having behaved differently.

The gap is not a constant, and that is the part worth reading. It runs from
1.8x to 205x, so a retention figure cannot be discounted by some rule of
thumb to recover the real one.

Four of the widest gaps belong to wrapped staking and stable tokens, which
are labelled by hand below and sit at ranks 1, 2, 3 and 6. That is the honest
reading of their position rather than a flaw in them: a token whose purpose is
to be deposited somewhere is supposed to move, and untouched is the wrong
question to ask about it. The measure says who sat still, and sitting still
means different things to different tokens.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 full_allocation.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
# Below this a cohort is too small for the median-receipt test to mean much,
# and the chart would be comparing a census to a handful.
MIN_ARRIVED = 5000
# Hand-labelled, and said so on the chart. Nothing in the data marks a token
# as one that is meant to be deposited rather than held, so this is a judgment
# about what each one is for, kept visible instead of folded into the sort.
WRAPPED = {"FRXETH", "FRXUSD", "SFRXETH", "PUFETH"}
# Same address-keyed drop as the other charts in this project: a ticker is
# whatever a contract claims, and the label is what misleads.
AMBIGUOUS = {
    "0x8cdf7af57e4c8b930e1b23c477c22f076530585e": "symbol APT, not Aptos",
    "0x8d010bf9c26881788b4e6bf5fd1bdc358c8f90b8": "symbol DOT, not Polkadot",
    "0x00f3c42833c3170159af4e92dbb451fb3f708917": "symbol ICP, first seen 2025",
    "0x33e2c129ea670031659ac8852c01d0fe4b297954": "symbol SKY, not Sky's token",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Per-character widths read back off a render rather than guessed: Charter
# sets at about 0.415 of its point size and 0.53 bold. A line that will not
# fit says so at render time instead of being drawn clipped.
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


doc = json.loads(SRC.read_text())
rows, dropped = [], []
for name, d in doc["tokens"].items():
    k = (d.get("dust") or {}).get("kinds") or {}
    if "untouched_large" not in k or d["arrived"] < MIN_ARRIVED:
        continue
    if d["address"].lower() in AMBIGUOUS:
        dropped.append(name.upper())
        continue
    full = d["raw"] * k["untouched_large"]
    if full <= 0:
        # A zero would divide into an infinite factor and print as one.
        continue
    rows.append({"sym": name.upper(), "arr": d["arrived"], "ret": d["raw"],
                 "full": full, "factor": d["raw"] / full,
                 "recv": k.get("typical_receipt_tokens")})
if len(rows) < 10:
    raise SystemExit(f"  only {len(rows)} tokens carry the allocation split "
                     f"above {MIN_ARRIVED:,} recipients")
rows.sort(key=lambda r: -r["ret"])
med_ret = statistics.median(r["ret"] for r in rows)
med_full = statistics.median(r["full"] for r in rows)
by_gap = sorted(rows, key=lambda r: -r["factor"])
widest, tightest = by_gap[0], by_gap[-1]
wrapped_ranks = [i for i, r in enumerate(by_gap, 1) if r["sym"] in WRAPPED]
biggest = max(rows, key=lambda r: r["arr"])

W = 1240
L, R = 60, 1180
LABEL = 118
RIGHT = 196                     # the full-allocation and factor columns
BARW = R - L - LABEL - RIGHT
BH, GAP = 22, 4
X0 = L + LABEL
COL1 = R - 96                   # full-allocation share
COL2 = R                        # the factor between the two

b = [txt(L, 58, 37, INK,
         f"Of everyone handed one of these tokens, {med_ret*100:.0f}%", 700),
     txt(L, 98, 37, INK,
         f"still hold a balance and {med_full*100:.1f}% hold a full "
         f"allocation.", 700),
     txt(L, 138, 20, SUB,
         "Blue is the usual retention figure, the share of recipients whose "
         "balance is not zero. Red is the share who"),
     txt(L, 164, 20, SUB,
         "received at least the typical allocation and still hold 90% or more "
         "of it, which is price-free: both halves"),
     txt(L, 190, 20, SUB,
         f"are relative to what the token handed out. {len(rows)} tokens, "
         f"every one above {MIN_ARRIVED:,} recipients.")]

y = 240
bars_top = y
for r in rows:
    wb, wf = BARW * r["ret"], BARW * r["full"]
    b.append(txt(L, y + BH - 7, 17, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{wb:.1f}" height="{BH}" fill="{BRAND}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{max(wf,1.5):.1f}" height="{BH}" '
             f'fill="{HOT}"/>')
    label = f"{r['ret']*100:.1f}%"
    if wb > 76:
        b.append(txt(X0 + wb - 10, y + BH - 7, 17, "#ffffff", label, 700,
                     "end", MONO))
    else:
        b.append(txt(X0 + wb + 10, y + BH - 7, 17, SUB, label, 400,
                     "start", MONO))
    b.append(txt(COL1, y + BH - 8, 16, HOT, f"{r['full']*100:.1f}%", 400, "end"))
    # Rounded to whole numbers the column printed 1.8x and 2.2x as the same
    # "2x", which contradicted the callout naming one of them the tightest.
    gap = (f"{r['factor']:.1f}x" if r["factor"] < 10
           else f"{r['factor']:.0f}x")
    b.append(txt(COL2, y + BH - 8, 16, SUB, gap, 400, "end"))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(COL1, bars_top - 10, 15, HOT, "full", 400, "end"))
b.append(txt(COL2, bars_top - 10, 15, SUB, "gap", 400, "end"))

y = bars_bot + 50
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"The gap runs from {tightest['factor']:.1f}x on "
             f"${tightest['sym']} to {widest['factor']:.0f}x on "
             f"${widest['sym']}, so no rule of thumb recovers it.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"${biggest['sym']} handed tokens to {biggest['arr']:,} wallets. "
             f"{biggest['ret']*100:.1f}% hold a balance and "
             f"{biggest['full']*100:.1f}% hold a full allocation."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"{len(wrapped_ranks)} of the {max(wrapped_ranks)} widest gaps "
             f"are wrapped staking or stable tokens, built to be deposited "
             f"somewhere rather than held."))
b.append(txt(L + 26, y + 124, 20, SUB,
             "Untouched is the wrong question about a token whose job is to "
             "move, and this measure cannot tell the two apart."))
y += 184

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Typical allocation is the median of every incoming total, so a "
             "wallet handed less than most got cannot clear the test by "
             "holding it."))
b.append(txt(L, y + 58, 19, SUB,
             "Nothing here is priced. A dollar cut moves with the market and "
             "shows a fallen token more residue without one holder having "
             "changed."))
b.append(txt(L, y + 84, 19, SUB,
             "Which tokens are wrapped staking or stable is labeled by hand. "
             "Everything else here is computed."
             + (f" {', '.join('$' + d for d in dropped)} dropped for ticker "
                f"collisions." if dropped else "")))
b.append(txt(R, y + 112, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 140

render("full_allocation", W, H, "".join(b))
print(f"  {len(rows)} tokens, median {med_ret*100:.1f}% kept against "
      f"{med_full*100:.1f}% full, gap {tightest['factor']:.1f}x to "
      f"{widest['factor']:.0f}x")
