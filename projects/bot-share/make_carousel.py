#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the bot-share leaderboard.

Reads out/report.json so the slides always match the last run.
Writes out/instagram/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
RED, AMBER, GREEN, DIM = "#f85149", "#d29922", "#3fb950", "#6e7681"
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


def color_for(share: float) -> str:
    return RED if share >= 0.5 else AMBER if share >= 0.25 else GREEN


def bars(rows, top: int, width: int = 620, row_h: int = 92) -> str:
    """Horizontal bars on a 0-100% scale, label left, value at the bar end."""
    out = []
    x0 = M + 150
    for i, s in enumerate(rows):
        y = top + i * row_h
        w = max(6, s["spamShare"] * width)
        c = color_for(s["spamShare"])
        out.append(txt(x0 - 24, y + 12, 36, TEXT, f'${s["symbol"]}', 700, "end"))
        out.append(f'<rect x="{x0}" y="{y - 20}" width="{width}" height="42" rx="10" fill="{TRACK}"/>')
        out.append(f'<rect x="{x0}" y="{y - 20}" width="{w:.0f}" height="42" rx="10" fill="{c}"/>')
        out.append(txt(int(x0 + w + 20), y + 12, 34, c, f'{round(s["spamShare"]*100)}%', 700))
    return "\n".join(out)


def slide1(median_share: float) -> str:
    return frame(1, f"""
{txt(M, 340, 52, SUB, "Everyone says crypto")}
{txt(M, 400, 52, SUB, "Twitter is full of bots.")}
{txt(M, 490, 52, SUB, "Nobody measures it.")}
{txt(M, 700, 190, RED, f"{round(median_share*100)}%", 800)}
{txt(M, 790, 46, TEXT, "of everything posted about", 700)}
{txt(M, 846, 46, TEXT, "major coins is flagged junk", 700)}
{txt(M, 940, 34, SUB, "median across 23 coins over $1B, last 30 days")}
""", "swipe for the leaderboard")


def slide2(dirty) -> str:
    return frame(2, f"""
{txt(M, 250, 54, TEXT, "The junkiest", 800)}
{txt(M, 312, 32, SUB, "share of posts flagged as spam")}
{bars(dirty, 500)}
""", "these are the ones I could measure honestly")


def slide3(clean) -> str:
    return frame(3, f"""
{txt(M, 250, 54, TEXT, "The cleanest", 800)}
{txt(M, 312, 32, SUB, "share of posts flagged as spam")}
{bars(clean, 500)}
""", "yes, that is Bitcoin at the bottom")


def slide4(pump: float, xrp: float, btc_posts: int) -> str:
    return frame(4, f"""
{txt(M, 250, 54, TEXT, "Two that surprised me", 800)}
{txt(M, 370, 40, TEXT, "Pump.fun", 700)}
{txt(M, 480, 92, GREEN, f"{round(pump*100)}%", 800)}
{txt(M, 542, 32, SUB, "the memecoin casino")}
{txt(M + 520, 370, 40, TEXT, "XRP", 700)}
{txt(M + 520, 480, 92, RED, f"{round(xrp*100)}%", 800)}
{txt(M + 520, 542, 32, SUB, "a top ten coin")}
{txt(M, 670, 38, TEXT, "And Bitcoin gets more posts than any", 700)}
{txt(M, 722, 38, TEXT, f"coin alive, about {btc_posts:,} a day,", 700)}
{txt(M, 774, 38, TEXT, "with one of the cleanest feeds.", 700)}
{txt(M, 870, 34, SUB, "Scale does not automatically bring bots.")}
{txt(M, 916, 34, SUB, "Incentives do. Airdrops and big retail")}
{txt(M, 962, 34, SUB, "communities attract automated posting")}
{txt(M, 1008, 34, SUB, "whether a project wants it or not.")}
""")


def slide5(excluded) -> str:
    names = ", ".join(f"${s}" for s in excluded[:6])
    more = f" and {len(excluded)-6} more" if len(excluded) > 6 else ""
    return frame(5, f"""
{txt(M, 250, 54, TEXT, "What I left out", 800)}
{txt(M, 350, 38, TEXT, "Some coins broke the measurement.")}
{txt(M, 420, 38, SUB, "On some days their flagged-post count")}
{txt(M, 466, 38, SUB, "is higher than their total post count.")}
{txt(M, 512, 38, SUB, "That is impossible if both numbers")}
{txt(M, 558, 38, SUB, "count the same thing. They do not.")}
{txt(M, 650, 34, RED, names, 700)}
{txt(M, 696, 34, RED, more.strip(), 700) if more else ""}
{txt(M, 790, 38, TEXT, "I could have clipped them to 99% and", 700)}
{txt(M, 842, 38, TEXT, "had a spicier chart. They are off it", 700)}
{txt(M, 894, 38, TEXT, "instead, because I do not have an", 700)}
{txt(M, 946, 38, TEXT, "honest number for them.", 700)}
{txt(M, 1040, 36, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · code NICKI gets 15% off")


def main() -> None:
    r = json.loads((HERE / "out" / "report.json").read_text())
    quotable = [s for s in r["scored"] if s["quotable"]]
    excluded = [s["symbol"] for s in r["scored"] if not s["quotable"]]
    dirty = quotable[:5]
    clean = list(reversed(quotable))[:5]
    median_share = quotable[len(quotable) // 2]["spamShare"]
    by_sym = {s["symbol"]: s for s in quotable}

    OUT.mkdir(parents=True, exist_ok=True)
    slides = [
        slide1(median_share),
        slide2(dirty),
        slide3(clean),
        slide4(by_sym["PUMP"]["spamShare"], by_sym["XRP"]["spamShare"],
               round(by_sym["BTC"]["postsPerDay"] / 1000) * 1000),
        slide5(excluded),
    ]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")
    print(f"median {median_share:.0%} · dirtiest {dirty[0]['symbol']} · cleanest {clean[0]['symbol']}")


if __name__ == "__main__":
    main()
