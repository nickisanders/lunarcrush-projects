#!/usr/bin/env python3
"""Three tokens with the same holder count and three different meanings.

$PUFETH, $PIEVERSE and $DRV all report between 44,000 and 63,000 holders. In
one, four fifths of those wallets already sold out and left a tail. In another,
almost every wallet has never sent a transaction and holds no ETH, so leaving
was never an option it had. In the third the holders could go whenever they
liked and mostly stayed.

Each bar is one token's current holders, its width set by how many there are so
the three are comparable, split by what the wallet actually did. The red end is
wallets that are finished. The pale blue is wallets that are still in and could
not act. Only the solid blue is somebody holding by choice.

Two measurements feed this and they are not the same kind. The split by what a
wallet did is computed over every holder, from its balance against what a
typical recipient of that token received. The share that cannot move is a
250-wallet sample, so it carries an interval and $PIEVERSE's band is drawn
rather than its point estimate being stated as fact.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 holder_meanings.py
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
PICKED = ("pufeth", "pieverse", "drv")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None, op=1.0):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="{op}" '
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
for sym in PICKED:
    d = doc["tokens"][sym]
    k = d["dust"]["kinds"]
    mo = d.get("mobility") or {}
    n = k["classified"]
    gone, part = k["exited_leaving_dust"], k["part_sold"]
    still = k["untouched_small"] + k["untouched_large"]
    imm = mo.get("immobile_share") or 0.0
    lo, hi = mo.get("immobile_ci") or (imm, imm)
    # The sampled share is of all holders and has to sit inside the segment of
    # wallets that never moved, or the bar would claim a wallet both left and
    # could not leave. It fits for all three, but clamp rather than trust it.
    imm = min(imm, still)
    rows.append({"sym": sym.upper(), "n": n, "gone": gone, "part": part,
                 "stuck": imm, "free": max(still - imm, 0.0),
                 "lo": min(lo, still), "hi": min(hi, still),
                 "med_usd": d["dust"].get("median_usd"),
                 "sampled": mo.get("sampled"), "ret": d["raw"]})

W = 1240
L, R = 60, 1180
LABEL, TAIL = 152, 150
BARW = R - L - LABEL - TAIL
X0 = L + LABEL
BH, GAP = 62, 46
nmax = max(r["n"] for r in rows)

b = [txt(L, 58, 37, INK, "Three tokens, the same number of holders,", 700),
     txt(L, 98, 37, INK, "and three different meanings of the word.", 700),
     txt(L, 138, 20, SUB,
         "Each bar is one token's current holders, its width set by how many "
         "there are, split by what the wallet actually did."),
     txt(L, 164, 20, SUB,
         "Only the solid blue is somebody who could have left and stayed "
         "anyway.")]

y = 226
for r in rows:
    w = BARW * r["n"] / nmax
    b.append(txt(L, y + 22, 19, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(txt(L, y + 46, 16, SUB, f"{r['ret']*100:.0f}% retention", 400,
                 "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{w:.1f}" height="{BH}" fill="{TRACK}"/>')
    x = X0
    for frac, col, op in ((r["gone"], HOT, 1.0), (r["part"], HOT, 0.45),
                          (r["stuck"], BRAND, 0.3), (r["free"], BRAND, 1.0)):
        seg = w * frac
        if seg <= 0.4:
            continue
        b.append(f'<rect x="{x:.1f}" y="{y}" width="{seg:.1f}" height="{BH}" '
                 f'fill="{col}" fill-opacity="{op}"/>')
        if seg > 54:
            mid = x + seg / 2
            pale = col == BRAND and op < 1
            b.append(txt(mid, y + BH / 2 + 7, 19, INK if pale else "#ffffff",
                         f"{frac*100:.0f}%", 700, "middle", MONO))
        x += seg
    # The stuck share is sampled, so draw where the interval actually sits
    # instead of letting a single edge read as a measured boundary. Below a
    # few percent the band is narrower than the bracket drawn around it and
    # only adds clutter, so those are left to the footnote.
    if r["hi"] > 0.05:
        a0 = X0 + w * (r["gone"] + r["part"] + r["lo"])
        a1 = X0 + w * (r["gone"] + r["part"] + r["hi"])
        b.append(f'<line x1="{a0:.1f}" y1="{y+BH+7}" x2="{a1:.1f}" '
                 f'y2="{y+BH+7}" stroke="{BRAND}" stroke-width="3"/>')
        for e in (a0, a1):
            b.append(f'<line x1="{e:.1f}" y1="{y+BH+2}" x2="{e:.1f}" '
                     f'y2="{y+BH+12}" stroke="{BRAND}" stroke-width="3"/>')
        note = f"sampled, {r['lo']*100:.0f} to {r['hi']*100:.0f}%"
        # Anchor so the note runs back along the bar rather than off the page.
        if a1 + 10 + len(note) * 8.2 < R:
            b.append(txt(a1 + 10, y + BH + 13, 16, SUB, note))
        else:
            b.append(txt(a1 - 6, y + BH + 13, 16, SUB, note, 400, "end"))
    b.append(txt(X0 + w + 14, y + BH / 2 + 7, 18, INK,
                 f"{r['n']:,}", 700, "start", MONO))
    y += BH + GAP

y += 2
sw = (R - L) / 4
for i, (col, op, label) in enumerate((
        (HOT, 1.0, "sold out, left a tail"),
        (HOT, 0.45, "sold part of it"),
        (BRAND, 0.3, "still in, cannot move"),
        (BRAND, 1.0, "still in by choice"))):
    x = L + i * sw
    b.append(f'<rect x="{x}" y="{y-13}" width="15" height="15" fill="{col}" '
             f'fill-opacity="{op}"/>')
    b.append(txt(x + 23, y, 18, SUB, label))

y += 40
pie = next(r for r in rows if r["sym"] == "PIEVERSE")
puf = next(r for r in rows if r["sym"] == "PUFETH")
# Rounded, because "around 8,899" reads as a precision the share it came
# from does not have.
real = round((puf["stuck"] + puf["free"] + puf["part"]) * puf["n"], -2)
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="140" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="140" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${pie['sym']}'s stranded wallets are not holding dust. The "
             f"typical one holds about ${pie['med_usd']:.0f}.", 700))
b.append(txt(L + 26, y + 66, 23, INK,
             f"It reads on a dashboard as {pie['ret']*100:.0f}% retention and "
             f"a committed community.", 700))
b.append(txt(L + 26, y + 98, 20, SUB,
             f"${puf['sym']} reads as {puf['n']:,} holders. Around {real:,.0f} of "
             f"those wallets still hold anything close to a real position."))
b.append(txt(L + 26, y + 124, 20, SUB,
             "A holder count asks whether an address has a balance. It never "
             "asks whether anyone chose to have it."))
y += 180

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "What a wallet did is computed over every holder, from its "
             "balance against what a typical recipient of that token received."))
b.append(txt(L, y + 58, 19, SUB,
             f"Cannot move means the wallet has never sent a transaction and "
             f"holds no ETH, from a {pie['sampled']}-wallet sample per token."))
b.append(txt(R, y + 84, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 112

render("holder_meanings", W, H, "".join(b))
for r in rows:
    print(f"  {r['sym']:<9}{r['n']:>7,}  gone {r['gone']*100:>3.0f}%  "
          f"part {r['part']*100:>3.0f}%  stuck {r['stuck']*100:>3.0f}%  "
          f"free {r['free']*100:>3.0f}%")
