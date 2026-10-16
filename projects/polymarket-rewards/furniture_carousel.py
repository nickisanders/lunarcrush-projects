#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the Polymarket trader-concentration post.

Reads out/traders.json, so the slides cannot drift from the measurement the
chart was drawn from. Layout, wrapping and the overflow guard are imported from
the crowd-check carousel rather than copied; duplicating them is how the text
started overlapping the first time.

Usage: python3 furniture_carousel.py
"""

import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "lunarcrush-projects/projects/crowd-check"))
from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, GREEN, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "furniture"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"polymarket, 2-7 october · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def stat(f: Flow, big: str, small: str, colour: str = TEXT) -> None:
    f.raw(txt(M, f.y, 86, colour, big, 700))
    f.raw(txt(M, f.y + 44, 34, SUB, small))
    f.y += 128


def slide1(d) -> str:
    f = Flow(300)
    f.say(62, TEXT, f"The median Polymarket trader bet ${d['median_volume']:.0f} last week.", 700, gap=36)
    f.say(62, RED, "The biggest one didn't really bet at all.", 700, gap=70)
    f.say(40, SUB, "Every fill on chain for five days, with the mint legs stripped out.", gap=0)
    return frame(1, f.svg())


def slide2(d) -> str:
    f = Flow(370)
    f.say(52, TEXT, "What actually changed hands", 700, gap=50)
    stat(f, f"${d['notional']/1e6:.0f}M", f"between {d['addresses']:,} addresses")
    stat(f, "76%", "of it from the top 1,000")
    stat(f, f"{d['over']['10000']:,}", "addresses cleared $10,000 all week")
    return frame(2, f.svg())


def slide3(d) -> str:
    t = max(d["top10"], key=lambda x: x["volume"])
    f = Flow(330)
    f.say(52, TEXT, "The number one address", 700, gap=44)
    stat(f, f"${t['volume']/1e6:.0f}M", f"across {t['tokens']:,} different outcomes", BLUE)
    stat(f, f"{t['maker_share']*100:.0f}%", "of it posted as the maker", BLUE)
    f.say(44, TEXT, f"Nobody has a view on {t['tokens']:,} things.", 700, gap=28)
    f.say(38, SUB, "That is someone quoting the whole board and collecting the "
                   "spread. A business rather than a bet.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    taker = min(d["top10"], key=lambda x: x["maker_share"])
    narrow = sorted(d["top10"], key=lambda x: x["tokens"])[:2]
    f = Flow(240)
    f.say(52, TEXT, "Then there is this one", 700, gap=40)
    f.say(40, SUB, f"{taker['fills']:,} fills across {taker['tokens']:,} outcomes, "
                   f"at a maker share of exactly zero. Pure taker, hits whatever moves.", gap=56)
    f.say(52, TEXT, "Two of the ten look like people", 700, gap=36)
    for t in narrow:
        f.raw(txt(M, f.y, 46, RED, f"${t['volume']/1e6:.1f}M", 700))
        f.raw(txt(M + 210, f.y, 36, SUB, f"in {t['tokens']} outcomes"))
        f.y += 70
    f.gap(20)
    f.say(38, SUB, "That is a position you could explain out loud.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    f = Flow(330)
    f.say(56, TEXT, "The liquidity is real and most of it just isn't anyone's opinion.", 700, gap=70)
    f.say(66, RED, "You're mostly trading with the furniture.", 700, gap=60)
    f.say(36, SUB, "Measured from the chain, not from an API's headline numbers.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = json.loads((HERE / "out" / "traders.json").read_text())
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
