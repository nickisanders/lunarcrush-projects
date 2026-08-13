#!/usr/bin/env python3
"""Instagram carousel: the BTC-to-alts attention cascade does not exist.

Writes out/instagram/slide-N.svg (1080x1350).
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, BLUE, YELLOW, TRACK, DIM = "#3fb950", "#f85149", "#58a6ff", "#d29922", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 6


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
{txt(M, 380, 46, SUB, "“Bitcoin pumps first,")}
{txt(M, 436, 46, SUB, "then majors, then alts,")}
{txt(M, 492, 46, SUB, "then memes.”")}
{txt(M, 620, 84, TEXT, "You've read that", 800)}
{txt(M, 712, 84, TEXT, "a thousand times.", 800)}
{txt(M, 840, 66, RED, "It isn't true.", 800)}
""", "swipe for what the data actually shows")


def slide2() -> str:
    return frame(2, f"""
{txt(M, 260, 58, TEXT, "What I measured", 800)}
{txt(M, 370, 40, TEXT, "Every day since 2020, I sorted")}
{txt(M, 422, 40, TEXT, "every coin into tiers by its size")}
{txt(M, 474, 40, TEXT, "at that moment:")}
{txt(M + 30, 570, 40, GREEN, "Bitcoin")}
{txt(M + 30, 626, 40, GREEN, "The majors")}
{txt(M + 30, 682, 40, BLUE, "Large alts")}
{txt(M + 30, 738, 40, YELLOW, "Mid alts")}
{txt(M + 30, 794, 40, DIM, "The long tail")}
{txt(M, 900, 42, TEXT, "Then one simple question:")}
{txt(M, 968, 44, RED, "When Bitcoin lights up Monday,", 700)}
{txt(M, 1022, 44, RED, "does the tier below light up Tuesday?", 700)}
""")


def slide3() -> str:
    # miniature of the lead-lag curve: peak at centre, flat elsewhere
    cx, cy, cw, ch = M, 520, W - 2 * M, 300
    lags = [-3, -2, -1, 0, 1, 2, 3]
    series = [("majors", GREEN, [-0.02, -0.03, -0.05, 0.281, 0.01, -0.05, -0.03]),
              ("large alts", BLUE, [-0.02, -0.02, -0.07, 0.142, 0.02, 0.00, 0.01]),
              ("mid alts", YELLOW, [-0.01, 0.01, 0.01, 0.082, 0.00, -0.04, -0.02])]
    def X(k): return cx + (k + 3) / 6 * cw
    def Y(v): return cy + ch - (v + 0.1) / 0.45 * ch
    body = [txt(M, 250, 58, TEXT, "The answer", 800),
            txt(M, 320, 36, SUB, "how strongly BTC relates to each tier N days later"),
            f'<rect x="{X(0.4):.0f}" y="{cy}" width="{X(3)-X(0.4):.0f}" height="{ch}" fill="#f8514915"/>',
            txt(int((X(0.4)+X(3))/2), cy + 34, 24, RED, "folklore says here", 400, "middle"),
            f'<line x1="{X(0):.0f}" y1="{cy}" x2="{X(0):.0f}" y2="{cy+ch}" stroke="#30363d" stroke-width="2" stroke-dasharray="6 6"/>']
    for name, color, vals in series:
        pts = " ".join(f"{X(k):.0f},{Y(v):.1f}" for k, v in zip(lags, vals))
        body.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round"/>')
        body.append(f'<circle cx="{X(0):.0f}" cy="{Y(vals[3]):.0f}" r="8" fill="{color}"/>')
    body.append(txt(int(X(0)), cy + ch + 44, 26, TEXT, "same day", 600, "middle"))
    body.append(txt(int(X(-3)), cy + ch + 44, 24, SUB, "-3d", 400, "middle"))
    body.append(txt(int(X(3)), cy + ch + 44, 24, SUB, "+3d", 400, "middle"))
    body.append(txt(M, 960, 46, TEXT, "Every line peaks the same day.", 700))
    body.append(txt(M, 1016, 40, SUB, "All ten tier pairs. Nothing at +1, +2, +3."))
    return frame(3, "\n".join(body))


def slide4() -> str:
    return frame(4, f"""
{txt(M, 300, 82, TEXT, "Attention doesn't", 800)}
{txt(M, 392, 82, TEXT, "trickle down.", 800)}
{txt(M, 520, 62, GREEN, "It arrives", 800)}
{txt(M, 592, 62, GREEN, "everywhere at once.", 800)}
{txt(M, 730, 40, SUB, "Which makes sense once you think about it.")}
{txt(M, 786, 40, SUB, "There's no delivery mechanism. The same")}
{txt(M, 838, 40, SUB, "people scroll the same feed at the same")}
{txt(M, 890, 40, SUB, "time. Nobody hears about Bitcoin Monday")}
{txt(M, 942, 40, SUB, "and gets around to alts on Thursday.")}
""")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 260, 58, TEXT, "Why it matters", 800)}
{txt(M, 370, 42, TEXT, "The cascade is only useful if")}
{txt(M, 424, 42, TEXT, "there's a gap. Watch the tier above")}
{txt(M, 478, 42, TEXT, "you, act before yours catches up.")}
{txt(M, 580, 46, RED, "There is no gap.", 700)}
{txt(M, 680, 42, TEXT, "By the time you notice Bitcoin")}
{txt(M, 734, 42, TEXT, "trending, the alt conversation")}
{txt(M, 788, 42, TEXT, "already happened.")}
{txt(M, 900, 54, RED, "You're not early.", 800)}
{txt(M, 966, 54, RED, "You're simultaneous.", 800)}
""")


def slide6() -> str:
    return frame(6, f"""
{txt(M, 280, 58, TEXT, "Three down", 800)}
{txt(M, 390, 40, TEXT, "Crypto beliefs I've tested and buried:")}
{txt(M + 20, 480, 38, DIM, "1. Rented attention dies faster")}
{txt(M + 20, 536, 38, DIM, "2. Attention breadth predicts alt season")}
{txt(M + 20, 592, 38, DIM, "3. Attention cascades down the market")}
{txt(M, 700, 40, TEXT, "One finding has survived.")}
{txt(M, 756, 40, TEXT, "It's more believable because of")}
{txt(M, 808, 40, TEXT, "the graveyard around it.")}
{txt(M, 920, 42, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 972, 42, GREEN, "lunarcrush-projects", 700)}
{txt(M, 1050, 34, SUB, "Data: LunarCrush · code NICKI gets 15% off")}
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5, slide6], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
