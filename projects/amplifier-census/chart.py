#!/usr/bin/env python3
"""Chart: one cross-token signal, produced by two unrelated behaviours.

Reads out/amplifiers.json, so the figure always matches the last run.

Usage: python3 chart.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, TRACK, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#161b22"
RED, GREEN, BLUE, GREY = "#f85149", "#3fb950", "#58a6ff", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, monospace"
W, H = 1200, 840


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
    d = json.loads((HERE / "out" / "amplifiers.json").read_text())
    tot = d["posts"] or 1
    b = [txt(60, 60, 36, TEXT, "One signal, two different behaviours", 700),
         txt(60, 94, 20, SUB,
             f"Posts from the {d['profiled']} accounts appearing across the most of "
             f"{d['verified_topics']} verified tokens, by tokens named per post")]

    rows = [("names 1 token", d["buckets"]["1"], GREY),
            ("names 2", d["buckets"]["2"], GREY),
            ("names 3 to 7", d["buckets"]["3-7"], GREY),
            ("names 8 or more", d["buckets"]["8+"], BLUE)]
    TOP, ROW, X0, BARW = 160, 62, 300, 560
    peak = max(n for _, n, _ in rows) or 1
    for i, (label, n, col) in enumerate(rows):
        y = TOP + i * ROW
        w = BARW * n / peak
        b.append(txt(X0 - 20, y + 26, 21, SUB, label, 400, "end"))
        b.append(f'<rect x="{X0}" y="{y}" width="{max(w,3):.0f}" height="34" rx="4" fill="{col}"/>')
        b.append(txt(X0 + max(w, 3) + 16, y + 27, 23, TEXT,
                     f"{n/tot*100:.0f}%", 700, "start", MONO))

    y = TOP + len(rows) * ROW + 14
    b.append(f'<rect x="60" y="{y}" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, y + 44, 25, TEXT,
                 f"One account reaches {d['max_topics']} of {d['verified_topics']} tokens. "
                 f"The median account in more than one reaches "
                 f"{d['median_topics_multi']:.0f}.", 700))

    # The two archetypes, which is the finding. A bar chart alone cannot show
    # that the same number comes from opposite behaviours.
    listy = max(d["profiles"], key=lambda p: p["median_tickers"])
    serial = max((p for p in d["profiles"] if p["list_share"] < 0.1),
                 key=lambda p: p["topics"], default=None)
    CY = y + 86
    panels = [("The list poster",
               f"{listy['median_tickers']:.0f} tickers in a typical post",
               f"{listy['posts']} posts reach {listy['topics']} tokens", GREY)]
    if serial:
        panels.append(("The serial poster",
                       f"{serial['median_tickers']:.0f} ticker in a typical post",
                       f"{serial['posts']} posts reach {serial['topics']} tokens", RED))
    for i, (title, line1, line2, col) in enumerate(panels):
        x = 60 + i * 560
        b.append(f'<rect x="{x}" y="{CY}" width="520" height="146" rx="8" fill="{PANEL}"/>')
        b.append(f'<rect x="{x}" y="{CY}" width="5" height="146" rx="2.5" fill="{col}"/>')
        b.append(txt(x + 26, CY + 42, 23, TEXT, title, 700))
        b.append(txt(x + 26, CY + 84, 24, col, line1, 700))
        b.append(txt(x + 26, CY + 120, 19, SUB, line2))

    b.append(txt(60, CY + 198, 23, TEXT,
                 "Both register as an account that also posts about other tokens.", 700))
    b.append(txt(60, CY + 230, 19, SUB,
                 "Which is why the posts behind the number have to be read."))
    b.append(txt(60, H - 22, 16, SUB, "Source: LunarCrush"))
    b.append(txt(1140, H - 22, 16, SUB,
                 "github.com/nickisanders/lunarcrush-projects", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    (HERE / "out" / "amplifiers.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/amplifiers.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/amplifiers.png')"
        f".then(i=>console.log('out/amplifiers.png',i.width+'x'+i.height));"], check=True)


if __name__ == "__main__":
    main()
