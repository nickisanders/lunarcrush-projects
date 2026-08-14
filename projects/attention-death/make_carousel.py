#!/usr/bin/env python3
"""Instagram carousel: the altcoin base rate.

Writes out/instagram/slide-N.svg (1080x1350).
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, TRACK, DIM, GHOST = "#3fb950", "#f85149", "#21262d", "#6e7681", "#484f58"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 6

RATES = [("1 day", 44.7), ("1 week", 40.4), ("1 month", 34.9),
         ("3 months", 28.2), ("6 months", 23.1)]


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
{txt(M, 400, 52, SUB, "Hold an altcoin for six months.")}
{txt(M, 530, 128, RED, "77%", 800)}
{txt(M, 640, 62, TEXT, "chance Bitcoin", 800)}
{txt(M, 712, 62, TEXT, "would have", 800)}
{txt(M, 784, 62, TEXT, "beaten it.", 800)}
{txt(M, 900, 38, SUB, "I found this by accident, while looking")}
{txt(M, 948, 38, SUB, "for something else entirely.")}
""", "swipe")


def slide2() -> str:
    return frame(2, f"""
{txt(M, 260, 58, TEXT, "What I was doing", 800)}
{txt(M, 360, 40, TEXT, "I wanted to know if a dying")}
{txt(M, 412, 40, TEXT, "community predicts a dying coin.")}
{txt(M, 500, 38, SUB, "Found 7,067 cases where a coin's")}
{txt(M, 548, 38, SUB, "conversation collapsed to under a third")}
{txt(M, 596, 38, SUB, "of normal, five days running, while the")}
{txt(M, 644, 38, SUB, "coin still had real size and volume.")}
{txt(M, 750, 50, TEXT, "Answer: nothing happens.", 700)}
{txt(M, 812, 38, SUB, "They performed the same as everything else.")}
{txt(M, 860, 38, SUB, "A quiet community is not a sell signal.")}
{txt(M, 960, 46, GREEN, "But then I looked at what", 700)}
{txt(M, 1014, 46, GREEN, "“everything else” was doing.", 700)}
""")


def slide3() -> str:
    cx, cy, cw, ch = M + 40, 480, W - 2 * M - 60, 330
    def X(i): return cx + i / (len(RATES) - 1) * cw
    def Y(v): return cy + ch - (v - 18) / 34 * ch
    body = [txt(M, 250, 56, TEXT, "The base rate", 800),
            txt(M, 320, 34, SUB, "chance a real altcoin beats Bitcoin"),
            txt(M, 366, 34, SUB, "661,800 coin-days · 838 coins")]
    ycf = Y(50)
    body.append(f'<line x1="{cx}" y1="{ycf:.0f}" x2="{cx+cw}" y2="{ycf:.0f}" stroke="{GHOST}" stroke-width="2" stroke-dasharray="8 8"/>')
    body.append(txt(int(cx + cw), int(ycf - 14), 22, SUB, "coin flip = 50%", 400, "end"))
    pts = " ".join(f"{X(i):.0f},{Y(v):.0f}" for i, (_, v) in enumerate(RATES))
    body.append(f'<polygon points="{pts} {X(4):.0f},{cy+ch:.0f} {X(0):.0f},{cy+ch:.0f}" fill="#f8514918"/>')
    body.append(f'<polyline points="{pts}" fill="none" stroke="{RED}" stroke-width="6" stroke-linejoin="round"/>')
    for i, (label, v) in enumerate(RATES):
        last = i == len(RATES) - 1
        body.append(f'<circle cx="{X(i):.0f}" cy="{Y(v):.0f}" r="{13 if last else 9}" fill="{RED}"/>')
        body.append(txt(int(X(i)), int(Y(v) - 26), 30 if last else 25, RED, f"{v}%", 700, "middle"))
    for i, (label, _) in enumerate(RATES):
        if i % 2 == 0 or i == len(RATES) - 1:
            body.append(txt(int(X(i)), cy + ch + 46, 24, TEXT, label, 400, "middle"))
    body.append(txt(M, 940, 46, TEXT, "It never touches the coin flip.", 700))
    body.append(txt(M, 1000, 38, SUB, "And the longer you hold, the worse it gets."))
    return frame(3, "\n".join(body))


def slide4() -> str:
    return frame(4, f"""
{txt(M, 260, 58, TEXT, "Before you blame", 800)}
{txt(M, 328, 58, TEXT, "the bear market", 800)}
{txt(M, 440, 40, TEXT, "Chance of beating BTC over 3 months,")}
{txt(M, 492, 40, TEXT, "by era:")}
{txt(M + 30, 580, 40, SUB, "2020 to 2022")}
{txt(W - M, 580, 40, RED, "37%", 700, "end")}
{txt(M + 30, 644, 40, SUB, "2023 to 2025")}
{txt(W - M, 644, 40, RED, "23%", 700, "end")}
{txt(M + 30, 708, 40, SUB, "2026 so far")}
{txt(W - M, 708, 40, RED, "32%", 700, "end")}
{txt(M, 820, 44, TEXT, "Every era loses.", 700)}
{txt(M, 900, 38, SUB, "Size barely helps either. Even $10B+ coins")}
{txt(M, 948, 38, SUB, "only beat Bitcoin 35.6% of the time.")}
""")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 300, 58, TEXT, "And it's worse", 800)}
{txt(M, 368, 58, TEXT, "than this", 800)}
{txt(M, 490, 42, TEXT, "My data only contains coins that")}
{txt(M, 544, 42, TEXT, "survived to be in today's top 1,000.")}
{txt(M, 640, 46, RED, "Every coin that went to zero", 700)}
{txt(M, 696, 46, RED, "is missing from the numbers.", 700)}
{txt(M, 800, 40, TEXT, "So 23% is the optimistic version.")}
{txt(M, 880, 38, SUB, "This is the survivors telling you")}
{txt(M, 928, 38, SUB, "how badly the survivors did.")}
""")


def slide6() -> str:
    return frame(6, f"""
{txt(M, 260, 56, TEXT, "Why this changed", 800)}
{txt(M, 326, 56, TEXT, "how I read my own work", 800)}
{txt(M, 440, 38, TEXT, "My best signal picks coins that beat")}
{txt(M, 490, 38, TEXT, "Bitcoin 49% of the time, versus 42%")}
{txt(M, 540, 38, TEXT, "for a random coin.")}
{txt(M, 620, 38, SUB, "I used to feel sheepish that both numbers")}
{txt(M, 668, 38, SUB, "are under half. Now I understand why.")}
{txt(M, 760, 44, GREEN, "Losing to Bitcoin is the", 700)}
{txt(M, 814, 44, GREEN, "default state of this market.", 700)}
{txt(M, 890, 38, TEXT, "An edge doesn't make you a winner.")}
{txt(M, 938, 38, TEXT, "It makes you lose less often.")}
{txt(M, 1030, 40, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · code NICKI gets 15% off · not financial advice")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5, slide6], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
