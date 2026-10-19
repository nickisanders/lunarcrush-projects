#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the two same-month airdrops.

Reads the same out/aztec-zama.json the chart does, so slides, chart and post
text cannot drift. Layout, wrapping and the overflow guard come from
carousel.py rather than being copied.

Slide two exists only to show the cohorts are the same size. Without it slide
three is two bars of different lengths, which proves nothing.

Usage: python3 airdrop_carousel.py
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/aztec-zama.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "airdrop"
BLUE = "#388bfd"
ORDER = ["aztec", "zama"]
COL = {"aztec": BLUE, "zama": RED}


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"two airdrops, one month · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def bars(f: Flow, d: dict, pick, denom: float, fmt, flat: bool) -> None:
    """`flat` draws both in one colour, for the panel whose point is sameness."""
    BW, BH = W - 2 * M - 190, 76
    for name in ORDER:
        v = pick(d[name])
        w = max(BW * v / denom, 2)
        col = SUB if flat else COL[name]
        f.raw(txt(M, f.y + 52, 36, TEXT, "$" + name.upper(), 700))
        f.raw(f'<rect x="{M+190}" y="{f.y+12}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+190}" y="{f.y+12}" width="{w:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        inside = w > 230
        f.raw(txt(M + 190 + w - 22 if inside else M + 190 + w + 18, f.y + 64,
                  42, BG if inside else TEXT, fmt(v), 700, "end" if inside else "start"))
        f.y += BH + 26


def caption(f: Flow, size: int, fill: str, text: str, weight: int = 400) -> None:
    """A line of text sitting directly under a raw block such as the bars.

    Flow.say places the first line's baseline at f.y, so its glyphs rise above
    that into whatever was drawn last. Following bars straight with a say put
    the caption on top of the final bar. Drop by the ascent before drawing.
    """
    f.gap(int(size * 0.82) + 22)
    f.say(size, fill, text, weight, gap=0)


def slide1(d) -> str:
    a, z = d["aztec"]["distribution"], d["zama"]["distribution"]
    f = Flow(300)
    f.say(60, TEXT, "Two privacy projects airdropped in the same month.", 700, gap=64)
    f.say(44, SUB, f"$AZTEC went to {a['arrived']:,} addresses in February. "
                   f"$ZAMA went to {z['arrived']:,}.", gap=56)
    f.say(48, BLUE, "Within 300 of each other.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    f = Flow(330)
    f.say(54, TEXT, "The same size giveaway", 700, gap=22)
    f.say(34, SUB, "Addresses that received the February 2026 distribution.", gap=56)
    top = max(d[n]["distribution"]["arrived"] for n in ORDER)
    bars(f, d, lambda t: t["distribution"]["arrived"], top, lambda v: f"{v:,.0f}", flat=True)
    caption(f, 38, SUB, "Same month, same market, same number of people handed a token.")
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(330)
    f.say(54, TEXT, "Eight months later", 700, gap=22)
    f.say(34, SUB, "Of those same addresses, the share that still holds.", gap=56)
    bars(f, d, lambda t: t["distribution"]["retention"], 0.5,
         lambda v: f"{v*100:.1f}%", flat=False)
    caption(f, 40, TEXT, "Two and a half times the gap, with everything else held still.", 700)
    return frame(3, f.svg())


def slide4(d) -> str:
    a = d["aztec"]["distribution"]["retention"]
    z = d["zama"]["after"]["retention"]
    f = Flow(300)
    f.say(52, TEXT, "The number that settles it", 700, gap=54)
    f.raw(txt(M, f.y + 20, 86, BLUE, f"{a*100:.1f}%", 700))
    f.raw(txt(M, f.y + 70, 32, SUB, "of Aztec's airdrop crowd still holds"))
    f.y += 146
    f.raw(txt(M, f.y + 20, 86, RED, f"{z*100:.1f}%", 700))
    f.raw(txt(M, f.y + 70, 32, SUB, "of Zama's non-airdrop crowd still holds"))
    f.y += 156
    f.say(40, TEXT, "Aztec's farmers held on better than the people who came to "
                    "Zama by choice.", 700, gap=30)
    f.say(34, SUB, "Which rules out the easy explanation, that Aztec simply drew "
                   "fewer farmers.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    w = d["aztec"]["worst_month"]
    month = datetime.strptime(w["month"], "%Y-%m").strftime("%B %Y")
    f = Flow(300)
    f.say(50, TEXT, "Aztec has its own hole", 700, gap=40)
    f.say(36, SUB, f"{w['arrived']:,} addresses arrived in {month}, "
                   f"{w['share']*100:.0f}% of everyone who has ever held it, and "
                   f"{w['retention']*100:.1f}% remain.", gap=64)
    f.say(44, TEXT, "What predicts retention is how concentrated the arrival was.",
          700, gap=38)
    f.say(36, SUB, "61% of Zama's holders showed up in one month and 43% of Aztec's. "
                   "For $STRK, $W and $APE it is 12% to 22%, and all three keep "
                   "about 40%.", gap=44)
    f.say(32, SUB, "Five tokens is a pattern, not a law. Nothing here is advice.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = json.loads(SRC.read_text())["tokens"]
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
