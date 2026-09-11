#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the top-ten seats finding.

Reads out/top_ten.json, so the slides always match the last run. Writes
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


def seats(fx, top=560) -> str:
    """Ten seats in two rows of five: seven filled, three dashed open."""
    sw, sg, sh = 168, 15, 170
    out = []
    for i in range(10):
        row, col = divmod(i, 5)
        x = M + col * (sw + sg)
        y = top + row * (sh + 22)
        if i < len(fx):
            out += [f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" fill="{PANEL}" rx="12"/>',
                    f'<rect x="{x}" y="{y}" width="{sw}" height="6" fill="{BLUE}" rx="3"/>',
                    txt(int(x + sw / 2), y + 82, 34, TEXT, fx[i]["symbol"], 800, "middle"),
                    txt(int(x + sw / 2), y + 128, 26, SUB, f"{fx[i]['share']*100:.0f}%", 400, "middle")]
        else:
            out += [f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" fill="none" stroke="{AMBER}" '
                    f'stroke-width="3" stroke-dasharray="9 8" rx="12"/>',
                    txt(int(x + sw / 2), y + 96, 28, AMBER, "open", 800, "middle")]
    return "\n".join(out)


def bars(hist, top=520, ch=380) -> str:
    bw, gap, x0 = 52, 10, M
    mx = max(hist.values())
    base = top + ch
    out = []
    for i in range(1, 15):
        v = hist.get(i, 0)
        h = v / mx * ch
        x = x0 + (i - 1) * (bw + gap)
        col = RED if i == 1 else AMBER if i <= 3 else GREY
        out.append(f'<rect x="{x}" y="{base - h:.0f}" width="{bw}" height="{h:.0f}" rx="6" fill="{col}"/>')
        if i in (1, 2, 3, 7, 14):
            out.append(txt(int(x + bw / 2), base + 36, 24, SUB, "14+" if i == 14 else str(i), 400, "middle"))
    out.append(f'<line x1="{M}" y1="{base}" x2="{W-M}" y2="{base}" stroke="{GRID}" stroke-width="2"/>')
    out.append(txt(M, base + 76, 24, GREY, "days in the top ten"))
    return "\n".join(out)


def slide1(d) -> str:
    return frame(1, f"""
{txt(M, 330, 62, TEXT, "Crypto's top ten", 800)}
{txt(M, 400, 62, TEXT, "has three", 800)}
{txt(M, 470, 62, AMBER, "open seats.", 800)}
{txt(M, 600, 36, SUB, "The ten most-talked-about coins,")}
{txt(M, 648, 36, SUB, "every day for six and a half years.")}
{seats(d["fixtures"], top=760)}
""", "swipe")


def slide2(d) -> str:
    fx = d["fixtures"]
    return frame(2, f"""
{txt(M, 240, 50, TEXT, "Seven coins are", 800)}
{txt(M, 300, 50, TEXT, "basically always there", 800)}
{txt(M, 370, 30, SUB, "share of days in the top ten, 2020 to 2026")}
""" + "\n".join(
        txt(M, 470 + i * 78, 40, TEXT, fx[i]["symbol"], 800)
        + txt(M + 220, 470 + i * 78, 40, BLUE if fx[i]["share"] > 0.9 else SUB, f"{fx[i]['share']*100:.0f}%", 700)
        + f'<rect x="{M + 340}" y="{470 + i * 78 - 28}" width="{(W - M - M - 340) * fx[i]["share"]:.0f}" height="36" rx="6" fill="{PANEL}"/>'
        for i in range(len(fx))) + f"""
{txt(M, 1060, 34, TEXT, "That leaves three seats for", 700)}
{txt(M, 1106, 34, TEXT, f"the other {d['distinctCoins'] - len(fx)} coins.", 700)}
""")


def slide3(d) -> str:
    hist = {int(k): v for k, v in d["stayHistogram"].items()}
    # fold 14+ into one bar for the carousel
    folded = {i: hist.get(i, 0) for i in range(1, 14)}
    folded[14] = sum(v for k, v in hist.items() if k >= 14)
    return frame(3, f"""
{txt(M, 240, 50, TEXT, "When another coin", 800)}
{txt(M, 300, 50, TEXT, "gets in, how long", 800)}
{txt(M, 360, 50, TEXT, "does it stay?", 800)}
{txt(M, 420, 30, SUB, f"{d['stints']:,} visits. Bars are how many ended on that day.")}
{bars(folded)}
{txt(M, 1070, 90, RED, f"{d['goneNextDay']*100:.0f}%", 800)}
{txt(M + 300, 1046, 34, TEXT, "are gone", 700)}
{txt(M + 300, 1090, 34, TEXT, "the next day", 700)}
""")


def slide4(d) -> str:
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "The visitor's", 800)}
{txt(M, 310, 50, TEXT, "scorecard", 800)}
{txt(M, 470, 110, TEXT, f"{d['medianStay']:.0f} day", 800)}
{txt(M, 520, 32, SUB, "median stay in the top ten")}
{txt(M, 660, 64, AMBER, f"{d['goneWithin3']*100:.0f}%", 800)}
{txt(M + 250, 660, 34, SUB, "gone within 3 days")}
{txt(M, 770, 64, AMBER, f"{d['goneWithin7']*100:.0f}%", 800)}
{txt(M + 250, 770, 34, SUB, "gone within a week")}
{txt(M, 880, 64, GREEN, f"{d['lastedMonth']*100:.1f}%", 800)}
{txt(M + 250, 880, 34, SUB, "lasted a month")}
{txt(M, 1020, 36, TEXT, "A coin trending today is,", 700)}
{txt(M, 1068, 36, TEXT, "on the median, off the list", 700)}
{txt(M, 1116, 36, TEXT, "tomorrow.", 700)}
""")


def slide5(d) -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "One thing I had", 800)}
{txt(M, 310, 50, TEXT, "to fix first", 800)}
{txt(M, 400, 34, SUB, "The raw list had these as fixtures:")}
{txt(M, 490, 44, RED, "$GIGA", 800)}
{txt(M + 200, 490, 34, SUB, "on 60% of days")}
{txt(M, 560, 44, RED, "$S", 800)}
{txt(M + 200, 560, 34, SUB, "on 47% of days")}
{txt(M, 660, 34, TEXT, "That would make them bigger", 700)}
{txt(M, 706, 34, TEXT, "than DOGE. They're not.", 700)}
{txt(M, 752, 34, TEXT, "They're words.", 700)}
{txt(M, 840, 32, SUB, "A ticker that's also a word gets counted")}
{txt(M, 884, 32, SUB, "every time anyone uses the word, so I")}
{txt(M, 928, 32, SUB, "filtered those out before ranking.")}
{txt(M, 1050, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    d = json.loads((HERE / "out" / "top_ten.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(d), slide2(d), slide3(d), slide4(d), slide5(d)]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
