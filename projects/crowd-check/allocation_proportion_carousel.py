#!/usr/bin/env python3
"""Instagram carousel: the decay is a fraction, not a number of points.

Reads receipt-deciles.json at render time. No token and no figure is named
in the source.

The wide chart puts the two fits side by side and lets a reader compare
them. A deck cannot show two scatters, so it argues the same thing in
sequence: slide two is the rule, slide three is why the obvious version of
it cannot travel between tokens, slide four is the pair of tokens that
proves it.

Slide five withdraws the precision. Groups at zero are dropped, the fit is
a median across a field with real spread in it, and the chain does not say
why any position shrank.

Usage: python3 allocation_proportion_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "receipt-deciles.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "proportion"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"a share, not points · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    st = doc["rate"]["elasticity"]
    rows = [r for r in doc["per_token"] if r["elasticity_kept"] is not None]
    return {"doc": doc, "st": st, "rows": rows,
            "hi": max(rows, key=lambda r: r["level_kept"]),
            "lo": min(rows, key=lambda r: r["level_kept"])}


def slide1(d) -> str:
    st = d["st"]
    f = Flow(330)
    f.say(58, TEXT, "Ten times the allocation", 700, gap=6)
    f.say(58, TEXT, "takes almost half the", 700, gap=6)
    f.say(58, TEXT, "odds it is still held.", 700, gap=54)
    f.say(44, SUB, f"Measured inside {st['tokens']} airdrops, one at a time, "
                   f"with nothing priced.", gap=62)
    f.say(44, BLUE, f"A share of whatever the chances were, not a fixed "
                    f"number of points.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    st = d["st"]
    q = st["quartiles"]
    f = Flow(300)
    f.say(48, TEXT, "The rule", 700, gap=44)
    f.raw(txt(M, f.y + 30, 104, RED, f"{(1-st['median_multiplier'])*100:.1f}%",
              700))
    f.y += 150
    f.say(36, SUB, "of the chances a wallet already had, gone for every "
                   "tenfold rise in what it was handed.", gap=48)
    f.say(34, SUB, f"Median across the field. It falls on {st['negative']} of "
                   f"{st['tokens']}, and half the tokens sit between "
                   f"{(1-10**q[2])*100:.0f}% and {(1-10**q[0])*100:.0f}%.",
          gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    """Why the obvious version of the rule cannot be carried anywhere."""
    st = d["st"]
    f = Flow(286)
    f.say(48, TEXT, "Why not points", 700, gap=40)
    f.say(36, SUB, "A token whose smallest recipients hold 5% of what they "
                   "got cannot lose ten points as the allocations grow. One "
                   "sitting at 60% has room to lose forty.", gap=50)
    f.raw(txt(M, f.y + 26, 92, BLUE, f"r = {st['level_vs_points']:.2f}", 700))
    f.y += 142
    f.say(36, SUB, "between a decay measured in points and the level the "
                   "token starts from. Most of it is height rather than "
                   "decay.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    hi, lo, st = d["hi"], d["lo"], d["st"]
    f = Flow(286)
    f.say(48, TEXT, "Two tokens, two readings", 700, gap=36)
    f.say(34, SUB, f"${hi['sym']}'s smallest recipients hold "
                   f"{hi['level_kept']*100:.1f}% of what they got. "
                   f"${lo['sym']}'s hold {lo['level_kept']*100:.1f}%.",
          gap=48)
    for lab, a, bq, col in (
            ("in points, per tenfold", f"{hi['rate_kept']:.1f}",
             f"{lo['rate_kept']:.1f}", BLUE),
            ("as a share of the odds", f"{(1-10**hi['elasticity_kept'])*-100:+.0f}%",
             f"{(1-10**lo['elasticity_kept'])*-100:+.0f}%", RED)):
        f.raw(txt(M, f.y + 24, 58, col, f"{a}  and  {bq}", 700))
        f.raw(txt(M, f.y + 62, 30, SUB, lab))
        f.y += 140
    f.gap(16)
    f.say(34, SUB, "Opposite ends of the field on one measure and the same "
                   "place on the other.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc, st = d["doc"], d["st"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, f"That it fits your token. It is a median across "
                   f"{st['tokens']} airdrops with real spread behind it, and "
                   f"one of them rises instead of falling.", gap=44)
    f.say(36, SUB, f"That the fit is clean everywhere. Groups at zero cannot "
                   f"be logged and get dropped, and a token with fewer than "
                   f"{st['min_live_groups']} groups left is not fitted at "
                   f"all.", gap=46)
    f.say(38, BLUE, "Both fits are against what the wallet itself received, "
                    "so neither moves when the price does.", 700, gap=44)
    f.say(30, SUB, "Why a position shrank is not visible from the chain. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    st = d["st"]
    if st["tokens"] < 20:
        raise SystemExit(f"  only {st['tokens']} tokens carry the "
                         f"proportional fit; the slides describe a field")
    if st["median_multiplier"] >= 1:
        raise SystemExit("  the median token no longer loses ground; every "
                         "slide here says it does")
    # Slides three and four are built on one measure tracking the level and
    # the other ignoring it.
    if abs(st["level_vs_points"]) < 0.5 or abs(st["level_vs_elasticity"]) > 0.3:
        raise SystemExit(f"  level reads {st['level_vs_points']:.2f} against "
                         f"points and {st['level_vs_elasticity']:.2f} against "
                         f"the proportion; slide three calls the first strong "
                         f"and the second absent")
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
