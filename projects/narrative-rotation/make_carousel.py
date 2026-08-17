#!/usr/bin/env python3
"""Instagram carousel for the weekly narrative rotation report.

Reads out/report.json so the slides always match the week's actual run.
Writes out/instagram/slide-N.svg (1080x1350).
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, ORANGE, TRACK, DIM = "#3fb950", "#f85149", "#f7931a", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5

PALETTE = {"DeFi": "#3fb950", "Solana": "#58a6ff", "Memecoins": "#d29922", "RWA": "#a371f7",
           "Stablecoins": "#39c5cf", "DePIN": "#db6d28", "AI Agents": "#e3b341", "NFTs": "#f778ba"}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    words = text.split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        factor = 0.45 if prev.endswith("%") else 0.30
        parts.append(f'<tspan dx="{size * factor:.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x, y, size, fill, content, weight=400, anchor="start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in content else esc(content)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>')


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 110, 28, SUB, footer) if footer else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{txt(M, 102, 30, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}
{body}
{f}
{dots}
</svg>"""


def slide1(d) -> str:
    return frame(1, f"""
{txt(M, 380, 50, SUB, "Bitcoin just had a")}
{txt(M, 436, 50, SUB, "bad week for attention.")}
{txt(M, 570, 68, TEXT, "It lost 2.5 points", 800)}
{txt(M, 646, 68, TEXT, "of share.", 800)}
{txt(M, 770, 56, ORANGE, "It still beat eight", 800)}
{txt(M, 834, 56, ORANGE, "narratives combined.", 800)}
{txt(M, 940, 38, SUB, "week ending {d}")}
""", "swipe")


def slide2(btc, rest, segs) -> str:
    top, ch, bw = 470, 340, 190
    maxv = 48
    x1, x2 = M + 60, M + 480
    def Y(v): return top + ch - v / maxv * ch
    body = [txt(M, 250, 54, TEXT, "One asset vs eight", 800),
            txt(M, 316, 34, SUB, "share of crypto's total conversation")]
    body.append(f'<rect x="{x1}" y="{Y(btc):.0f}" width="{bw}" height="{btc/maxv*ch:.0f}" rx="10" fill="{ORANGE}"/>')
    body.append(txt(int(x1 + bw / 2), int(Y(btc) - 20), 46, ORANGE, f"{btc:.1f}%", 800, "middle"))
    body.append(txt(int(x1 + bw / 2), top + ch + 46, 28, TEXT, "Bitcoin", 600, "middle"))
    y = top + ch
    for name, v in segs:
        seg = v / maxv * ch
        y -= seg
        body.append(f'<rect x="{x2}" y="{y:.0f}" width="{bw}" height="{seg:.0f}" rx="4" fill="{PALETTE.get(name, DIM)}"/>')
        if v >= 4:
            body.append(txt(int(x2 + bw + 14), int(y + seg / 2 + 7), 21, PALETTE.get(name, DIM), name))
    body.append(txt(int(x2 + bw / 2), int(Y(rest) - 20), 46, TEXT, f"{rest:.1f}%", 800, "middle"))
    body.append(txt(int(x2 + bw / 2), top + ch + 46, 28, TEXT, "the other 8", 600, "middle"))
    body.append(txt(M, 960, 38, TEXT, "DeFi, Solana, memecoins, RWA, stablecoins,"))
    body.append(txt(M, 1008, 38, TEXT, "DePIN, AI agents and NFTs. All of them."))
    return frame(2, "\n".join(body), "Ethereum (11.2%) not shown")


def slide3(gain, lose) -> str:
    body = [txt(M, 250, 54, TEXT, "Where it moved", 800),
            txt(M, 320, 34, SUB, "change in share of conversation, week over week")]
    y = 420
    body.append(txt(M, y, 32, GREEN, "rotated in", 700))
    y += 60
    for n in gain[:4]:
        body.append(txt(M + 20, y, 38, TEXT, n["title"]))
        body.append(txt(W - M, y, 38, GREEN, f"+{n['shareDeltaPp']:.1f}", 700, "end"))
        y += 58
    y += 40
    body.append(txt(M, y, 32, RED, "rotated out", 700))
    y += 60
    for n in lose[:3]:
        body.append(txt(M + 20, y, 38, TEXT, n["title"]))
        body.append(txt(W - M, y, 38, RED, f"{n['shareDeltaPp']:.1f}", 700, "end"))
        y += 58
    return frame(3, "\n".join(body), "measured in percentage points of total attention")


def slide4() -> str:
    return frame(4, f"""
{txt(M, 260, 54, TEXT, "The trap", 800)}
{txt(M, 370, 42, TEXT, "NFT conversation is up")}
{txt(M, 470, 110, GREEN, "50%", 800)}
{txt(M, 550, 42, TEXT, "week over week.")}
{txt(M, 650, 42, SUB, "That's a headline. Here's the rest of it:")}
{txt(M, 730, 44, TEXT, "it moved NFTs from 1.6% of the", 700)}
{txt(M, 784, 44, TEXT, "conversation to 2.6%.", 700)}
{txt(M, 880, 38, SUB, "Both facts are true. Most coverage")}
{txt(M, 928, 38, SUB, "will only give you the first one.")}
""")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 320, 62, TEXT, "“Attention to X", 800)}
{txt(M, 392, 62, TEXT, "doubled” means", 800)}
{txt(M, 464, 62, TEXT, "nothing on its own.", 800)}
{txt(M, 580, 44, GREEN, "Doubled from what?", 700)}
{txt(M, 660, 40, TEXT, "1% to 2% and 20% to 40% are the")}
{txt(M, 710, 40, TEXT, "same percentage change and")}
{txt(M, 760, 40, TEXT, "completely different events.")}
{txt(M, 860, 38, SUB, "The share number tells you whether")}
{txt(M, 908, 38, SUB, "anyone actually noticed.")}
{txt(M, 1010, 40, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "weekly · Data: LunarCrush · code NICKI gets 15% off")


def main() -> None:
    r = json.loads((HERE / "out" / "report.json").read_text())
    ns = sorted(r["narratives"], key=lambda n: -n["shareNow"])
    btc = next(n["shareNow"] for n in ns if n["title"] == "Bitcoin")
    others = [n for n in ns if n["title"] not in ("Bitcoin", "Ethereum")]
    segs = [(n["title"], n["shareNow"]) for n in sorted(others, key=lambda n: n["shareNow"])]
    rest = sum(v for _, v in segs)
    gain = [n for n in sorted(ns, key=lambda n: -n["shareDeltaPp"]) if n["shareDeltaPp"] > 0]
    lose = [n for n in sorted(ns, key=lambda n: n["shareDeltaPp"]) if n["shareDeltaPp"] < 0]

    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(r["weekEnding"]), slide2(btc, rest, segs), slide3(gain, lose), slide4(), slide5()]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT} (BTC {btc:.1f}% vs others {rest:.1f}%)")


if __name__ == "__main__":
    main()
