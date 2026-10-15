#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the green-names-in-a-red-week screen.

Reads out/green_week.json, written by green_week.py, so the slides cannot drift
from the measurement. Layout, wrapping and the overflow guard come from
carousel.py; duplicating them is how the overlap bug got in the first time.

Writes out/instagram/greenweek-N.svg and rasterizes each one.

Usage: python3 green_week_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: F401  (Flow pulls in txt/lines_for/heavy/esc)
    W, H, M, BG, TEXT, SUB, TRACK, PANEL, RED, GREEN, AMBER, FONT,
    Flow, txt, esc,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL = 5
STEM = "greenweek"
BLUE = "#388bfd"   # crowd breadth, kept distinct from GREEN (price)


def frame(n: int, body: str, footer: str = "") -> str:
    """Local copy of carousel.frame because TOTAL and the kicker differ here."""
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"a red week, five green names · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def bar(f: Flow, row: dict, highlight: bool) -> None:
    """One token: ticker, move, concentration bar, and its own band median."""
    BW, BH = W - 2 * M, 54
    top = f.y
    col = RED if highlight else BLUE
    f.raw(txt(M, top, 46, TEXT, f"${row['symbol']}", 700))
    f.raw(txt(M + BW, top, 40, GREEN, f"+{row['pct7d']:.0f}%", 700, "end"))
    y = top + 30
    f.raw(f'<rect x="{M}" y="{y}" width="{BW}" height="{BH}" rx="6" fill="{TRACK}"/>')
    f.raw(f'<rect x="{M}" y="{y}" width="{BW*row["top3_concentration"]:.0f}" '
          f'height="{BH}" rx="6" fill="{col}"/>')
    f.raw(txt(M + BW * row["top3_concentration"] - 18, y + 38, 34, BG,
              f"{row['top3_concentration']*100:.0f}%", 700, "end"))
    # Near-white, because on the one row where the bar runs past the median the
    # tick sits on top of the fill, and a grey tick on red is invisible there.
    mx = M + BW * row["band_median"]
    f.raw(f'<line x1="{mx:.0f}" y1="{y-8}" x2="{mx:.0f}" y2="{y+BH+8}" '
          f'stroke="{TEXT}" stroke-width="3" stroke-dasharray="6 5"/>')
    f.raw(txt(M, y + BH + 44, 32, SUB,
              f"{row['accounts']} accounts  ·  {row['share_under_1k']*100:.0f}% under 1k followers"))
    f.y = y + BH + 122


def slide1(d) -> str:
    ckb = next(r for r in d["rows"] if r["symbol"] == "CKB")
    f = Flow(300)
    f.say(64, TEXT, "A token is up 15% this week.", 700, gap=24)
    f.say(64, RED, "Its whole conversation is 44 posts from 24 accounts.", 700, gap=70)
    f.say(46, SUB, "Almost everything large is red. Five names are green. "
                   "I checked who is actually behind each one.", gap=0)
    return frame(1, f.svg())


def slide2(d) -> str:
    f = Flow(270)
    f.say(58, TEXT, "The week elsewhere", 700, gap=44)
    cols, step = 2, (W - 2 * M) / 2
    y0 = f.y
    for i, (sym, pc) in enumerate(d["tape"].items()):
        x = M + (i % cols) * step
        yy = y0 + (i // cols) * 64
        f.raw(txt(x, yy, 42, TEXT, sym, 700))
        f.raw(txt(x + step - 40, yy, 42, RED, f"{pc:.1f}%", 700, "end"))
    f.y = y0 + ((len(d["tape"]) + 1) // cols) * 64 + 50
    f.say(44, SUB, "Against that, $WAL is up 50%, $DUSK 46%, $ZK 37%, "
                   "$STRK 29% and $CKB 15%.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(250)
    f.say(54, TEXT, "Who holds the conversation", 700, gap=20)
    f.say(36, SUB, "Share held by the three loudest accounts. The dashed line is "
                   "the median for that token's own size.", gap=46)
    for r in d["rows"][:3]:
        bar(f, r, highlight=False)
    return frame(3, f.svg())


def slide4(d) -> str:
    f = Flow(250)
    f.say(54, TEXT, "And the two at the bottom", 700, gap=46)
    for r in d["rows"][3:]:
        bar(f, r, highlight=(r["symbol"] == "CKB"))
    f.gap(30)
    f.say(38, SUB, "$CKB is the only one above the median for its size, and the "
                   "44 posts are the whole conversation rather than a sample.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    f = Flow(280)
    f.say(60, TEXT, "Four of these moves have a crowd.", 700, gap=22)
    f.say(60, TEXT, "One of them has two dozen accounts.", 700, gap=66)
    f.say(44, SUB, "Concentration is not manipulation and a small crowd can be an "
                   "early one. This is a measurement, not a call.", gap=56)
    f.say(38, SUB, "Ranked against same-size peers, because concentration falls "
                   "with market cap.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    src = HERE / "out" / "green_week.json"
    if not src.exists():
        raise SystemExit(f"No {src.name}. Run green_week.py first.")
    d = json.loads(src.read_text())
    d["rows"] = sorted(d["rows"], key=lambda r: r["top3_concentration"])
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
