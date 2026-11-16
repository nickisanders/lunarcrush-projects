#!/usr/bin/env python3
"""Instagram carousel: the first big airdrop, six years on.

Reads arrival-years.json and the baseline at render time. The token is the
one the most addresses have ever received rather than a name in the source,
and every figure on every slide comes out of those two files.

The deck argues the case in a different order from the post. The post opens
on the giveaway and lets the quoted figure arrive as the twist. Five slides
cannot hold a twist, so slide two puts the two numbers side by side
immediately and the rest of the deck is about why they differ.

Slide five is the one that withdraws things. The later cohorts have had less
time to leave, buying is not claiming, and an airdrop can do its job without
producing holders. All three belong on the slide a reader stops at.

Usage: python3 original_airdrop_carousel.py
"""

import json
import statistics
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
SRC = ROOT / "arrival-years.json"
BASE = ROOT / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "original"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"the first one · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    base = json.loads(BASE.read_text())["tokens"]
    t = max(doc["per_token"], key=lambda r: r["recipients"])
    spiked = [r for r in doc["per_token"] if r["spike"]]
    rank = sorted(spiked, key=lambda r: r["giveaway"]["holding"])
    return {"doc": doc, "t": t, "whole": base[t["sym"].lower()]["raw"],
            "spiked": spiked,
            "place": [r["sym"] for r in rank].index(t["sym"]) + 1,
            "median_week": statistics.median(
                r["giveaway"]["holding"] for r in spiked)}


def slide1(d) -> str:
    t = d["t"]
    f = Flow(330)
    f.say(58, TEXT, "The airdrop every other", 700, gap=6)
    f.say(58, TEXT, "airdrop is measured", 700, gap=6)
    f.say(58, TEXT, "against, six years on.", 700, gap=54)
    f.say(44, SUB, f"${t['sym']} has reached {t['recipients']:,} wallets "
                   f"since September 2020.", gap=62)
    f.say(44, BLUE, f"{t['giveaway']['holding']*100:.1f}% of the ones it paid "
                    f"still hold any.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    """Both numbers at once. The gap between them is the whole deck."""
    t = d["t"]
    f = Flow(300)
    f.say(48, TEXT, "Two retention figures", 700, gap=44)
    for val, lab, col in (
            (t["giveaway"]["holding"], "the giveaway week", RED),
            (d["whole"], "the token as a whole", BLUE)):
        f.raw(txt(M, f.y + 20, 90, col, f"{val*100:.1f}%", 700))
        f.raw(txt(M, f.y + 70, 34, SUB, lab))
        f.y += 158
    f.gap(24)
    f.say(36, SUB, "Same token, same day, same test: a balance above zero. "
                   "The second one is the number that gets quoted.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    t = d["t"]
    f = Flow(286)
    f.say(48, TEXT, "Because they count different people", 700, gap=40)
    f.say(36, SUB, f"The giveaway week is {t['giveaway']['n']:,} wallets, "
                   f"found from the arrival dates rather than looked up: the "
                   f"busiest day and the {d['doc']['window']} either side.",
          gap=50)
    f.raw(txt(M, f.y + 30, 96, BLUE,
              f"{(1 - t['event_share'])*100:.1f}%", 700))
    f.y += 146
    f.say(36, SUB, "of every wallet the quoted figure counts arrived after "
                   "the giveaway was already over.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    t = d["t"]
    # The giveaway year's remaining arrivals are not the giveaway, and
    # labelled with the bare year they read as though they were.
    drop_year = t["peak_day"][:4]
    rows = [("giveaway week", t["giveaway"])] + [
        (f"rest of {y}" if y == drop_year else y, v)
        for y, v in t["years"].items()]
    f = Flow(268)
    f.say(46, TEXT, "By the year they turned up", 700, gap=14)
    f.say(30, SUB, "Share of each arrival cohort still holding any.", gap=40)
    # The track ran to where the label sits, so the two longest bars
    # printed straight through their own percentages.
    BW, RH = W - 2 * M - 210 - 120, 46
    peak = max(v["holding"] for _, v in rows)
    for lab, v in rows:
        y = f.y
        f.raw(f'<rect x="{M + 180}" y="{y}" width="{BW}" height="24" '
              f'fill="{TRACK}"/>')
        f.raw(f'<rect x="{M + 180}" y="{y}" '
              f'width="{BW * v["holding"] / peak:.1f}" height="24" '
              f'fill="{RED if lab == "giveaway week" else BLUE}"/>')
        f.raw(txt(M, y + 19, 26, SUB, lab))
        f.raw(txt(M + 180 + BW + 16, y + 19, 24, SUB,
                  f"{v['holding']*100:.1f}%"))
        f.y += RH
    f.gap(42)
    f.say(32, SUB, "The later rows have had less time to leave, so the rise "
                   "is partly the calendar.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    t, doc = d["t"], d["doc"]
    f = Flow(286)
    f.say(48, TEXT, "What this does not say", 700, gap=42)
    f.say(36, SUB, "That the airdrop failed. It bought a user base, a "
                   "governance system and six years of people having heard "
                   "of the place. It did not buy holders.", gap=44)
    f.say(36, SUB, "That the later wallets are loyal. They bought in, and "
                   "buying is not claiming, and most of them arrived with "
                   "far less time to change their minds.", gap=46)
    f.say(38, BLUE, f"Of {len(d['spiked'])} airdrops with a findable "
                    f"giveaway week, the median week still holds "
                    f"{d['median_week']*100:.1f}%. This one is "
                    f"{d['place']}th from the bottom.", 700, gap=44)
    f.say(30, SUB, "Nothing here is priced and nothing here is advice.",
          gap=0)
    return frame(5, f.svg(),
                 f"measured {doc['measured']} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    t = d["t"]
    if not t["spike"]:
        raise SystemExit(f"  ${t['sym']} has no findable giveaway week and "
                         f"every slide here is about one")
    # Slide two prints the two figures as a gap and slide three explains the
    # gap in one direction. Both are claims rather than readings if the
    # giveaway week ever scores the higher of the two.
    if t["giveaway"]["holding"] >= d["whole"]:
        raise SystemExit(f"  ${t['sym']}'s giveaway week now holds "
                         f"{t['giveaway']['holding']*100:.1f}% against the "
                         f"token's {d['whole']*100:.1f}%; slides two and "
                         f"three read the other way")
    if len(t["years"]) < 4:
        raise SystemExit(f"  only {len(t['years'])} arrival years; slide "
                         f"four is a ladder")
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
