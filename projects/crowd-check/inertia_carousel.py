#!/usr/bin/env python3
"""Instagram carousel: holding still is usually a choice.

Reads retention-baseline.json at render time so slides, chart and post cannot
drift while the queue keeps adding tokens.

The two numbers on slide two are deliberately shown before the explanation.
75.4% and 99.4% look like the same fact, and the slide only works if the
reader sits with that for a beat before slide three splits them.

Slide five states the correlation and then withdraws it. That number is the
most quotable thing here and the least able to carry weight, so it never
appears without the figure that kills it.

Usage: python3 inertia_carousel.py
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
TOTAL, STEM = 5, "inertia"
BLUE = "#388bfd"
MIN_HOLDERS = 100


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"choice or paralysis · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        k = (d.get("dust") or {}).get("kinds") or {}
        m = d.get("mobility") or {}
        if "exited_leaving_dust" not in k or "immobile_share" not in m:
            continue
        if m["of_holders"] < MIN_HOLDERS:
            continue
        inert = k["untouched_small"] + k["untouched_large"]
        rows.append({"sym": name.upper(), "inert": inert,
                     "immobile": min(m["immobile_share"], inert),
                     "holders": m["of_holders"]})
    rows.sort(key=lambda r: -r["immobile"])
    return rows, doc["measured"]


def pearson(a, b):
    n = len(a); ma, mb = sum(a)/n, sum(b)/n
    c = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    d = (sum((x-ma)**2 for x in a)**0.5) * (sum((y-mb)**2 for y in b)**0.5)
    return c/d if d else 0


def slide1(rows, _) -> str:
    f = Flow(330)
    f.say(58, TEXT, "Two tokens that look identical", 700, gap=6)
    f.say(58, TEXT, "on every metric I had.", 700, gap=50)
    # "Three quarters of their holders" described only one of the pair: the
    # other is 99.4%, so the hook was overstating the similarity it sets up.
    f.say(44, SUB, "Most of their holders have never moved what they were "
                   "originally sent.", gap=62)
    f.say(44, BLUE, "They are nothing alike.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows, _) -> str:
    hi = max(rows, key=lambda r: r["inert"])
    lo = next(r for r in rows if r["sym"] == "MSTRX") if any(
        r["sym"] == "MSTRX" for r in rows) else rows[-1]
    f = Flow(300)
    f.say(48, TEXT, "Never moved what they were sent", 700, gap=52)
    for r, col in ((lo, TEXT), (hi, TEXT)):
        f.raw(txt(M, f.y + 20, 90, col, f"{r['inert']*100:.1f}%", 700))
        f.raw(txt(M, f.y + 70, 34, SUB, "$" + r["sym"]))
        f.y += 158
    f.gap(18)
    f.say(38, SUB, "On every holder metric I had a week ago, these two tokens "
                   "look the same.", gap=0)
    return frame(2, f.svg())


def slide3(rows, _) -> str:
    hi = max(rows, key=lambda r: r["inert"])
    lo = next((r for r in rows if r["sym"] == "MSTRX"), rows[-1])
    f = Flow(292)
    f.say(48, TEXT, "Could they have done otherwise?", 700, gap=40)
    f.say(34, SUB, "An address with no ETH that has never sent a transaction "
                   "cannot pay gas, so it cannot sell, vote or leave.", gap=56)
    for r, col in ((lo, BLUE), (hi, RED)):
        f.raw(txt(M, f.y + 20, 82, col, f"{r['immobile']*100:.1f}%", 700))
        f.raw(txt(M, f.y + 66, 32, SUB, f"of ${r['sym']} holders cannot act at all"))
        f.y += 146
    f.gap(12)
    f.say(34, SUB, "Two RPC calls answer it. Almost nobody asks.", gap=0)
    return frame(3, f.svg())


def slide4(rows, _) -> str:
    f = Flow(276)
    f.say(46, TEXT, "Ten tokens, split the same way", 700, gap=16)
    f.say(30, SUB, "Red could not act. Blue could, and chose not to.", gap=42)
    BW, BH = W - 2 * M - 190, 46
    for r in rows:
        stuck, free = BW * r["immobile"], BW * (r["inert"] - r["immobile"])
        f.raw(txt(M, f.y + 32, 25, SUB, "$" + r["sym"]))
        f.raw(f'<rect x="{M+190}" y="{f.y+6}" width="{BW}" height="{BH}" rx="6" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+190}" y="{f.y+6}" width="{stuck:.1f}" height="{BH}" rx="6" fill="{RED}"/>')
        f.raw(f'<rect x="{M+190+stuck:.1f}" y="{f.y+6}" width="{free:.1f}" height="{BH}" fill="{BLUE}"/>')
        f.y += BH + 12
    return frame(4, f.svg())


def slide5(rows, measured) -> str:
    gaps = [r["inert"] - r["immobile"] for r in rows[1:]]
    full = pearson([r["immobile"] for r in rows], [r["inert"] for r in rows])
    sub = rows[1:]
    drop = pearson([r["immobile"] for r in sub], [r["inert"] for r in sub])
    f = Flow(286)
    f.say(48, TEXT, "Inertia is usually a choice", 700, gap=44)
    f.say(36, SUB, f"On nine of the ten, between {min(gaps)*100:.0f} and "
                   f"{max(gaps)*100:.0f} percent of the holders who never moved "
                   f"anything had the gas and the history to do it.", gap=40)
    f.say(38, TEXT, "They just didn't.", 700, gap=48)
    f.say(34, SUB, f"The two measures correlate at {full:+.2f} across all ten "
                   f"and {drop:+.2f} once the outlier comes out, so they are "
                   f"not the same thing being counted twice.", gap=44)
    f.say(30, SUB, "Inertia read from every holder, mobility sampled per token. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(), f"measured {measured} · github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows, measured = load()
    if not rows:
        raise SystemExit("  no token carries both measures yet")
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
