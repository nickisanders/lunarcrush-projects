#!/usr/bin/env python3
"""Chart: the 2021 metaverse cohort, then and now.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER, PURPLE = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922", "#a371f7"
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


def render(d: dict) -> str:
    W, H = 1300, 1040
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 37, TEXT, "The 2021 metaverse bags just woke up.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"{d['n']} gaming and NFT coins that peaked by 2022 and fell 90%+. "
                 f"{d['beat']} of {d['n']} beat the market today."))

    # The headline comparison: combined market cap then vs now.
    cy = 170
    o.append(f'<rect x="60" y="{cy}" width="1180" height="128" fill="{PANEL}" rx="8"/>')
    o.append(txt(84, cy + 36, 15, SUB, "COMBINED MARKET CAP OF ALL 29", 700))
    o.append(txt(84, cy + 92, 44, GREY, f"${d['mcapPeak'] / 1e9:,.0f}B", 700))
    o.append(txt(84 + 230, cy + 92, 20, SUB, "at their peaks"))
    o.append(txt(620, cy + 92, 44, AMBER, f"${d['mcapNow'] / 1e9:,.1f}B", 700))
    o.append(txt(620 + 160, cy + 92, 20, SUB, "today"))
    o.append(txt(1216, cy + 92, 30, RED, f"-{(1 - d['mcapNow'] / d['mcapPeak']) * 100:.0f}%", 700, "end"))

    # Coin rows: price today, how far off peak, crowd change.
    ly = 340
    o.append(txt(60, ly, 16, SUB, "COIN", 700))
    o.append(txt(330, ly, 16, SUB, "PEAK", 700, "end"))
    o.append(txt(470, ly, 16, SUB, "NOW", 700, "end"))
    o.append(txt(620, ly, 16, SUB, "TODAY", 700, "end"))
    o.append(txt(760, ly, 16, SUB, "CROWD, LAST WEEK vs PRIOR MONTH", 700))
    picks = [c for c in d["coins"] if c["symbol"] in
             ("SAND", "MANA", "AXS", "GALA", "ENJ", "APE", "ICP", "ILV", "FLOW", "OMI", "SLP", "CHR")]
    picks = sorted(picks, key=lambda c: -c["peakMcap"])[:11]
    mx = max(abs(c["crowdChange"]) for c in picks if c["crowdChange"] is not None)
    for i, c in enumerate(picks):
        y = ly + 36 + i * 46
        o.append(txt(60, y, 20, TEXT, f"${c['symbol']}", 700))
        o.append(txt(168, y, 15, GREY, c["name"][:14]))
        o.append(txt(330, y, 18, GREY, f"${c['peakMcap'] / 1e9:,.1f}B", 400, "end"))
        o.append(txt(470, y, 18, AMBER, f"${c['mcap'] / 1e6:,.0f}M", 700, "end"))
        o.append(txt(620, y, 19, GREEN if c["pct24h"] > 0 else RED, f"{c['pct24h']:+.0f}%", 700, "end"))
        cc = c["crowdChange"]
        if cc is not None:
            w = 260 * abs(cc) / mx
            col = BLUE if cc > 0 else RED
            x0 = 790
            o.append(f'<rect x="{x0 if cc > 0 else x0 - w:.1f}" y="{y - 14}" width="{w:.1f}" height="18" fill="{col}" rx="3"/>')
            o.append(txt(x0 + w + 10 if cc > 0 else x0 - w - 10, y, 16, col, f"{cc * 100:+.0f}%", 700,
                         "start" if cc > 0 else "end"))
    o.append(f'<line x1="790" y1="{ly + 14}" x2="790" y2="{ly + 36 + 11 * 46 - 30}" stroke="{GRID}"/>')

    by = ly + 36 + 11 * 46 + 6
    o.append(f'<rect x="60" y="{by}" width="1180" height="96" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, by + 38, 19, TEXT,
                 f"The crowd is coming back too: median {d['crowdMedian'] * 100:+.0f}% more people posting, "
                 f"and {d['crowdGrew']} of {d['n']} grew.", 700))
    o.append(txt(84, by + 72, 16, SUB,
                 "Which is the part a price screen cannot tell you, and the part that was missing in most of this year's bounces."))

    o.append(txt(60, 1012, 14, GREY,
                 f"Cohort defined by LunarCrush's own gaming and NFT tags plus a 90% drawdown, not by name. As of {d['asOf']}."))
    o.append(txt(1240, 1012, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "metaverse.json").read_text())
    out = HERE / "out" / "metaverse.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
