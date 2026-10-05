#!/usr/bin/env python3
"""Chart: spikes on top, the people behind them below, the floor underneath.

Usage: python3 chart.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
RED, GREEN, TRACK = "#f85149", "#3fb950", "#21262d"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
W, H = 1200, 770


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            parts.append(f'<tspan dx="{size * (0.45 if prev.endswith("%") else 0.30):.0f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def bars(rows, key, top, base, left, right, hot, colour, fmt, label_hot_only=True):
    peak = max(r[key] for r in rows)
    step = (right - left) / len(rows)
    bw = step - 9
    out = []
    for i, r in enumerate(rows):
        x = left + i * step
        h = (base - top) * r[key] / peak
        is_hot = r["day"] in hot
        out.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                   f'rx="3" fill="{colour if is_hot else "#30363d"}"/>')
        if is_hot or not label_hot_only:
            out.append(txt(x + bw / 2, base - h - 12, 21, colour, fmt(r[key]), 700, "middle"))
    return "".join(out)


def main() -> None:
    d = json.loads((HERE / "out" / "floor.json").read_text())
    rows, sym = d["recent"], d["symbol"]
    hot = {s["day"] for s in d["spikes_21d"]}
    L, R = 70, 1140
    body = [txt(60, 62, 38, TEXT, f"${sym} spiked {len(hot)} times in three weeks", 700),
            txt(60, 96, 21, SUB, "and more people turned up for every single one")]

    body.append(bars(rows, "interactions", 190, 500, L, R, hot, RED,
                     lambda v: f"{v/1e6:.2f}M"))
    body.append(f'<rect x="{L}" y="500" width="{R-L}" height="1.5" fill="{TRACK}"/>')
    peak = max(r["interactions"] for r in rows)
    body.append(f'<rect x="{L}" y="{500 - 310*d["baseline_30d"]/peak:.1f}" width="{R-L}" '
                f'height="1.5" fill="{SUB}" opacity="0.45"/>')
    body.append(txt(L, 170, 17, SUB, f"30-day normal {d['baseline_30d']/1e6:.2f}M"))
    body.append(txt(L, 526, 17, SUB, rows[0]["day"][5:]))
    body.append(txt(R, 526, 17, SUB, rows[-1]["day"][5:], 400, "end"))

    body.append(txt(60, 548, 21, TEXT, "people posting", 700))
    body.append(bars(rows, "people", 560, 650, L, R, hot, GREEN, lambda v: f"{v:,.0f}"))
    body.append(f'<rect x="{L}" y="650" width="{R-L}" height="1.5" fill="{TRACK}"/>')

    lift = d.get("floor_lift")
    body.append(txt(60, 708, 22, TEXT,
                    f"Between the spikes, attention sits {lift:.1f}x where it did two months ago.", 700))
    body.append(txt(60, 736, 19, SUB,
                    f"The crowd is not round-tripping. Price is up {d['price_90d_change']:.0%} "
                    f"over the same stretch."))
    body.append(txt(R, 736, 17, SUB, "Data: LunarCrush", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(body) + "</svg>")
    (HERE / "out" / "floor.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/floor.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/floor.png')"
        f".then(i=>console.log('out/floor.png',i.width+'x'+i.height));"], check=True)


if __name__ == "__main__":
    main()
