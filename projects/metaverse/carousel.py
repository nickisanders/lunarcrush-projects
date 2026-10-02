#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the metaverse cohort.

Reads out/metaverse.json, so the slides always match the last run. Writes
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


def pick(d, syms):
    by = {c["symbol"]: c for c in d["coins"]}
    return [by[s] for s in syms if s in by]


def slide1(d) -> str:
    return frame(1, f"""
{txt(M, 330, 56, TEXT, "The 2021", 800)}
{txt(M, 396, 56, TEXT, "metaverse bags", 800)}
{txt(M, 462, 56, AMBER, "just woke up.", 800)}
{txt(M, 580, 36, SUB, "$SAND +60% today. $ENJ +27%.")}
{txt(M, 626, 36, SUB, "$MANA and $GALA +18%. $AXS +11%.")}
{txt(M, 760, 34, TEXT, f"{d['beat']} of {d['n']} beat the market.", 700)}
{txt(M, 880, 32, SUB, "Every coin tagged gaming or NFT that")}
{txt(M, 924, 32, SUB, "peaked by 2022 and fell 90% or more.")}
""", "swipe")


def slide2(d) -> str:
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "All 29 of them,", 800)}
{txt(M, 310, 50, TEXT, "added up", 800)}
{txt(M, 450, 34, SUB, "at their peaks")}
{txt(M, 560, 130, GREY, f"${d['mcapPeak']/1e9:,.0f}B", 800)}
{txt(M, 700, 34, SUB, "today")}
{txt(M, 810, 130, AMBER, f"${d['mcapNow']/1e9:,.1f}B", 800)}
{txt(M, 940, 80, RED, f"-{(1-d['mcapNow']/d['mcapPeak'])*100:.0f}%", 800)}
{txt(M, 1070, 32, TEXT, "A lot of people bought these at the", 700)}
{txt(M, 1114, 32, TEXT, "top. Today was a good day and", 700)}
{txt(M, 1158, 32, TEXT, "they're still down 97%.", 700)}
""")


def slide3(d) -> str:
    rows = pick(d, ["ICP", "MANA", "AXS", "SAND", "APE", "GALA", "FLOW"])
    body = [txt(M, 240, 50, TEXT, "Then and now", 800),
            txt(M, 300, 28, SUB, "peak market cap, and what it is today")]
    for i, c in enumerate(rows):
        y = 400 + i * 108
        body.append(txt(M, y, 36, TEXT, f"${c['symbol']}", 800))
        body.append(txt(M + 230, y, 32, GREY, f"${c['peakMcap']/1e9:,.1f}B"))
        body.append(txt(M + 400, y, 28, SUB, "to"))
        body.append(txt(W - M, y, 34, AMBER, f"${c['mcap']/1e6:,.0f}M", 800, "end"))
    return frame(3, "\n".join(body))


def slide4(d) -> str:
    rows = sorted([c for c in d["coins"] if c["crowdChange"] is not None],
                  key=lambda c: -c["crowdChange"])[:7]
    body = [txt(M, 240, 50, BLUE, "The crowd came", 800), txt(M, 300, 50, BLUE, "back too", 800),
            txt(M, 366, 28, SUB, "more people posting this week than last month")]
    for i, c in enumerate(rows):
        y = 470 + i * 96
        body.append(txt(M, y, 38, TEXT, f"${c['symbol']}", 800))
        body.append(txt(M + 260, y, 28, SUB, c["name"][:16]))
        body.append(txt(W - M, y, 38, BLUE, f"+{c['crowdChange']*100:.0f}%", 800, "end"))
    body.append(txt(M, 1180, 32, TEXT, f"Median across all 29: +{d['crowdMedian']*100:.0f}%.", 700))
    body.append(txt(M, 1224, 32, TEXT, f"{d['crowdGrew']} of {d['n']} grew.", 700))
    return frame(4, "\n".join(body))


def slide5(d) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "Why that matters", 800)}
{txt(M, 350, 34, SUB, "Yesterday I posted that September's")}
{txt(M, 394, 34, SUB, "biggest price gains and biggest crowd")}
{txt(M, 438, 34, SUB, "gains were mostly different coins.")}
{txt(M, 520, 34, TEXT, "$RAY went up 134% with its", 700)}
{txt(M, 566, 34, TEXT, "crowd up 1%. Nobody behind it.", 700)}
{txt(M, 648, 34, GREEN, "This one has both.", 800)}
{txt(M, 740, 30, SUB, "Worth saying: ten days ago I posted a")}
{txt(M, 782, 30, SUB, "similar group and it fell 6.8% the next")}
{txt(M, 824, 30, SUB, "day. One day is one day.")}
{txt(M, 920, 34, TEXT, "All 34 projects are open source.", 700)}
{txt(M, 986, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
{txt(M, 1070, 32, TEXT, "Want the same data?", 700)}
{txt(M, 1116, 32, AMBER, "Code NICKI gets 15% off LunarCrush.", 700)}
""", "Data: LunarCrush · not advice")


def main() -> None:
    d = json.loads((HERE / "out" / "metaverse.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([slide1(d), slide2(d), slide3(d), slide4(d), slide5(d)], 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
