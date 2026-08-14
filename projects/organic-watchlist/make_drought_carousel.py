#!/usr/bin/env python3
"""Instagram carousel: five days of nothing, and why that is the point.

Writes out/instagram-drought/slide-N.svg (1080x1350).
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-drought"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, YELLOW, TRACK, DIM = "#3fb950", "#f85149", "#d29922", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 6

SPAM_FAILS = [("$TRAC", "100%"), ("$NEO", "100%"), ("$ETC", "89%"),
              ("$KCS", "86%"), ("$PENGU", "63%"), ("$QNT", "52%")]
WEAK_FAILS = [("$PUMP", "2.7"), ("$QNT", "2.7"), ("$VELO", "2.4"),
              ("$PENDLE", "2.4"), ("$XMR", "2.3"), ("$STETH", "2.2")]


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
{txt(M, 400, 46, SUB, "My daily crypto scanner has")}
{txt(M, 456, 46, SUB, "found nothing for")}
{txt(M, 620, 190, RED, "5 days", 800)}
{txt(M, 740, 54, TEXT, "That's not a bug.", 800)}
{txt(M, 820, 40, SUB, "But I checked anyway, because")}
{txt(M, 868, 40, SUB, "“found nothing” and “is broken”")}
{txt(M, 916, 40, SUB, "look identical from outside.")}
""", "swipe")


def slide2() -> str:
    return frame(2, f"""
{txt(M, 250, 56, TEXT, "What it looks for", 800)}
{txt(M, 320, 34, SUB, "1,000 coins scanned every morning, for one setup")}
{txt(M, 440, 56, GREEN, "1", 800)}
{txt(M + 64, 440, 40, TEXT, "A coin's conversation")}
{txt(M + 64, 490, 40, TEXT, "explodes past its own normal")}
{txt(M, 600, 56, GREEN, "2", 800)}
{txt(M + 64, 600, 40, TEXT, "It's real people, not bots")}
{txt(M + 64, 650, 40, TEXT, "(under 50% spam)")}
{txt(M, 760, 56, GREEN, "3", 800)}
{txt(M + 64, 760, 40, TEXT, "The price hasn't moved yet")}
{txt(M, 890, 38, SUB, "That combination beat Bitcoin over the next")}
{txt(M, 938, 38, SUB, "3 days 49% of the time, vs 42% for a random")}
{txt(M, 986, 38, SUB, "coin. All three, or it doesn't count.")}
""")


def slide3() -> str:
    return frame(3, f"""
{txt(M, 250, 56, TEXT, "First suspicion", 800)}
{txt(M, 340, 40, TEXT, "It only examines the 80 most")}
{txt(M, 392, 40, TEXT, "promising coins in detail.")}
{txt(M, 452, 38, SUB, "Checking all 1,000 would mean 1,000 API calls a day.")}
{txt(M, 550, 40, TEXT, "So what if the real candidates")}
{txt(M, 602, 40, TEXT, "were sitting at position 90?")}
{txt(M, 700, 44, GREEN, "I widened it to 200.", 700)}
{txt(M, 760, 38, SUB, "180 coins cleared the filters. More than double.")}
{txt(M, 870, 66, RED, "Zero extra finds.", 800)}
{txt(M, 950, 38, SUB, "Not one additional coin, anywhere near the bar.")}
{txt(M, 998, 38, SUB, "The scan was already seeing everything.")}
""")


def slide4() -> str:
    y = 420
    rows = ""
    for sym, val in SPAM_FAILS:
        rows += txt(M + 20, y, 34, TEXT, sym) + txt(M + 250, y, 34, RED, val, 700, "end")
        y += 52
    y2 = 420
    rows2 = ""
    for sym, val in WEAK_FAILS:
        rows2 += txt(M + 560, y2, 34, TEXT, sym) + txt(M + 810, y2, 34, YELLOW, val, 700, "end")
        y2 += 52
    return frame(4, f"""
{txt(M, 250, 56, TEXT, "What killed them", 800)}
{txt(M, 316, 34, SUB, "12 coins got close. They split exactly in half.")}
{txt(M, 384, 30, RED, "too much spam", 700)}
{txt(M + 560, 384, 30, YELLOW, "spike too weak", 700)}
{rows}
{rows2}
{txt(M, 800, 40, TEXT, "Six had real spikes made of bots.")}
{txt(M, 852, 40, TEXT, "Six had real crowds, too quiet.")}
{txt(M, 940, 38, SUB, "$QNT nearly made it twice and failed a")}
{txt(M, 988, 38, SUB, "different test each time.")}
""", "the bar is 3.0 standard deviations")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 260, 56, TEXT, "Is 5 days weird?", 800)}
{txt(M, 380, 44, GREEN, "No.", 800)}
{txt(M, 470, 40, TEXT, "In 6.5 years of history this setup")}
{txt(M, 522, 40, TEXT, "showed up 403 times across")}
{txt(M, 574, 40, TEXT, "2,402 days. About one in six.")}
{txt(M, 680, 40, TEXT, "Run the maths and a five-day")}
{txt(M, 732, 40, TEXT, "drought happens roughly")}
{txt(M, 830, 96, GREEN, "43%", 800)}
{txt(M + 230, 830, 40, TEXT, "of the time,")}
{txt(M, 900, 40, TEXT, "purely by chance.")}
{txt(M, 990, 38, SUB, "Two weeks would be 8%. That's when I'd audit.")}
""")


def slide6() -> str:
    return frame(6, f"""
{txt(M, 260, 56, TEXT, "Here's the temptation", 800)}
{txt(M, 370, 40, TEXT, "Drop the bar from 3.0 to 2.5 and")}
{txt(M, 422, 40, TEXT, "I'd have had six picks this week.")}
{txt(M, 520, 44, RED, "They'd also be coins my own", 700)}
{txt(M, 574, 44, RED, "research says carry no edge,", 700)}
{txt(M, 628, 44, RED, "dressed up as signals.", 700)}
{txt(M, 730, 38, SUB, "The thresholds aren't adjustable for exactly")}
{txt(M, 778, 38, SUB, "this reason. Move them to make content and")}
{txt(M, 826, 38, SUB, "the 49% I publish stops being true.")}
{txt(M, 920, 50, GREEN, "Five days of nothing is", 800)}
{txt(M, 976, 50, GREEN, "what working looks like.", 800)}
{txt(M, 1050, 34, SUB, "open source · github.com/nickisanders/lunarcrush-projects")}
""", "Data: LunarCrush · code NICKI gets 15% off · not financial advice")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5, slide6], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
