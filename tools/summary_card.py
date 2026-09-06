#!/usr/bin/env python3
"""Summary card for the repo: what was asked, what was found, what was not.

Deliberately gives the null results equal weight to the finding. A card that
showed only the working signal would misrepresent six weeks in which most
tested claims did not survive.

Usage: python3 tools/summary_card.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
W, H = 1300, 900
BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
GREEN, RED, ORANGE = "#3fb950", "#f85149", "#f7931a"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

WORKS = [
    ("Spam filtering", "85% of spikes are spam-heavy and carry no signal"),
    ("Organic spike, flat price", "beats Bitcoin 49.0% vs 41.9%, p = 0.002"),
    ("In every market regime", "no reversal in bull, bear or flat"),
]
DOES_NOT = [
    ("Predicting direction", "price simply rising: +1.5pp, p = 0.54"),
    ("Sentiment", "net positive 97.6% of days, including every crash"),
    ("Influencer mentions", "7,053 calls, no better than coins nobody named"),
    ("Chasing a pump", "after a 200% week, 45% lose half in 90 days"),
    ("A bigger signal", "clearing the bar by more predicts nothing"),
    ("The same spike, late", "after a 5% run it is worth exactly zero"),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def main() -> None:
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         txt(60, 78, 40, TEXT, "Does social attention predict crypto prices?", 700),
         txt(60, 124, 24, SUB, "14 open-source projects, 6.5 years of data, 1,000 coins. Everything reproducible."),
         txt(60, 162, 24, SUB, "Most of what I tested did not survive. Those results are published too.")]

    # What works
    p += [f'<rect x="60" y="210" width="560" height="250" rx="14" fill="{PANEL}"/>',
          txt(90, 254, 26, GREEN, "What held up", 700)]
    for i, (head, sub) in enumerate(WORKS):
        y = 300 + i * 54
        p += [txt(90, y, 22, TEXT, head, 700), txt(90, y + 26, 19, SUB, sub)]

    # What doesn't
    p += [f'<rect x="660" y="210" width="580" height="450" rx="14" fill="{PANEL}"/>',
          txt(690, 254, 26, RED, "What did not", 700)]
    for i, (head, sub) in enumerate(DOES_NOT):
        y = 300 + i * 58
        p += [txt(690, y, 22, TEXT, head, 700), txt(690, y + 26, 19, SUB, sub)]

    # The honest summary of the finding
    p += [f'<rect x="60" y="490" width="560" height="170" rx="14" fill="{PANEL}"/>',
          txt(90, 534, 24, ORANGE, "Stated precisely", 700),
          txt(90, 574, 20, SUB, "A genuine attention spike on a coin whose"),
          txt(90, 600, 20, SUB, "price has not moved shifts the odds of"),
          txt(90, 626, 20, SUB, "beating Bitcoin over 3 days from 42% to 49%.")]

    p += [txt(60, 716, 24, TEXT, "It is an odds shift, not a prediction. Roughly half of these still lose.", 700),
          txt(60, 754, 21, SUB, "Live picks are tracked publicly, win or lose, and the tracker counts only what was actually published."),
          txt(60, 786, 21, SUB, "Every chart, threshold and rejected idea is in the repo with the reasoning that produced it."),
          txt(60, 840, 26, GREEN, "github.com/nickisanders/lunarcrush-projects", 700),
          txt(60, 872, 19, SUB, "Data: LunarCrush · not advice"),
          "</svg>"]

    OUT.mkdir(exist_ok=True)
    (OUT / "summary-card.svg").write_text("\n".join(p))
    print(f"Wrote {OUT / 'summary-card.svg'}")


if __name__ == "__main__":
    main()
