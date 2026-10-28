#!/usr/bin/env python3
"""One token's holders cannot sell, and the contract is not what stops them.

Every bar is the share of a token's holders that hold no ETH and have never
sent a transaction. Such an address cannot pay gas, so it cannot sell, vote or
leave, whatever its balance says. Across 29 tokens the median is about 5% of
holders, which is roughly what forgotten wallets look like. $PIEVERSE reads
96.4%, and the gap to the next token is more than fifty points, so this is not
the tail of a distribution.

The obvious objection is that the token must be locked, and it is not. Its
contract does carry a transfer gate, and that gate opened in November 2025. A
simulated transfer from 40 of these holders cleared 40 times, none of those
addresses was whitelisted, and 193 of 194 measured transactions moved in a
single leg, so nothing is taking a fee either. The token would let these
holders sell. They cannot afford the gas to try.

Two things the chart has to carry honestly. Immobility is sampled at 250
addresses per token, so each bar has a confidence interval and the pale
extension past each bar is it. Tokens under 100 holders are dropped, because a
five-holder census produces a share with an interval wide enough to span most
of the axis and it would read as a measurement.

What it cannot show is intent. A token whose holders happen to be unable to
move it and a token where that was arranged look identical from here.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 mobility_spread.py
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
# The interval has to read as the same measurement as its bar, so each band is
# its bar's color lightened rather than a neutral gray.
BAND, BAND_HOT = "#c5d0e0", "#e6c5bf"
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
    m = d.get("mobility") or {}
    if m.get("immobile_share") is None:
        continue
    if m["of_holders"] < MIN_HOLDERS:
        continue
    lo, hi = m.get("immobile_ci") or [m["immobile_share"]] * 2
    rows.append({"sym": name.upper(), "share": m["immobile_share"],
                 "lo": lo, "hi": hi, "holders": m["of_holders"],
                 "mobile": m.get("mobile_holders_est")})
if len(rows) < 5:
    raise SystemExit(f"  only {len(rows)} tokens carry mobility above "
                     f"{MIN_HOLDERS} holders")
rows.sort(key=lambda r: -r["share"])
med = statistics.median(r["share"] for r in rows)
top, second = rows[0], rows[1]
gap = top["share"] - second["share"]

W = 1240
L, R = 60, 1180
LABEL = 112
RIGHT = 168                     # the holders column
BARW = R - L - LABEL - RIGHT
BH, GAP = 26, 6
X0 = L + LABEL

b = [txt(L, 58, 37, INK, "One token's holders cannot sell.", 700),
     txt(L, 98, 37, INK, "The contract is not what stops them.", 700),
     txt(L, 138, 20, SUB,
         "Share of holders that hold no ETH and have never sent a transaction, "
         "so they cannot pay gas to move anything."),
     txt(L, 164, 20, SUB,
         f"{len(rows)} tokens, every one above {MIN_HOLDERS} holders. "
         f"Sampled 250 addresses each, pale band is the interval.")]

y = 214
bars_top = y
for r in rows:
    hot = r is top
    w_est = BARW * r["share"]
    w_lo, w_hi = BARW * r["lo"], BARW * r["hi"]
    b.append(txt(L, y + BH - 7, 17, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    # Interval first, so the solid estimate sits on top of it and what stays
    # visible is the uncertainty above the estimate.
    b.append(f'<rect x="{X0+w_lo:.1f}" y="{y}" width="{max(0,w_hi-w_lo):.1f}" '
             f'height="{BH}" fill="{BAND_HOT if hot else BAND}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{w_est:.1f}" height="{BH}" '
             f'fill="{HOT if hot else BRAND}"/>')
    label = f"{r['share']*100:.1f}%"
    if w_est > 78:
        b.append(txt(X0 + w_est - 10, y + BH - 7, 17, "#ffffff", label,
                     700, "end", MONO))
    else:
        # A near-zero bar puts its label right where the median rule is, so
        # the two were overprinting: $STRCX read as "0|4%".
        lx = max(X0 + w_hi + 9, X0 + BARW * med + 13)
        b.append(txt(lx, y + BH - 7, 17, SUB, label, 400, "start", MONO))
    b.append(txt(R, y + BH - 8, 16, SUB, f"{r['holders']:,}", 400, "end"))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(R, bars_top - 10, 15, SUB, "holders", 400, "end"))

# The median is the whole reason the outlier reads as one, so it gets a line
# rather than a sentence.
mx = X0 + BARW * med
b.append(f'<line x1="{mx:.1f}" y1="{bars_top-6}" x2="{mx:.1f}" y2="{bars_bot+6}" '
         f'stroke="{INK}" stroke-width="2" stroke-dasharray="3 4" opacity="0.55"/>')
b.append(txt(mx + 9, bars_bot + 26, 18, INK,
             f"median {med*100:.1f}%", 700))

y = bars_bot + 52
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="112" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="112" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${top['sym']} sits {gap*100:.0f} points clear of the next token, "
             f"against a {med*100:.1f}% median.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Transfers are allowed: 40 of 40 sampled ${top['sym']} holders could "
             f"move their whole balance, none of them whitelisted."))
b.append(txt(L + 26, y + 94, 20, SUB,
             "No fee on transfer either, with 193 of 194 measured transactions "
             "moving in a single leg."))
y += 152

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Immobility is sampled at 250 addresses per token, so every bar "
             "carries an interval."))
b.append(txt(L, y + 58, 19, SUB,
             f"Tokens under {MIN_HOLDERS} holders are dropped rather than shown "
             f"with an interval spanning the axis."))
b.append(txt(L, y + 84, 19, SUB,
             f"Of ${top['sym']}'s {top['holders']:,} holders, about "
             f"{top['mobile']:,} could act. The mechanism is measurable; intent "
             f"is not."))
b.append(txt(R, y + 110, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 138

render("mobility_spread", W, H, "".join(b))
print(f"  {len(rows)} tokens, median {med*100:.1f}%, "
      f"top ${top['sym']} {top['share']*100:.1f}%")
