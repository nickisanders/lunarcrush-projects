#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the follow-up: the crowd grew, the price did not.

Reads out/divergence-<sym>.json, so the slides always match the last run of
divergence.py. Layout helpers come from carousel.py rather than being copied,
which is what kept the two sets consistent when the overlap bug was fixed there.

This is a separate carousel from the spotlight one because it tells a different
story. The spotlight set answers whether a crowd was real. This set answers what
happened after, which is the part almost nobody posts, and the honest ending is
that a real crowd was never a reason to buy.

Usage: python3 divergence_carousel.py STRK
"""

import argparse
import json
import subprocess
from pathlib import Path

from carousel import AMBER, GREEN, RED, SUB, TEXT, Flow, W, H, M, frame, txt

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"


def slide1(d) -> str:
    f = Flow(300)
    f.say(80, TEXT, f"Four days ago I said {d['name']}'s crowd was real.", 700, gap=56)
    f.say(52, SUB, "It still is. That is not the interesting part.")
    f.gap(110)
    f.say(46, AMBER, "Here is the follow-up.", 700)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    f = Flow(250)
    f.say(64, TEXT, "The crowd kept growing.", 700, gap=90)
    y = f.y
    f.raw(txt(M, y, 38, SUB, "people posting, per day"))
    f.raw(txt(M, y + 86, 76, SUB, f"{d['people'][0]:,}", 700))
    f.raw(txt(M + 230, y + 86, 56, SUB, "to"))
    f.raw(txt(M + 350, y + 86, 76, GREEN, f"{d['people'][-1]:,}", 700), 180)
    f.say(46, SUB, "Posts and interactions went with it. Nothing about the attention "
                   "looked bought.")
    return frame(2, f.svg(), "over fourteen days")


def slide3(d) -> str:
    pk = d["price_peak"]
    f = Flow(250)
    f.say(64, TEXT, "The price did not.", 700, gap=80)
    y = f.y
    f.raw(txt(M, y, 38, SUB, "price"))
    f.raw(txt(M, y + 86, 72, SUB, f"${pk['value']:.4f}", 700))
    f.raw(txt(M + 320, y + 86, 56, SUB, "to"))
    f.raw(txt(M + 440, y + 86, 72, RED, f"${d['live_price']:.4f}", 700), 170)
    f.say(52, RED, f"Down {abs(d['from_peak_pct']):.0f}% from the peak.", 700, gap=36)
    f.say(44, SUB, "While the number of people posting about it was still climbing.")
    return frame(3, f.svg())


def slide4(d) -> str:
    gap = d["crowd_peaked_days_after_price"]
    f = Flow(250)
    f.say(64, TEXT, "Look at the order.", 700, gap=50)
    f.say(48, SUB, f"The price peaked on {d['price_peak']['day']}. The crowd peaked "
                   f"{'the next day' if gap == 1 else f'{gap} days later'}.", gap=64)
    f.say(50, AMBER, "People arrive after the move, not before it.", 700, gap=40)
    f.say(42, SUB, "Every live case I have tracked has run in that order, which makes a "
                   "growing crowd a confirmation rather than a signal.")
    return frame(4, f.svg())


def slide5(d) -> str:
    f = Flow(250)
    f.say(60, TEXT, "A real crowd is not a good entry.", 700, gap=60)
    f.say(46, SUB, "My own backtest of coins whose conversation spikes into the top ten "
                   "found the median one trailing Bitcoin by 21% three months later.",
          gap=70)
    f.say(50, RED, "The attention was genuine.", 700, gap=14)
    f.say(50, RED, "It was never a reason to buy.", 700, gap=50)
    f.say(40, SUB, "Method and code are public. Nothing here is advice.")
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    a = ap.parse_args()
    sym = a.symbol.upper()
    src = HERE / "out" / f"divergence-{sym.lower()}.json"
    if not src.exists():
        raise SystemExit(f"No {src.name}. Run: python3 divergence.py {sym}")
    d = json.loads(src.read_text())

    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{sym.lower()}-div-{i}.svg"
        p.write_text(fn(d))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{sym.lower()}-div-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
