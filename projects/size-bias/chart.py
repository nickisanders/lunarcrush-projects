#!/usr/bin/env python3
"""Chart: both signals against market cap, in opposite directions.

Usage: python3 chart.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
RED, GREEN = "#f85149", "#3fb950"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
W, H = 1200, 780


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start"):
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def main() -> None:
    d = json.loads((HERE / "out" / "size_bias.json").read_text())
    bands, sp = d["bands"], d["spearman"]

    b = [txt(60, 62, 38, TEXT, "Two of these signals are measuring size", 700),
         txt(60, 96, 21, SUB, f"median value by market-cap band · {d['n']} tokens")]

    # 1080 usable over two panels is 540 each: label, bar, then the value.
    panels = [("cross-token accounts", "median_overlap", RED),
              ("creator concentration", "median_concentration", GREEN)]
    for pi, (title, key, col) in enumerate(panels):
        x0 = 70 + pi * 540
        peak = max(x[key] for x in bands) or 1
        b.append(txt(x0, 180, 25, TEXT, title, 700))
        for i, band in enumerate(bands):
            y = 230 + i * 92
            w = 290 * band[key] / peak
            b.append(txt(x0, y + 20, 20, SUB, band["label"]))
            b.append(f'<rect x="{x0+110}" y="{y}" width="{max(w,3):.0f}" height="30" '
                     f'rx="4" fill="{col}"/>')
            b.append(txt(x0 + 110 + max(w, 3) + 12, y + 22, 22, TEXT, f"{band[key]:.0%}", 700))

    b.append(f'<rect x="60" y="540" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, 584, 23, TEXT,
                 "Big tokens get mentioned by accounts that post about everything.", 700))
    b.append(txt(60, 616, 20, SUB,
                 "Small tokens have fewer people talking, so the loudest three own more of it."))
    b.append(txt(60, 668, 23, RED, "Neither gradient is manipulation. Both are arithmetic.", 700))
    b.append(txt(60, 706, 19, SUB,
                 f"Rank correlation with market cap: {sp['overlap_vs_mcap']:+.2f} and "
                 f"{sp['concentration_vs_mcap']:+.2f}. Real, and noisy."))
    b.append(txt(1140, 706, 17, SUB, "Data: LunarCrush", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    (HERE / "out" / "size_bias.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/size_bias.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/size_bias.png')"
        f".then(i=>console.log('out/size_bias.png',i.width+'x'+i.height));"], check=True)


if __name__ == "__main__":
    main()
