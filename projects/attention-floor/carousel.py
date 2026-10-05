#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the attention-floor finding.

Reads out/floor.json, so the slides always match the last run of floor.py. A
carousel with numbers typed in by hand goes stale the moment the data moves,
and the spike day in particular keeps settling for hours after midnight UTC.

Writes out/instagram/slide-N.svg and rasterizes them.

Usage: python3 carousel.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#161b22"
RED, GREEN, AMBER = "#f85149", "#3fb950", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """librsvg drops word spaces at weight >= 700, so set them by hand. The %
    glyph overhangs its advance width and needs a wider gap after it."""
    words = str(text).split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        parts.append(f'<tspan dx="{size * (0.45 if prev.endswith("%") else 0.30):.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x, y, size, fill, content, weight=400, anchor="start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in str(content) else esc(content)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>')


def wrap(x, y, size, fill, text, width, weight=400, lh=1.42) -> str:
    """Greedy wrap at an estimated glyph width. Measured against this font at
    these sizes; close enough that nothing has overrun the margin."""
    per = size * (0.54 if weight >= 700 else 0.50)
    out, line, cy = [], [], y
    for word in str(text).split():
        if line and (len(" ".join(line + [word])) * per) > width:
            out.append(txt(x, cy, size, fill, " ".join(line), weight))
            line, cy = [word], cy + size * lh
        else:
            line.append(word)
    if line:
        out.append(txt(x, cy, size, fill, " ".join(line), weight))
    return "".join(out)


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def slide1(d) -> str:
    return frame(1,
        wrap(M, 330, 86, TEXT, f"Heard some alpha on ${d['symbol']}.", W - 2*M, 700)
        + wrap(M, 560, 52, SUB, "A spike is easy to see. The only question that matters is "
                                "whether anyone stayed.", W - 2*M)
        + txt(M, 880, 44, GREEN, "So I measured the quiet days.", 700),
        "swipe")


def slide2(d) -> str:
    sp = d["spikes_21d"]
    rows = []
    y = 420
    for s in sp:
        rows.append(txt(M, y, 42, SUB, s["day"][5:].replace("-", "/")))
        rows.append(txt(M + 230, y, 42, TEXT, f"{s['interactions']/1e6:.2f}M", 700))
        rows.append(txt(M + 500, y, 42, SUB, f"{s['multiple']:.1f}x"))
        rows.append(txt(W - M, y, 46, GREEN, f"{s['people']:,} people", 700, "end"))
        y += 76
    return frame(2,
        wrap(M, 250, 62, TEXT, f"{len(sp)} spikes in three weeks.", W - 2*M, 700)
        + txt(M, 340, 38, SUB, "and more people at every one")
        + "".join(rows)
        + txt(M, y + 70, 44, TEXT, f"{sp[0]['people']} → {sp[-1]['people']}", 700)
        + txt(M + 260, y + 70, 40, SUB, "turning up"),
        "vs its own 30-day normal")


def slide3(d) -> str:
    w = d["windows"]
    rows, y = [], 530
    for win in w:
        rows.append(txt(M, y, 40, SUB, win["label"]))
        rows.append(txt(W - M, y, 48, TEXT, f"{win['interactions']/1e3:,.0f}k", 700, "end"))
        y += 92
    return frame(3,
        wrap(M, 250, 62, TEXT, "Then I threw the spikes away.", W - 2*M, 700)
        + txt(M, 420, 38, SUB, "daily interactions on the quiet days only")
        + "".join(rows)
        + txt(M, y + 60, 72, GREEN, f"{d['floor_lift']:.1f}x", 700)
        + txt(M + 180, y + 60, 44, TEXT, "higher floor", 700)
        + txt(M, y + 118, 38, SUB, f"with {d['people_lift']:.2f}x the people posting"),
        "quiet = below 2x the coin's own normal")


def slide4(d) -> str:
    return frame(4,
        wrap(M, 300, 64, TEXT, "A campaign leaves a crater once the budget stops.",
             W - 2*M, 700)
        + wrap(M, 560, 64, GREEN, "This one left a floor instead.", W - 2*M, 700)
        + wrap(M, 760, 44, SUB, "The people who arrived are still here on the ordinary days. "
                                "No copypasta across accounts, and spam grew in step with the "
                                "crowd rather than ahead of it.", W - 2*M),
        "")


def slide5(d) -> str:
    return frame(5,
        wrap(M, 270, 62, AMBER, "The catch is timing.", W - 2*M, 700)
        + wrap(M, 400, 46, TEXT, f"Price is already up {d['price_90d_change']:.0%} over the "
                                 f"same 90 days.", W - 2*M)
        + wrap(M, 600, 44, SUB, "My backtest found organic attention only shifts the odds "
                                "while the price has not moved yet. The same spike after a run "
                                "is worth nothing.", W - 2*M)
        + txt(M, 900, 54, TEXT, "The alpha looks real, and late.", 700)
        + txt(M, 1010, 38, SUB, "Method and code: github.com/nickisanders"),
        "Data: LunarCrush · code NICKI for 15% off · not advice")


def main() -> None:
    d = json.loads((HERE / "out" / "floor.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), start=1):
        (OUT / f"slide-{i}.svg").write_text(fn(d))
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');"
        f"[1,2,3,4,5].forEach(i=>s(`{OUT}/slide-${{i}}.svg`,{{density:144}})"
        f".resize({W},{H}).png().toFile(`{OUT}/slide-${{i}}.png`));"], check=True)
    print(f"  wrote 5 slides to {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
