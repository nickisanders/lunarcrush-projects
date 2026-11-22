#!/usr/bin/env python3
"""Instagram carousel: the wallets that cannot sell what they hold.

Reads the baseline at render time. No token and no figure is named in the
source: the deck takes the largest stuck population and, as its foil, the
worst rate.

The wide chart ranks the field and lets the reader notice that the two
orderings disagree. A deck has to state the disagreement, so slide three
puts the worst rate next to the largest population and slide four is the
field total behind both.

Slide five withdraws what the sample and the definition cannot carry.

Usage: python3 stuck_wallets_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "stuck"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"cannot sell · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        m = d.get("mobility") or {}
        if m.get("immobile_share") is None or not m.get("of_holders"):
            continue
        rows.append({"sym": name.upper(), "holders": m["of_holders"],
                     "share": m["immobile_share"], "sampled": m["sampled"],
                     "n": m["of_holders"] * m["immobile_share"],
                     "arrived": d["arrived"]})
    rows.sort(key=lambda r: -r["n"])
    return {"doc": doc, "rows": rows, "most": rows[0],
            "worst": max(rows, key=lambda r: r["share"]),
            "total": sum(r["n"] for r in rows)}


def slide1(d) -> str:
    m = d["most"]
    f = Flow(330)
    f.say(58, TEXT, f"{m['n']:,.0f} wallets", 700, gap=6)
    f.say(58, TEXT, f"are holding ${m['sym']}", 700, gap=6)
    f.say(58, TEXT, "and cannot sell it.", 700, gap=54)
    f.say(44, SUB, "That is inability rather than reluctance: no ETH to pay "
                   "gas with, and no transaction ever sent.", gap=62)
    f.say(44, BLUE, "Every retention figure counts them as holders who "
                    "stayed.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    m = d["most"]
    f = Flow(300)
    f.say(48, TEXT, "The largest crowd measured", 700, gap=44)
    f.raw(txt(M, f.y + 30, 94, TEXT, f"{m['arrived']:,}", 700))
    f.y += 148
    f.say(36, SUB, f"addresses have received ${m['sym']}, three times the "
                   f"next token in the set. {m['holders']:,} of them still "
                   f"hold a balance.", gap=48)
    f.say(34, SUB, f"{m['share']*100:.1f}% of those holders cannot act on "
                   f"it either way.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    """Rate and population rank differently, which is the whole chart."""
    m, w = d["most"], d["worst"]
    f = Flow(286)
    f.say(48, TEXT, "The rate is not the story", 700, gap=40)
    for r, lab, col in ((w, "worst rate in the set", BLUE),
                        (m, "largest population", RED)):
        f.raw(txt(M, f.y + 20, 72, col,
                  f"{r['share']*100:.1f}%  =  {r['n']:,.0f}", 700))
        f.raw(txt(M, f.y + 64, 30, SUB, f"${r['sym']}, the {lab}"))
        f.y += 148
    f.gap(18)
    f.say(34, SUB, f"${w['sym']} has nearly all of its holders stuck and "
                   f"${m['sym']} has {m['n']/w['n']:.0f} times as many "
                   f"people.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    m, rows = d["most"], d["rows"]
    f = Flow(286)
    f.say(48, TEXT, "Across the whole set", 700, gap=44)
    f.raw(txt(M, f.y + 30, 96, RED, f"{d['total']:,.0f}", 700))
    f.y += 148
    f.say(36, SUB, f"wallets across {len(rows)} tokens are holding "
                   f"something they cannot move.", gap=48)
    f.say(34, SUB, f"{m['n']/d['total']*100:.0f}% of them are holding the "
                   f"same one. The same address can be stuck on more than "
                   f"one token and is counted on each.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc, m = d["doc"], d["most"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, f"That the count is exact. Mobility is sampled at "
                   f"{m['sampled']} holders a token, so each figure is an "
                   f"estimate and the chart carries its interval.", gap=44)
    f.say(36, SUB, "That everyone else can leave. It is a floor: a wallet "
                   "with a dollar of ETH it will never spend on gas counts "
                   "as perfectly mobile here.", gap=46)
    f.say(38, BLUE, "A stuck wallet is not a person who wants out. It is a "
                    "wallet with no way to act either way.", 700, gap=44)
    f.say(30, SUB, "Ethereum only. Nothing here is priced or advice.",
          gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    m, w = d["most"], d["worst"]
    if len(d["rows"]) < 20:
        raise SystemExit(f"  only {len(d['rows'])} tokens carry sampled "
                         f"mobility; the slides describe a field")
    # Slide three is the turn and needs the two orderings to disagree.
    if m["sym"] == w["sym"]:
        raise SystemExit(f"  ${m['sym']} now holds both the worst rate and "
                         f"the largest population; slide three sets them "
                         f"against each other")
    if m["n"] < 2 * w["n"]:
        raise SystemExit(f"  the largest population is only "
                         f"{m['n']/w['n']:.1f}x the worst rate's; slide "
                         f"three calls that a gap worth seeing")
    # Slide two says three times the next token, read off the field.
    second = max(r["arrived"] for r in d["rows"] if r["sym"] != m["sym"])
    if m["arrived"] < 3 * second:
        raise SystemExit(f"  ${m['sym']} is {m['arrived']/second:.1f}x the "
                         f"next crowd, not three; slide two says three")
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
