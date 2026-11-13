#!/usr/bin/env python3
"""Instagram carousel: the bigger the allocation, the less of it survives.

Reads receipt-deciles.json and decile-code.json at render time, so no token
and no figure is named in the source. The deck carries its own case rather
than compressing the post: the post spends its length on the two objections,
and these five slides spend theirs on the one thing a reader has to accept
before the objections matter, which is that the ten groups are a ladder of
real sizes rather than a statistical slice.

Slide two is that ladder and nothing else. A reader who sees the retention
numbers first reads the deciles as arbitrary buckets, and the finding dies
there.

Slide five withdraws what the measurement cannot support. A wallet that
trimmed a position and a wallet that forgot one look the same, and the chain
does not say which happened.

Usage: python3 allocation_carousel.py
"""

import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
SRC = ROOT / "receipt-deciles.json"
CODE = ROOT / "decile-code.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "allocation"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"what size does · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    code = json.loads(CODE.read_text())
    rows = doc["per_token"]
    spread = sorted(r["groups"][-1]["received"] / r["groups"][0]["received"]
                    for r in rows if r["groups"][0]["received"] > 0)
    d = {"doc": doc, "code": code, "rows": rows,
         "med": doc["median"],
         "falling": sum(1 for r in rows if r["slope"] < 0),
         "spread": statistics.median(spread),
         "steep": max(rows, key=lambda r: r["bottom"] - r["top"]),
         "biggest": max(rows, key=lambda r: r["recipients"])}
    return d


def slide1(d) -> str:
    f = Flow(330)
    f.say(58, TEXT, "The more an airdrop", 700, gap=6)
    f.say(58, TEXT, "gave a wallet,", 700, gap=6)
    f.say(58, TEXT, "the less it still holds.", 700, gap=54)
    f.say(44, SUB, f"Measured inside {d['doc']['tokens']} airdrops, one at a "
                   f"time, with nothing priced.", gap=62)
    f.say(44, BLUE, "The size of the gift predicts its fate.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    """The ladder first. Everything after this is a rate measured along it."""
    f = Flow(300)
    f.say(48, TEXT, "Airdrops are not flat", 700, gap=40)
    f.say(36, SUB, "Sort one airdrop's recipients by what they received and "
                   "cut them into ten equal groups. The gap between the ends "
                   "is not a rounding error.", gap=56)
    f.raw(txt(M, f.y + 30, 104, BLUE, f"{d['spread']:,.0f}x", 700))
    f.y += 150
    f.say(36, SUB, "what the median airdrop in this set handed its largest "
                   "tenth, compared with its smallest.", gap=48)
    f.say(34, SUB, f"The widest runs to more than a billion times. The "
                   f"narrowest is under four.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    med = d["med"]
    f = Flow(286)
    f.say(48, TEXT, "Now walk up that ladder", 700, gap=36)
    f.say(34, SUB, f"Share of each group still holding "
                   f"{d['doc']['untouched']*100:.0f}% or more of what it was "
                   f"given. Not a balance above zero, the allocation itself.",
          gap=54)
    for lab, val, col in (("smallest tenth", med[0]["kept"], BLUE),
                          ("largest tenth", med[-1]["kept"], RED)):
        f.raw(txt(M, f.y + 20, 82, col, f"{val*100:.1f}%", 700))
        f.raw(txt(M, f.y + 66, 32, SUB, lab))
        f.y += 146
    f.gap(10)
    f.say(34, SUB, f"Median across the {d['doc']['tokens']}. Both groups were "
                   f"handed the same token on the same day.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    med, doc = d["med"], d["doc"]
    f = Flow(276)
    f.say(46, TEXT, "Every rung, in order", 700, gap=14)
    f.say(30, SUB, "Median share still holding the allocation, smallest group "
                   "on the left.", gap=44)
    BW, GAP, PH = 78, 13, 470
    top = f.y
    peak = max(m["kept"] for m in med)
    for i, m in enumerate(med):
        h = PH * m["kept"] / peak
        x = M + i * (BW + GAP)
        f.raw(f'<rect x="{x}" y="{top + PH - h:.1f}" width="{BW}" '
              f'height="{h:.1f}" fill="{RED if i == len(med)-1 else BLUE}"/>')
        # Bare numbers over the bars read as counts of something. The unit
        # is on every one of them rather than on the tallest alone.
        f.raw(txt(x + BW / 2, top + PH - h - 16, 24, SUB,
                  f"{m['kept']*100:.0f}%", 400, "middle"))
    f.y = top + PH + 12
    f.raw(f'<line x1="{M}" y1="{f.y}" x2="{M + 10*BW + 9*GAP}" y2="{f.y}" '
          f'stroke="{TRACK}" stroke-width="2"/>')
    f.gap(64)
    # Rounded to whole numbers the steepest token printed "100% to 8%", which
    # claims a group where nobody at all sold.
    f.say(34, SUB, f"{d['falling']} of the {doc['tokens']} airdrops run "
                   f"downhill like this. ${d['steep']['sym']} falls from "
                   f"{d['steep']['bottom']*100:.1f}% to "
                   f"{d['steep']['top']*100:.1f}%.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc, code = d["doc"], d["code"]
    big, med = d["biggest"], d["med"]
    f = Flow(286)
    f.say(48, TEXT, "What it is not", 700, gap=42)
    f.say(36, SUB, f"A small position can be held because selling costs more "
                   f"than it is worth. Over the top half alone, where that is "
                   f"hard to argue, {doc['falling_top_half']} of "
                   f"{doc['tokens']} still fall.", gap=44)
    f.say(36, SUB, f"The largest receivers are not simply pools and "
                   f"treasuries. Asked for code, the top tenth comes back "
                   f"{code['ends']['top']['share']*100:.1f}% contracts "
                   f"against {code['ends']['bottom']['share']*100:.1f}% at "
                   f"the bottom.", gap=46)
    f.say(38, BLUE, f"${big['sym']} paid {big['recipients']:,} wallets and "
                    f"falls {big['bottom']*100:.1f}% to "
                    f"{big['top']*100:.1f}%.", 700, gap=44)
    f.say(30, SUB, "Why a position shrank is not visible from the chain. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    doc = d["doc"]
    if doc["tokens"] < 20:
        raise SystemExit(f"  only {doc['tokens']} airdrops carry receipts; "
                         f"the slides describe a field")
    # Slide three reads the ladder downhill and slide four draws it that way.
    # If the median ever turns, both slides are claims about nothing.
    if d["med"][0]["kept"] <= d["med"][-1]["kept"]:
        raise SystemExit("  the median ladder no longer falls; slides three "
                         "and four both assert that it does")
    # Slide two says the narrowest spread is under four and the widest past a
    # billion, which are read off the field rather than from these two.
    spread = sorted(r["groups"][-1]["received"] / r["groups"][0]["received"]
                    for r in d["rows"] if r["groups"][0]["received"] > 0)
    if not (spread[0] < 4 and spread[-1] > 1e9):
        raise SystemExit(f"  spreads now run {spread[0]:.1f}x to "
                         f"{spread[-1]:,.0f}x; slide two names the ends")
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
