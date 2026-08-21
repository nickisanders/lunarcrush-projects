#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the price-context finding.

Reads out/price-context.csv, so the numbers always match the last run of
price_context.py. The day-of market figures on the first and last slides are
not in that CSV and are passed in, since they describe the day you post.

Writes out/instagram-price-context/slide-N.svg (kept apart from the main
backtest carousel in out/instagram/). Rasterize with sharp:
    node -e "const s=require('../hype-detector/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram-price-context/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram-price-context/slide-${i}.png`))"

Usage:
    python3 price_context_carousel.py --btc 7.6 --green-share 88 --scanned 1000 --candidates 41
"""

import argparse
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-price-context"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
GREEN, GREY, ORANGE = "#3fb950", "#6e7681", "#f7931a"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """librsvg drops word spaces at font-weight >= 700, so space words by hand.
    The % glyph overhangs its advance width and needs a wider gap after it."""
    words = text.split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        factor = 0.45 if prev.endswith("%") else 0.30
        parts.append(f'<tspan dx="{size * factor:.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x, y, size, fill, content, weight=400, anchor="start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in content else esc(content)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>')


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 110, 28, SUB, footer) if footer else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{txt(M, 102, 30, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}
{body}
{f}
{dots}
</svg>"""


def bars(rows, base_rate: float, top: int = 560, ch: int = 330) -> str:
    """Five buckets. Colour marks significance, not height: three of these
    cannot be told apart from an ordinary day and must not read as edges."""
    bw, gap, x0, top_val = 130, 62, M, 0.55

    def y(v: float) -> float:
        return top + ch - v / top_val * ch

    out = [f'<line x1="{x0 - 26}" y1="{y(base_rate):.0f}" x2="{W - 60}" y2="{y(base_rate):.0f}" '
           f'stroke="{GRID}" stroke-width="2" stroke-dasharray="6 7"/>',
           txt(x0 - 36, int(y(base_rate)) + 8, 22, SUB, f"{base_rate:.0%}", 400, "end")]
    for i, r in enumerate(rows):
        x = x0 + i * (bw + gap)
        color = GREEN if r["p"] < 0.05 else GREY
        out += [
            f'<rect x="{x}" y="{y(r["rate"]):.0f}" width="{bw}" height="{top + ch - y(r["rate"]):.0f}" rx="8" fill="{color}"/>',
            txt(int(x + bw / 2), int(y(r["rate"])) - 16, 32, color, f'{r["rate"]:.0%}', 700, "middle"),
            txt(int(x + bw / 2), top + ch + 40, 23, TEXT, r["label"], 400, "middle"),
            txt(int(x + bw / 2), top + ch + 74, 20, SUB, f'n={r["n"]}', 400, "middle"),
        ]
    return "\n".join(out)


def slide1(a) -> str:
    return frame(1, f"""
{txt(M, 320, 54, TEXT, f"Bitcoin +{a.btc}%.", 800)}
{txt(M, 384, 54, TEXT, f"{a.green_share}% of major", 800)}
{txt(M, 448, 54, TEXT, "coins green.", 800)}
{txt(M, 560, 42, GREEN, "That rally is real.", 700)}
{txt(M, 616, 34, SUB, "I am not arguing with the prices.")}
{txt(M, 730, 40, TEXT, "I measure the other number:", 700)}
{txt(M, 828, 78, ORANGE, "social volume", 800)}
{txt(M, 888, 34, SUB, "how many people are posting. that is all.")}
{txt(M, 972, 34, SUB, "Here is whether it has ever told you")}
{txt(M, 1018, 34, SUB, "anything useful on a day like this.")}
""", "swipe")


