#!/usr/bin/env python3
"""Chart: the month's biggest price gains against its biggest crowd gains.

Usage: python3 chart.py
"""

import json
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


def render(d: dict) -> str:
    W, H = 1300, 1010
    both = set(d["both"])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 37, TEXT, f"{d['month']}'s best coins and its loudest coins are not the same list.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Only {len(both)} of 10 appear on both. Bitcoin {d['btc']:+.0f}%, market median {d['market']:+.0f}%."))

    lx, rx = 60, 700
    top = 200
    o.append(txt(lx, top - 26, 17, ORANGE, "BIGGEST PRICE GAINS", 700))
    o.append(txt(rx, top - 26, 17, BLUE, "BIGGEST CROWD GAINS", 700))
    o.append(txt(lx, top - 6, 14, SUB, "over 30 days"))
    o.append(txt(rx, top - 6, 14, SUB, "people posting a day, last week of the month vs the week before it"))

    rows_l = {r["symbol"]: i for i, r in enumerate(d["price"])}
    rows_r = {r["symbol"]: i for i, r in enumerate(d["crowd"])}
    step = 56

    # Connectors first, so the rows sit on top of them.
    for s in both:
        y1 = top + 28 + rows_l[s] * step
        y2 = top + 28 + rows_r[s] * step
        o.append(f'<path d="M{lx + 480},{y1 - 6} C{lx + 560},{y1 - 6} {rx - 60},{y2 - 6} {rx - 14},{y2 - 6}" '
                 f'fill="none" stroke="{GREEN}" stroke-width="2" opacity="0.55"/>')

    for i, r in enumerate(d["price"]):
        y = top + 28 + i * step
        hot = r["symbol"] in both
        o.append(txt(lx, y, 21, GREEN if hot else TEXT, f"${r['symbol']}", 700))
        o.append(txt(lx + 130, y, 15, GREY, r["name"][:14]))
        o.append(txt(lx + 330, y, 20, ORANGE, f"+{r['pct30d']:.0f}%", 700, "end"))
        c = r["crowdChange"] * 100
        o.append(txt(lx + 470, y, 16, GREEN if c > 60 else RED if c < 10 else SUB,
                     f"crowd {c:+.0f}%", 700, "end"))

    for i, r in enumerate(d["crowd"]):
        y = top + 28 + i * step
        hot = r["symbol"] in both
        o.append(txt(rx, y, 21, GREEN if hot else TEXT, f"${r['symbol']}", 700))
        o.append(txt(rx + 120, y, 20, BLUE, f"+{r['crowdChange'] * 100:.0f}%", 700))
        o.append(txt(rx + 250, y, 15, SUB, f"{r['crowdBefore']:,.0f} to {r['crowdAfter']:,.0f} a day"))
        o.append(txt(1240, y, 16, ORANGE, f"price +{r['pct30d']:.0f}%", 700, "end"))

    by = top + 28 + 10 * step + 26
    o.append(f'<rect x="60" y="{by}" width="1180" height="118" fill="{PANEL}" rx="6"/>')
    ray = next((r for r in d["price"] if r["symbol"] == "RAY"), None)
    qnt = next((r for r in d["price"] if r["symbol"] == "QNT"), None)
    if ray:
        o.append(txt(84, by + 40, 19, TEXT,
                     f"$RAY rose {ray['pct30d']:.0f}% and its crowd grew {ray['crowdChange'] * 100:.0f}%. "
                     f"Almost nobody new turned up for it.", 700))
    if qnt:
        o.append(txt(84, by + 76, 19, TEXT,
                     f"$QNT rose {qnt['pct30d']:.0f}% and went from {qnt['crowdBefore']:,.0f} to "
                     f"{qnt['crowdAfter']:,.0f} people a day. Everyone did.", 700))
    o.append(txt(84, by + 102, 15, SUB,
                 "A coin can double with no audience, and an audience can arrive without the price doing much."))

    o.append(txt(60, 982, 14, GREY,
                 f"Coins over $100M with real volume. Source: LunarCrush, as of {d['asOf']}."))
    o.append(txt(1240, 982, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "month.json").read_text())
    out = HERE / "out" / "month.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
