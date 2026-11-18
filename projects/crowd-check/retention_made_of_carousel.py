#!/usr/bin/env python3
"""Instagram carousel: what a retention figure is made of.

Reads the baseline at render time. No token and no figure is named in the
source: the slides take whichever tokens print the same headline retention
as each other.

The wide chart shows the whole field and lets the reader find the
coincidence in it. A deck has to lead with the coincidence, so slide two is
the tokens that report the same number and slide three is what is
underneath it.

Slide five withdraws the part the measurement cannot carry. A wallet under
1% of its allocation did not necessarily sell, and the split is of current
holders rather than of everyone the token ever reached.

Usage: python3 retention_made_of_carousel.py
"""

import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "madeof"
BLUE = "#388bfd"
MIN_ARRIVED, PLACES = 5000, 1


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"made of what · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        k = (d.get("dust") or {}).get("kinds") or {}
        if "untouched_large" not in k or d["arrived"] < MIN_ARRIVED:
            continue
        rows.append({"sym": name.upper(), "raw": d["raw"],
                     "held": k["untouched_large"] + k["untouched_small"],
                     "part": k["part_sold"],
                     "gone": k["exited_leaving_dust"]})
    ties = {}
    for r in rows:
        ties.setdefault(round(r["raw"] * 100, PLACES), []).append(r)
    ties = {k: sorted(v, key=lambda r: r["gone"])
            for k, v in ties.items() if len(v) > 1}
    crowd = max(ties.items(),
                key=lambda kv: (len(kv[1]), kv[1][-1]["gone"] - kv[1][0]["gone"]))
    return {"doc": doc, "rows": rows, "ties": ties, "crowd": crowd,
            "worst": max(rows, key=lambda r: r["gone"]),
            "median": statistics.median(r["gone"] for r in rows)}


def slide1(d) -> str:
    f = Flow(330)
    f.say(58, TEXT, "Two tokens can report", 700, gap=6)
    f.say(58, TEXT, "the same retention and", 700, gap=6)
    f.say(58, TEXT, "mean opposite things.", 700, gap=54)
    f.say(44, SUB, f"The holders of {len(d['rows'])} tokens, sorted by how "
                   f"much of what they received they still hold.", gap=62)
    f.say(44, BLUE, "Nothing in the measure is priced.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    val, group = d["crowd"]
    f = Flow(300)
    f.say(48, TEXT, "Start with a coincidence", 700, gap=44)
    f.raw(txt(M, f.y + 30, 104, TEXT, f"{val:.1f}%", 700))
    f.y += 150
    f.say(36, SUB, f"retention, reported by {len(group)} different tokens in "
                   f"the set: {', '.join('$' + r['sym'] for r in group[:-1])} "
                   f"and ${group[-1]['sym']}.", gap=48)
    f.say(34, SUB, "Same number, same test: a balance above zero.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    """The split, on the tokens slide two just tied together."""
    val, group = d["crowd"]
    f = Flow(276)
    f.say(46, TEXT, "Now look underneath it", 700, gap=14)
    f.say(30, SUB, "Share of each token's holders sitting on under 1% of "
                   "what they received: they sold out and left a tail.",
          gap=46)
    BW, RH = W - 2 * M - 200 - 110, 92
    peak = max(r["gone"] for r in group)
    for r in group:
        y = f.y
        f.raw(f'<rect x="{M + 160}" y="{y}" width="{BW}" height="30" '
              f'fill="{TRACK}"/>')
        f.raw(f'<rect x="{M + 160}" y="{y}" '
              f'width="{BW * r["gone"] / peak:.1f}" height="30" '
              f'fill="{RED}"/>')
        f.raw(txt(M, y + 23, 30, SUB, "$" + r["sym"]))
        f.raw(txt(M + 160 + BW + 16, y + 23, 28, TEXT,
                  f"{r['gone']*100:.1f}%", 700))
        f.y += RH
    f.gap(30)
    f.say(34, SUB, "Every retention figure counts all of these wallets as "
                   "holders who stayed.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    w, rows = d["worst"], d["rows"]
    f = Flow(286)
    f.say(48, TEXT, "Across the whole set", 700, gap=40)
    f.say(36, SUB, f"That share runs from "
                   f"{min(r['gone'] for r in rows)*100:.1f}% to "
                   f"{max(r['gone'] for r in rows)*100:.1f}% of a token's "
                   f"holders, with a median of {d['median']*100:.1f}%.",
          gap=50)
    f.raw(txt(M, f.y + 30, 96, RED, f"{w['gone']*100:.1f}%"))
    f.y += 146
    f.say(36, SUB, f"of ${w['sym']}'s holders, the wallets behind its "
                   f"{w['raw']*100:.1f}% retention, hold under a hundredth "
                   f"of what they were given.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc = d["doc"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, "That these wallets sold. Moving a position somewhere "
                   "else and leaving the remainder behind looks identical "
                   "from the chain.", gap=44)
    f.say(36, SUB, "That the two measures are unrelated. Tokens that retain "
                   "more do carry less of this, at r of -0.57. The gap is "
                   "that the link is loose, not absent.", gap=46)
    f.say(38, BLUE, "Every cut is against what that wallet itself received, "
                    "so none of it moves when the price does.", 700, gap=44)
    f.say(30, SUB, "The split is of current holders. Nothing here is "
                   "advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    if len(d["rows"]) < 20:
        raise SystemExit(f"  only {len(d['rows'])} tokens carry the split; "
                         f"the slides describe a field")
    if not d["ties"]:
        raise SystemExit("  no two tokens print the same headline figure; "
                         "slides two and three are built on that")
    val, group = d["crowd"]
    # Slide three is the turn and it only turns if the tied tokens differ.
    span = group[-1]["gone"] - group[0]["gone"]
    if span < 0.10:
        raise SystemExit(f"  the tokens tied at {val:.1f}% now differ by "
                         f"{span*100:.1f} points; slide three calls that a "
                         f"difference worth seeing")
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{STEM}-{i}.svg"
        p.write_text(fn(d))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
