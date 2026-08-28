#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the crowd-growth finding.

Reads out/crowd-growth.json, so the slides always match the last run of
crowd_growth.py. Writes out/instagram-crowd-growth/slide-N.svg, kept apart from
the other two carousels in this project.

Rasterize with sharp:
    node -e "const s=require('../hype-detector/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram-crowd-growth/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram-crowd-growth/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-crowd-growth"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
BLUE, GREY, ORANGE, GREEN = "#58a6ff", "#8b949e", "#f7931a", "#3fb950"
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


def slide1() -> str:
    return frame(1, f"""
{txt(M, 340, 46, SUB, "When a coin's conversation")}
{txt(M, 396, 46, SUB, "goes 5x, you assume a")}
{txt(M, 452, 46, SUB, "crowd showed up.")}
{txt(M, 600, 54, TEXT, "Two thirds of the", 800)}
{txt(M, 662, 54, TEXT, "time, nobody did.", 800)}
{txt(M, 780, 42, BLUE, "The same people just", 700)}
{txt(M, 830, 42, BLUE, "started shouting.", 700)}
{txt(M, 930, 32, SUB, "402 genuine attention spikes, 2020 to 2026")}
""", "swipe")


def slide2(s) -> str:
    share = s["shareSameCrowd"]
    bw = 900
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "What a spike is", 800)}
{txt(M, 310, 50, TEXT, "actually made of", 800)}
{txt(M, 380, 30, SUB, "interactions count engagement. contributors count humans.")}
<rect x="{M}" y="470" width="{bw}" height="110" rx="14" fill="{BLUE}"/>
<rect x="{M + bw * share:.0f}" y="470" width="{bw * (1 - share):.0f}" height="110" rx="14" fill="{TRACK}"/>
{txt(M + 30, 545, 54, "#0d1117", f"{share*100:.0f}%", 800)}
{txt(M, 660, 40, BLUE, "the same crowd, posting more", 700)}
{txt(M, 730, 36, SUB, f'The other {(1-share)*100:.0f}% had a real influx')}
{txt(M, 776, 36, SUB, "of new contributors.")}
{txt(M, 880, 36, TEXT, "So the audience did not grow.", 700)}
{txt(M, 928, 36, TEXT, "The volume did.", 700)}
""", "same spike test, run on people instead of engagement")


def slide3(s) -> str:
    return frame(3, f"""
{txt(M, 250, 50, TEXT, "The number that", 800)}
{txt(M, 310, 50, TEXT, "made it click", 800)}
{txt(M, 420, 34, SUB, "interactions per active contributor")}
{txt(M, 500, 34, SUB, "a normal day")}
{txt(M, 590, 96, TEXT, f'{s["normalPerContributor"]:,}', 800)}
{txt(M, 700, 34, SUB, "a spike day")}
{txt(M, 790, 96, ORANGE, f'{s["spikePerContributor"]:,}', 800)}
{txt(M, 890, 40, TEXT, "Roughly five times the noise,", 700)}
{txt(M, 938, 40, TEXT, "out of the same room.", 700)}
""")


def slide4(s, g) -> str:
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "Does it pay?", 800)}
{txt(M, 320, 32, SUB, "beat Bitcoin over the next 3 days")}
{txt(M, 430, 34, BLUE, f'crowd grew (n={g["grew"]["n"]})', 700)}
{txt(M, 520, 88, BLUE, f'{s["grewRate"]*100:.1f}%', 800)}
{txt(M, 620, 34, GREY, f'same crowd, louder (n={g["same"]["n"]})', 700)}
{txt(M, 710, 88, GREY, f'{s["sameRate"]*100:.1f}%', 800)}
{txt(M, 800, 44, TEXT, "No. It does not.", 800)}
{txt(M, 866, 32, SUB, f'Medians identical. Mean gap {s["gap"]*100:+.1f}pp,')}
{txt(M, 910, 32, SUB, f'CI [{s["ci"][0]*100:+.1f}, {s["ci"][1]*100:+.1f}], p = {s["p"]:.2f}.')}
{txt(M, 986, 34, ORANGE, "Not going in my scanner.", 700)}
""", "if someone sells you this as a filter, ignore them")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "So what is it for", 800)}
{txt(M, 380, 38, TEXT, "It is a description of what hype", 700)}
{txt(M, 428, 38, TEXT, "is made of, not a way to trade it.", 700)}
{txt(M, 540, 36, SUB, "It still changed how I read one of")}
{txt(M, 586, 36, SUB, "those charts.")}
{txt(M, 680, 40, BLUE, "Forty people having a loud day", 700)}
{txt(M, 728, 40, BLUE, "and a thousand new people", 700)}
{txt(M, 776, 40, BLUE, "arriving produce the same", 700)}
{txt(M, 824, 40, BLUE, "vertical line.", 700)}
{txt(M, 940, 34, SUB, "Every number here is reproducible.")}
{txt(M, 986, 34, SUB, "The code is public.")}
{txt(M, 1070, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    blob = json.loads((HERE / "out" / "crowd-growth.json").read_text())
    s, g = blob["stats"], blob["groups"]
    OUT.mkdir(parents=True, exist_ok=True)
    for i, sl in enumerate([slide1(), slide2(s), slide3(s), slide4(s, g), slide5()], 1):
        (OUT / f"slide-{i}.svg").write_text(sl)
    print(f"Wrote {TOTAL} slides to {OUT}  ({s['shareSameCrowd']*100:.0f}% same crowd, "
          f"{s['normalPerContributor']:,} -> {s['spikePerContributor']:,} per contributor)")


if __name__ == "__main__":
    main()
