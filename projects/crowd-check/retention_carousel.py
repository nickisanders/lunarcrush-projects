#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the retention baseline.

Reads the same out/retention-baseline.json the chart does, so slides, chart and
post text cannot drift. Layout, wrapping and the overflow guard are imported
from carousel.py rather than copied.

Usage: python3 retention_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, GREEN, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools/out/retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "retention"
BLUE = "#388bfd"
ORDER = ["strk", "fet", "w", "ape", "ens", "aztec", "zama"]


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"holder retention, measured 19 october · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def bars(f: Flow, d: dict, key: str, highlight: bool, full: float = 0.5) -> None:
    """`full` is the value that fills the track, and a missing key stops the
    run. Skipping an absent value rendered a slide with no bars at all, which
    looks deliberate and published silently once already."""
    BW, BH = W - 2 * M - 180, 56
    for name in ORDER:
        if key not in d[name]:
            raise SystemExit(f"{name} has no '{key}' in retention-baseline.json")
        v = d[name][key]
        col = RED if (highlight and name == "zama") else (BLUE if highlight else SUB)
        w = min(BW * v / full, BW)
        f.raw(txt(M, f.y + 40, 32, TEXT, "$" + name.upper(), 700))
        f.raw(f'<rect x="{M+180}" y="{f.y+10}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+180}" y="{f.y+10}" width="{w:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        inside = w > 110
        f.raw(txt(M + 180 + w - (18 if inside else -14), f.y + 50, 34,
                  BG if inside else TEXT, f"{v*100:.0f}%", 700,
                  "end" if inside else "start"))
        f.y += BH + 18


def slide1(d) -> str:
    f = Flow(300)
    f.say(58, TEXT, "The more of a token's holders arrive in one month,", 700, gap=26)
    f.say(58, RED, "the fewer of them stay.", 700, gap=60)
    f.say(38, SUB, "Every transfer since each contract was deployed, joined to "
                   "who still holds today.", gap=0)
    return frame(1, f.svg())


def slide2(d) -> str:
    f = Flow(380)
    f.say(50, TEXT, "Retention", 700, gap=22)
    f.say(34, SUB, "Everyone who ever received the token, against who still "
                   "holds it.", gap=44)
    bars(f, d, "raw", highlight=False)
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(340)
    f.say(50, TEXT, "Concentration of arrival", 700, gap=22)
    f.say(34, SUB, "Share of all holders who first received the token in its "
                   "single biggest month.", gap=44)
    bars(f, d, "concentration", highlight=True, full=0.7)
    return frame(3, f.svg())


def slide4(d) -> str:
    z = d["zama"]["biggest_cohort"]
    f = Flow(400)
    f.say(50, TEXT, "The one that falls away", 700, gap=44)
    f.raw(txt(M, f.y + 20, 90, RED, f"{z['arrived']:,}", 700))
    f.raw(txt(M, f.y + 68, 34, SUB, f"addresses arrived in {z['month']}"))
    f.y += 140
    f.raw(txt(M, f.y + 20, 90, RED, f"{100-z['retention']*100:.0f}%", 700))
    f.raw(txt(M, f.y + 68, 34, SUB, "of them are gone"))
    f.y += 150
    f.say(36, SUB, "$ZAMA is the one token here scored manufactured on its social "
                   "data alone, at 98 out of 100.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    f = Flow(330)
    f.say(54, TEXT, "Seven tokens, r = -0.84.", 700, gap=50)
    f.say(42, SUB, "The tokens whose holders arrived all at once are the ones "
                   "with the fewest left.", gap=50)
    f.say(34, SUB, "The concentrated ones here are also the young ones, so part "
                   "of that gap is age rather than acquisition. $PEPE is still "
                   "counting.", gap=0)
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
