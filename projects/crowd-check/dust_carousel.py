#!/usr/bin/env python3
"""Instagram carousel: what a holder count is actually counting.

Reads the same out/*-wallets.json the dust chart does, so slides and chart
cannot drift. Layout, wrapping and the overflow guard come from carousel.py.

The reveal is held to slide four. $BLUR's 51,179 holders against its 1,240
above $100 lands harder after the reader has seen the ranking than as an
opening claim.

Usage: python3 dust_carousel.py
"""

import glob
import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "dust"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"what a holder count counts · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def caption(f: Flow, size: int, fill: str, text: str, weight: int = 400) -> None:
    """Flow.say puts the first baseline at f.y, so glyphs rise into whatever
    was drawn last. Drop by the ascent before writing under bars."""
    f.gap(int(size * 0.82) + 20)
    f.say(size, fill, text, weight, gap=0)


def load():
    rows = []
    for p in sorted(glob.glob(str(SRC / "*-wallets.json"))):
        d = json.loads(Path(p).read_text())
        h = d.get("holders_headline") or 0
        if not h:
            continue
        b = d.get("buckets") or {}
        k = [x for x in b if "under" in x]
        rows.append({"sym": d["symbol"], "holders": h, "big": d.get("with_100_usd") or 0,
                     "dust": b[k[0]] if k else 0})
    for r in rows:
        r["big_s"] = r["big"] / r["holders"]
        r["dust_s"] = r["dust"] / r["holders"]
    rows.sort(key=lambda r: -r["big_s"])
    return rows


def bars(f: Flow, rows, value, label, hot) -> None:
    BW, BH = W - 2 * M - 200, 56
    for r in rows:
        v = value(r)
        w = max(BW * v, 3)
        col = RED if r["sym"] in hot else BLUE
        f.raw(txt(M, f.y + 40, 31, TEXT, "$" + r["sym"], 700))
        f.raw(f'<rect x="{M+200}" y="{f.y+10}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+200}" y="{f.y+10}" width="{w:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        inside = w > 130
        f.raw(txt(M + 200 + w - (18 if inside else -14), f.y + 50, 34,
                  BG if inside else TEXT, label(v), 700, "end" if inside else "start"))
        f.y += BH + 18


def slide1(rows) -> str:
    f = Flow(300)
    f.say(58, TEXT, "Every project quotes a holder count.", 700, gap=54)
    f.say(44, SUB, "None of them say what those holders actually hold.", gap=60)
    f.say(46, BLUE, "So I read the balance of every one.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows) -> str:
    f = Flow(290)
    f.say(50, TEXT, "Holders with $100 or more", 700, gap=20)
    f.say(32, SUB, "Eight tokens, every holder, not a sample.", gap=46)
    bars(f, rows, lambda r: r["big_s"], lambda v: f"{v*100:.1f}%", ("APE", "BLUR"))
    return frame(2, f.svg())


def slide3(rows) -> str:
    f = Flow(290)
    f.say(50, TEXT, "Holders with under $1", 700, gap=20)
    f.say(32, SUB, "The same wallets, the other end of the scale.", gap=46)
    bars(f, rows, lambda r: r["dust_s"], lambda v: f"{v*100:.1f}%", ("APE", "BLUR"))
    return frame(3, f.svg())


def slide4(rows) -> str:
    b = next(r for r in rows if r["sym"] == "BLUR")
    f = Flow(320)
    f.say(52, TEXT, "Put that another way", 700, gap=54)
    f.raw(txt(M, f.y + 20, 96, TEXT, f"{b['holders']:,}", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "wallets hold $BLUR"))
    f.y += 160
    f.raw(txt(M, f.y + 20, 96, RED, f"{b['big']:,}", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "of them hold more than $100"))
    f.y += 168
    f.say(40, TEXT, "A holder count treats a wallet with eleven cents exactly "
                    "like one with eleven thousand dollars.", 700, gap=0)
    return frame(4, f.svg())


def slide5(rows) -> str:
    best = rows[0]
    f = Flow(300)
    f.say(52, TEXT, "The ranking tracks nothing obvious.", 700, gap=48)
    f.say(38, SUB, f"${best['sym']} leads at {best['big_s']*100:.1f}% and $APE has the most "
                   f"holders of any token here, 195,278, with the second-worst quality. "
                   f"Size and age do not predict it.", gap=52)
    f.say(34, SUB, "Worth stating: these are dollar thresholds, so a token that has "
                   "fallen hard shows more dust for that reason alone.", gap=44)
    f.say(30, SUB, "Balances read off the chain. Nothing here is advice.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows = load()
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{STEM}-{i}.svg"
        p.write_text(fn(rows))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
