#!/usr/bin/env python3
"""Instagram carousel: retention counts who stayed, not who ever did anything.

Reads the same retention-baseline.json the chart does, so slides and chart
cannot drift. Everything is computed at render time because the scan queue
finishes roughly a token an hour and every figure here goes stale fast.

Slide three carries one number per token rather than the four-way stack from
the chart. At 1080 wide the stack's narrow segments lose their labels, and the
share who never moved is the claim the post actually makes.

The correlation is held back to slide five on purpose. It is the most
quotable number here and the one least able to carry weight, so it arrives
already qualified rather than as a headline someone screenshots.

Usage: python3 residue_carousel.py
"""

import json
import statistics as st
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "residue"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"what retention misses · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        k = (d.get("dust") or {}).get("kinds") or {}
        if "exited_leaving_dust" not in k:
            continue
        rows.append({"sym": name.upper(), "ret": d["raw"], "held": d["kept"],
                     "arrived": d["arrived"],
                     "inert": k["untouched_small"] + k["untouched_large"]})
    rows.sort(key=lambda r: -r["ret"])
    return rows, doc["measured"]


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    d = (sum((x - ma) ** 2 for x in a) ** 0.5) * (sum((y - mb) ** 2 for y in b) ** 0.5)
    return cov / d if d else 0


def slide1(rows, _) -> str:
    f = Flow(300)
    f.say(58, TEXT, "Retention tells you who is still there.", 700, gap=50)
    f.say(44, SUB, "It says nothing about whether they ever moved.", gap=64)
    f.say(46, BLUE, "Those turn out to be very different questions.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows, _) -> str:
    f = Flow(286)
    f.say(50, TEXT, "A wallet holding $3 of a token", 700, gap=40)
    f.say(38, SUB, "got there one of two ways.", gap=58)
    f.say(40, TEXT, "Someone was handed an airdrop and never touched it.", 700, gap=40)
    f.say(40, TEXT, "Someone bought a real position, rode it down, and sold out "
                    "leaving a tail.", 700, gap=56)
    f.say(36, SUB, "One is a wallet that never really showed up, the other "
                   "is a holder who showed up and left, and a holder count "
                   "reports both the same way.", gap=0)
    return frame(2, f.svg())


def slide3(rows, _) -> str:
    f = Flow(282)
    f.say(50, TEXT, "Never moved what they were sent", 700, gap=18)
    f.say(32, SUB, f"Share of current holders, {len(rows)} tokens, sorted by "
                   f"retention.", gap=44)
    BW, BH = W - 2 * M - 250, 54
    for r in rows:
        v = r["inert"]
        w = max(BW * v, 3)
        col = RED if v >= 0.9 else BLUE
        f.raw(txt(M, f.y + 38, 27, SUB, f"kept {r['ret']*100:.0f}%"))
        f.raw(f'<rect x="{M+250}" y="{f.y+8}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+250}" y="{f.y+8}" width="{w:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        inside = w > 130
        f.raw(txt(M + 250 + w - (18 if inside else -14), f.y + 46, 30,
                  BG if inside else TEXT, f"{v*100:.1f}%", 700,
                  "end" if inside else "start"))
        f.y += BH + 14
    return frame(3, f.svg())


def slide4(rows, _) -> str:
    t = rows[0]
    f = Flow(300)
    f.say(52, TEXT, "The best retention in the set", 700, gap=48)
    f.raw(txt(M, f.y + 20, 98, TEXT, f"{t['ret']*100:.1f}%", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "of everyone who ever held it, still holding"))
    f.y += 162
    f.raw(txt(M, f.y + 20, 98, RED, f"{t['inert']*100:.1f}%", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "of those have never moved a single token"))
    f.y += 170
    f.say(38, TEXT, "That project could truthfully say it retains three quarters "
                    "of its community.", 700, gap=36)
    f.say(38, RED, "Almost none of that community has done anything.", 700, gap=0)
    return frame(4, f.svg())


def slide5(rows, measured) -> str:
    inert = [r["inert"] for r in rows]
    full = pearson([r["ret"] for r in rows], inert)
    sub = [r for r in rows if r is not rows[0]]
    drop = pearson([r["ret"] for r in sub], [r["inert"] for r in sub])
    f = Flow(292)
    f.say(48, TEXT, "What I will and will not claim", 700, gap=44)
    f.say(36, SUB, f"Retention appears to climb as engagement falls. Across "
                   f"{len(rows)} tokens that correlation is {full:+.2f}, which "
                   f"sounds like a finding. Drop the one extreme token and it "
                   f"falls to {drop:+.2f}.", gap=46)
    f.say(38, TEXT, "I am not claiming it yet.", 700, gap=46)
    f.say(36, BLUE, f"What holds up: a median {st.median(inert)*100:.1f}% of a "
                    f"holder count is people who were handed something once and "
                    f"never came back.", 700, gap=40)
    f.say(30, SUB, "Every balance and every receipt read off the chain. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(), f"measured {measured} · github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows, measured = load()
    if not rows:
        raise SystemExit("  no token carries the split yet")
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
