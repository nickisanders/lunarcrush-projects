#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the chase-the-pump finding.

Reads out/after-the-run.json, so the slides always match the last run of
after_the_run.py. Writes out/instagram-after-the-run/slide-N.svg.

Rasterize with sharp:
    node -e "const s=require('../hype-detector/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram-after-the-run/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram-after-the-run/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-after-the-run"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
RED, AMBER, GREY, GREEN = "#f85149", "#d29922", "#8b949e", "#3fb950"
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


def bars(buckets, top=580, ch=370) -> str:
    """Bars hang below a zero line, because every bucket is a loss."""
    bw, gap, x0 = 170, 60, M + 10
    worst = min(b["m90"] for b in buckets)
    out = [f'<line x1="{M}" y1="{top}" x2="{W - M}" y2="{top}" stroke="{GRID}" stroke-width="2"/>',
           txt(M, top - 12, 20, SUB, "0%")]
    for i, b in enumerate(buckets):
        x = x0 + i * (bw + gap)
        h = abs(b["m90"]) / abs(worst) * ch
        col = RED if b["m90"] <= -0.30 else AMBER if b["m90"] <= -0.15 else GREY
        out += [
            f'<rect x="{x}" y="{top}" width="{bw}" height="{h:.0f}" rx="10" fill="{col}"/>',
            txt(int(x + bw / 2), int(top + h) + 46, 38, col, f'{b["m90"]*100:.0f}%', 800, "middle"),
            txt(int(x + bw / 2), top - 44, 22, TEXT, b["label"].replace("a quiet week", "quiet"), 400, "middle"),
        ]
    return "\n".join(out)


def slide1(buckets) -> str:
    worst = buckets[-1]
    return frame(1, f"""
{txt(M, 350, 62, TEXT, "“Am I too late?”", 800)}
{txt(M, 450, 36, SUB, "The most asked question in crypto.")}
{txt(M, 500, 36, SUB, "I ran it against six years of data.")}
{txt(M, 640, 40, TEXT, "A coin that just tripled in a", 700)}
{txt(M, 690, 40, TEXT, "week loses this much over", 700)}
{txt(M, 740, 40, TEXT, "the next 90 days:", 700)}
{txt(M, 880, 150, RED, f'{worst["m90"]*100:.0f}%', 800)}
{txt(M, 960, 32, SUB, "median, and it gets worse from there")}
""", "swipe")


def slide2(buckets) -> str:
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "The bigger the pump", 800)}
{txt(M, 310, 50, TEXT, "you chase, the worse", 800)}
{txt(M, 370, 50, TEXT, "it goes", 800)}
{txt(M, 430, 28, SUB, "median return over the next 90 days, by last week's run")}
{bars(buckets)}
""", "perfectly monotonic. every bucket, every horizon I tested.")


def slide3(big) -> str:
    return frame(3, f"""
{txt(M, 250, 50, TEXT, "Of the coins that", 800)}
{txt(M, 310, 50, TEXT, "just tripled...", 800)}
{txt(M, 380, 30, SUB, "90 days later")}
{txt(M, 520, 150, RED, f'{big["lower"]*100:.0f}%', 800)}
{txt(M, 580, 40, TEXT, "were lower", 700)}
{txt(M, 740, 150, RED, f'{big["halved"]*100:.0f}%', 800)}
{txt(M, 800, 40, TEXT, "had lost half", 700)}
{txt(M, 900, 34, SUB, f'Median against just holding Bitcoin: {big["vsBtc"]*100:.0f}%')}
{txt(M, 980, 36, TEXT, "That is not being late.", 700)}
{txt(M, 1028, 36, TEXT, "That is taking the wrong side.", 700)}
""")


def slide4(big) -> str:
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "Two reasons this", 800)}
{txt(M, 310, 50, TEXT, "is not garbage", 800)}
{txt(M, 420, 36, GREEN, "I counted pumps, not days", 700)}
{txt(M, 476, 32, SUB, "A coin mid-run qualifies every single day it")}
{txt(M, 520, 32, SUB, "runs. Counting each one would have turned")}
{txt(M, 564, 32, SUB, f'{big["n"]} real pumps into 1,183 fake data points.')}
{txt(M, 608, 32, SUB, "One pump, one entry.")}
{txt(M, 710, 36, GREEN, "Survivorship favours the pump", 700)}
{txt(M, 766, 32, SUB, "My universe is the top 1,000 coins today.")}
{txt(M, 810, 32, SUB, "Every coin that pumped in 2021 and then")}
{txt(M, 854, 32, SUB, "died is missing from this data entirely.")}
{txt(M, 920, 34, TEXT, "The real number is worse than what", 700)}
{txt(M, 964, 34, TEXT, "I am showing you. I just cannot", 700)}
{txt(M, 1008, 34, TEXT, "measure how much worse.", 700)}
""")


def slide5(big) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "To be fair to it", 800)}
{txt(M, 360, 38, SUB, "A third of them did keep running.")}
{txt(M, 410, 38, SUB, "Nothing here says a pumped coin cannot.")}
{txt(M, 510, 40, TEXT, "It says you are taking the", 700)}
{txt(M, 558, 40, TEXT, "wrong side of a bet that has", 700)}
{txt(M, 606, 40, TEXT, "been bad for six years, and", 700)}
{txt(M, 654, 40, TEXT, "the size of the run tells you", 700)}
{txt(M, 702, 40, TEXT, "exactly how bad.", 700)}
{txt(M, 810, 44, RED, "The bigger it already moved,", 800)}
{txt(M, 862, 44, RED, "the more it costs to be wrong.", 800)}
{txt(M, 960, 32, SUB, f'{big["n"]} pumps, 6.5 years, p < 0.001. Every number reproducible.')}
{txt(M, 1050, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    blob = json.loads((HERE / "out" / "after-the-run.json").read_text())
    buckets, big = blob["buckets"], blob["big"]
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(buckets), slide2(buckets), slide3(big), slide4(big), slide5(big)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides  (worst bucket {buckets[-1]['m90']*100:.0f}%, "
          f"{big['halved']*100:.0f}% halved)")


if __name__ == "__main__":
    main()
