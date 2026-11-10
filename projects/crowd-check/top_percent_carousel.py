#!/usr/bin/env python3
"""Instagram carousel: the top 1% holds everything and that says nothing.

Reads top-code.json at render time, so no token is named in the source. The
two tokens on slides two, three and five are whichever ends of the field the
data puts there, and the text is built from their numbers rather than around
them.

Slide two shows the headline figure on both tokens before the split, because
the whole point is that those two numbers are indistinguishable. A reader who
sees the code share first has nothing left to be surprised by on slide three.

Slide five is the one that matters and it withdraws the finding in both
directions. A red bar does not mean the holders are gone and a blue bar does
not mean there is a crowd, and the single wallet holding most of the least
coded token on the chart is the cheapest way to show the second half.

Usage: python3 top_percent_carousel.py
"""

import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "top-code.json"
BASE = SRC.parent / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "toppercent"
BLUE = "#388bfd"
MIN_TOP1, MIN_HOLDERS = 0.90, 1000
# Same address-keyed drop as top_percent.py, for the same reason: the label is
# what misleads, not the measurement.
AMBIGUOUS = {"0x8cdf7af57e4c8b930e1b23c477c22f076530585e",
             "0x8d010bf9c26881788b4e6bf5fd1bdc358c8f90b8",
             "0x00f3c42833c3170159af4e92dbb451fb3f708917",
             "0x33e2c129ea670031659ac8852c01d0fe4b297954"}


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"code or wallets · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    base = json.loads(BASE.read_text())["tokens"]
    rows = []
    for name, d in doc["tokens"].items():
        if d["top1pct_supply_share"] < MIN_TOP1 or d["holders"] < MIN_HOLDERS:
            continue
        if (base.get(name) or {}).get("address", "").lower() in AMBIGUOUS:
            continue
        c = d["classes"]
        if c["unknown"]["n"]:
            raise SystemExit(f"  {name} carries {c['unknown']['n']} addresses "
                             f"nobody answered for; rerun top_code.py")
        rows.append({"sym": name.upper(), "holders": d["holders"],
                     "n": d["top1pct_n"], "top1": d["top1pct_supply_share"],
                     "code": c["contract"]["supply_share"],
                     "own": c["wallet"]["supply_share"]
                            + c["delegated"]["supply_share"],
                     "first": d["biggest_holder"]["supply_share"],
                     "firstkind": d["biggest_holder"]["class"]})
    rows.sort(key=lambda r: -r["code"])
    return rows, doc["measured"]


