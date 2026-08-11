#!/usr/bin/env python3
"""Instagram carousel for the daily organic watchlist.

Reads out/report.json so the slides always match the day's actual run.
Writes out/instagram/slide-N.svg (1080x1350).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, TRACK, DIM = "#3fb950", "#f85149", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5


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
{txt(M, 400, 82, TEXT, "Every alpha", 800)}
{txt(M, 494, 82, TEXT, "account has a", 800)}
{txt(M, 588, 82, TEXT, "pick for you", 800)}
{txt(M, 682, 82, TEXT, "every day.", 800)}
{txt(M, 810, 52, RED, "That's your first clue.", 700)}
""", "swipe")


def slide2() -> str:
    return frame(2, f"""
{txt(M, 260, 60, TEXT, "I built the opposite", 800)}
{txt(M, 330, 36, SUB, "a list that only fires when all three happen")}
{txt(M, 460, 60, GREEN, "1", 800)}
{txt(M + 70, 460, 40, TEXT, "A coin's conversation")}
{txt(M + 70, 512, 40, TEXT, "spikes way above its normal")}
{txt(M, 630, 60, GREEN, "2", 800)}
{txt(M + 70, 630, 40, TEXT, "It's real people, not bots")}
{txt(M + 70, 682, 40, TEXT, "(under 50% spam)")}
{txt(M, 800, 60, GREEN, "3", 800)}
{txt(M + 70, 800, 40, TEXT, "The price hasn't moved yet")}
{txt(M, 940, 38, SUB, "All three at once. Miss one and it doesn't count.")}
""")


def slide3() -> str:
    return frame(3, f"""
{txt(M, 250, 56, TEXT, "Does it work?", 800)}
{txt(M, 320, 36, SUB, "tested on 6.5 years, 997 coins")}
{txt(M, 460, 40, TEXT, "When all three line up, the coin beat")}
{txt(M, 512, 40, TEXT, "Bitcoin over the next 3 days:")}
{txt(M, 640, 120, GREEN, "49%", 800)}
{txt(M + 290, 620, 34, SUB, "of the time")}
{txt(M, 760, 40, TEXT, "A random coin on a random day:")}
{txt(M, 860, 90, DIM, "42%", 800)}
{txt(M, 990, 38, TEXT, "A 7 point edge. Not a money printer.")}
{txt(M, 1040, 38, TEXT, "Half of them still lose.")}
""", "an odds shift, not a prediction · not financial advice")


def slide4(report: dict) -> str:
    date = datetime.now(timezone.utc).strftime("%B %-d")
    entries = report.get("entries") or []
    near = report.get("nearMisses") or []
    if entries:
        rows = ""
        y = 520
        for e in entries[:4]:
            rows += txt(M, y, 44, GREEN, f"${e['symbol']}", 700)
            rows += txt(M + 240, y, 34, SUB,
                        f"{e['multiple']:.0f}x normal · {round(e['spam']*100)}% spam")
            y += 90
        head = txt(M, 250, 56, TEXT, f"Today, {date}", 800) + \
            txt(M, 330, 36, SUB, "genuine spikes, price hasn't reacted")
        tail = txt(M, 1040, 36, SUB, "every one shows its evidence")
        return frame(4, head + rows + tail)
    miss = ""
    if near:
        n = near[0]
        miss = (txt(M, 700, 36, SUB, "One got close:") +
                txt(M, 780, 52, TEXT, f"${n['symbol']}", 700) +
                txt(M, 850, 38, TEXT, f"flagged, then rejected: {n['failed']}") +
                txt(M, 916, 38, DIM, "That's not a crowd finding a coin.") +
                txt(M, 962, 38, DIM, "That's a campaign."))
    return frame(4, f"""
{txt(M, 250, 56, TEXT, f"Today, {date}", 800)}
{txt(M, 420, 130, TEXT, "Nothing.", 800)}
{txt(M, 500, 36, SUB, "the list is empty, and that is normal")}
{miss}
""", "this setup shows up about one day in six")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 340, 74, TEXT, "A list that has", 800)}
{txt(M, 424, 74, TEXT, "something for you", 800)}
{txt(M, 508, 74, TEXT, "every day isn't", 800)}
{txt(M, 592, 74, TEXT, "finding signals.", 800)}
{txt(M, 700, 74, RED, "It's filling a", 800)}
{txt(M, 784, 74, RED, "schedule.", 800)}
{txt(M, 900, 38, SUB, "Runs daily. Open source. Every post ships")}
{txt(M, 948, 38, SUB, "the hit rate so you can hold it accountable.")}
{txt(M, 1040, 42, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 1090, 42, GREEN, "lunarcrush-projects", 700)}
""", "Data: LunarCrush · code NICKI gets 15% off")


def main() -> None:
    report = json.loads((HERE / "out" / "report.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(), slide2(), slide3(), slide4(report), slide5()]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    state = "picks" if report.get("entries") else "empty"
    print(f"Wrote {TOTAL} slides ({state} day) to {OUT}")


if __name__ == "__main__":
    main()
