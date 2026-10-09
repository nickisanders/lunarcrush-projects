#!/usr/bin/env python3
"""Chart: the volume is machines, the people are tiny.

Usage: python3 chart.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
RED, GREEN, BLUE, GREY = "#f85149", "#3fb950", "#58a6ff", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, monospace"
W, H = 1200, 900


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{body}</text>')


def main() -> None:
    d = json.loads((HERE / "out" / "traders.json").read_text())
    c = d["concentration"]

    b = [txt(60, 62, 37, TEXT,
             f"{d['addresses']:,} addresses traded ${d['notional']/1e6:,.0f}M. "
             f"The median did ${d['median_volume']:,.0f}.", 700),
         txt(60, 96, 20, SUB,
             "Polymarket, one week on Polygon. Trader-to-trader fills only; "
             "the exchange router is excluded.")]

    # Concentration bars. A linear axis is right here because the quantity is a
    # share of one total and the reader is comparing shares to each other.
    rows = [("top 10 addresses", c["10"], RED),
            ("top 100", c["100"], RED),
            ("top 1,000", c["1000"], BLUE),
            ("top 5,000", c["5000"], BLUE),
            (f"the other {d['addresses']-5000:,}", 1 - c["5000"], GREY)]
    TOP, ROW, X0, BARW = 160, 66, 300, 620
    b.append(txt(60, TOP - 24, 21, TEXT, "share of all volume", 700))
    for i, (label, share, col) in enumerate(rows):
        y = TOP + i * ROW
        w = BARW * share
        b.append(txt(X0 - 20, y + 26, 21, SUB, label, 400, "end"))
        b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="34" rx="4" fill="{TRACK}"/>')
        b.append(f'<rect x="{X0}" y="{y}" width="{max(w,4):.0f}" height="34" rx="4" fill="{col}"/>')
        b.append(txt(X0 + BARW + 16, y + 27, 23, TEXT, f"{share*100:.1f}%", 700, "start", MONO))

    y = TOP + len(rows) * ROW + 10
    b.append(f'<rect x="60" y="{y}" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, y + 44, 24, TEXT,
                 "The biggest accounts are not people with opinions.", 700))

    # The honest part: maker share and breadth are what separate a market maker
    # from a whale, and the distinction decides what the concentration means.
    b.append(txt(60, y + 84, 17, SUB, "largest addresses by volume"))
    hx = [60, 300, 470, 650, 880]
    for x, head in zip(hx, ["", "volume", "fills", "outcome tokens", "quotes posted"]):
        b.append(txt(x if head else 60, y + 112, 16, SUB, head, 400,
                     "start" if head != "volume" else "start"))
    for i, t in enumerate(d["top10"][:4]):
        ty = y + 144 + i * 30
        b.append(txt(60, ty, 18, SUB, t["address"][:10] + "..", 400, "start", MONO))
        b.append(txt(300, ty, 18, TEXT, f"${t['volume']/1e6:,.1f}M", 400, "start", MONO))
        b.append(txt(470, ty, 18, TEXT, f"{t['fills']:,}", 400, "start", MONO))
        b.append(txt(650, ty, 18, TEXT, f"{t['tokens']:,}", 400, "start", MONO))
        b.append(txt(880, ty, 18, TEXT, f"{t['maker_share']*100:.0f}%", 400, "start", MONO))

    # The table ends at y+234; the closing lines sit below that, not on top of
    # it, which the first render did.
    close = y + 272
    b.append(txt(60, close, 22, RED,
                 "Nobody holds views on nine thousand questions.", 700))
    b.append(txt(60, close + 30, 19, SUB,
                 "That is inventory management, and it is most of what the volume is."))
    b.append(txt(1140, H - 20, 16, SUB,
                 "github.com/nickisanders/lunarcrush-projects", 400, "end"))
    b.append(txt(60, H - 20, 16, SUB, "Source: Polygon logs, 2026-10-01 to 10-08"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    (HERE / "out" / "traders.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/traders.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/traders.png')"
        f".then(i=>console.log('out/traders.png',i.width+'x'+i.height));"], check=True)


if __name__ == "__main__":
    main()
