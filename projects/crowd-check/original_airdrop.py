#!/usr/bin/env python3
"""The biggest giveaway in the baseline, by the year its wallets arrived.

One bar per cohort, split out of the token with the most recipients in the
set rather than named in the source. The bar is everyone who first received
the token in that period and the solid part is the share of them still
holding any of it at all, which is the loosest retention test there is: a
balance above zero.

The giveaway week is cut out of its own year and placed first. It is found
by the busiest single day of arrivals and the days either side, so it comes
from the arrival data rather than from a date anyone looked up.

The ladder these cohorts make is partly elapsed time. A wallet that arrived
this year has not had the chance to leave that a wallet from the first year
has had, so the later bars are flattered and the chart says so rather than
reading the rise as behaviour. What the comparison does support is the
first bar against the rest: those wallets are the oldest in the set and the
year behind them is older still, and they are the ones who held least.

The figure usually quoted for this token is its whole-population retention,
which is computed across every bar at once and is mostly about wallets that
were not in the giveaway.

Reads out/arrival-years.json and out/retention-baseline.json.

Usage: python3 original_airdrop.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"

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


doc = json.loads((ROOT / "arrival-years.json").read_text())
base = json.loads((ROOT / "retention-baseline.json").read_text())["tokens"]

# Named by rule: the token the most addresses have ever received.
t = max(doc["per_token"], key=lambda r: r["recipients"])
if not t["spike"]:
    raise SystemExit(f"  ${t['sym']} has no giveaway week to cut out; the "
                     f"chart's first bar is that week")
whole = base[t["sym"].lower()]["raw"]
drop_year = t["peak_day"][:4]

spiked = [r for r in doc["per_token"] if r["spike"]]
rank = sorted(spiked, key=lambda r: r["giveaway"]["holding"])
place = [r["sym"] for r in rank].index(t["sym"]) + 1
med_give = statistics.median(r["giveaway"]["holding"] for r in spiked)

rows = [{"label": "the giveaway week",
         "sub": f"{t['peak_day']} and either side", **t["giveaway"]}]
for y, v in t["years"].items():
    rows.append({"label": f"arrived in {y}",
                 "sub": "the rest of that year" if y == drop_year else "",
                 **v})
widest = max(r["n"] for r in rows)

PX, PW = L + 232, 620
TOP, RH = 302, 56
C_N, C_PCT = PX + PW + 36, R

b = [txt(L, 58, 37, INK,
         f"The {t['recipients']:,} wallets that have held ${t['sym']},", 700),
     txt(L, 98, 37, INK, "by the year they turned up.", 700),
     txt(L, 138, 20, SUB,
         f"Each bar is everyone who first received ${t['sym']} in that "
         f"period. The solid part is the share of them still holding any "
         f"of it,"),
     txt(L, 164, 20, SUB,
         "which is the loosest retention test there is: a balance above "
         "zero, with no question of how much."),
     txt(L, 190, 20, SUB,
         f"The giveaway week is found from the arrival data, by the busiest "
         f"single day and the {doc['window']} days either side.")]

b.append(txt(PX, TOP - 30, 17, SUB, "wallets that arrived"))
b.append(txt(C_PCT, TOP - 30, 17, SUB, "still holding", 400, "end"))

for i, r in enumerate(rows):
    y = TOP + i * RH
    bw = PW * r["n"] / widest
    hot = bw * r["holding"]
    first = i == 0
    b.append(txt(L, y + 20, 19, INK if first else SUB, r["label"],
                 700 if first else 400))
    if r["sub"]:
        b.append(txt(L, y + 42, 16, SUB, r["sub"]))
    b.append(f'<rect x="{PX}" y="{y}" width="{bw:.1f}" height="26" '
             f'fill="{TRACK}"/>')
    b.append(f'<rect x="{PX}" y="{y}" width="{hot:.1f}" height="26" '
             f'fill="{HOT if first else BRAND}"/>')
    b.append(txt(C_N, y + 20, 18, SUB, f"{r['n']:,}", 400, "start", MONO))
    b.append(txt(C_PCT, y + 20, 19, INK if first else SUB,
                 f"{r['holding']*100:.1f}%", 700 if first else 400, "end"))

y = TOP + len(rows) * RH + 18
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"The wallets that were there for the giveaway are the ones "
             f"least likely to still hold it.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"{rows[0]['n']:,} of them, "
             f"{rows[0]['holding']*100:.1f}% still holding, against "
             f"{whole*100:.1f}% for the token as a whole."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"That whole-token figure is the one usually quoted, and "
             f"{(1 - t['event_share'])*100:.1f}% of what it counts arrived "
             f"after the giveaway was over."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"Across the {len(spiked)} tokens here with a findable "
             f"giveaway week, the median week still holds "
             f"{med_give*100:.1f}%. This one is {place}th from the bottom."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "The later bars are flattered by having had less time. A "
             "wallet that arrived this year has not had the chance to leave "
             "that the first"))
b.append(txt(L, y + 58, 19, SUB,
             "bar has had, so the rise across the years is partly elapsed "
             "time and is not read here as anyone changing their mind."))
b.append(txt(L, y + 84, 19, SUB,
             "What the bars do carry is the first against the rest: those "
             "wallets are the oldest in the token and they held the least "
             "of it."))
b.append(txt(L, y + 110, 19, SUB,
             "Arrivals after the giveaway are buyers, late claimers and "
             "wallets someone else sent the token to, and the quoted figure "
             "counts them all."))
b.append(txt(L, y + 136, 19, SUB,
             f"Nothing here is priced. Every Transfer event since the "
             f"contract's first block, netted into who holds what on "
             f"{doc['measured']}."))
b.append(txt(R, y + 164, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 196
render("original_airdrop", W, H, "".join(b))
print(f"  ${t['sym']}: {t['recipients']:,} recipients, giveaway week "
      f"{rows[0]['n']:,} at {rows[0]['holding']*100:.1f}%, whole token "
      f"{whole*100:.1f}%")
