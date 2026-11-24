#!/usr/bin/env python3
"""Instagram carousel: the airdrop crowd that sat through a falling market.

Reads drawdown-daily.json at render time. No number is typed in, and no
token is named in the source: the deck leads with whichever token has the
larger crowd and uses the other as the second reading.

The wide chart draws 54 days and lets a reader see the line never move. A
deck cannot carry a 54 point series as its argument, so it opens on the
single busiest day, which is the same claim in one number, and spends the
middle slides on the two objections a reader raises before the end: that
these wallets could not sell anyway, and that they are dust.

Usage: python3 drawdown_quiet_carousel.py
"""

import json
import subprocess
from pathlib import Path

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "quiet"
BLUE = "#388bfd"


def held(v: float) -> str:
    """A dust median rounds to zero, and "a median of 0" reads as nothing
    held rather than as almost nothing held."""
    return "under 1" if v < 1 else f"{v:,.0f}"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"nobody moved · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def load():
    doc = json.loads((ROOT / "drawdown-daily.json").read_text())
    syms = sorted(doc, key=lambda s: -doc[s]["wallets"])
    return {"doc": doc, "syms": syms, "lead": doc[syms[0]],
            "lead_sym": syms[0], "other": doc[syms[1]],
            "other_sym": syms[1], "days": len(doc[syms[0]]["series"])}


def slide1(d) -> str:
    a, s = d["lead"], d["lead_sym"]
    f = Flow(300)
    f.say(58, TEXT, "A market fell for", 700, gap=6)
    f.say(58, TEXT, "eight weeks straight.", 700, gap=54)
    f.say(44, SUB, f"On the busiest single day of it, this many of ${s}'s "
                   f"{a['wallets']:,} airdrop wallets moved anything:", gap=50)
    f.raw(txt(M, f.y + 96, 128, BLUE, f"{a['peak']['share']*100:.2f}%", 700))
    f.y += 170
    f.say(40, SUB, f"{a['peak']['moved']} wallets. That was the busy day.",
          gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(d) -> str:
    a, s = d["lead"], d["lead_sym"]
    o, os_ = d["other"], d["other_sym"]
    f = Flow(300)
    f.say(48, TEXT, "Across the whole window", 700, gap=40)
    f.raw(txt(M, f.y + 30, 112, TEXT, f"{a['inert_share']*100:.1f}%", 700))
    f.y += 162
    f.say(38, SUB, f"of ${s} wallets never touched the position once in "
                   f"{d['days']} days.", gap=46)
    f.say(34, SUB, f"${os_} came in at {o['inert_share']*100:.1f}%. The "
                   f"median day moved {a['median_share']*100:.2f}% of the "
                   f"crowd and {o['median_share']*100:.2f}%.", gap=0)
    return frame(2, f.svg())


def slide3(d) -> str:
    """The objection that makes the headline number mean nothing if it holds."""
    a, s = d["lead"], d["lead_sym"]
    o, os_ = d["other"], d["other_sym"]
    f = Flow(276)
    f.say(46, TEXT, "But could they even sell?", 700, gap=22)
    f.say(32, SUB, "A wallet with no ETH that has never sent a transaction "
                   "cannot pay gas, so holding still was never its call.",
          gap=44)
    BW, RH = W - 2 * M - 210 - 130, 104
    for sym, r in ((s, a), (os_, o)):
        y = f.y
        f.raw(f'<rect x="{M + 170}" y="{y}" width="{BW}" height="34" '
              f'fill="{TRACK}"/>')
        f.raw(f'<rect x="{M + 170}" y="{y}" '
              f'width="{BW * r["chose_share"]:.1f}" height="34" '
              f'fill="{BLUE}"/>')
        f.raw(txt(M, y + 27, 30, SUB, "$" + sym))
        f.raw(txt(M + 170 + BW + 16, y + 27, 30, TEXT,
                  f"{r['chose_share']*100:.1f}%", 700))
        f.y += RH
    f.gap(18)
    f.say(32, SUB, f"Taking the stuck wallets out still leaves this much of "
                   f"the crowd able to act and choosing not to. Gas is "
                   f"sampled 250 wallets per token.", gap=0)
    return frame(3, f.svg())


def slide4(d) -> str:
    """The dust objection, which the data answers backwards."""
    a, s = d["lead"], d["lead_sym"]
    bot, top = a["deciles"]["bottom"], a["deciles"]["top"]
    f = Flow(286)
    f.say(46, TEXT, "Then it is all dust, surely", 700, gap=22)
    f.say(32, SUB, f"Sorting ${s} wallets by what they were sitting on, "
                   f"smallest to largest.", gap=52)
    for lab, r in (("smallest tenth", bot), ("largest tenth", top)):
        f.say(34, SUB, lab, gap=4)
        f.raw(txt(M, f.y + 62, 76, RED if r is top else TEXT,
                  f"{r['unchanged']*100:.1f}%", 700))
        f.y += 104
        f.say(30, SUB, f"unchanged, holding a median of "
                       f"{held(r['median_held'])} ${s}", gap=40)
    f.say(32, SUB, "The wallets with the most at stake are the ones that "
                   "moved. Inertia is heaviest where the position is "
                   "smallest.", gap=0)
    return frame(4, f.svg())


def slide5(d) -> str:
    a, s = d["lead"], d["lead_sym"]
    f = Flow(300)
    f.say(46, TEXT, "How this is measured", 700, gap=36)
    f.say(32, SUB, "A balance is a sum, so the balance at an earlier block is "
                   "today's balance minus everything that moved after it. One "
                   "window of blocks gives both ends and every day between.",
          gap=40)
    f.say(32, SUB, f"Every Transfer event across {d['days']} days, per wallet, "
                   f"per day. Contracts dropped. Nothing here moves with "
                   f"price.", gap=40)
    f.say(32, SUB, f"{len(d['syms'])} tokens so far, which is a pilot and not "
                   f"a finding. The method reads any token from one scan.",
          gap=0)
    return frame(5, f.svg(),
                 f"measured {a['window'][1]} · "
                 f"github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    d = load()
    if len(d["syms"]) < 2:
        raise SystemExit(f"  {len(d['syms'])} token measured; the deck reads "
                         f"one against another")
    a = d["lead"]
    # Slide one calls the busiest day of the window quiet.
    if a["peak"]["share"] >= 0.01:
        raise SystemExit(f"  the busiest day moved "
                         f"{a['peak']['share']*100:.2f}% of ${d['lead_sym']}; "
                         f"slide one calls that day nothing happening")
    # Slide three claims most of the crowd could have acted and did not.
    for s in d["syms"]:
        if not d["doc"][s]["chose_share"] or d["doc"][s]["chose_share"] <= 0.5:
            raise SystemExit(f"  ${s} has no majority that could have acted "
                             f"and did not; slide three asserts one")
    # Slide four claims the smallest holders are the stillest.
    if a["deciles"]["bottom"]["unchanged"] <= a["deciles"]["top"]["unchanged"]:
        raise SystemExit(f"  ${d['lead_sym']}'s smallest holders are no "
                         f"stiller than its largest; slide four says the "
                         f"dust objection runs backwards")
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
