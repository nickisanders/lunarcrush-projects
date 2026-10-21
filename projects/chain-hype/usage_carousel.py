#!/usr/bin/env python3
"""Instagram carousel: the capital-efficiency chart and the objection to it.

Two days of posts make one story and it is better told together, because the
first chart is wrong on its own in a way the second one fixes. Fees per dollar
of TVL says capital works 111x harder on Hyperliquid than Tron. Someone
pointed out that measure rewards automated flow, which was right, so the back
half is what came back from counting the wallets.

The twist is that it does not land where the objection pointed. Hyperliquid is
fourth most concentrated of eight, and Ethereum is the only chain measured
where paying for blockspace is spread across a broad set of people.

Reads out/usage.json and proof-of-crowd-tools/out/payers.json, so the slides
cannot drift from the two charts they summarize.

Usage: python3 usage_carousel.py
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "crowd-check"))

from carousel import (  # noqa: E402
    W, H, M, BG, TEXT, SUB, TRACK, RED, FONT, Flow, txt,
)

USAGE = HERE / "out" / "usage.json"
PAYERS = Path.home() / "proof-of-crowd-tools/out/payers.json"
OUT = HERE / "out" / "instagram"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
TOTAL, STEM = 5, "chains"
BLUE = "#388bfd"


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 112, 27, SUB, footer) if footer else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{txt(M, 102, 29, SUB, f"which chains actually get used · {n}/{TOTAL}")}'
            f'{body}{f}{dots}</svg>')


def caption(f: Flow, size: int, fill: str, text: str, weight: int = 400) -> None:
    """Flow.say puts the first line's baseline at f.y, so its glyphs rise into
    whatever was drawn last. Drop by the ascent before writing under bars."""
    f.gap(int(size * 0.82) + 20)
    f.say(size, fill, text, weight, gap=0)


def bars(f: Flow, rows, value, label, highlight, full=None) -> None:
    BW, BH = W - 2 * M - 230, 52
    top = full or max(value(r) for r in rows)
    for r in rows:
        v = value(r)
        w = max(BW * v / top, 3)
        col = BLUE if highlight(r) else RED
        f.raw(txt(M, f.y + 38, 30, TEXT, r["short"], 700))
        f.raw(f'<rect x="{M+230}" y="{f.y+8}" width="{BW}" height="{BH}" rx="8" fill="{TRACK}"/>')
        f.raw(f'<rect x="{M+230}" y="{f.y+8}" width="{w:.0f}" height="{BH}" rx="8" fill="{col}"/>')
        inside = w > 170
        f.raw(txt(M + 230 + w - (16 if inside else -12), f.y + 46, 32,
                  BG if inside else TEXT, label(v), 700,
                  "end" if inside else "start"))
        f.y += BH + 16


def load():
    u = [r for r in json.loads(USAGE.read_text()) if r["tvl"] >= 1e8]
    for r in u:
        r["per1k"] = r["fees"] / r["tvl"] * 1000
        r["short"] = r["chain"].replace(" L1", "")
    u.sort(key=lambda r: -r["per1k"])
    p = json.loads(PAYERS.read_text())
    for r in p:
        r["short"] = r["chain"].replace(" L1", "")
    p.sort(key=lambda r: -r["top1pct_tx_share"])
    return u, p


def slide1(u, p) -> str:
    eth = next(r for r in u if r["chain"] == "Ethereum")
    sol = next(r for r in u if r["chain"] == "Solana")
    f = Flow(290)
    f.say(58, TEXT, "Ethereum holds $49.5B. Solana holds $5.9B.", 700, gap=46)
    f.say(46, SUB, "Over 30 days Ethereum collected $346M in fees. "
                   "Solana collected $445M.", gap=66)
    f.say(50, BLUE, f"Per $1,000 parked, that is ${eth['per1k']:,.2f} "
                    f"against ${sol['per1k']:,.2f}.", 700, gap=0)
    return frame(1, f.svg(), "swipe")


def slide2(u, p) -> str:
    pick = [r for r in u if r["chain"] in
            ("Hyperliquid L1", "Solana", "Polygon", "Base", "Ethereum", "Tron")]
    f = Flow(300)
    f.say(50, TEXT, "How hard a parked dollar works", 700, gap=20)
    f.say(32, SUB, "Fee revenue over 30 days per $1,000 of capital on the chain.", gap=46)
    bars(f, pick, lambda r: r["per1k"], lambda v: f"${v:,.0f}",
         lambda r: r["chain"] in ("Ethereum", "Tron"))
    caption(f, 34, SUB, "Hyperliquid gets 111x what Tron does out of a parked dollar.")
    return frame(2, f.svg())


def slide3(u, p) -> str:
    f = Flow(300)
    f.say(52, TEXT, "Then someone pointed out the problem.", 700, gap=50)
    f.say(42, SUB, "That measure rewards a chain with heavy bot flow. Fees can "
                   "come from a handful of automated wallets trading with "
                   "themselves all day.", gap=54)
    f.say(46, BLUE, "Fair. So I counted the wallets.", 700, gap=40)
    f.say(32, SUB, "Every block on eight chains for 24 hours. Distinct senders, "
                   "and the share of transactions from the busiest 1%.", gap=0)
    return frame(3, f.svg())


def slide4(u, p) -> str:
    f = Flow(280)
    f.say(50, TEXT, "Transactions from the top 1%", 700, gap=20)
    f.say(32, SUB, "Of the addresses that sent anything that day.", gap=40)
    bars(f, p, lambda r: r["top1pct_tx_share"], lambda v: f"{v*100:.0f}%",
         lambda r: r["chain"] == "Ethereum", full=1.0)
    return frame(4, f.svg())


def slide5(u, p) -> str:
    eth = next(r for r in p if r["chain"] == "Ethereum")
    hyp = next(r for r in p if r["chain"] == "Hyperliquid L1")
    f = Flow(290)
    f.say(54, TEXT, "Hyperliquid was not the concentrated one.", 700, gap=44)
    f.say(40, SUB, f"It is fourth of eight. Seven of the eight push two thirds "
                   f"or more of their traffic through 1% of senders.", gap=56)
    f.say(46, BLUE, "Ethereum is the only one where paying for "
                    "blockspace is broad.", 700, gap=44)
    f.say(32, SUB, f"48.8% from its top 1%, spread across {eth['senders']:,} "
                   f"wallets. Hyperliquid earns the most per wallet, "
                   f"${hyp['fee_per_sender']:,.0f}, from {hyp['senders']:,} of them.", gap=38)
    f.say(28, SUB, "DeFiLlama and onchain data. Nothing here is advice.", gap=0)
    return frame(5, f.svg(), "github.com/nickisanders/lunarcrush-projects")


def main() -> None:
    u, p = load()
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate((slide1, slide2, slide3, slide4, slide5), 1):
        path = OUT / f"{STEM}-{i}.svg"
        path.write_text(fn(u, p))
        subprocess.run(["node", "-e",
            f"const s=require('{SHARP}');s('{path}',{{density:144}})"
            f".resize({W*2},{H*2}).png().toFile('{OUT}/{STEM}-{i}.png')"
            f".then(r=>console.log('  slide {i}  '+r.width+'x'+r.height));"], check=True)


if __name__ == "__main__":
    main()