def slide1(rows, _) -> str:
    f = Flow(330)
    f.say(58, TEXT, "The top 1% of addresses", 700, gap=6)
    f.say(58, TEXT, "holds nearly all the supply.", 700, gap=54)
    f.say(44, SUB, f"On every one of the {len(rows)} tokens I checked, and it "
                   f"is the most quoted number in token analysis.", gap=62)
    f.say(44, BLUE, "It cannot tell them apart.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows, _) -> str:
    f = Flow(300)
    f.say(48, TEXT, "Two tokens, one number", 700, gap=48)
    for r in (rows[0], rows[-1]):
        f.raw(txt(M, f.y + 20, 90, TEXT, f"{r['top1']*100:.1f}%", 700))
        f.raw(txt(M, f.y + 70, 34, SUB, "$" + r["sym"]))
        f.y += 158
    f.gap(20)
    f.say(38, SUB, "Share of all supply held by the top 1% of addresses. On "
                   "this measure the two are the same token.", gap=0)
    return frame(2, f.svg())


def slide3(rows, _) -> str:
    hi, lo = rows[0], rows[-1]
    checked = sum(r["n"] for r in rows)
    f = Flow(286)
    f.say(48, TEXT, "Then I asked the chain", 700, gap=36)
    f.say(34, SUB, f"eth_getCode on all {checked:,} of those addresses. Code "
                   f"means a contract: a pool, a bridge, a vesting escrow, an "
                   f"exchange's omnibus wallet.", gap=54)
    for r, col in ((hi, RED), (lo, BLUE)):
        f.raw(txt(M, f.y + 20, 82, col, f"{r['code']*100:.1f}%", 700))
        f.raw(txt(M, f.y + 66, 32, SUB, f"of ${r['sym']} is held by code"))
        f.y += 146
    f.gap(10)
    f.say(34, SUB, "Same headline. Nothing alike underneath it.", gap=0)
    return frame(3, f.svg())


def slide4(rows, _) -> str:
    med = statistics.median(r["code"] for r in rows)
    f = Flow(276)
    f.say(46, TEXT, f"All {len(rows)}, sorted by code", 700, gap=14)
    f.say(30, SUB, "Red is supply in contracts. Blue is supply in wallets.",
          gap=40)
    # The track stops short of the right margin so the two end labels have
    # somewhere to sit. At full width $SPCXX ran off the slide.
    BW, BH, GAP = W - 2 * M - 140, 12, 2
    top = f.y
    for r in rows:
        wc, ww = BW * r["code"], BW * r["own"]
        f.raw(f'<rect x="{M}" y="{f.y}" width="{BW}" height="{BH}" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M}" y="{f.y}" width="{wc:.1f}" height="{BH}" fill="{RED}"/>')
        f.raw(f'<rect x="{M+wc:.1f}" y="{f.y}" width="{ww:.1f}" height="{BH}" '
              f'fill="{BLUE}"/>')
        f.y += BH + GAP
    bot = f.y - GAP
    # Labelling 45 tickers at this height is unreadable, so only the two ends
    # are named and the rest reads as the continuum it is.
    f.raw(txt(M + BW + 14, top + BH + 2, 22, SUB, "$" + rows[0]["sym"]))
    f.raw(txt(M + BW + 14, bot, 22, SUB, "$" + rows[-1]["sym"]))
    mx = M + BW * med
    f.raw(f'<line x1="{mx:.1f}" y1="{top-8}" x2="{mx:.1f}" y2="{bot+8}" '
          f'stroke="{TEXT}" stroke-width="2" stroke-dasharray="3 4" opacity="0.6"/>')
    f.gap(44)
    f.say(32, SUB, f"The median token holds {med*100:.1f}% of its supply in "
                   f"code.", gap=0)
    return frame(4, f.svg())


def slide5(rows, measured) -> str:
    lo = rows[-1]
    mostly = sum(1 for r in rows if r["code"] > 0.5)
    f = Flow(286)
    f.say(48, TEXT, "It reads in neither direction", 700, gap=42)
    f.say(36, SUB, "A contract is not a person and it is not nobody. An "
                   "exchange omnibus holds for thousands and a pool holds for "
                   "its depositors, so red means this cannot see those holders "
                   "rather than that they left.", gap=44)
    # Wrapped to two lines deliberately: the longer phrasing left "of it."
    # orphaned on a third, which reads as a mistake at this size.
    f.say(36, SUB, f"Blue is no safer. ${lo['sym']} carries almost no code in "
                   f"its top 1%, and one wallet holds "
                   f"{lo['first']*100:.1f}% of it.", gap=46)
    f.say(38, BLUE, f"Code holds most of the supply on {mostly} of {len(rows)}.",
          700, gap=44)
    f.say(30, SUB, "The chain says there is code at the address and not what "
                   "the code does. Nothing here is advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {measured} · github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows, measured = load()
    if len(rows) < 10:
        raise SystemExit(f"  only {len(rows)} tokens clear the filters; the "
                         f"slides describe a field and would be describing a "
                         f"handful")
    # Slide five says one wallet holds most of the least-coded token. If that
    # end of the field is a contract the sentence is simply false.
    if rows[-1]["firstkind"] != "wallet":
        raise SystemExit(f"  ${rows[-1]['sym']} now has a {rows[-1]['firstkind']} "
                         f"as its biggest holder; slide five claims a wallet")
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{STEM}-{i}.svg"
        p.write_text(fn(rows, measured))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
