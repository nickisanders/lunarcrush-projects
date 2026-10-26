#!/usr/bin/env python3
"""How much of a holder count could actually act on it.

Two panels because the finding needs both halves. The top one is the single
token: 62,835 holders, and the share of them that hold no ETH and have never
sent a transaction, which is to say cannot sell, cannot vote, cannot move.

The bottom one is every token measured, and it is there to stop the top one
being read as a general truth about crypto. The median token is 5.2% immobile
and three quarters sit under 15%, so a dead address is an ordinary small
fraction of any distribution. One token is not in that distribution at all,
and the strip makes the gap visible rather than asserted.

Tokens are unlabelled on purpose. The measurement supports the proportion; it
does not support saying why, and a named dot invites a conclusion the data
cannot carry.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 mobile_holders.py
"""

import json
import statistics as st
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
MIN_HOLDERS = 100          # below this the interval is too wide to place a dot


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
    if "immobile_share" not in m or m["of_holders"] < MIN_HOLDERS:
        continue
    rows.append({"sym": name.upper(), "share": m["immobile_share"],
                 "holders": m["of_holders"], "act": m["mobile_holders_est"],
                 "ci": m["immobile_ci"], "n": m["sampled"]})
if not rows:
    raise SystemExit("  no token carries a mobility figure yet")
rows.sort(key=lambda r: -r["share"])
worst = rows[0]
med = st.median(r["share"] for r in rows)

W = 1240
L, R = 60, 1180

b = [txt(L, 58, 37, INK, "A holder count cannot tell you", 700),
     txt(L, 98, 37, INK, "whether the holder exists.", 700),
     txt(L, 138, 20, SUB,
         "An address with no ETH that has never sent a transaction cannot sell, "
         "cannot vote, and cannot leave.")]

# Top panel: the one token, at the scale of its own holder count.
y = 200
BW, BH = R - L - 250, 62
b.append(txt(L, y - 14, 21, INK, "One token, by what its holders can do", 700))
y += 16
for label, val, col in (("reported holders", worst["holders"], BRAND),
                        ("could actually act", worst["act"], HOT)):
    w = max(BW * val / worst["holders"], 4)
    b.append(txt(L, y + BH - 22, 19, SUB, label))
    b.append(f'<rect x="{L+250}" y="{y}" width="{BW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{L+250}" y="{y}" width="{w:.0f}" height="{BH}" fill="{col}"/>')
    inside = w > 190
    b.append(txt(L + 250 + w - (16 if inside else -14), y + BH - 20, 30,
                 "#ffffff" if inside else INK, f"{val:,}", 700,
                 "end" if inside else "start", MONO))
    y += BH + 14

y += 26
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="84" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="84" fill="{HOT}"/>')
b.append(txt(L + 26, y + 34, 22, INK,
             f"{worst['share']*100:.1f}% of its holders hold no ETH and have never "
             f"sent a transaction.", 700))
b.append(txt(L + 26, y + 64, 20, SUB,
             f"Sampled at {worst['n']}, so the true share is between "
             f"{worst['ci'][0]*100:.1f}% and {worst['ci'][1]*100:.1f}%."))
y += 128

# Bottom panel: the same measure for every token, so the top one is not read
# as a statement about crypto in general.
b.append(txt(L, y, 21, INK, f"The same measure, every token with "
             f"{MIN_HOLDERS}+ holders ({len(rows)} of them)", 700))
b.append(txt(L, y + 26, 19, SUB,
             f"Median {med*100:.1f}%. Dead addresses are a small, ordinary part "
             f"of any distribution. One token is not in that distribution."))
y += 72
AX_L, AX_R = L + 10, R - 30
b.append(f'<line x1="{AX_L}" y1="{y+34}" x2="{AX_R}" y2="{y+34}" '
         f'stroke="{RULE}" stroke-width="2"/>')
for pct in (0, 25, 50, 75, 100):
    x = AX_L + (AX_R - AX_L) * pct / 100
    b.append(f'<line x1="{x:.0f}" y1="{y+28}" x2="{x:.0f}" y2="{y+40}" '
             f'stroke="{RULE}" stroke-width="2"/>')
    b.append(txt(x, y + 64, 18, SUB, f"{pct}%", 400, "middle", MONO))
for r in rows:
    x = AX_L + (AX_R - AX_L) * r["share"]
    top = r is worst
    b.append(f'<circle cx="{x:.1f}" cy="{y+34}" r="{9 if top else 7}" '
             f'fill="{HOT if top else BRAND}" fill-opacity="{1 if top else 0.45}"/>')
b.append(txt(AX_L + (AX_R - AX_L) * worst["share"], y + 10, 19, HOT,
             "this token", 700, "middle"))
y += 96

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Balances read for every holder. Mobility sampled per token, "
             "two calls per address, intervals on the sampled figure only."))
b.append(txt(L, y + 58, 19, SUB,
             "Tokens unlabelled: the measure supports the proportion, not a reason for it."))
b.append(txt(R, y + 58, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 88

render("mobile_holders", W, H, "".join(b))
