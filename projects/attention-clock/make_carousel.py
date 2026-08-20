#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the attention clock.

Reads out/report.json so the slides always match the last run.
Writes out/instagram/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('../hype-detector/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from math import cos, pi, sin
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
BLUE, ORANGE, GREEN = "#58a6ff", "#f7931a", "#3fb950"
NIGHT, DAY = (31, 111, 235), (247, 147, 26)
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


def lerp(a, b, t) -> str:
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dial(hours, cx, cy, r0, r1, ratio) -> str:
    lo, hi = min(hours), max(hours)
    out = []
    for h, v in enumerate(hours):
        t = (v - lo) / (hi - lo)
        ang = (h + 0.5) / 24 * 2 * pi - pi / 2
        r = r0 + t * (r1 - r0)
        out.append(
            f'<line x1="{cx + r0*cos(ang):.1f}" y1="{cy + r0*sin(ang):.1f}" '
            f'x2="{cx + r*cos(ang):.1f}" y2="{cy + r*sin(ang):.1f}" '
            f'stroke="{lerp(NIGHT, DAY, t)}" stroke-width="20" stroke-linecap="round"/>')
    for h in range(0, 24, 6):
        ang = h / 24 * 2 * pi - pi / 2
        out.append(txt(int(cx + (r1 + 44) * cos(ang)), int(cy + (r1 + 44) * sin(ang)) + 10,
                       28, SUB, f"{h:02d}", 400, "middle"))
    out.append(txt(cx, cy - 2, 62, TEXT, ratio, 800, "middle"))
    out.append(txt(cx, cy + 38, 24, SUB, "swing", 400, "middle"))
    return "\n".join(out)


def slide1(s) -> str:
    return frame(1, f"""
{txt(M, 340, 50, SUB, "“Crypto never sleeps”")}
{txt(M, 400, 50, SUB, "is the most repeated")}
{txt(M, 460, 50, SUB, "line in this industry.")}
{txt(M, 600, 56, TEXT, "I measured it.", 800)}
{txt(M, 800, 170, ORANGE, f'{s["ratio"]:.1f}x', 800)}
{txt(M, 890, 44, TEXT, "more posting at crypto's", 700)}
{txt(M, 942, 44, TEXT, "busiest hour than its quietest", 700)}
{txt(M, 1030, 32, SUB, f'{s["coins"]} coins over $1B · last 30 days')}
""", "swipe")


def slide2(s) -> str:
    return frame(2, f"""
{txt(M, 240, 52, TEXT, "The crypto day", 800)}
{txt(M, 296, 30, SUB, "posts per hour, UTC. each spoke is one hour.")}
{dial(s["hours"], 540, 730, 128, 278, f'{s["ratio"]:.1f}x')}
{txt(M, 1120, 32, SUB, f'busiest {s["loudestHour"]:02d}:00 UTC · quietest {s["quietestHour"]:02d}:00 UTC')}
""", "blue is night, orange is day")


def slide3(s) -> str:
    return frame(3, f"""
{txt(M, 250, 52, TEXT, "Every coin keeps", 800)}
{txt(M, 310, 52, TEXT, "the same hours", 800)}
{txt(M, 470, 120, GREEN, f'{s["peakInAfternoon"]}/{s["coins"]}', 800)}
{txt(M, 530, 36, TEXT, "peak between 11:00 and 17:00 UTC", 700)}
{txt(M, 680, 120, GREEN, f'{s["medianPairwiseCorr"]:.2f}', 800)}
{txt(M, 740, 36, TEXT, "correlation between any two", 700)}
{txt(M, 788, 36, TEXT, "coins' hourly shapes", 700)}
{txt(M, 880, 34, SUB, "Bitcoin, Monero, BNB, Pump.fun, XRP.")}
{txt(M, 926, 34, SUB, "Supposedly different communities on")}
{txt(M, 972, 34, SUB, "different continents. They behave like")}
{txt(M, 1018, 34, SUB, "one crowd on one clock.")}
""")


def slide4(s) -> str:
    return frame(4, f"""
{txt(M, 250, 52, TEXT, "And the clock", 800)}
{txt(M, 310, 52, TEXT, "is Western", 800)}
{txt(M, 440, 34, BLUE, f'{s["quietestHour"]:02d}:00 UTC · quietest hour', 700)}
{txt(M, 496, 40, TEXT, "= 1pm in Tokyo")}
{txt(M, 548, 32, SUB, "peak lunchtime across Asia, and it is the")}
{txt(M, 592, 32, SUB, "deadest the conversation ever gets")}
{txt(M, 700, 34, ORANGE, f'{s["loudestHour"]:02d}:00 UTC · busiest hour', 700)}
{txt(M, 756, 40, TEXT, "= 9am in New York")}
{txt(M, 870, 40, TEXT, "An industry that never stops", 700)}
{txt(M, 922, 40, TEXT, "calling itself borderless keeps", 700)}
{txt(M, 974, 40, TEXT, "London-to-New-York office hours.", 700)}
""")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 250, 52, TEXT, "What I nearly", 800)}
{txt(M, 310, 52, TEXT, "got wrong", 800)}
{txt(M, 420, 38, TEXT, "My first pass used averages.")}
{txt(M, 490, 38, SUB, "BNB lit up with a peak at 01:00 UTC.")}
{txt(M, 536, 38, SUB, "A perfect Asia-hours schedule. I had")}
{txt(M, 582, 38, SUB, "the post half written: the one major")}
{txt(M, 628, 38, SUB, "coin running on Singapore time.")}
{txt(M, 716, 38, TEXT, "It was one overnight event.", 700)}
{txt(M, 768, 38, SUB, "A single listing dragging one hour's")}
{txt(M, 814, 38, SUB, "average across a whole month.")}
{txt(M, 880, 38, SUB, "On medians it peaks at 13:00, like")}
{txt(M, 926, 38, SUB, "everything else. The story evaporated.")}
{txt(M, 1010, 36, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · code NICKI gets 15% off")


def main() -> None:
    s = json.loads((HERE / "out" / "report.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, sl in enumerate([slide1(s), slide2(s), slide3(s), slide4(s), slide5()], 1):
        (OUT / f"slide-{i}.svg").write_text(sl)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
