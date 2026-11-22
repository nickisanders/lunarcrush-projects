#!/usr/bin/env python3
"""How many wallets are holding a token they cannot move.

Immobility is usually reported as a share, and a share answers a question
about a token. This is the same measurement read as a population: how many
addresses hold no ETH, have never sent a transaction, and are sitting on a
balance they therefore cannot sell at any price.

The two orderings are not the same, which is the point of the right-hand
column. The worst rate in the set belongs to a token with a crowd small
enough that it barely registers as a bar, and the longest bar belongs to a
token whose rate is nowhere near the worst.

Mobility is sampled at 250 holders a token, so every count here is an
estimate and carries the interval that sample supports. The counts are of
current holders rather than of everyone the token ever paid.

Reads out/retention-baseline.json.

Usage: python3 stuck_wallets.py
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
SHOW = 14

W = 1240
L, R = 60, 1180


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Per-character widths read back off a render: Charter sets at about 0.415 of
# its point size and 0.53 bold. A line that will not fit says so at render
# time instead of being drawn clipped.
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
rows = []
for name, d in doc["tokens"].items():
    m = d.get("mobility") or {}
    if m.get("immobile_share") is None or not m.get("of_holders"):
        continue
    lo, hi = m["immobile_ci"]
    rows.append({"sym": name.upper(), "holders": m["of_holders"],
                 "share": m["immobile_share"], "sampled": m["sampled"],
                 "n": m["of_holders"] * m["immobile_share"],
                 "lo": m["of_holders"] * lo, "hi": m["of_holders"] * hi,
                 "arrived": d["arrived"]})
if len(rows) < 20:
    raise SystemExit(f"  only {len(rows)} tokens carry sampled mobility; the "
                     f"chart ranks a field")
total = sum(r["n"] for r in rows)
rows.sort(key=lambda r: -r["n"])
shown = rows[:SHOW]

# Named by rule: the largest stuck population and the worst rate, which are
# the two orderings the chart exists to separate.
most = rows[0]
worst = max(rows, key=lambda r: r["share"])
NAMED = {most["sym"], worst["sym"]}

PX, PW = L + 112, 690
TOP, RH = 322, 40
C_PCT = R
widest = max(r["hi"] for r in shown)

b = [txt(L, 58, 37, INK,
         f"{most['n']:,.0f} wallets are holding ${most['sym']}", 700),
     txt(L, 98, 37, INK, "and cannot sell it at any price.", 700),
     txt(L, 138, 20, SUB,
         "A wallet that holds no ETH and has never sent a transaction "
         "cannot pay gas, so it cannot move the token whatever the balance "
         "says."),
     txt(L, 164, 20, SUB,
         f"Bars are how many such wallets a token has, not what share of it "
         f"they are. The {SHOW} largest of "
         f"{len(rows)} tokens measured."),
     txt(L, 190, 20, SUB,
         f"Mobility is sampled at {shown[0]['sampled']} holders a token, so "
         f"every count is an estimate and carries that sample's interval.")]

b.append(txt(PX, TOP - 28, 17, SUB, "wallets that cannot move it"))
b.append(txt(C_PCT, TOP - 28, 17, SUB, "share of holders", 400, "end"))

for i, r in enumerate(shown):
    y = TOP + i * RH
    named = r["sym"] in NAMED
    col = HOT if named else BRAND
    bw = PW * r["n"] / widest
    b.append(txt(L, y + 20, 17, INK if named else SUB, "$" + r["sym"],
                 700 if named else 400, "start", MONO))
    b.append(f'<rect x="{PX}" y="{y + 4}" width="{bw:.1f}" height="22" '
             f'fill="{col}"/>')
    b.append(f'<line x1="{PX + PW * r["lo"] / widest:.1f}" y1="{y + 15}" '
             f'x2="{PX + PW * r["hi"] / widest:.1f}" y2="{y + 15}" '
             f'stroke="{INK}" stroke-width="2" opacity="0.45"/>')
    # Placed at the end of the bar, the count printed through the interval
    # whenever the interval was wider than the bar, which read as a
    # strikethrough on the longest row.
    b.append(txt(PX + PW * r["hi"] / widest + 14, y + 21, 17, SUB,
                 f"{r['n']:,.0f}", 400, "start", MONO))
    b.append(txt(C_PCT, y + 20, 17, INK if named else SUB,
                 f"{r['share']*100:.1f}%", 700 if named else 400, "end"))

y = TOP + len(shown) * RH + 30
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"The worst rate and the largest population are different "
             f"tokens, and not by a little.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"${worst['sym']} has the worst rate in the set at "
             f"{worst['share']*100:.1f}% of its holders, which is "
             f"{worst['n']:,.0f} wallets."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"${most['sym']} sits at {most['share']*100:.1f}% and that is "
             f"{most['n']:,.0f} wallets, "
             f"{most['n']/rows[1]['n']:.0f} times the next token here."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"Across all {len(rows)} tokens the estimate is "
             f"{total:,.0f} stuck wallets, and "
             f"{most['n']/total*100:.0f}% of them are holding one token."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Immobile is a floor rather than a census. A wallet holding a "
             "dollar of ETH against a gas price it will never pay counts as "
             "mobile here."))
b.append(txt(L, y + 58, 19, SUB,
             "The counts are of current holders, not of everyone a token "
             "ever paid, and the same address can be stuck on more than one "
             "token."))
b.append(txt(L, y + 84, 19, SUB,
             "A stuck wallet is not necessarily a person who wants out. It "
             "is a wallet with no way to act on the question either way."))
b.append(txt(L, y + 110, 19, SUB,
             "Ethereum only. Nothing here is priced, and a balance above "
             "zero is all it takes to be counted as a holder."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 170
render("stuck_wallets", W, H, "".join(b))
print(f"  {len(rows)} tokens, ${most['sym']} {most['n']:,.0f} stuck "
      f"({most['share']*100:.1f}%), worst rate ${worst['sym']} at "
      f"{worst['share']*100:.1f}%, field total {total:,.0f}")
