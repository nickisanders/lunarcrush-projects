#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for one coin from the screen.

Reads out/spotlight-<sym>.json, so the slides always match the last run of
spotlight.py. Numbers typed into slides by hand go stale the moment the data
moves, and the current day keeps settling for hours after midnight UTC.

Writes out/instagram/<sym>-N.svg and rasterizes them.

Usage: python3 carousel.py STRK
"""

import argparse
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
        wrap(M, 320, 84, TEXT, f"{d['name']}'s price doubled this week.", W - 2*M, 700)
        + wrap(M, 580, 52, SUB, "Most pumps arrive with a crowd that was already there, "
                                "just shouting louder.", W - 2*M)
        + txt(M, 900, 46, GREEN, "So I counted the people.", 700),
        "swipe")


def slide2(d) -> str:
    rows, y = [], 490
    for m in d["metrics"]:
        rows.append(txt(M, y, 38, SUB, m["label"].split(",")[0]))
        rows.append(txt(M, y + 62, 54, TEXT, f"{m['before']:,}", 700))
        rows.append(txt(M + 250, y + 62, 46, SUB, "to"))
        rows.append(txt(M + 350, y + 62, 54, GREEN, f"{m['after']:,}", 700))
        y += 196
    return frame(2,
        wrap(M, 250, 64, TEXT, "The crowd actually turned up.", W - 2*M, 700)
        + "".join(rows), "per day, this week against the 30 days before")


def slide3(d) -> str:
    return frame(3,
        wrap(M, 250, 64, TEXT, "And the junk thinned out.", W - 2*M, 700)
        + txt(M, 470, 40, SUB, "spam as a share of posts")
        + txt(M, 560, 86, SUB, f"{d['spam_before']*100:.0f}%", 700)
        + txt(M + 230, 560, 60, SUB, "to")
        + txt(M + 360, 560, 86, GREEN, f"{d['spam_after']*100:.0f}%", 700)
        + wrap(M, 720, 48, TEXT, "A bought wave runs the other way. Paid posts crowd in "
                                 "as the price goes, and the share climbs.", W - 2*M)
        + txt(M, 980, 42, GREEN, "Real people dilute spam. Bots concentrate it.", 700))


def slide4(d) -> str:
    pk = d["year_peak"] or {}
    mult = (d["price"] / pk["price"]) if pk.get("price") else 0
    return frame(4,
        wrap(M, 250, 64, TEXT, "So the attention is real.", W - 2*M, 700)
        + wrap(M, 360, 56, AMBER, "Whether that is good news is a different question.",
               W - 2*M, 700)
        + txt(M, 580, 44, SUB, "people posting today")
        + txt(M, 660, 90, TEXT, f"{d['today_people']:,}", 700)
        + wrap(M, 800, 46, SUB, f"Near its highest in a year. The last time it was this "
                                f"loud was {pk.get('day','')}, when it traded at "
                                f"${pk.get('price',0):.4f}.", W - 2*M)
        # "A 16th of today's price" reads as a typo. Stating the multiple
        # avoids spelling an ordinal that changes with every coin.
        + txt(M, 1010, 50, AMBER, f"Today's price is {mult:.0f}x higher.", 700))


def slide5(d) -> str:
    return frame(5,
        wrap(M, 250, 62, TEXT, "I measure whether a crowd is real.", W - 2*M, 700)
        + wrap(M, 420, 48, SUB, "Not whether it is a good entry. My own backtest of coins "
                                "whose conversation spikes into the top ten found the "
                                "median one trailing Bitcoin by 21% three months later.",
               W - 2*M)
        + txt(M, 790, 52, RED, "Those are different questions.", 700)
        + wrap(M, 900, 42, SUB, "Method and code are public. Nothing here is advice.",
               W - 2*M),
        "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    a = ap.parse_args()
    sym = a.symbol.upper()
    src = HERE / "out" / f"spotlight-{sym.lower()}.json"
    if not src.exists():
        raise SystemExit(f"No {src.name}. Run spotlight.py {sym} first.")
    d = json.loads(src.read_text())

    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{sym.lower()}-{i}.svg"
        p.write_text(fn(d))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{sym.lower()}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
