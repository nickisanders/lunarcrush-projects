#!/usr/bin/env python3
"""Instagram carousel: what a tenfold bigger allocation costs.

Reads receipt-deciles.json at render time. No token and no figure is named
in the source.

The wide chart leads with the rate and spends its second panel retiring the
range objection. A deck cannot hold a methodological panel, so slide four
carries the objection as the turn: the thing a reader would say back, and
the number that answers it.

Slide three is the spread between tokens, which is the part the headline
rate hides. A median of ten points is a useful rule and a bad description
of any particular airdrop.

Usage: python3 allocation_rate_carousel.py
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
TOTAL, STEM = 5, "rate"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"what size costs · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = sorted((r for r in doc["per_token"] if r["rate_kept"] is not None),
                  key=lambda r: r["rate_kept"])
    return {"doc": doc, "st": doc["rate"], "rows": rows,
            "steep": rows[0], "gentle": rows[-1]}


def slide1(d) -> str:
    st = d["st"]
    f = Flow(330)
    f.say(58, TEXT, "Ten times the airdrop,", 700, gap=6)
    f.say(58, TEXT, "ten points off the odds", 700, gap=6)
    f.say(58, TEXT, "it is still held.", 700, gap=54)
    f.say(44, SUB, f"Measured inside {st['tokens']} airdrops, one at a time, "
                   f"with nothing priced.", gap=62)
    f.say(44, BLUE, f"{st['negative_kept']} of the {st['tokens']} lose "
                    f"ground as the allocation grows.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    st = d["st"]
    f = Flow(300)
    f.say(48, TEXT, "A rate, not a gap", 700, gap=40)
    f.say(36, SUB, "Sort one airdrop's recipients by what they received, cut "
                   "them into ten equal groups, and fit how often the "
                   "allocation survives against how big it was.", gap=54)
    f.raw(txt(M, f.y + 30, 100, RED, f"{st['median_kept']:.1f}", 700))
    f.y += 150
    f.say(36, SUB, "points of allocation retention, lost for every tenfold "
                   "rise in what a wallet was handed. Median across the "
                   "set.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    st, steep, gentle = d["st"], d["steep"], d["gentle"]
    q = st["quartiles_kept"]
    f = Flow(286)
    f.say(48, TEXT, "The median hides a lot", 700, gap=40)
    f.say(36, SUB, f"Half the tokens lose between {abs(q[2]):.1f} and "
                   f"{abs(q[0]):.1f} points a tenfold. The ends are further "
                   f"apart than that.", gap=50)
    for r, col, lab in ((steep, RED, "steepest"), (gentle, BLUE, "gentlest")):
        f.raw(txt(M, f.y + 20, 76, col, f"{r['rate_kept']:+.1f}", 700))
        f.raw(txt(M, f.y + 64, 32, SUB, f"${r['sym']}, the {lab}"))
        f.y += 142
    f.gap(14)
    f.say(34, SUB, "Same ten groups, cut the same way, inside each token.",
          gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    """The objection a reader would raise, and the number that answers it."""
    st = d["st"]
    jl, jh = st["spread_vs_rate_jackknife"]
    f = Flow(286)
    f.say(48, TEXT, "The objection", 700, gap=40)
    f.say(36, SUB, "Some airdrops spread their allocations across two orders "
                   "of magnitude and some across five. A wider spread has "
                   "more room to show a difference, so maybe this is range "
                   "and not behaviour.", gap=50)
    f.raw(txt(M, f.y + 26, 92, BLUE, f"r = {st['spread_vs_rate']:.2f}", 700))
    f.y += 142
    f.say(36, SUB, f"between the rate and how far a token spread its "
                   f"allocations, with a jackknife from {jl:.2f} to {jh:.2f}. "
                   f"A flat giveaway decays just as fast, over less ground.",
          gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    st, doc = d["st"], d["doc"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, f"That the rule fits your token. It is a median, and the "
                   f"airdrops behind it run from "
                   f"{abs(d['steep']['rate_kept']):.1f} points a tenfold to "
                   f"under one.", gap=44)
    f.say(36, SUB, "Why they differ. Age, crowd size and the share of "
                   "holders who cannot transact at all all come back weak "
                   "against the rate.", gap=46)
    f.say(38, BLUE, f"On a balance above zero, the figure airdrop reports "
                    f"quote, the same fit reads {st['median_holding']:.1f} "
                    f"points.", 700, gap=44)
    f.say(30, SUB, "Why a position shrank is not visible from the chain. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    st = d["st"]
    if st["median_kept"] is None or st["median_kept"] >= 0:
        raise SystemExit("  the median rate no longer falls; every slide "
                         "here says it does")
    if len(d["rows"]) < 20:
        raise SystemExit(f"  only {len(d['rows'])} tokens carry a rate; the "
                         f"slides describe a field")
    # Slide four reads the correlation as nothing. A real one would make
    # that slide an assertion against its own number.
    if abs(st["spread_vs_rate"]) > 0.3:
        raise SystemExit(f"  spread against rate is now "
                         f"{st['spread_vs_rate']:.2f}; slide four calls that "
                         f"relationship absent")
    if d["gentle"]["rate_kept"] >= 0 and d["steep"]["rate_kept"] >= 0:
        raise SystemExit("  both ends of the field rise; slide three names "
                         "a steepest and a gentlest")
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
