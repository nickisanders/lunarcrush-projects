#!/usr/bin/env python3
"""A 354% week with a hundred-post conversation.

Reads out/agt-anatomy.json, measured from the verified topic
`alaya-governance-token`, which runs 94% on its own ticker. The bare `agt`
topic returns 387 posts at 20%, and the coins list reports 969 for the same
day: the headline social figure is roughly ten times the real conversation,
which is why the post count here comes from the verified topic and no chart
on this page uses social_volume_24h for anything.

Usage: python3 silent_mover.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/agt-anatomy.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
NEUTRAL, BRAND, HOT, OK = "#8d8578", "#1b3a6b", "#a33228", "#236440"


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


d = json.loads(SRC.read_text())
W, H = 1200, 880
L, R = 60, 1140

b = [txt(L, 58, 36, INK, "$AGT is up 354% this week.", 700),
     txt(L, 96, 36, INK, "A hundred posts have been written about it.", 700),
     txt(L, 132, 20, SUB,
         f"Every post on the verified topic, which runs 94% on its own ticker. "
         f"Market cap ${d['mcap']/1e6:.0f}M.")]

# The two numbers that do not belong beside each other.
y = 190
for i, (big, small) in enumerate(
        [(f"${d['volume24h']/1e6:.0f}M", "traded in 24 hours,\n68% of its market cap"),
         (f"{d['posts']}", "posts in the\nentire conversation"),
         (f"{d['accounts']}", "accounts wrote them,\nall of them on X")]):
    x = L + i * ((R - L) / 3)
    b.append(txt(x, y + 20, 56, INK if i else BRAND, big, 700, "start", MONO))
    for j, ln in enumerate(small.split("\n")):
        b.append(txt(x, y + 58 + j * 27, 20, SUB, ln))
b.append(f'<line x1="{L}" y1="{y+128}" x2="{R}" y2="{y+128}" stroke="{RULE}" stroke-width="2"/>')

# Who holds the attention. Two bars: share of posts, share of interactions.
y = 390
b.append(txt(L, y, 24, INK, "Of those hundred posts, eighteen are automated position trackers", 700))
share_posts = d["tracker_posts"] / d["posts"]
share_inter = d["tracker_interaction_share"]
BW, BH = R - L, 52
for lab, frac, yy in (("share of posts", share_posts, y + 46),
                      ("share of all interactions", share_inter, y + 150)):
    b.append(txt(L, yy, 20, SUB, lab))
    top = yy + 16
    b.append(f'<rect x="{L}" y="{top}" width="{BW}" height="{BH}" fill="#f2efe8"/>')
    b.append(f'<rect x="{L}" y="{top}" width="{BW*frac:.0f}" height="{BH}" fill="{HOT}"/>')
    b.append(txt(L + BW * frac - 16, top + 36, 28, "#ffffff", f"{frac*100:.0f}%", 700, "end", MONO))
    b.append(txt(L + BW - 16, top + 36, 22, SUB, "everyone else", 400, "end"))

# What those posts say, in their own words.
y = 666
b.append(f'<rect x="{L}" y="{y-26}" width="{R-L}" height="92" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y-26}" width="5" height="92" fill="{HOT}"/>')
for i, q in enumerate(d["quotes"][:2]):
    b.append(txt(L + 26, y + 4 + i * 34, 21, INK, q[:72], 400, "start", MONO))

y = H - 54
b.append(f'<line x1="{L}" y1="{y-40}" x2="{R}" y2="{y-40}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y, 25, INK,
             "The loudest voice around a 4.5x move is bots narrating a few leveraged bets.", 700))
b.append(txt(R, y + 28, 17, SUB, "measured 2026-10-17  ·  @nickisanders", 400, "end"))

render("silent_mover", W, H, "".join(b))
