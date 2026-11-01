#!/usr/bin/env python3
"""Eighteen tokens can freeze transfers. One of them did.

Each row is a token's life, from the first Transfer it ever emitted to today,
for every token in the set whose contract carries a control that halts
something. Red is a stretch when the pause was actually on.

The capability is ordinary and sits in public in the ABI. Whether anyone ever
pulled it is a different question, and the only way to answer it is to read
the pause flag as it stood at old blocks, which an archive node will serve.
Sixty points were read across each token's life.

Two things the chart has to carry. A clean track means the token was not
paused at any point sampled, which is weaker than never paused, since sixty
points across a year cannot see a pause lasting days. And a pause is not by
itself evidence of anything wrong: contracts are paused for migrations, bugs
and live incidents, and pausing quickly during one is a team doing its job.

Reads out/pause-history.json from proof-of-crowd-tools.

Usage: python3 pause_timeline.py
"""

import datetime as dt
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "pause-history.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"


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


def day(s):
    return dt.date.fromisoformat(s)


doc = json.loads(SRC.read_text())
today = day(doc["measured"])
rows = []
for sym, r in doc["tokens"].items():
    if not r.get("first_seen"):
        continue
    rows.append({"sym": sym.upper(), "start": day(r["first_seen"]),
                 "holders": r.get("holders") or 0,
                 "begin": day(r["pause_begin"]) if r.get("pause_begin") else None,
                 "end": day(r["pause_end"]) if r.get("pause_end") else None,
                 "inside": r.get("transfers_inside"),
                 "now": r.get("transfers_now"),
                 "checked": r.get("checked"), "samples": r.get("samples")})
if not rows:
    raise SystemExit("  no tokens in the pause history")
rows.sort(key=lambda r: r["start"])
paused = [r for r in rows if r["begin"]]
first = min(r["start"] for r in rows)
span = (today - first).days or 1

W = 1240
L, R = 60, 1180
LABEL = 108
RIGHT = 128
BARW = R - L - LABEL - RIGHT
BH, GAP = 26, 8
X0 = L + LABEL


def xof(d):
    return X0 + BARW * ((d - first).days / span)


b = [txt(L, 58, 37, INK, "Eighteen tokens can freeze your transfers.", 700),
     txt(L, 98, 37, INK, "One of them did it.", 700),
     txt(L, 138, 20, SUB,
         "Each line is a token's life, from its first transfer to today. Red "
         "is a stretch when the pause was switched on."),
     txt(L, 164, 20, SUB,
         f"Read from the pause flag as it stood at {rows[0]['samples']} blocks "
         f"across each token's history, on an archive node.")]

y = 214
bars_top = y
for r in rows:
    x1, x2 = xof(r["start"]), xof(today)
    hot = r["begin"] is not None
    b.append(txt(L, y + BH - 7, 17, INK if hot else SUB, "$" + r["sym"],
                 700, "start", MONO))
    b.append(f'<rect x="{x1:.1f}" y="{y+BH/2-5:.0f}" width="{x2-x1:.1f}" '
             f'height="10" rx="2" fill="{TRACK if not hot else "#e7dfd2"}"/>')
    if hot:
        px1, px2 = xof(r["begin"]), xof(r["end"])
        b.append(f'<rect x="{px1:.1f}" y="{y:.0f}" '
                 f'width="{max(px2-px1,3):.1f}" height="{BH}" rx="2" fill="{HOT}"/>')
        days = (r["end"] - r["begin"]).days
        lab = f"{days} days frozen"
        if px2 + 12 + len(lab) * 9 < X0 + BARW:
            b.append(txt(px2 + 12, y + BH - 7, 17, HOT, lab, 700, "start"))
        else:
            b.append(txt(px1 - 12, y + BH - 7, 17, HOT, lab, 700, "end"))
    b.append(txt(R, y + BH - 8, 16, SUB, f"{r['holders']:,}", 400, "end", MONO))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(R, bars_top - 10, 15, SUB, "holders", 400, "end"))

# A year scale, so the red band can be placed in time rather than in sequence.
y_ax = bars_bot + 14
b.append(f'<line x1="{X0}" y1="{y_ax}" x2="{X0+BARW}" y2="{y_ax}" '
         f'stroke="{RULE}" stroke-width="2"/>')
yr = dt.date(first.year + 1, 1, 1)
while yr <= today:
    x = xof(yr)
    b.append(f'<line x1="{x:.1f}" y1="{y_ax-5}" x2="{x:.1f}" y2="{y_ax+5}" '
             f'stroke="{RULE}" stroke-width="2"/>')
    b.append(txt(x, y_ax + 26, 18, SUB, str(yr.year), 400, "middle"))
    yr = dt.date(yr.year + 1, 1, 1)

y = y_ax + 54
if paused:
    p = paused[0]
    ins, now = p["inside"] or {}, p["now"] or {}
    b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="112" fill="#fbf7ef"/>')
    b.append(f'<rect x="{L}" y="{y}" width="5" height="112" fill="{HOT}"/>')
    b.append(txt(L + 26, y + 36, 23, INK,
                 f"${p['sym']} was frozen for {(p['end']-p['begin']).days} days, "
                 f"{p['begin']:%B %-d %Y} to {p['end']:%B %-d %Y}.", 700))
    b.append(txt(L + 26, y + 68, 20, SUB,
                 f"A pause can gate minting and leave holders alone, so its "
                 f"holders were simulated sending a unit inside the window: "
                 f"{ins.get('reverted',0)} of "
                 f"{ins.get('reverted',0)+ins.get('cleared',0)} reverted."))
    b.append(txt(L + 26, y + 94, 20, SUB,
                 f"The same wallets today: {now.get('cleared',0)} of "
                 f"{now.get('cleared',0)+now.get('reverted',0)} clear. The "
                 f"contract was what stopped them, and it has let go."))
    y += 152

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"A clean line means the token was not paused at any of the "
             f"{rows[0]['samples']} points sampled, which is weaker than never "
             f"paused."))
b.append(txt(L, y + 58, 19, SUB,
             "A pause lasting a few days would fall between the samples and "
             "not be seen, so one is a floor rather than a count."))
b.append(txt(L, y + 84, 19, SUB,
             "Contracts are paused for migrations, bugs and live incidents, "
             "and pausing fast during one is a team doing its job."))
b.append(txt(L, y + 110, 19, SUB,
             "This says a pause happened and what it stopped, not why it was "
             "switched on."))
b.append(txt(R, y + 136, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 164

render("pause_timeline", W, H, "".join(b))
print(f"  {len(rows)} tokens, {len(paused)} paused: "
      f"{[r['sym'] for r in paused]}")
