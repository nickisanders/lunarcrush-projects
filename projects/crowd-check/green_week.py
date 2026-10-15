#!/usr/bin/env python3
"""Who is behind the five names that are green in a red week.

Every figure measured 2026-10-15 and listed in out/green_week.json. The bar is
top-three creator concentration; the tick behind it is the median for that
token's own market-cap band, because concentration falls with size and ranking
across bands would charge the small ones for being small.

The band medians come from a 116-topic baseline with seven confirmed name
collisions removed (humanity, vision, just, kucoin, olympus, sonic-3, celestia),
each checked by pulling its posts and counting how many carry the token's own
ticker. All seven came back at or near zero.

Usage: python3 green_week.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = "/Users/nicki/lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
NEUTRAL, OK, BAD, BRAND = "#8d8578", "#236440", "#a33228", "#1b3a6b"

# symbol, 7d %, mcap $M, top-3 concentration, band median, accounts, platforms,
# share of accounts under 1,000 followers, posts in the sample
ROWS = [
    ("STRK", 29.1, 570, 0.200, 0.572, 114, 3, 0.05, 147),
    ("WAL",  50.3, 140, 0.267, 0.601,  68, 1, 0.07, 100),
    ("ZK",   37.4, 177, 0.444, 0.601,  83, 1, 0.34, 100),
    ("DUSK", 46.0,  69, 0.464, 0.601,  61, 1, 0.20, 100),
    ("CKB",  15.3,  74, 0.669, 0.601,  24, 1, 0.50,  44),
]
# Eight fits the width at this size; a tenth collided with the ninth.
TAPE = [("BTC", -1.2), ("ETH", -5.6), ("SOL", -7.5), ("XRP", -6.1),
        ("ADA", -9.2), ("DOGE", -8.9), ("ZEC", -6.9), ("LTC", -7.9)]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>{body}</svg>')
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('{name}.png',i.width+'x'+i.height));"], check=True)


W, H = 1200, 840
L, R = 60, 1140

b = [txt(L, 58, 36, INK, "Five green names in a red week, and who is behind them.", 700),
     txt(L, 92, 20, SUB,
         "Share of the conversation held by each token's three loudest accounts, "
         "against the median for its own size.")]

# The tape, so the "red week" claim is on the chart rather than asserted.
y = 130
b.append(txt(L, y, 19, SUB, "The week elsewhere"))
y += 32
step = (R - L) / len(TAPE)
for i, (sym, pc) in enumerate(TAPE):
    x = L + i * step
    b.append(txt(x, y, 19, INK, sym, 700, "start", MONO))
    b.append(txt(x + 58, y, 19, BAD, f"{pc:.1f}%", 400, "start", MONO))
b.append(f'<line x1="{L}" y1="{y+26}" x2="{R}" y2="{y+26}" stroke="{RULE}" stroke-width="2"/>')

# One row per token. The bar is concentration; the dashed tick is that band's
# median, so each token is read against its own peers and not against the others.
BX, BW, RH = L + 230, 480, 92
y = 230
for sym, pc7, mcap, conc, med, accts, nplat, sub1k, posts in ROWS:
    weak = conc > med
    col = BAD if weak else BRAND
    b.append(txt(L, y + 6, 30, INK, f"${sym}", 700, "start", MONO))
    b.append(txt(L, y + 32, 19, OK, f"+{pc7:.0f}%", 700, "start", MONO))
    b.append(txt(L + 92, y + 32, 18, SUB, f"${mcap}M", 400, "start", MONO))

    b.append(f'<rect x="{BX}" y="{y-14}" width="{BW}" height="34" fill="#f2efe8"/>')
    b.append(f'<rect x="{BX}" y="{y-14}" width="{BW*conc:.0f}" height="34" fill="{col}"/>')
    b.append(txt(BX + BW * conc - 12, y + 10, 20, "#ffffff", f"{conc*100:.1f}%", 700, "end", MONO))
    mx = BX + BW * med
    b.append(f'<line x1="{mx:.0f}" y1="{y-22}" x2="{mx:.0f}" y2="{y+28}" stroke="{INK}" '
             f'stroke-width="2" stroke-dasharray="4 3"/>')
    if sym == "STRK":
        b.append(txt(mx, y - 30, 17, INK, "its band's median", 400, "middle"))

    b.append(txt(BX + BW + 34, y + 6, 20, INK, f"{accts} accounts", 700))
    tail = f"{posts} posts" + (f", {nplat} platforms" if nplat > 1 else ", 1 platform")
    b.append(txt(BX + BW + 34, y + 32, 18, SUB, tail))
    b.append(txt(R, y + 6, 20, BAD if sub1k >= 0.3 else SUB,
                 f"{sub1k*100:.0f}%", 700, "end", MONO))
    b.append(txt(R, y + 32, 16, SUB, "under 1k followers", 400, "end"))
    y += RH

# The one that reads differently, named rather than left to the colour.
y += 4
b.append(f'<line x1="{L}" y1="{y-40}" x2="{R}" y2="{y-40}" stroke="{RULE}" stroke-width="2"/>')
b.append(f'<rect x="{L}" y="{y-20}" width="5" height="62" fill="{BAD}"/>')
b.append(txt(L + 26, y + 4, 23, INK,
             "$CKB is the one that reads differently. A 15% week carried by 24 accounts, "
             "half under 1,000 followers.", 700))
b.append(txt(L + 26, y + 32, 20, SUB,
             "Concentration is not manipulation and a small crowd can be an early one. "
             "This is a measurement, not a call."))
b.append(txt(R, y + 62, 17, SUB, "measured 2026-10-15  ·  @nickisanders", 400, "end"))

render("green_week", W, H, "".join(b))
json.dump({"measured": "2026-10-15",
           "note": "band medians from a 116-topic baseline, 7 name collisions removed",
           "tape": dict(TAPE),
           "rows": [dict(zip(("symbol", "pct7d", "mcap_musd", "top3_concentration",
                              "band_median", "accounts", "platforms", "share_under_1k",
                              "posts"), r)) for r in ROWS]},
          open(HERE / "out" / "green_week.json", "w"), indent=1)
