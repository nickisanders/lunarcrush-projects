#!/usr/bin/env python3
"""Instagram carousel: ten tokens that are one airdrop each.

Reads retention-baseline.json at render time, so the slides cannot drift from
the chart and the post while the queue keeps adding tokens. Every figure on
every slide is computed, including the membership of the ten: the group is
whatever currently satisfies the two thresholds rather than a list typed in
once.

Slide four is the one that earns the set. The spread is the hook, and the
honest answer to "why" is that nothing measured explains it, so the slide
names four candidates and says each of them failed rather than implying an
explanation the data does not support.

Slide five exists because slide three invites the wrong read. The longest bar
belongs to a token whose median holder has 83 cents, and a reader who swipes
away at slide three leaves thinking it is the success story of the group.

The eyebrow does not say LunarCrush. This measurement never touches it: the
baseline is built from transfer scans, and the series label on the shared
frame would be crediting an API that had no part in it.

Usage: python3 one_month_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "onemonth"
BLUE = "#388bfd"
MIN_SHARE, MIN_COHORT = 0.5, 5000
LEAD = "DRV"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"one airdrop each · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads(SRC.read_text())
    rows = []
    for name, d in doc["tokens"].items():
        bc = d.get("biggest_cohort") or {}
        if not bc or not d["arrived"]:
            continue
        if bc["arrived"] / d["arrived"] < MIN_SHARE or bc["arrived"] < MIN_COHORT:
            continue
        k = (d.get("dust") or {}).get("kinds") or {}
        rows.append({
            "sym": name.upper(), "month": bc["month"], "cohort": bc["arrived"],
            "share": bc["arrived"] / d["arrived"], "ret": bc["retention"],
            "kept": round(bc["arrived"] * bc["retention"]),
            "med": (d.get("dust") or {}).get("median_usd"),
            "never": (k["untouched_small"] + k["untouched_large"]
                      if "untouched_small" in k else None),
            "imm": (d.get("mobility") or {}).get("immobile_share"),
        })
    rows.sort(key=lambda r: -r["ret"])
    return rows, doc["measured"]


def slide1(rows, _) -> str:
    hi, lo = rows[0], rows[-1]
    f = Flow(330)
    f.say(58, TEXT, f"{len(rows)} tokens that are really", 700, gap=6)
    f.say(58, TEXT, "one airdrop each.", 700, gap=54)
    f.say(44, SUB, "Same shape, same kind of event, as close to a controlled "
                   "comparison as this gets.", gap=58)
    f.say(46, BLUE, f"They kept between {lo['ret']*100:.1f}% "
                    f"and {hi['ret']*100:.1f}%.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(rows, _) -> str:
    hi, lo = rows[0], rows[-1]
    f = Flow(286)
    f.say(46, TEXT, "One month, most of the holders", 700, gap=30)
    f.say(32, SUB, f"For each of these a single month brought more than half "
                   f"of everyone who ever held the coin, and that month was at "
                   f"least {MIN_COHORT:,} wallets.", gap=54)
    for r, col in ((lo, RED), (hi, BLUE)):
        f.raw(txt(M, f.y + 20, 72, col,
                  f"{r['cohort']:,} to {r['kept']:,}", 700))
        f.raw(txt(M, f.y + 64, 30, SUB,
                  f"${r['sym']}, {r['month']}, kept {r['ret']*100:.1f}%"))
        f.y += 150
    f.gap(14)
    f.say(34, SUB, "Both of them handed tokens to a crowd and waited. "
                   "Nothing else about them matches.", gap=0)
    return frame(2, f.svg())


def slide3(rows, _) -> str:
    f = Flow(268)
    f.say(46, TEXT, "What each one kept", 700, gap=14)
    f.say(30, SUB, "Share of that month's wallets still holding today.", gap=40)
    LAB, PCT = 132, 104
    BW = W - 2 * M - LAB - PCT
    top = max(r["ret"] for r in rows)
    for r in rows:
        lead = r["sym"] == LEAD
        w = BW * r["ret"] / top
        f.raw(txt(M, f.y + 34, 25, SUB, "$" + r["sym"]))
        f.raw(f'<rect x="{M+LAB}" y="{f.y+8}" width="{BW}" height="{42}" '
              f'rx="6" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+LAB}" y="{f.y+8}" width="{w:.1f}" height="{42}" '
              f'rx="6" fill="{RED if lead else BLUE}"/>')
        f.raw(txt(M + LAB + BW + 16, f.y + 38, 26,
                  TEXT if lead else SUB, f"{r['ret']*100:.1f}%", 700 if lead else 400))
        f.y += 54
    return frame(3, f.svg())


def slide4(rows, _) -> str:
    f = Flow(300)
    f.say(48, TEXT, "Why the spread?", 700, gap=36)
    f.say(34, SUB, "Four things that could have explained it, and the result "
                   "of testing each against these ten.", gap=46)
    for label in ("how big the cohort was", "how long ago it happened",
                  "how concentrated arrival was", "what the survivors hold"):
        f.raw(txt(M, f.y + 28, 32, SUB, label))
        f.raw(txt(W - M, f.y + 28, 32, RED, "no", 700, "end"))
        f.y += 62
    f.gap(30)
    f.say(38, TEXT, f"A {rows[0]['ret']/rows[-1]['ret']:.0f}-fold spread across "
                    f"{len(rows)} near-identical events, unexplained.", 700, gap=0)
    return frame(4, f.svg())


def slide5(rows, measured) -> str:
    lead = next(r for r in rows if r["sym"] == LEAD)
    f = Flow(276)
    f.say(46, TEXT, "The best number is the one", 700, gap=6)
    f.say(46, TEXT, "to trust least.", 700, gap=44)
    f.raw(txt(M, f.y + 20, 86, BLUE, f"${lead['med']:.2f}", 700))
    f.raw(txt(M, f.y + 66, 30, SUB,
              f"what the median ${lead['sym']} holder is sitting on"))
    f.y += 152
    f.say(34, SUB, f"${lead['sym']} kept {lead['ret']*100:.1f}% of its cohort. "
                   f"{lead['never']*100:.0f}% of its holders have never sold "
                   f"anything and only {lead['imm']*100:.1f}% cannot transact, "
                   f"so almost all of them could have left.", gap=40)
    f.say(36, TEXT, "A position that size is not worth an action, and "
                    "retention cannot tell that apart from conviction.", 700,
          gap=34)
    f.say(28, SUB, "Nobody is trapped and nothing was done to anyone. "
                   "Nothing here is advice.", gap=0)
    return frame(5, f.svg(),
                 f"measured {measured} · github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    rows, measured = load()
    if len(rows) < 5:
        raise SystemExit(f"  only {len(rows)} tokens meet the thresholds")
    if not any(r["sym"] == LEAD for r in rows):
        raise SystemExit(f"  ${LEAD} is no longer in the group; slide five "
                         f"names it and would be describing a token that is "
                         f"not on slide three")
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        p = OUT / f"{STEM}-{i}.svg"
        p.write_text(fn(rows, measured))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{p}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
