#!/usr/bin/env python3
"""Instagram carousel: how much of a holder count could actually act.

Reads retention-baseline.json at render time, so slides and chart cannot
drift while the scan queue keeps adding tokens.

Slide four is the whole argument. Without the rest of the set, "96% of this
token's holders are dead addresses" reads as a claim about crypto in general
and gets answered with "every token has dead wallets". The strip shows the
median is 5.2% and that one token sits alone past every other, which is the
difference between an anecdote and a measurement with a reference.

Slide five carries the gameability point rather than the opening, because it
is an argument about incentives and it only lands once the reader has seen
that normal tokens do not look like this.

Usage: python3 mobile_carousel.py
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
TOTAL, STEM = 5, "mobile"
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
            f'{txt(M, 102, 29, SUB, f"can your holders act? · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        m = d.get("mobility") or {}
        if "immobile_share" not in m or m["of_holders"] < MIN_HOLDERS:
            continue
        rows.append({"sym": name.upper(), "share": m["immobile_share"],
                     "holders": m["of_holders"], "act": m["mobile_holders_est"],
                     "ci": m["immobile_ci"], "n": m["sampled"],
                     "ret": d["raw"]})
    rows.sort(key=lambda r: -r["share"])
    return rows, doc["measured"]


def slide1(rows, _) -> str:
    f = Flow(330)
    f.say(58, TEXT, "A holder count cannot tell you", 700, gap=6)
    f.say(58, TEXT, "whether the holder exists.", 700, gap=60)
    f.say(42, SUB, "So I checked whether they could do anything at all.", gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows, _) -> str:
    f = Flow(292)
    f.say(50, TEXT, "What the check is", 700, gap=42)
    f.say(38, SUB, "An address with no ETH that has never sent a transaction "
                   "cannot pay gas.", gap=50)
    f.say(40, TEXT, "It cannot sell.", 700, gap=22)
    f.say(40, TEXT, "It cannot vote or stake.", 700, gap=22)
    f.say(40, TEXT, "It cannot leave.", 700, gap=50)
    f.say(34, SUB, "Two calls per address answer it. Almost nobody asks.", gap=0)
    return frame(2, f.svg())


def slide3(rows, _) -> str:
    t = rows[0]
    f = Flow(300)
    f.say(50, TEXT, "One token in the set", 700, gap=46)
    f.raw(txt(M, f.y + 20, 96, TEXT, f"{t['holders']:,}", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "holders reported"))
    f.y += 162
    f.raw(txt(M, f.y + 20, 96, RED, f"{t['act']:,}", 700))
    f.raw(txt(M, f.y + 72, 34, SUB, "that could actually act"))
    f.y += 170
    f.say(38, TEXT, f"At {t['ret']*100:.1f}% it also has the best retention "
                    f"I have measured.", 700, gap=24)
    f.say(36, RED, "Nobody can leave.", 700, gap=0)
    return frame(3, f.svg())


def slide4(rows, _) -> str:
    med = st.median(r["share"] for r in rows)
    f = Flow(286)
    f.say(48, TEXT, "Is that just how crypto is?", 700, gap=40)
    f.say(34, SUB, f"The same measure on every token with {MIN_HOLDERS}+ "
                   f"holders, {len(rows)} so far. Median {med*100:.1f}%.", gap=76)
    ax_l, ax_r = M + 10, W - M - 10
    y = f.y
    f.raw(f'<line x1="{ax_l}" y1="{y}" x2="{ax_r}" y2="{y}" stroke="{TRACK}" stroke-width="3"/>')
    for pct in (0, 50, 100):
        x = ax_l + (ax_r - ax_l) * pct / 100
        f.raw(f'<line x1="{x:.0f}" y1="{y-9}" x2="{x:.0f}" y2="{y+9}" '
              f'stroke="{TRACK}" stroke-width="3"/>')
        f.raw(txt(x, y + 46, 26, SUB, f"{pct}%", 400, "middle"))
    for r in rows:
        x = ax_l + (ax_r - ax_l) * r["share"]
        top = r is rows[0]
        f.raw(f'<circle cx="{x:.1f}" cy="{y}" r="{13 if top else 10}" '
              f'fill="{RED if top else BLUE}" fill-opacity="{1 if top else 0.5}"/>')
    f.raw(txt(ax_l + (ax_r - ax_l) * rows[0]["share"], y - 30, 27, RED,
              "this one", 700, "middle"))
    f.y = y + 124
    f.say(34, TEXT, "Dead addresses are an ordinary small part of any "
                    "distribution. One token is not in that distribution.", 700, gap=0)
    return frame(4, f.svg())


def slide5(rows, measured) -> str:
    f = Flow(286)
    f.say(48, TEXT, "Why this is worth watching", 700, gap=42)
    f.say(36, SUB, "Generating addresses is free. The only cost is the gas to "
                   "send tokens to them.", gap=46)
    f.say(36, TEXT, "Do it and the holder count rises, retention rises for "
                    "good because those addresses can never leave, and sell "
                    "pressure stays at zero.", 700, gap=46)
    f.say(34, BLUE, "On every public dashboard that looks like growth.", 700, gap=44)
    f.say(30, SUB, "Balances read for every holder. Mobility sampled per token. "
                   "Nothing here is advice, and no token is named.", gap=0)
    return frame(5, f.svg(), f"measured {measured} · github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows, measured = load()
    if not rows:
        raise SystemExit("  no token carries a mobility figure yet")
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
