#!/usr/bin/env python3
"""Chart: what a real incident post looks like next to the ones that fool you.

Usage: python3 filter_chart.py
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    body = esc(s)
    if weight >= 700 and " " in str(s):
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            dx = size * (0.45 if prev.endswith("%") else 0.30)
            parts.append(f'<tspan dx="{dx:.2f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def wrap(s, n=64):
    out, line = [], ""
    for w in s.split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = f"{line} {w}".strip()
    if line: out.append(line)
    return out


CARDS = [
    {"verdict": "REAL", "col": GREEN, "coin": "$ZANO", "chars": 168, "others": 0,
     "text": "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO AND fUSD IMMEDIATELY. "
             "The $Zano blockchain will be rolled back by approximately 24 hours.",
     "why": "names the coin twice, warning sits 20 characters from it, no other project mentioned"},
    {"verdict": "NOISE", "col": RED, "coin": "$NOCK", "chars": 2434, "others": 4,
     "text": "For the Meridian Buildathon, I built NOCK. April 1: Drift on Solana lost $285M. "
             "April 18: Attackers drained $292M of rsETH from Kelp's bridge, used it as collateral on Aave...",
     "why": "names Bitget, Drift, Kelp and Aave. An incident report is about one project"},
    {"verdict": "NOISE", "col": RED, "coin": "$LIT", "chars": 79, "others": 0,
     "text": "My neighbors side light for their trash cans. Motion sensitive. Someone stole it",
     "why": "the topic “lit” is not the coin. The post never names Lighter"},
]


def render() -> str:
    W = 1300
    card_h = 168
    H = 190 + len(CARDS) * (card_h + 22) + 150
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 37, TEXT, "Three posts about hacks. One of them is real.", 700))
    o.append(txt(60, 112, 20, SUB,
                 "All three name a falling coin and all three contain words like drained, breach and stolen."))

    y = 170
    for c in CARDS:
        o.append(f'<rect x="60" y="{y}" width="1180" height="{card_h}" fill="{PANEL}" rx="8"/>')
        o.append(f'<rect x="60" y="{y}" width="6" height="{card_h}" fill="{c["col"]}" rx="3"/>')
        o.append(txt(92, y + 38, 22, TEXT, c["coin"], 700))
        o.append(txt(200, y + 38, 15, c["col"], c["verdict"], 700))
        o.append(txt(1216, y + 38, 15, SUB, f"{c['chars']:,} chars  ·  {c['others']} other projects named", 400, "end"))
        yy = y + 78
        for ln in wrap(c["text"], 92):
            o.append(txt(92, yy, 17, TEXT, ln))
            yy += 26
        o.append(txt(92, y + card_h - 20, 15, c["col"], c["why"]))
        y += card_h + 22

    o.append(txt(60, y + 44, 19, TEXT,
                 "Three rules, each one added after the tool got it wrong in public.", 700))
    o.append(txt(60, y + 74, 17, SUB,
                 "The post must name the coin. The warning must sit within 100 characters of that name. "
                 "It must not name more than one other project."))
    o.append(txt(60, y + 112, 14, GREY, "Source: LunarCrush topic posts, 2026-09-25 to 2026-09-27. Post content is reported, not verified."))
    o.append(txt(1240, y + 112, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    out = HERE / "out" / "filter.svg"
    out.write_text(render())
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
