#!/usr/bin/env python3
"""Chart: a coin named after the most common word in crypto.

Usage: python3 one_chart.py
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER, ORANGE = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922", "#f7931a"
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


def human(n: float) -> str:
    if n >= 1e9: return f"{n / 1e9:.1f}B"
    # A 1.3M contributor count rounds to "1M" at zero decimals and reads as a
    # different number from the 1.3 million quoted in the panel below.
    if n >= 1e6: return f"{n / 1e6:.1f}M" if n < 1e7 else f"{n / 1e6:.0f}M"
    if n >= 1e3: return f"{n / 1e3:.0f}k"
    return f"{n:,.0f}"


def render(d: dict) -> str:
    W, H = 1300, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "$ONE is up 446% this week. Good luck measuring it.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"{d['name']} is a ${d['mcap'] / 1e6:.0f}M coin, #{d['mcapRank']} by market cap. Its ticker is the word “one”."))

    # Log bars: topic vs BTC vs the coin.
    by = 230
    rows = [("the word “one”, 24h", d["topicInteractions"], RED, f"{human(d['topicContributors'])} people"),
            ("Bitcoin's entire daily conversation", d["btcInteractions"], ORANGE, ""),
            ("$ONE the coin, 24h", d["coinInteractions"], BLUE, f"{d['crowdNow']:.0f} people a day")]
    o.append(txt(60, by - 26, 17, TEXT, "INTERACTIONS IN 24 HOURS, LOG SCALE", 700))
    mx = math.log10(d["topicInteractions"])
    mn = math.log10(d["coinInteractions"] / 3)
    bw = 900
    for i, (lab, v, col, note) in enumerate(rows):
        y = by + i * 96
        w = bw * (math.log10(v) - mn) / (mx - mn)
        o.append(f'<rect x="60" y="{y}" width="{w:.1f}" height="56" fill="{col}" rx="5"/>')
        o.append(txt(74, y - 10, 16, TEXT, lab, 700))
        o.append(txt(74, y + 36, 26, "#ffffff", human(v), 700))
        if note:
            o.append(txt(w + 76, y + 36, 16, SUB, note))
    o.append(txt(60, by + 3 * 96 + 4, 15, SUB,
                 f"The word outruns the coin by {d['topicInteractions'] / d['coinInteractions']:,.0f}x, "
                 f"and outruns all of Bitcoin by {d['topicInteractions'] / d['btcInteractions']:.0f}x."))

    # Price + crowd, last 30 days.
    py0, py1 = 560, 700
    s = d["series"]
    n = len(s)
    def X(i): return 60 + 1180 * i / (n - 1)
    closes = [x["close"] for x in s]
    lo, hi = min(closes) * 0.9, max(closes) * 1.1
    def Y(v): return py1 - (py1 - py0) * (v - lo) / (hi - lo)
    o.append(txt(60, py0 - 18, 16, TEXT, "THE ACTUAL COIN, LAST 30 DAYS", 700))
    path = "M" + " L".join(f"{X(i):.1f},{Y(x['close']):.1f}" for i, x in enumerate(s))
    o.append(f'<path d="{path}" fill="none" stroke="{ORANGE}" stroke-width="3" stroke-linejoin="round"/>')
    o.append(txt(1240, Y(closes[-1]) - 14, 16, ORANGE, f"${d['price']:.5f}", 700, "end"))
    o.append(txt(60, Y(closes[0]) + 22, 15, SUB, f"${closes[0]:.5f}"))

    # Crowd panel.
    cy = 740
    o.append(f'<rect x="60" y="{cy}" width="1180" height="96" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, cy + 32, 15, SUB, "HOW MANY PEOPLE ACTUALLY POST ABOUT THE COIN, PER DAY", 700))
    o.append(txt(84, cy + 70, 30, TEXT, f"{d['crowdBefore']:.0f}", 700))
    o.append(txt(150, cy + 70, 16, SUB, "before the run"))
    o.append(txt(320, cy + 70, 30, GREEN, f"{d['crowdNow']:.0f}", 700))
    o.append(txt(390, cy + 70, 16, SUB, "now"))
    o.append(txt(620, cy + 70, 16, TEXT,
                 f"1.3 million people used the word. {d['crowdNow']:.0f} are talking about the coin.", 700))

    o.append(txt(60, 872, 14, GREY,
                 f"Source: LunarCrush, {d['asOf']}. Topic interactions are for the bare ticker as a word, not the coin."))
    o.append(txt(1240, 872, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "one.json").read_text())
    out = HERE / "out" / "one.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