def slide2(rows, base_rate) -> str:
    flat = next(r for r in rows if r["label"].startswith("flat"))
    rose = next(r for r in rows if r["label"] == "rose >5%")
    return frame(2, f"""
{txt(M, 240, 50, TEXT, "Same spike. One", 800)}
{txt(M, 300, 50, TEXT, "difference.", 800)}
{txt(M, 400, 32, SUB, "how often the coin beat Bitcoin over 3 days")}
{txt(M, 500, 34, GREEN, "talk spiked while price was FLAT", 700)}
{txt(M, 596, 96, GREEN, f'{flat["rate"]:.0%}', 800)}
{txt(M, 720, 34, GREY, "talk spiked AFTER price ran 5%+", 700)}
{txt(M, 816, 96, GREY, f'{rose["rate"]:.0%}', 800)}
{txt(M, 920, 34, SUB, "an ordinary, nothing-happening coin-day")}
{txt(M, 1000, 60, SUB, f"{base_rate:.0%}", 800)}
""", "the second one is not a weaker signal. it is none.")


def slide3(rows, base_rate) -> str:
    return frame(3, f"""
{txt(M, 250, 50, TEXT, "All five buckets", 800)}
{txt(M, 320, 30, SUB, "1,218 spam-filtered social volume spikes,")}
{txt(M, 362, 30, SUB, "split by what price did that same day")}
{bars(rows, base_rate)}
{txt(M, 1090, 30, SUB, "green = tells you something. grey = does not.")}
""", "only the flat bar clears its own significance test")


def slide4() -> str:
    return frame(4, f"""
{txt(M, 250, 52, TEXT, "Why", 800)}
{txt(M, 370, 40, TEXT, "Talk that shows up AFTER a", 700)}
{txt(M, 422, 40, TEXT, "price move is people reacting", 700)}
{txt(M, 474, 40, TEXT, "to the candle.", 700)}
{txt(M, 540, 34, SUB, "It describes something that already happened.")}
{txt(M, 640, 40, TEXT, "Talk that shows up BEFORE a", 700)}
{txt(M, 692, 40, TEXT, "move is the only kind that can", 700)}
{txt(M, 744, 40, TEXT, "hold something new.", 700)}
{txt(M, 850, 38, ORANGE, "So the days your feed is wall to", 700)}
{txt(M, 898, 38, ORANGE, "wall with trending tickers are the", 700)}
{txt(M, 946, 38, ORANGE, "days trending is worth the least.", 700)}
{txt(M, 1030, 34, SUB, "Today is exactly that day.")}
""")


def slide5(a) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "What my scanner", 800)}
{txt(M, 310, 50, TEXT, "found today", 800)}
{txt(M, 430, 110, TEXT, "0", 800)}
{txt(M, 500, 34, SUB, f"out of {a.scanned:,} coins scanned. only {a.candidates} were even")}
{txt(M, 546, 34, SUB, "candidates, because almost nothing is flat.")}
{txt(M, 622, 32, SUB, "On a huge green day it has nothing to say,")}
{txt(M, 664, 32, SUB, "and that is it working correctly.")}
{txt(M, 760, 36, TEXT, "To be clear about the claim:", 700)}
{txt(M, 816, 34, SUB, "I am NOT saying the rally is fake or about to")}
{txt(M, 862, 34, SUB, "reverse. The price data is real and I have no")}
{txt(M, 908, 34, SUB, "forecast for it. I am saying today's social")}
{txt(M, 954, 34, SUB, "volume is a reaction to a move that already")}
{txt(M, 1000, 34, SUB, "happened, so it is not evidence about tomorrow.")}
{txt(M, 1080, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--btc", type=float, required=True, help="BTC 24h %% change today")
    ap.add_argument("--green-share", type=int, required=True, help="%% of coins over $1B up on 24h")
    ap.add_argument("--scanned", type=int, default=1000)
    ap.add_argument("--candidates", type=int, required=True, help="coins that passed the flat-price filter")
    a = ap.parse_args()

    df = pd.read_csv(HERE / "out" / "price-context.csv")
    rows = df.to_dict("records")
    # The baseline is the ordinary coin-day rate the gaps are measured against.
    base_rate = rows[0]["rate"] - rows[0]["diff"]

    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(a), slide2(rows, base_rate), slide3(rows, base_rate), slide4(), slide5(a)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}  (baseline {base_rate:.1%})")


if __name__ == "__main__":
    main()
