#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the altseason reading.

Reads out/altseason.json, so the slides always match the last run. Writes
out/instagram/slide-N.svg.

Rasterize with sharp:
    node -e "const s=require('../crowd-size/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from pathlib import Path

import pandas as pd

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
{txt(M, 330, 170, GREEN, f"{d['today']*100:.0f}%", 800)}
{txt(M, 410, 44, TEXT, "of the top 100 coins", 700)}
{txt(M, 462, 44, TEXT, "are beating Bitcoin.", 700)}
{txt(M, 560, 32, SUB, f"Over the last {d['window']} days.")}
{txt(M, 700, 36, TEXT, "The six-year median is", 400)}
{txt(M, 780, 110, AMBER, f"{d['median']*100:.0f}%", 800)}
{txt(M, 900, 32, SUB, "Everyone keeps asking if it's altseason.")}
{txt(M, 944, 32, SUB, "This is the number instead of the vibe.")}
""", "swipe")


def slide2(d) -> str:
    s = pd.DataFrame(d["series"]); s["date"] = pd.to_datetime(s["date"])
    n = len(s)
    x0, x1, y0, y1 = M, W - M, 520, 900
    def X(i): return x0 + (x1 - x0) * i / (n - 1)
    def Y(v): return y1 - (y1 - y0) * v
    body = [txt(M, 240, 50, TEXT, "Every day", 800), txt(M, 300, 50, TEXT, "since 2020", 800),
            txt(M, 370, 30, SUB, f"share of the top 100 beating BTC over {d['window']} days"),
            txt(M, 424, 28, AMBER, f"six-year median {d['median']*100:.0f}%", 700)]
    for lv in (0.25, 0.5, 0.75):
        body.append(f'<line x1="{x0}" y1="{Y(lv):.0f}" x2="{x1}" y2="{Y(lv):.0f}" stroke="{GRID}"/>')
        body.append(txt(x0 - 12, Y(lv) + 8, 22, SUB, f"{lv*100:.0f}%", 400, "end"))
    body.append(f'<line x1="{x0}" y1="{Y(d["median"]):.0f}" x2="{x1}" y2="{Y(d["median"]):.0f}" stroke="{AMBER}" stroke-width="2" stroke-dasharray="7 6"/>')
    path = "M" + " L".join(f"{X(i):.0f},{Y(v):.0f}" for i, v in enumerate(s["share"]))
    body.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="2" opacity="0.9"/>')
    body.append(f'<circle cx="{x1:.0f}" cy="{Y(d["today"]):.0f}" r="11" fill="{GREEN}" stroke="{BG}" stroke-width="3"/>')
    body.append(txt(x1 - 16, Y(d["today"]) - 22, 28, GREEN, "today", 700, "end"))
    body.append(txt(M, 960, 34, TEXT, f"Today is the {d['percentile']*100:.0f}th percentile", 700))
    body.append(txt(M, 1006, 34, TEXT, f"of {d['days']:,} days.", 700))
    return frame(2, "\n".join(body))


def slide3(d) -> str:
    yrs = d["years"]
    body = [txt(M, 240, 50, TEXT, "How often it", 800), txt(M, 300, 50, TEXT, "gets this broad", 800),
            txt(M, 366, 28, SUB, "share of days each year with more than half")]
    body.append(txt(M, 404, 28, SUB, "the top 100 beating Bitcoin"))
    mx = max(y["above"] for y in yrs)
    for i, y in enumerate(yrs):
        yy = 480 + i * 92
        w = (W - 2*M - 160) * y["above"] / mx
        col = GREEN if y["year"] == 2021 else GREY
        body.append(txt(M, yy + 30, 32, TEXT, str(y["year"]), 700))
        body.append(f'<rect x="{M+120}" y="{yy}" width="{w:.0f}" height="44" rx="8" fill="{col}"/>')
        body.append(txt(M + 140 + w, yy + 33, 30, col, f"{y['above']*100:.0f}%", 800))
    body.append(txt(M, 1130, 32, TEXT, "2021 is the year everyone means.", 700))
    body.append(txt(M, 1174, 32, TEXT, "It cleared half on 45% of days.", 700))
    return frame(3, "\n".join(body))


def slide4(d) -> str:
    w = d["winners"][:7]
    body = [txt(M, 240, 50, TEXT, "Bitcoin is up 7%", 800), txt(M, 300, 50, TEXT, "and still losing", 800),
            txt(M, 366, 30, SUB, "best of the top 100 over 30 days")]
    for i, r in enumerate(w):
        yy = 460 + i * 86
        body.append(txt(M, yy, 38, TEXT, f"${r['symbol']}", 800))
        body.append(txt(M + 260, yy, 30, SUB, r["name"][:14]))
        body.append(txt(W - M, yy, 38, GREEN, f"+{r['pct30d']:.0f}%", 800, "end"))
    body.append(txt(M, 1120, 30, SUB, "Breadth this wide usually shows up when"))
    body.append(txt(M, 1162, 30, SUB, "Bitcoin is falling. It isn't."))
    return frame(4, "\n".join(body))


def slide5(d) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "What it doesn't", 800)}
{txt(M, 310, 50, TEXT, "tell you", 800)}
{txt(M, 410, 34, SUB, "Nothing about what happens next.")}
{txt(M, 480, 34, TEXT, "A week ago I posted nine coins", 700)}
{txt(M, 526, 34, TEXT, "that were ripping. They fell a", 700)}
{txt(M, 572, 34, TEXT, "median 6.8% the following day.", 700)}
{txt(M, 680, 32, SUB, "No index, no weighting, no threshold I")}
{txt(M, 724, 32, SUB, "picked. Just a count of who is ahead of")}
{txt(M, 768, 32, SUB, "Bitcoin, every day for six years.")}
{txt(M, 880, 34, TEXT, "All 31 projects are open source.", 700)}
{txt(M, 950, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
{txt(M, 1040, 32, TEXT, "Want the same data?", 700)}
{txt(M, 1086, 32, AMBER, "Code NICKI gets 15% off LunarCrush.", 700)}
""", "Data: LunarCrush · not advice")


def main() -> None:
    d = json.loads((HERE / "out" / "altseason.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([slide1(d), slide2(d), slide3(d), slide4(d), slide5(d)], 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
