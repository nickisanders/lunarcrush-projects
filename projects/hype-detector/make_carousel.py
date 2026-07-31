#!/usr/bin/env python3
"""Generate an Instagram 'specimen' carousel (1080x1350) from the top verdict
in out/report.json: the anatomy of one manufactured hype spike.

Writes out/instagram/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('sharp');[1,2,3,4].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"
"""

import json
from datetime import datetime, timezone
from pathlib import Path

W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, YELLOW, TRACK = "#3fb950", "#f85149", "#d29922", "#21262d"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
TOTAL = 4


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """Word gaps via tspan dx: librsvg loses spaces at heavy weights. The %
    glyph overhangs its advance width, so gaps after it need to be wider."""
    words = text.split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        factor = 0.45 if prev.endswith("%") else 0.30
        parts.append(f'<tspan dx="{size * factor:.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x: int, y: int, size: int, fill: str, content: str, weight: int = 400, anchor: str = "start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in content else esc(content)
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>'
    )


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W / 2 + (i - (TOTAL - 1) / 2) * 36}" cy="{H - 60}" r="7" '
        f'fill="{TEXT if i == n - 1 else TRACK}"/>'
        for i in range(TOTAL)
    )
    f = txt(M, H - 110, 28, SUB, footer) if footer else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{txt(M, 102, 30, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}
{body}
{f}
{dots}
</svg>"""


def evidence_bar(label: str, pct: int, y: int, color: str) -> str:
    bar_w = W - 2 * M - 160
    w = max(8, round(bar_w * pct / 100))
    return f"""
{txt(M, y, 34, TEXT, label)}
<rect x="{M}" y="{y + 22}" width="{bar_w}" height="34" rx="9" fill="{TRACK}"/>
<rect x="{M}" y="{y + 22}" width="{w}" height="34" rx="9" fill="{color}"/>
{txt(M + bar_w + 24, y + 50, 36, color, f"{pct}%", 700)}"""


def main() -> None:
    report = json.loads((HERE / "out" / "report.json").read_text())
    top = report["verdicts"][0]
    sym = top["symbol"]
    score = top["score"]
    spam = round(top["evidence"]["spamRatio"] * 100)
    conc = round(top["evidence"]["top3CreatorShare"] * 100)
    date = datetime.now(timezone.utc).strftime("%B %d")

    s1 = frame(
        1,
        f"""
{txt(M, 400, 96, TEXT, "3 accounts", 800)}
{txt(M, 515, 96, TEXT, "manufactured", 800)}
{txt(M, 630, 96, TEXT, f"{conc}% of the hype", 800)}
{txt(M, 745, 96, RED, "for one coin.", 800)}
{txt(M, 880, 44, SUB, f"Caught live, {date}.")}
""",
        "swipe for the anatomy",
    )

    s2 = frame(
        2,
        f"""
{txt(M, 280, 72, TEXT, "The specimen", 800)}
{txt(M, 400, 60, RED, f"${sym}", 800)}
{txt(M + 260, 400, 44, SUB, f"manufactured score {score}/100")}
{evidence_bar("Posts flagged as spam", spam, 500, RED)}
{evidence_bar("Interactions from top 3 accounts", conc, 660, RED)}
{evidence_bar("Verdict threshold", 60, 820, YELLOW)}
{txt(M, 1000, 38, TEXT, "A community discovering a coin")}
{txt(M, 1052, 38, TEXT, "does not look like this.")}
""",
        "in a genuine social spike, 2+ standard deviations above baseline",
    )

    s3 = frame(
        3,
        f"""
{txt(M, 280, 72, TEXT, "How the score works", 800)}
<circle cx="{M + 10}" cy="405" r="9" fill="{GREEN}"/>
{txt(M + 48, 420, 40, TEXT, "Scan 1,000 coins every day")}
<circle cx="{M + 10}" cy="525" r="9" fill="{GREEN}"/>
{txt(M + 48, 540, 40, TEXT, "Find real spikes: 2+ std devs")}
{txt(M + 48, 595, 40, TEXT, "above the coin's own baseline")}
<circle cx="{M + 10}" cy="700" r="9" fill="{GREEN}"/>
{txt(M + 48, 715, 40, TEXT, "Score 0-100: spam share,")}
{txt(M + 48, 770, 40, TEXT, "creator concentration,")}
{txt(M + 48, 825, 40, TEXT, "sentiment uniformity")}
<circle cx="{M + 10}" cy="930" r="9" fill="{GREEN}"/>
{txt(M + 48, 945, 40, TEXT, "Weights come from a 6.5-year")}
{txt(M + 48, 1000, 40, TEXT, "backtest, not vibes")}
""",
        "the backtest: 85% of hype spikes are spam, and they underperform",
    )

    s4 = frame(
        4,
        f"""
{txt(M, 380, 84, TEXT, "Check the hype", 800)}
{txt(M, 480, 84, TEXT, "before it checks", 800)}
{txt(M, 580, 84, RED, "your bags.", 800)}
{txt(M, 720, 42, SUB, "Open source, daily, evidence shown:")}
{txt(M, 790, 46, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 850, 46, GREEN, "lunarcrush-projects", 700)}
{txt(M, 990, 42, SUB, "Data: LunarCrush")}
{txt(M, 1055, 46, TEXT, "Code NICKI gets 15% off", 700)}
""",
    )

    OUT.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([s1, s2, s3, s4], 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides for ${sym} ({score}/100) to {OUT}")


if __name__ == "__main__":
    main()
