#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the month review.

Reads out/month.json, so the slides always match the last run. Writes
out/instagram/slide-N.svg.

Rasterize with sharp:
    node -e "const s=require('../crowd-size/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d", "#161b22"
RED, AMBER, GREY, GREEN, BLUE, ORANGE = "#f85149", "#d29922", "#8b949e", "#3fb950", "#58a6ff", "#f7931a"
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


def slide1(d) -> str:
    return frame(1, f"""
{txt(M, 320, 54, TEXT, "September's best", 800)}
{txt(M, 384, 54, TEXT, "coins and its", 800)}
{txt(M, 448, 54, TEXT, "loudest coins", 800)}
{txt(M, 520, 54, AMBER, "are different.", 800)}
{txt(M, 660, 36, SUB, "I ranked the month twice. Once by price,")}
{txt(M, 706, 36, SUB, "once by how many people showed up.")}
{txt(M, 850, 150, GREEN, "3 of 10", 800)}
{txt(M, 910, 36, TEXT, "appear on both lists.", 700)}
{txt(M, 1000, 32, SUB, f"Bitcoin {d['btc']:+.0f}%. Median coin {d['market']:+.0f}%.")}
""", "swipe")


def slide2(d) -> str:
    both = set(d["both"])
    body = [txt(M, 240, 50, ORANGE, "Biggest price", 800), txt(M, 300, 50, ORANGE, "gains", 800),
            txt(M, 356, 28, SUB, "over 30 days")]
    for i, r in enumerate(d["price"][:9]):
        y = 440 + i * 86
        hot = r["symbol"] in both
        body.append(txt(M, y, 38, GREEN if hot else TEXT, f"${r['symbol']}", 800))
        body.append(txt(W - M, y, 38, ORANGE, f"+{r['pct30d']:.0f}%", 800, "end"))
    body.append(txt(M, 1230, 28, GREEN, "green = also top 10 by crowd"))
    return frame(2, "\n".join(body))


def slide3(d) -> str:
    both = set(d["both"])
    body = [txt(M, 240, 50, BLUE, "Biggest crowd", 800), txt(M, 300, 50, BLUE, "gains", 800),
            txt(M, 356, 28, SUB, "people posting a day, end of month vs before it")]
    for i, r in enumerate(d["crowd"][:9]):
        y = 440 + i * 86
        hot = r["symbol"] in both
        body.append(txt(M, y, 38, GREEN if hot else TEXT, f"${r['symbol']}", 800))
        body.append(txt(M + 260, y, 30, SUB, f"{r['crowdBefore']:,.0f} to {r['crowdAfter']:,.0f}"))
        body.append(txt(W - M, y, 38, BLUE, f"+{r['crowdChange']*100:.0f}%", 800, "end"))
    body.append(txt(M, 1230, 28, GREEN, "green = also top 10 by price"))
    return frame(3, "\n".join(body))


def slide4(d) -> str:
    ray = next((r for r in d["price"] if r["symbol"] == "RAY"), d["price"][4])
    qnt = next((r for r in d["price"] if r["symbol"] == "QNT"), d["price"][0])
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "The two ends", 800)}
{txt(M, 310, 50, TEXT, "of it", 800)}
{txt(M, 430, 44, TEXT, f"${ray['symbol']}", 800)}
{txt(M, 510, 96, ORANGE, f"+{ray['pct30d']:.0f}%", 800)}
{txt(M + 330, 510, 34, SUB, "price")}
{txt(M, 606, 96, RED, f"+{ray['crowdChange']*100:.0f}%", 800)}
{txt(M + 240, 606, 34, SUB, "crowd")}
{txt(M, 666, 30, SUB, "It more than doubled and almost")}
{txt(M, 706, 30, SUB, "nobody new turned up.")}
{txt(M, 830, 44, TEXT, f"${qnt['symbol']}", 800)}
{txt(M, 910, 96, ORANGE, f"+{qnt['pct30d']:.0f}%", 800)}
{txt(M + 400, 910, 34, SUB, "price")}
{txt(M, 1006, 96, GREEN, f"+{qnt['crowdChange']*100:.0f}%", 800)}
{txt(M + 400, 1006, 34, SUB, "crowd")}
{txt(M, 1066, 30, SUB, f"{qnt['crowdBefore']:,.0f} to {qnt['crowdAfter']:,.0f} people a day.")}
{txt(M, 1106, 30, SUB, "Everyone turned up.")}
""")


def slide5(d) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "Two different", 800)}
{txt(M, 310, 50, TEXT, "things", 800)}
{txt(M, 420, 36, TEXT, "A coin can double with no", 700)}
{txt(M, 468, 36, TEXT, "audience, and an audience can", 700)}
{txt(M, 516, 36, TEXT, "arrive without the price", 700)}
{txt(M, 564, 36, TEXT, "doing much.", 700)}
{txt(M, 670, 32, SUB, "$ZAMA's crowd grew 169% for a 54% move.")}
{txt(M, 714, 32, SUB, "$ARB's grew 136% for 77%.")}
{txt(M, 758, 32, SUB, "$RAY's grew 1% for 134%.")}
{txt(M, 880, 34, TEXT, "All 33 projects are open source.", 700)}
{txt(M, 950, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
{txt(M, 1040, 32, TEXT, "Want the same data?", 700)}
{txt(M, 1086, 32, AMBER, "Code NICKI gets 15% off LunarCrush.", 700)}
""", "Data: LunarCrush · not advice")


def main() -> None:
    d = json.loads((HERE / "out" / "month.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([slide1(d), slide2(d), slide3(d), slide4(d), slide5(d)], 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
