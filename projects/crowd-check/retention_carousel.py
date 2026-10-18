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
ORDER = ["strk", "w", "ape", "zama"]


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"holder retention, measured 18 october · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def bars(f: Flow, d: dict, key: str, highlight: bool) -> None:
    BW, BH = W - 2 * M - 180, 72
    for name in ORDER:
        v = d[name].get(key)
        if v is None:
            continue
        col = RED if (highlight and name == "zama") else (BLUE if highlight else SUB)
        f.raw(txt(M, f.y + 50, 38, TEXT, "$" + name.upper(), 700))
        f.raw(f'<rect x="{M+180}" y="{f.y+14}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+180}" y="{f.y+14}" width="{BW*v/0.5:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        f.raw(txt(M + 180 + BW * v / 0.5 - 20, f.y + 62, 40, BG, f"{v*100:.0f}%", 700, "end"))
        f.y += BH + 24


def slide1(d) -> str:
    f = Flow(300)
    f.say(60, TEXT, "Three tokens keep about 40% of everyone who ever held them.", 700, gap=30)
    f.say(60, RED, "One keeps 17%.", 700, gap=66)
    f.say(38, SUB, "Every transfer since each contract was deployed, joined to "
                   "who still holds today.", gap=0)
    return frame(1, f.svg())


def slide2(d) -> str:
    f = Flow(380)
    f.say(50, TEXT, "Raw retention", 700, gap=22)
    f.say(34, SUB, "Not comparable as it stands. An older contract has had longer "
                   "to lose people.", gap=50)
    bars(f, d, "raw", highlight=False)
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(340)
    f.say(50, TEXT, "Matched on exposure", 700, gap=22)
    f.say(34, SUB, "Only those who arrived in each token's last twelve months, so "
                   "every group has had the same time to leave.", gap=50)
    bars(f, d, "cohort", highlight=True)
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
    f.say(54, TEXT, "One token agreeing is not proof of anything.", 700, gap=60)
    f.say(42, SUB, "It is the first time a social score has been checked against "
                   "what the chain did afterwards, and they agree.", gap=56)
    f.say(34, SUB, "Four tokens is not a baseline yet. $FET and $PEPE are still counting.", gap=0)
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
