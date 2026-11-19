#!/usr/bin/env python3
"""Instagram carousel: the oldest big airdrop that is mostly still held.

Reads the baseline at render time. The token is the best survivor of the
mobility adjustment among the large crowds rather than a name in the
source, and the foil is whichever token the quoted figure puts first.

The wide chart lays out the cohort and lets the swap be found in it. The
deck has to put the swap on a slide, so slide three is the token that leads
the quoted figure and loses that lead, and slide four is the one that keeps
it.

Slide five is the withdrawal. The adjustment is a 250-holder sample, the
immobile count is a floor, and a balance above zero is still the whole of
the retention test.

Usage: python3 still_here_carousel.py
"""

import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "stillhere"
BLUE = "#388bfd"
MIN_AGE, MIN_ARRIVED, BIG = 60, 20000, 100000


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"who is left · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        m = d.get("mobility") or {}
        if (d.get("age_months") or 0) < MIN_AGE or d["arrived"] < MIN_ARRIVED:
            continue
        if m.get("immobile_share") is None:
            continue
        k = (d.get("dust") or {}).get("kinds") or {}
        rows.append({"sym": name.upper(), "arr": d["arrived"],
                     "age": d["age_months"], "raw": d["raw"],
                     "im": m["immobile_share"],
                     "adj": d["raw"] * (1 - m["immobile_share"]),
                     "sampled": m["sampled"],
                     "full": k.get("untouched_large"),
                     "gone": k.get("exited_leaving_dust")})
    rows.sort(key=lambda r: -r["raw"])
    big = [r for r in rows if r["arr"] >= BIG]
    field = [d for d in doc["tokens"].values()
             if (d.get("dust") or {}).get("kinds", {}).get("untouched_large")
             is not None and d["arrived"] >= 5000]
    return {"doc": doc, "rows": rows,
            "star": max(big, key=lambda r: r["adj"]), "head": rows[0],
            "med_full": statistics.median(
                d["dust"]["kinds"]["untouched_large"] for d in field),
            "med_gone": statistics.median(
                d["dust"]["kinds"]["exited_leaving_dust"] for d in field)}


def slide1(d) -> str:
    s = d["star"]
    f = Flow(330)
    f.say(58, TEXT, f"${s['sym']} paid", 700, gap=6)
    f.say(58, TEXT, f"{s['arr']:,} wallets.", 700, gap=6)
    f.say(58, TEXT, "Most of them stayed.", 700, gap=54)
    f.say(44, SUB, f"{s['age']} months later, {s['raw']*100:.1f}% of them "
                   f"still hold a balance.", gap=62)
    f.say(44, BLUE, "The question is whether they could have left.", 700,
          gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    s = d["star"]
    f = Flow(300)
    f.say(48, TEXT, "A retention figure counts the stuck", 700, gap=44)
    f.say(36, SUB, "A wallet holding no ETH that has never sent a "
                   "transaction cannot pay gas, so it cannot sell at any "
                   "price. It is counted as a holder anyway.", gap=54)
    f.raw(txt(M, f.y + 30, 100, RED, f"{s['im']*100:.1f}%"))
    f.y += 150
    f.say(36, SUB, f"of ${s['sym']}'s holders are in that position. Taking "
                   f"them out leaves {s['adj']*100:.1f}%.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    """The token the adjustment actually punishes."""
    h, s = d["head"], d["star"]
    f = Flow(286)
    f.say(48, TEXT, "On one token it is most of them", 700, gap=40)
    f.say(36, SUB, f"${h['sym']} reports the highest retention in this "
                   f"group. {h['im']*100:.1f}% of its holders cannot "
                   f"transact at all.", gap=54)
    for val, lab, col in ((h["raw"], "as quoted", BLUE),
                          (h["adj"], "with the stuck removed", RED)):
        f.raw(txt(M, f.y + 20, 82, col, f"{val*100:.1f}%", 700))
        f.raw(txt(M, f.y + 66, 32, SUB, lab))
        f.y += 146
    f.gap(10)
    f.say(34, SUB, f"That puts it below ${s['sym']}, which it led by "
                   f"{(h['raw']-s['raw'])*100:.1f} points a moment ago.",
          gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    s = d["star"]
    f = Flow(286)
    f.say(48, TEXT, "What is behind the one that holds", 700, gap=42)
    f.say(36, SUB, f"{s['full']*100:.1f}% of ${s['sym']}'s holders are "
                   f"sitting on a full allocation they never moved, against "
                   f"a field median of {d['med_full']*100:.1f}%.", gap=46)
    f.say(36, SUB, f"{s['gone']*100:.1f}% hold under 1% of what they "
                   f"received, meaning they sold out and left a tail. The "
                   f"field median is {d['med_gone']*100:.1f}%.", gap=46)
    f.say(38, BLUE, f"Both cuts are against what each wallet itself "
                    f"received, so neither moves with the price.", 700,
          gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc, s = d["doc"], d["star"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, f"That {s['im']*100:.1f}% is exact. Mobility is sampled "
                   f"at {s['sampled']} holders a token, so every adjusted "
                   f"figure here is a range and the chart draws it.", gap=44)
    f.say(36, SUB, "That everyone else could leave. The count is a floor: a "
                   "wallet with a dollar of ETH and no intention of "
                   "spending it reads as mobile.", gap=46)
    f.say(38, BLUE, "A balance above zero is the whole of the retention "
                    "test, however small that balance is.", 700, gap=44)
    f.say(30, SUB, "Nothing here is priced and nothing here is advice.",
          gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    s, h = d["star"], d["head"]
    if len(d["rows"]) < 6:
        raise SystemExit(f"  only {len(d['rows'])} tokens in the cohort; the "
                         f"slides compare a field")
    # Slides three and four are a swap. Without it the deck has no turn.
    if not (h["raw"] > s["raw"] and h["adj"] < s["adj"]):
        raise SystemExit(f"  ${h['sym']} no longer leads ${s['sym']} on the "
                         f"quoted figure and trails it on the adjusted one; "
                         f"slide three is built on that swap")
    if s["full"] is None or s["gone"] is None:
        raise SystemExit(f"  ${s['sym']} carries no holder split; slide four "
                         f"is that split")
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
