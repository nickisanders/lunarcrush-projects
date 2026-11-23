#!/usr/bin/env python3
"""Instagram carousel: did the token ever reach anyone it did not pay?

Reads arrival-years.json and the baseline at render time. No token is named
in the source: the deck takes the two ends of the sort and the youngest
token that has already recruited past its giveaway.

The wide chart ranks 27 tokens and lets a reader find the ends. A deck
cannot carry 27 bars, so it opens on the extreme, gives the field's median
as the thing that extreme is extreme against, and spends slide four on the
age objection, which is the one a reader will raise before anything else.

Usage: python3 after_the_drop_carousel.py
"""

import datetime
import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "afterdrop"
BLUE = "#388bfd"
BEFORE_MAX = 0.25


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"who came later · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads((ROOT / "arrival-years.json").read_text())
    base = json.loads((ROOT / "retention-baseline.json").read_text())["tokens"]
    rows = []
    for r in doc["per_token"]:
        if not r["spike"]:
            continue
        t = base[r["sym"].lower()]
        n = r["recipients"]
        peak = datetime.date.fromisoformat(r["peak_day"])
        meas = datetime.date.fromisoformat(
            t["measured"] if t.get("measured") else doc["measured"])
        row = {"sym": r["sym"], "n": n, "before": r["before"]["n"] / n,
               "week": r["giveaway"]["n"] / n, "after": r["after"]["n"] / n,
               "since": (meas - peak).days / 30.44}
        if row["before"] < BEFORE_MAX:
            rows.append(row)
    rows.sort(key=lambda r: -r["after"])
    young = [r for r in rows if r["since"] < 24]
    return {"doc": doc, "rows": rows, "top": rows[0], "bottom": rows[-1],
            "biggest": max(rows, key=lambda r: r["n"]),
            "young": young,
            "early": max(young, key=lambda r: r["after"]),
            "median": statistics.median(r["after"] for r in rows),
            "stalled": [r for r in rows if r["after"] < 0.25]}


def slide1(d) -> str:
    b = d["bottom"]
    f = Flow(330)
    f.say(58, TEXT, "An airdrop is meant to", 700, gap=6)
    f.say(58, TEXT, "start a user base.", 700, gap=6)
    f.say(58, TEXT, f"On ${b['sym']} it is one.", 700, gap=54)
    f.say(44, SUB, f"{b['week']*100:.1f}% of every address that has ever held "
                   f"it arrived in a single week.", gap=62)
    f.say(44, BLUE, f"{b['after']*100:.1f}% turned up in the "
                    f"{b['since']:.0f} months since.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    t, big = d["top"], d["biggest"]
    f = Flow(300)
    f.say(48, TEXT, "Most tokens are not like that", 700, gap=44)
    f.raw(txt(M, f.y + 30, 100, BLUE, f"{d['median']*100:.1f}%", 700))
    f.y += 150
    f.say(36, SUB, "of the median token's crowd arrived after its giveaway "
                   "was already over.", gap=48)
    f.say(34, SUB, f"${t['sym']} reaches {t['after']*100:.1f}% and "
                   f"${big['sym']} {big['after']*100:.1f}% across "
                   f"{big['n']:,} recipients.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    f = Flow(276)
    f.say(46, TEXT, "The ones that never got past it", 700, gap=14)
    f.say(30, SUB, "Share of each token's lifetime holders who arrived after "
                   "the giveaway week ended.", gap=44)
    BW, RH = W - 2 * M - 230 - 110, 96
    peak = max(r["after"] for r in d["stalled"]) or 1
    for r in d["stalled"]:
        y = f.y
        f.raw(f'<rect x="{M + 190}" y="{y}" width="{BW}" height="30" '
              f'fill="{TRACK}"/>')
        f.raw(f'<rect x="{M + 190}" y="{y}" '
              f'width="{BW * r["after"] / peak:.1f}" height="30" '
              f'fill="{RED}"/>')
        f.raw(txt(M, y + 23, 30, SUB, "$" + r["sym"]))
        f.raw(txt(M + 190 + BW + 16, y + 23, 28, TEXT,
                  f"{r['after']*100:.1f}%", 700))
        f.y += RH
    f.gap(26)
    f.say(32, SUB, f"{len(d['stalled'])} of the {len(d['rows'])} measured. "
                   f"Everyone else is above a quarter.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    """The objection every reader raises before the chart has finished."""
    e, b = d["early"], d["bottom"]
    young = d["young"]
    f = Flow(286)
    f.say(48, TEXT, "Is it just age?", 700, gap=40)
    f.say(36, SUB, "A token whose giveaway was last month has had a month to "
                   "find anyone else. Partly right: the correlation with "
                   "months elapsed is 0.45.", gap=50)
    f.say(36, SUB, f"It does not decide the order. The {len(young)} tokens "
                   f"under two years old run from "
                   f"{min(r['after'] for r in young)*100:.0f}% to "
                   f"{max(r['after'] for r in young)*100:.0f}% among "
                   f"themselves.", gap=46)
    f.say(38, BLUE, f"${e['sym']} is {e['since']:.0f} months past its "
                    f"giveaway and already at {e['after']*100:.1f}%. "
                    f"${b['sym']} is {b['since']:.0f} months past its own "
                    f"and at {b['after']*100:.1f}%.", 700, gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    doc = d["doc"]
    f = Flow(286)
    f.say(48, TEXT, "What it does not say", 700, gap=42)
    f.say(36, SUB, "Why anyone arrived later. Buying, being sent the token "
                   "and claiming late all look the same from the chain.", gap=44)
    f.say(36, SUB, "That a low number is failure. A token can be worth "
                   "holding and reach nobody new, and this measures reach "
                   "rather than worth.", gap=46)
    f.say(38, BLUE, "The giveaway week is found from the arrival data, not "
                    "from a date anyone looked up.", 700, gap=44)
    f.say(30, SUB, "Nothing here is priced and nothing here is advice.",
          gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    if len(d["rows"]) < 12:
        raise SystemExit(f"  only {len(d['rows'])} tokens have a findable "
                         f"giveaway; the slides describe a field")
    # Slide three draws the stalled ones one bar each and has room for four.
    if not 1 <= len(d["stalled"]) <= 4:
        raise SystemExit(f"  {len(d['stalled'])} tokens sit under a quarter; "
                         f"slide three draws them individually")
    if not d["young"]:
        raise SystemExit("  nothing under two years old; slide four answers "
                         "the age objection with young tokens")
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
