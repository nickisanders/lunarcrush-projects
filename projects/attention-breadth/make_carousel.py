#!/usr/bin/env python3
"""Instagram carousel: the era artifact that faked a perfect result.

Writes out/instagram/slide-N.svg (1080x1350).
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, TRACK, DIM = "#3fb950", "#f85149", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 6

STAIRS = [("most concentrated", "+2.0%", GREEN), ("", "+0.6%", GREEN),
          ("", "-1.5%", DIM), ("", "-3.4%", RED), ("most spread out", "-6.2%", RED)]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
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
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 34}" cy="{H-60}" r="7" '
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
{txt(M, 420, 96, TEXT, "I got a", 800)}
{txt(M, 530, 96, TEXT, "perfect result.", 800)}
{txt(M, 660, 96, RED, "It was fake.", 800)}
{txt(M, 800, 42, SUB, "How I caught it, and the trap")}
{txt(M, 852, 42, SUB, "that catches everyone.")}
""", "swipe")


def slide2() -> str:
    return frame(2, f"""
{txt(M, 260, 60, TEXT, "What I measured", 800)}
{txt(M, 360, 40, TEXT, "Crypto talks about thousands of")}
{txt(M, 412, 40, TEXT, "coins, but not evenly. So:")}
{txt(M, 500, 38, SUB, "how many coins is crypto")}
{txt(M, 548, 38, SUB, "effectively talking about?")}
{txt(M, 700, 150, GREEN, "5", 800)}
{txt(M + 150, 700, 44, TEXT, "coins.")}
{txt(M + 150, 756, 34, SUB, "that's the whole conversation")}
{txt(M, 880, 40, TEXT, "Bitcoin alone takes 41% of it.")}
{txt(M, 932, 40, TEXT, "The top ten take 82%.")}
{txt(M, 1010, 36, SUB, "In six years it has never gone above 12.")}
""")


def slide3() -> str:
    rows = ""
    y = 460
    for label, val, color in STAIRS:
        rows += txt(M, y, 40, SUB, label)
        rows += txt(W - M, y, 46, color, val, 700, "end")
        y += 92
    return frame(3, f"""
{txt(M, 250, 56, TEXT, "Then I tested it", 800)}
{txt(M, 320, 36, SUB, "when attention spreads out, do small")}
{txt(M, 364, 36, SUB, "coins beat Bitcoin next month?")}
{rows}
{txt(M, 990, 40, TEXT, "A perfect staircase.")}
{txt(M, 1042, 40, TEXT, "Every step in the right direction.")}
""", "this is the point where you should get suspicious")


def slide4() -> str:
    df = pd.read_csv(HERE / "out" / "breadth.csv", parse_dates=["date"])
    df["q"] = pd.qcut(df["effective_n"], 5, labels=list("ABCDE"))
    t0, t1 = df["date"].min().value, df["date"].max().value
    cx, cw = M, W - 2 * M
    def X(d): return cx + (d.value - t0) / (t1 - t0) * cw
    marks = ""
    for d in df.loc[df["q"] == "A", "date"]:
        marks += f'<rect x="{X(d):.1f}" y="620" width="2" height="34" fill="{GREEN}" opacity="0.85"/>'
    for d in df.loc[df["q"] == "E", "date"]:
        marks += f'<rect x="{X(d):.1f}" y="664" width="2" height="34" fill="{RED}" opacity="0.85"/>'
    years = "".join(
        txt(X(pd.Timestamp(f"{y}-01-01")), 740, 24, SUB, str(y), 400, "middle")
        for y in range(2020, 2027))
    return frame(4, f"""
{txt(M, 250, 56, TEXT, "So I asked one", 800)}
{txt(M, 316, 56, TEXT, "basic question", 800)}
{txt(M, 400, 44, GREEN, "When did those days", 700)}
{txt(M, 452, 44, GREEN, "actually happen?", 700)}
<rect x="{cx}" y="610" width="{cw}" height="98" rx="10" fill="{TRACK}"/>
{marks}
{years}
{txt(M, 850, 40, TEXT, "465 of the 467 most concentrated")}
{txt(M, 902, 40, TEXT, "days were 2020 to 2022.")}
{txt(M, 972, 40, TEXT, "Every spread out day was 2023+.")}
{txt(M, 1050, 40, RED, "The groups never overlap.", 700)}
""", "green = concentrated · red = spread out")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 250, 56, TEXT, "Why it happened", 800)}
{txt(M, 350, 40, TEXT, "My number drifts upward over time,")}
{txt(M, 402, 40, TEXT, "because more coins qualify as the")}
{txt(M, 454, 40, TEXT, "market grows.")}
{txt(M, 560, 44, RED, "When a number drifts,", 700)}
{txt(M, 614, 44, RED, "sorting days by it is almost", 700)}
{txt(M, 668, 44, RED, "the same as sorting by date.", 700)}
{txt(M, 780, 40, TEXT, "I never compared attention patterns.")}
{txt(M, 832, 40, TEXT, "I compared 2021 to 2024.")}
{txt(M, 930, 38, SUB, "The fix: compare each day to the past year,")}
{txt(M, 978, 38, SUB, "not to all of history. Do that and the")}
{txt(M, 1026, 38, SUB, "result disappears completely.")}
""")


def slide6() -> str:
    return frame(6, f"""
{txt(M, 300, 56, TEXT, "What survives", 800)}
{txt(M, 400, 40, TEXT, "The gauge is real: crypto's attention")}
{txt(M, 452, 40, TEXT, "lives in about five coins.")}
{txt(M, 524, 40, TEXT, "It predicts nothing I can find.")}
{txt(M, 640, 42, GREEN, "If a measurement drifts,", 700)}
{txt(M, 692, 42, GREEN, "check when your data points", 700)}
{txt(M, 744, 42, GREEN, "fall before you trust it.", 700)}
{txt(M, 830, 38, SUB, "A perfect staircase is usually the bug talking.")}
{txt(M, 940, 42, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 992, 42, GREEN, "lunarcrush-projects", 700)}
{txt(M, 1060, 36, SUB, "Data: LunarCrush · code NICKI gets 15% off")}
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5, slide6], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
