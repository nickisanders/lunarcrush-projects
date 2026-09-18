#!/usr/bin/env python3
"""Chart: the chance a price move triggers an attention spike, up vs down.

Usage: python3 chart.py
"""

import json
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


def render(d: dict) -> str:
    W, H = 1300, 860
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "Crypto talks about pumps, not dumps.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Chance that a day's price move triggers an attention spike. {d['coinDays']:,} coin-days, 2020 to 2026."))

    # Grouped bars: for each move size, P(spike|up) vs P(spike|down), plus the flat reference line.
    bx, by, bw, bh = 100, 190, 700, 380
    mx = max(r["pUp"] for r in d["rows"]) * 1.15
    o.append(txt(bx, by - 26, 17, TEXT, "CHANCE OF A SPIKE, BY WHAT THE PRICE DID THAT DAY", 700))
    for lv in (0.05, 0.10):
        y = by + bh - lv / mx * bh
        o.append(f'<line x1="{bx}" y1="{y:.1f}" x2="{bx + bw}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(txt(bx - 10, y + 5, 13, SUB, f"{lv * 100:.0f}%", 400, "end"))
    yf = by + bh - d["pFlat"] / mx * bh
    o.append(f'<line x1="{bx}" y1="{yf:.1f}" x2="{bx + bw}" y2="{yf:.1f}" stroke="{AMBER}" stroke-width="2" stroke-dasharray="6 5"/>')
    o.append(txt(bx + bw + 10, yf + 5, 14, AMBER, f"flat day  {d['pFlat'] * 100:.1f}%", 700))
    n = len(d["rows"])
    slot = bw / n
    for i, r in enumerate(d["rows"]):
        cx = bx + i * slot + slot / 2
        w = 90
        hu = r["pUp"] / mx * bh
        hd = r["pDown"] / mx * bh
        o.append(f'<rect x="{cx - w - 6:.1f}" y="{by + bh - hu:.1f}" width="{w}" height="{hu:.1f}" fill="{GREEN}" rx="5"/>')
        o.append(f'<rect x="{cx + 6:.1f}" y="{by + bh - hd:.1f}" width="{w}" height="{hd:.1f}" fill="{RED}" rx="5"/>')
        o.append(txt(cx - w / 2 - 6, by + bh - hu - 12, 20, TEXT, f"{r['pUp'] * 100:.1f}%", 700, "middle"))
        o.append(txt(cx + w / 2 + 6, by + bh - hd - 12, 20, TEXT, f"{r['pDown'] * 100:.1f}%", 700, "middle"))
        o.append(txt(cx, by + bh + 28, 16, TEXT, f"±{r['move'] * 100:.0f}% day", 700, "middle"))
        o.append(txt(cx, by + bh + 52, 22, AMBER, f"{r['ratio']:.1f}x", 700, "middle"))
    o.append(f'<rect x="{bx}" y="{by + bh}" width="{bw}" height="1" fill="{GRID}"/>')
    o.append(f'<rect x="{bx}" y="{by + bh + 74}" width="14" height="14" fill="{GREEN}" rx="2"/>')
    o.append(txt(bx + 22, by + bh + 86, 14, SUB, "price up"))
    o.append(f'<rect x="{bx + 110}" y="{by + bh + 74}" width="14" height="14" fill="{RED}" rx="2"/>')
    o.append(txt(bx + 132, by + bh + 86, 14, SUB, "price down"))
    o.append(txt(bx + 250, by + bh + 86, 14, SUB, f"ratio is up over down. 95% CI on the 5% ratio: [{d['ci5'][0]:.1f}, {d['ci5'][1]:.1f}]"))

    # Right panel: composition.
    rx = 880
    o.append(txt(rx, by - 26, 17, TEXT, "WHAT SPIKE DAYS LOOK LIKE", 700))
    c, b = d["spikeComposition"], d["baseComposition"]
    segs = [("up 5%+", "up5", GREEN), ("in between", "flat", GREY), ("down 5%+", "down5", RED)]
    for j, (lab, key, src) in enumerate((("all days", "base", b), ("spike days", "spike", c))):
        y = by + 20 + j * 130
        o.append(txt(rx, y, 15, SUB, lab.upper(), 700))
        x = rx
        for name, k, col in segs:
            w = 360 * src[k]
            o.append(f'<rect x="{x:.1f}" y="{y + 12}" width="{w:.1f}" height="44" fill="{col}"/>')
            if w > 40:
                o.append(txt(x + w / 2, y + 40, 15, "#ffffff", f"{src[k] * 100:.0f}%", 700, "middle"))
            x += w
        o.append(txt(rx, y + 78, 13, GREY, "green up 5%+ · grey in between · red down 5%+"))
    o.append(txt(rx, by + 300, 15, TEXT, "Up and down days are equally common.", 700))
    o.append(txt(rx, by + 322, 15, TEXT, "Spike days are 27% up and 12% down.", 700))

    o.append(txt(60, 750, 19, TEXT,
                 "A coin falling 5% is barely more interesting to the crowd than a coin doing nothing.", 700))
    o.append(txt(60, 782, 15, SUB,
                 "Spike: interactions 3+ standard deviations above the coin's own trailing 30 days. Coins over $50M cap and $1M volume."))
    o.append(txt(60, 826, 14, GREY, "Source: LunarCrush daily history, 1,000 coins. Bitcoin excluded as the benchmark."))
    o.append(txt(1240, 826, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "asymmetry.json").read_text())
    out = HERE / "out" / "asymmetry.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
