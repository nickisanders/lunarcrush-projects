#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for where-are-they-now.

Reads out/fallen.json. Writes out/instagram/slide-N.svg.

Rasterize with sharp:
    node -e "const s=require('../crowd-size/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d", "#161b22"
RED, AMBER, GREY, GREEN, BLUE = "#f85149", "#d29922", "#8b949e", "#3fb950", "#58a6ff"
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
{txt(M, 330, 150, TEXT, str(d["everTop"]), 800)}
{txt(M, 400, 40, SUB, "coins have made crypto's", 400)}
{txt(M, 452, 40, SUB, "top 20 since 2020.", 400)}
{txt(M, 640, 150, GREEN, str(d["held"]), 800)}
{txt(M, 710, 40, TEXT, "are still there.", 700)}
{txt(M, 880, 32, SUB, "Ranked by how many people post about")}
{txt(M, 924, 32, SUB, "each coin, every month for six years.")}
""", "swipe")


def slide2(d) -> str:
    rows = [(d["held"], "still top 20", GREEN), (d["top50"] - d["held"], "slipped to 21–50", AMBER),
            (d["everTop"] - d["top50"] - d["past100"], "slipped to 51–100", GREY), (d["past100"], "fell past #100", RED)]
    body = [txt(M, 240, 50, TEXT, "Where they", 800), txt(M, 300, 50, TEXT, "are now", 800)]
    mx = max(r[0] for r in rows)
    for i, (n, lab, col) in enumerate(rows):
        y = 420 + i * 150
        w = (W - 2 * M) * n / mx
        body.append(f'<rect x="{M}" y="{y}" width="{w:.0f}" height="70" rx="10" fill="{col}"/>')
        body.append(txt(M, y - 16, 30, TEXT, lab, 700))
        body.append(txt(M + 20 if w > 120 else M + w + 16, y + 49, 40, "#ffffff" if w > 120 else col, str(n), 800))
    body.append(txt(M, 1060, 34, SUB, f"Median seat today for a coin that"))
    body.append(txt(M, 1106, 34, SUB, f"was once top 20: #{d['medianNow']:.0f}."))
    return frame(2, "\n".join(body))


def slide3(d) -> str:
    picks = {f["symbol"]: f for f in d["fallers"]}
    order = ["YFI", "SUSHI", "MANA", "GMT", "BLUR", "MEME"]
    body = [txt(M, 240, 50, TEXT, "The ones you", 800), txt(M, 300, 50, TEXT, "remember", 800),
            txt(M, 360, 28, SUB, "best seat and month  ·  seat now")]
    for i, s in enumerate(order):
        f = picks[s]
        y = 460 + i * 96
        body.append(txt(M, y, 40, TEXT, f"${s}", 800))
        body.append(txt(M + 250, y, 30, SUB, f"#{f['peakRank']:.0f}  {f['peakMonth'][:4]}"))
        body.append(txt(W - M, y, 40, RED, f"#{f['nowRank']:.0f}", 800, "end"))
    m = picks["MEME"]
    body.append(txt(M, 1070, 32, TEXT, f"$MEME had {m['peakContrib']:,.0f} people a day", 700))
    body.append(txt(M, 1116, 32, TEXT, f"posting at the peak. It has {m['nowContrib']:.0f} now.", 700))
    return frame(3, "\n".join(body))


def slide4(d) -> str:
    body = [txt(M, 240, 50, TEXT, "By the year", 800), txt(M, 300, 50, TEXT, "they peaked", 800),
            txt(M, 360, 28, SUB, "green: still top 20  ·  red: fell past #100")]
    cls = [c for c in d["classes"] if c["year"] <= "2025"]
    for i, c in enumerate(cls):
        y = 440 + i * 92
        bw = W - 2 * M - 150
        body.append(txt(M, y + 30, 32, TEXT, c["year"], 700))
        body.append(f'<rect x="{M + 110}" y="{y}" width="{bw}" height="44" rx="8" fill="{PANEL}"/>')
        body.append(f'<rect x="{M + 110}" y="{y}" width="{bw * c["held"] / c["n"]:.0f}" height="44" rx="8" fill="{GREEN}"/>')
        body.append(f'<rect x="{M + 110 + bw - bw * c["past100"] / c["n"]:.0f}" y="{y}" width="{bw * c["past100"] / c["n"]:.0f}" height="44" rx="8" fill="{RED}"/>')
        body.append(txt(M + 110 + bw + 14, y + 30, 24, SUB, f"{c['held']}/{c['n']}"))
    body.append(txt(M, 1040, 34, TEXT, "Of the 20 coins that peaked in", 700))
    body.append(txt(M, 1086, 34, TEXT, "2021, one still holds a seat.", 700))
    body.append(txt(M, 1132, 34, AMBER, "It's DOGE.", 800))
    return frame(4, "\n".join(body))


def slide5(d) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "It's worse than this", 800)}
{txt(M, 350, 34, SUB, "My data is today's top 1,000 coins by")}
{txt(M, 396, 34, SUB, "market cap. A coin that made the top 20")}
{txt(M, 442, 34, SUB, "in 2021 and has since dropped out of the")}
{txt(M, 488, 34, SUB, "top 1,000 entirely isn't counted at all.")}
{txt(M, 590, 38, TEXT, "Every number here", 700)}
{txt(M, 638, 38, TEXT, "is a floor.", 700)}
{txt(M, 760, 34, SUB, "The 17 that held: BTC, ETH, SOL, XRP,")}
{txt(M, 806, 34, SUB, "ADA, DOGE, LINK, LTC, and nine that")}
{txt(M, 852, 34, SUB, "peaked in the last two years and")}
{txt(M, 898, 34, SUB, "haven't had time to fall yet.")}
{txt(M, 1050, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    d = json.loads((HERE / "out" / "fallen.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(d), slide2(d), slide3(d), slide4(d), slide5(d)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
