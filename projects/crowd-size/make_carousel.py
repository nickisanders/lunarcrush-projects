#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the crowd-size finding.

Reads out/report.json, so the slides always match the last `npm run daily`.
Note this is a 24h snapshot: the exact counts move day to day, which is why
nothing here is hardcoded.

Writes out/instagram/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from math import log10
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
GREEN, AMBER, RED, ORANGE = "#3fb950", "#d29922", "#f85149", "#f7931a"
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


def color(n: int) -> str:
    return GREEN if n >= 50 else AMBER if n >= 15 else RED


def bars(coins, top: int, width: int = 560, row_h: int = 62) -> str:
    """Log scale: the range runs from single digits to hundreds, and a linear
    axis would flatten every narrow coin into the same stub."""
    x0 = M + 150
    hi = log10(max(c["accountsToHalf"] for c in coins))
    out = []
    for i, c in enumerate(coins):
        y = top + i * row_h
        n = c["accountsToHalf"]
        w = max(8, log10(max(n, 1.2)) / hi * width)
        col = color(n)
        out.append(txt(x0 - 22, y + 11, 32, TEXT, f'${c["symbol"]}', 700, "end"))
        out.append(f'<rect x="{x0}" y="{y - 16}" width="{w:.0f}" height="34" rx="8" fill="{col}"/>')
        out.append(txt(int(x0 + w + 18), y + 11, 30, col, str(n), 700))
    return "\n".join(out)


def slide1(widest, narrowest) -> str:
    return frame(1, f"""
{txt(M, 330, 44, SUB, "How many accounts does")}
{txt(M, 386, 44, SUB, "it take to make a coin")}
{txt(M, 442, 44, SUB, "look popular?")}
{txt(M, 590, 40, TEXT, f'${widest["symbol"]}', 700)}
{txt(M, 690, 118, GREEN, str(widest["accountsToHalf"]), 800)}
{txt(M, 810, 40, TEXT, f'${narrowest["symbol"]}', 700)}
{txt(M, 910, 118, RED, str(narrowest["accountsToHalf"]), 800)}
{txt(M, 990, 32, SUB, "same day, same method, same question")}
""", "swipe")


def slide2(sample) -> str:
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "Accounts needed to", 800)}
{txt(M, 310, 50, TEXT, "make half the talk", 800)}
{txt(M, 370, 30, SUB, "log scale. green is a real crowd, red is a handful.")}
{bars(sample, 470)}
""", "24h snapshot of every coin over $1B")


def slide3(narrowest, widest) -> str:
    return frame(3, f"""
{txt(M, 250, 50, TEXT, "What that means", 800)}
{txt(M, 310, 50, TEXT, "in practice", 800)}
{txt(M, 430, 34, RED, f'On ${narrowest["symbol"]}, one account is', 700)}
{txt(M, 520, 108, RED, f'{narrowest["top1Share"]*100:.0f}%', 800)}
{txt(M, 570, 32, SUB, "of everything said about it.")}
{txt(M, 620, 32, SUB, f'Three accounts are {narrowest["top3Share"]*100:.0f}%.')}
{txt(M, 730, 34, GREEN, f'On ${widest["symbol"]}, the single', 700)}
{txt(M, 776, 34, GREEN, "loudest account is", 700)}
{txt(M, 866, 108, GREEN, f'{widest["top1Share"]*100:.0f}%', 800)}
{txt(M, 950, 32, SUB, "Same market. Completely different thing.")}
""")


def slide4(repeats, n_coins) -> str:
    top = repeats[0]
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "And it is largely", 800)}
{txt(M, 310, 50, TEXT, "the same people", 800)}
{txt(M, 440, 118, ORANGE, str(len(repeats)), 800)}
{txt(M, 500, 36, TEXT, "accounts sit in the top 10 of", 700)}
{txt(M, 548, 36, TEXT, "more than one coin at once", 700)}
{txt(M, 660, 34, SUB, "One of them, " + esc(top["name"]) + ", is in")}
{txt(M, 752, 68, ORANGE, f'{len(top["coins"])} of them', 800)}
{txt(M, 856, 36, TEXT, "So the tail of this market is not", 700)}
{txt(M, 904, 36, TEXT, f'{n_coins} separate communities.', 700)}
{txt(M, 952, 36, TEXT, "It is one rotating cast, moving", 700)}
{txt(M, 1000, 36, TEXT, "ticker to ticker.", 700)}
""")


def slide5(median_n) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "The takeaway", 800)}
{txt(M, 370, 36, SUB, "Median across every coin I could measure:")}
{txt(M, 460, 108, TEXT, str(median_n), 800)}
{txt(M, 510, 34, SUB, "accounts cover half the conversation.")}
{txt(M, 610, 34, SUB, "What this does NOT show is whether those")}
{txt(M, 656, 34, SUB, "accounts are paid, automated, or just very")}
{txt(M, 702, 34, SUB, "online. That is not in the data and I am")}
{txt(M, 748, 34, SUB, "not going to pretend it is.")}
{txt(M, 850, 40, ORANGE, "Next time you see social volume", 700)}
{txt(M, 898, 40, ORANGE, "exploding, do not ask how loud.", 700)}
{txt(M, 962, 46, TEXT, "Ask how many.", 800)}
{txt(M, 1060, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    r = json.loads((HERE / "out" / "report.json").read_text())
    known = [c for c in r["coins"] if c["accountsToHalf"] is not None]
    widest, narrowest = known[0], known[-1]
    median_n = sorted(c["accountsToHalf"] for c in known)[len(known) // 2]
    # A spread across the whole range rather than only the extremes.
    sample = known[:3] + known[len(known) // 2 - 1 : len(known) // 2 + 1] + known[-4:]

    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(widest, narrowest), slide2(sample), slide3(narrowest, widest),
              slide4(r["repeats"], len(known)), slide5(median_n)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides  ({widest['symbol']} {widest['accountsToHalf']} vs "
          f"{narrowest['symbol']} {narrowest['accountsToHalf']}, median {median_n})")


if __name__ == "__main__":
    main()
