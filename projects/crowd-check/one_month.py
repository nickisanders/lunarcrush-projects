#!/usr/bin/env python3
"""Ten tokens that are one airdrop each, keeping between 1.5% and 81.5%.

For each of these the single biggest month of arrivals brought more than half
of everyone who ever held the token, and that month was at least 5,000
wallets. Whatever else happened to them, their holder history is one giveaway
and a long decay, which makes them as close to the same event as this data
gets. The share of that month's wallets still holding runs from 1.5% to
81.5%, a factor of fifty-four.

Nothing measured here explains the spread. Cohort size does not, age does not,
how concentrated arrival was does not, and neither does what the survivors
hold: against the median dollar position the correlation is -0.21 across ten
tokens, which at that count is not a number to lean on and is drawn as a
column to read rather than as a claim.

The second panel is the reason the top of the chart is not a success story.
$DRV kept four wallets in five and the median one holds 83 cents, with 95.7%
of its holders never having sold anything and only 1.2% unable to. Nobody is
trapped and nothing was done to anyone. The position is simply too small to
be worth an action, and a retention figure cannot tell that apart from
conviction.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 one_month.py
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
MIN_SHARE, MIN_COHORT = 0.5, 5000
LEAD = "drv"


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
for sym, v in doc["tokens"].items():
    bc = v.get("biggest_cohort") or {}
    if not bc or not v["arrived"]:
        continue
    share = bc["arrived"] / v["arrived"]
    if share < MIN_SHARE or bc["arrived"] < MIN_COHORT:
        continue
    k = v["dust"].get("kinds") or {}
    rows.append({"sym": sym.upper(), "key": sym, "month": bc["month"],
                 "cohort": bc["arrived"], "share": share, "ret": bc["retention"],
                 "kept": round(bc["arrived"] * bc["retention"]),
                 "med": v["dust"].get("median_usd"),
                 "never": (k.get("untouched_small", 0) + k.get("untouched_large", 0)
                           if "untouched_small" in k else None),
                 "imm": (v.get("mobility") or {}).get("immobile_share")})
rows.sort(key=lambda r: -r["ret"])

W = 1240
L, R = 60, 1180
LABEL, TAIL = 200, 186
BARW = R - L - LABEL - TAIL
X0 = L + LABEL
BH, GAP = 44, 28
top = max(r["ret"] for r in rows)

b = [txt(L, 58, 37, INK, "Ten tokens that are really one airdrop each.", 700),
     txt(L, 98, 37, INK, "They kept between 1.5% and 81.5% of it.", 700),
     txt(L, 140, 20, SUB,
         "For each of these, one month brought more than half of everyone who "
         "ever held the token, and that month was at least 5,000"),
     txt(L, 166, 20, SUB,
         "wallets. The bar is how much of that one cohort is still holding. "
         "The right column is what the survivors actually have.")]

y = 226
b.append(txt(X0, y - 12, 17, SUB, "share of that month's wallets still holding",
             400, "start", MONO))
b.append(txt(R, y - 12, 17, SUB, "median position", 400, "end", MONO))
for r in rows:
    lead = r["key"] == LEAD
    col = HOT if lead else BRAND
    w = BARW * r["ret"] / top
    b.append(txt(L, y + 20, 19, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(txt(L, y + 40, 15, SUB,
                 f"{r['month']}  {r['cohort']:,}", 400, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{w:.1f}" height="{BH}" fill="{col}"/>')
    # Under about a tenth of the track the bar is narrower than its own label,
    # so the figure moves outside rather than being squeezed or clipped.
    if w > 86:
        b.append(txt(X0 + w - 12, y + BH / 2 + 7, 19, "#ffffff",
                     f"{r['ret']*100:.1f}%", 700, "end", MONO))
    else:
        b.append(txt(X0 + w + 12, y + BH / 2 + 7, 19, INK,
                     f"{r['ret']*100:.1f}%", 700, "start", MONO))
    b.append(txt(R, y + BH / 2 + 7, 19, INK if lead else SUB,
                 f"${r['med']:,.2f}", 700 if lead else 400, "end", MONO))
    y += BH + GAP

y += 6
lead = next(r for r in rows if r["key"] == LEAD)
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="170" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="170" fill="{HOT}"/>')
b.append(txt(L + 26, y + 40, 23, INK,
             f"${lead['sym']} is the best number on this chart and it is not a "
             f"success story.", 700))
b.append(txt(L + 26, y + 72, 23, INK,
             f"{lead['never']*100:.0f}% of its holders have never sold "
             f"anything, and the median one holds ${lead['med']:.2f}.", 700))
b.append(txt(L + 26, y + 104, 20, SUB,
             f"Only {lead['imm']*100:.1f}% of them cannot transact, so almost "
             f"all of them could have left. A position that size is not worth "
             f"an action,"))
b.append(txt(L + 26, y + 130, 20, SUB,
             "and a retention figure cannot tell that apart from conviction."))
b.append(txt(L + 26, y + 156, 20, SUB,
             "Nobody is trapped here and nothing was done to anyone."))
y += 210

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Every transfer since each contract's first block, joined to who "
             "holds today. The cohort is the calendar month that brought the "
             "most wallets."))
b.append(txt(L, y + 58, 19, SUB,
             "Cohort size, age, concentration of arrival and the median "
             "position were each tested against the spread and none of them "
             "accounts for it."))
# The dollar column invites a comparison down it, and the thing being
# compared is partly how far each token has fallen.
b.append(txt(L, y + 84, 19, SUB,
             "Median position is in dollars and moves with the price, so a "
             "token that has fallen further shows a smaller one."))
b.append(txt(R, y + 110, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 138

render("one_month", W, H, "".join(b))
for r in rows:
    print(f"  {r['sym']:<7}{r['month']}  {r['cohort']:>7,} ({r['share']*100:>3.0f}%)  "
          f"kept {r['ret']*100:>5.1f}%  median ${r['med']:.2f}")
