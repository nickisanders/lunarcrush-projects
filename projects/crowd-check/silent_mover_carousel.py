#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the $AGT silent-mover post.

Reads the same out/agt-anatomy.json the chart does, so the slides cannot drift
from it. Layout, wrapping and the overflow guard come from carousel.py rather
than being copied; duplicating them is how the text started overlapping before.

Usage: python3 silent_mover_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, GREEN, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/agt-anatomy.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "agt"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"$AGT, measured 17 october · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def stat(f: Flow, big: str, small: str, colour: str = TEXT) -> None:
    f.raw(txt(M, f.y, 84, colour, big, 700))
    f.raw(txt(M, f.y + 44, 34, SUB, small))
    f.y += 126


def bar(f: Flow, label: str, frac: float) -> None:
    BW, BH = W - 2 * M, 88
    f.raw(txt(M, f.y, 34, SUB, label))
    top = f.y + 26
    f.raw(f'<rect x="{M}" y="{top}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
    f.raw(f'<rect x="{M}" y="{top}" width="{BW*frac:.0f}" height="{BH}" rx="8" fill="{RED}"/>')
    f.raw(txt(M + BW * frac - 24, top + 60, 52, BG, f"{frac*100:.0f}%", 700, "end"))
    f.y = top + BH + 76


def slide1(d) -> str:
    f = Flow(290)
    f.say(62, TEXT, "A token is up 354% this week.", 700, gap=30)
    f.say(62, RED, "A hundred posts have been written about it.", 700, gap=66)
    f.say(40, SUB, "Every post on its verified topic, which runs 94% on its own ticker.", gap=0)
    return frame(1, f.svg())


def slide2(d) -> str:
    f = Flow(350)
    f.say(52, TEXT, "The two numbers", 700, gap=48)
    stat(f, f"${d['volume24h']/1e6:.0f}M", "traded in 24 hours, 68% of its market cap", BLUE)
    stat(f, f"{d['posts']}", f"posts, written by {d['accounts']} accounts, all on X")
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(300)
    f.say(52, TEXT, "Eighteen of them are bots", 700, gap=24)
    f.say(36, SUB, "Automated trackers narrating leveraged wallets. They are a fifth "
                   "of the posts and nearly half the attention.", gap=56)
    bar(f, "share of posts", d["tracker_posts"] / d["posts"])
    bar(f, "share of all interactions", d["tracker_interaction_share"])
    return frame(3, f.svg())


def slide4(d) -> str:
    f = Flow(390)
    f.say(48, TEXT, "What they actually say", 700, gap=54)
    for q in d["quotes"][:2]:
        f.say(36, RED, '"' + q.strip()[:68] + '..."', gap=42, lh=1.38)
    f.gap(16)
    f.say(34, SUB, "That is the loudest voice in the room.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    f = Flow(320)
    f.say(56, TEXT, "A token can trade two thirds of itself in a day while "
                    "forty-two people write about it.", 700, gap=66)
    f.say(40, SUB, "No call either way. It is a measurement.", gap=50)
    f.say(34, SUB, "Taken from the verified topic, not from a headline social "
                   "number that reads ten times higher.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = json.loads(SRC.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{STEM}-{i}.svg"
        p.write_text(fn(d))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
