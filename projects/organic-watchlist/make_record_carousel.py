#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the published track record.

Reads out/track.json, so the slides always match the last `npm run track`.
Built for the record as a whole rather than a single pick: the point is that
both outcomes get the same treatment.

Writes out/instagram-record/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram-record/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram-record/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-record"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
GREEN, RED, ORANGE = "#3fb950", "#f85149", "#f7931a"
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


def slide1(loss) -> str:
    return frame(1, f"""
{txt(M, 350, 58, TEXT, "My second pick", 800)}
{txt(M, 416, 58, TEXT, "lost.", 800)}
{txt(M, 520, 36, SUB, "Here it is.")}
{txt(M, 650, 44, TEXT, f'${loss["symbol"]}, over the 3 days', 700)}
{txt(M, 702, 44, TEXT, "my signal covers:", 700)}
{txt(M, 820, 120, RED, f'{loss["spread"]*100:.1f}pp', 800)}
{txt(M, 880, 34, SUB, "against Bitcoin")}
{txt(M, 970, 34, SUB, "Posted for the same reason I posted the")}
{txt(M, 1014, 34, SUB, "winner.")}
""", "swipe")


def slide2(loss) -> str:
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "How it lost", 800)}
{txt(M, 380, 40, TEXT, f'the coin: {loss["coinReturn"]*100:.1f}%', 700)}
{txt(M, 432, 32, SUB, "basically flat")}
{txt(M, 530, 40, TEXT, f'Bitcoin: {loss["btcReturn"]*100:.1f}%', 700)}
{txt(M, 582, 32, SUB, "also basically flat")}
{txt(M, 700, 38, ORANGE, "Nothing happened. Nothing", 700)}
{txt(M, 748, 38, ORANGE, "happening is a loss.", 700)}
{txt(M, 850, 34, SUB, "My claim was never \u201cthis goes up.\u201d")}
{txt(M, 896, 34, SUB, "It was \u201cthis beats Bitcoin over 3 days.\u201d")}
{txt(M, 980, 34, TEXT, "The direction of the candle is not", 700)}
{txt(M, 1024, 34, TEXT, "the scoreboard.", 700)}
""")


def slide3(rows) -> str:
    body = [txt(M, 250, 50, TEXT, "Both picks so far", 800),
            txt(M, 312, 30, SUB, "performance against Bitcoin, which is the claim")]
    cx, scale = 560, 26
    body.append(f'<line x1="{cx}" y1="400" x2="{cx}" y2="{400 + len(rows)*220}" stroke="{TRACK}" stroke-width="3"/>')
    for i, r in enumerate(rows):
        y = 480 + i * 220
        w = max(-330, min(330, r["spread"] * 100 * scale))
        col = GREEN if r["beatBtc"] else RED
        body += [
            txt(M, y - 44, 40, TEXT, f'${r["symbol"]}', 700),
            txt(M, y - 8, 26, SUB, r["date"]),
            f'<rect x="{cx if w >= 0 else cx + w:.0f}" y="{y - 34}" width="{max(8, abs(w)):.0f}" height="48" rx="10" fill="{col}"/>',
            txt(int(cx + max(w, 0) + 20), y + 4, 34, col, f'{"+" if r["spread"] >= 0 else ""}{r["spread"]*100:.1f}pp', 800),
            txt(M, y + 34, 26, SUB, f'coin {r["coinReturn"]*100:.1f}%  ·  BTC {r["btcReturn"]*100:.1f}%'),
        ]
    return frame(3, "\n".join(body), "one rose 25% and won. one drifted and lost.")


def slide4() -> str:
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "It passed every", 800)}
{txt(M, 310, 50, TEXT, "check I have", 800)}
{txt(M, 430, 36, TEXT, "5% spam", 700)}
{txt(M, 474, 30, SUB, "against a 40% market median")}
{txt(M, 560, 36, TEXT, "169 accounts talking", 700)}
{txt(M, 604, 30, SUB, "the biggest holding just 6%")}
{txt(M, 690, 36, TEXT, "no prior run, no ticker collision", 700)}
{txt(M, 734, 30, SUB, "the two traps that fooled me last month")}
{txt(M, 850, 46, RED, "It still lost.", 800)}
{txt(M, 940, 36, TEXT, "That is what a 49% edge feels", 700)}
{txt(M, 986, 36, TEXT, "like from the inside.", 700)}
""")


def slide5(summary) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "The number", 800)}
{txt(M, 310, 50, TEXT, "people skip", 800)}
{txt(M, 440, 110, ORANGE, "49% vs 42%", 800)}
{txt(M, 510, 36, TEXT, "Roughly half of these lose by design.", 700)}
{txt(M, 610, 34, SUB, "A signal that wins seven times out of ten")}
{txt(M, 656, 34, SUB, "is not my signal. It is someone else\u2019s")}
{txt(M, 702, 34, SUB, "marketing.")}
{txt(M, 800, 40, TEXT, f'At {summary["n"]} picks my record tells', 700)}
{txt(M, 848, 40, TEXT, "you nothing. It would tell you", 700)}
{txt(M, 896, 40, TEXT, "nothing at 2 for 2 as well.", 700)}
{txt(M, 970, 44, GREEN, "Ask me at 30.", 800)}
{txt(M, 1060, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    track = json.loads((HERE / "out" / "track.json").read_text())
    rows, summary = track["rows"], track["summary"]
    loss = next((r for r in rows if not r["beatBtc"]), rows[-1])
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(loss), slide2(loss), slide3(rows), slide4(), slide5(summary)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides  ({summary['wins']} of {summary['n']})")


if __name__ == "__main__":
    main()
