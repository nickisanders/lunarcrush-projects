#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for a resolved pick.

Reads out/track.json, so the numbers always match the last `npm run track`.
The attention-decay figures come from the same file, so the final slide can
never be handed a partial day by mistake.

Writes out/instagram/slide-N.svg. Rasterize with sharp:
    node -e "const s=require('sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram/slide-${i}.png`))"

Usage:
    python3 make_carousel.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
GREEN, GREY, ORANGE = "#3fb950", "#6e7681", "#f7931a"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
TOTAL = 5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """librsvg drops word spaces at font-weight >= 700, so space words by hand.
    The % glyph overhangs its advance width and needs a wider gap after it."""
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


def pct(v: float) -> str:
    return f"{'+' if v >= 0 else ''}{v * 100:.1f}%"


def stacked(r, top_y=520, ch=360) -> str:
    """Bitcoin's bar beside the pick's, with the pick's split into the part the
    market gave and the part the signal claims. The split is the whole point."""
    bw, x_btc, x_coin = 170, 190, 520
    top = max(r["coinReturn"], r["btcReturn"]) * 1.28

    def y(v):
        return top_y + ch - v / top * ch

    market_h = ch - (y(r["btcReturn"]) - top_y)
    spread_h = ch - (y(r["coinReturn"]) - top_y) - market_h
    return "\n".join([
        f'<line x1="{M}" y1="{top_y + ch}" x2="{W - M}" y2="{top_y + ch}" stroke="{TRACK}" stroke-width="2"/>',
        f'<rect x="{x_btc}" y="{y(r["btcReturn"]):.0f}" width="{bw}" height="{market_h:.0f}" rx="8" fill="{GREY}"/>',
        txt(x_btc + bw // 2, int(y(r["btcReturn"])) - 18, 34, GREY, pct(r["btcReturn"]), 700, "middle"),
        txt(x_btc + bw // 2, top_y + ch + 44, 26, TEXT, "Bitcoin", 400, "middle"),
        f'<rect x="{x_coin}" y="{y(r["btcReturn"]):.0f}" width="{bw}" height="{market_h:.0f}" rx="8" fill="{GREY}"/>',
        f'<rect x="{x_coin}" y="{y(r["coinReturn"]):.0f}" width="{bw}" height="{spread_h:.0f}" rx="8" fill="{GREEN}"/>',
        txt(x_coin + bw // 2, int(y(r["coinReturn"])) - 18, 34, GREEN, pct(r["coinReturn"]), 700, "middle"),
        txt(x_coin + bw // 2, top_y + ch + 44, 26, TEXT, f'${r["symbol"]}', 400, "middle"),
        txt(x_coin + bw + 24, int(y(r["coinReturn"]) + spread_h / 2) + 8, 26, GREEN, "the signal", 700),
        txt(x_coin + bw + 24, int(y(r["btcReturn"]) + market_h / 2) + 8, 26, GREY, "the market", 700),
    ])


def slide1(r) -> str:
    return frame(1, f"""
{txt(M, 330, 46, SUB, "Last Tuesday I published")}
{txt(M, 388, 46, SUB, "a pick. It resolved Friday.")}
{txt(M, 500, 56, TEXT, "It won.", 800)}
{txt(M, 640, 150, GREEN, pct(r["coinReturn"]), 800)}
{txt(M, 720, 40, TEXT, f'${r["symbol"]}, over the 3 days', 700)}
{txt(M, 772, 40, TEXT, "the signal actually covers", 700)}
{txt(M, 880, 34, SUB, "That is the number most accounts")}
{txt(M, 926, 34, SUB, "would screenshot and stop there.")}
{txt(M, 1010, 36, ORANGE, "Swipe for the rest of it.", 700)}
""", "swipe")


def slide2(r) -> str:
    return frame(2, f"""
{txt(M, 250, 50, TEXT, "The rest of it", 800)}
{txt(M, 312, 32, SUB, "Bitcoin over the exact same three days")}
{stacked(r)}
{txt(M, 1000, 36, TEXT, f'{pct(r["btcReturn"])} of that was just being in', 700)}
{txt(M, 1048, 36, TEXT, "crypto during a rally.", 700)}
""", "you would have gotten it holding BTC and reading nothing")


def slide3(r) -> str:
    return frame(3, f"""
{txt(M, 250, 50, TEXT, "So what did the", 800)}
{txt(M, 310, 50, TEXT, "signal actually do?", 800)}
{txt(M, 450, 130, GREEN, f'{r["spread"] * 100:.1f}', 800)}
{txt(M, 510, 36, TEXT, "points. That gap is the entire claim.", 700)}
{txt(M, 620, 36, SUB, "My backtest never said this coin goes up.")}
{txt(M, 668, 36, SUB, "It said this setup beats Bitcoin over 3 days")}
{txt(M, 716, 36, SUB, "49% of the time, versus 42% for a random")}
{txt(M, 764, 36, SUB, "coin. Relative, not directional.")}
{txt(M, 870, 40, ORANGE, "If I sold you the big number,", 700)}
{txt(M, 918, 40, ORANGE, "I would be selling you beta", 700)}
{txt(M, 966, 40, ORANGE, "and calling it alpha.", 700)}
""")


def slide4() -> str:
    return frame(4, f"""
{txt(M, 250, 50, TEXT, "And one pick", 800)}
{txt(M, 310, 50, TEXT, "proves nothing", 800)}
{txt(M, 430, 36, SUB, "At a 49/42 edge, roughly half of these lose.")}
{txt(M, 478, 36, SUB, "An early run of wins is exactly what you")}
{txt(M, 526, 36, SUB, "would expect either way.")}
{txt(M, 630, 40, TEXT, "So I built a tracker instead of", 700)}
{txt(M, 678, 40, TEXT, "a victory lap.", 700)}
{txt(M, 760, 36, SUB, "Every pick this bot publishes, resolved")}
{txt(M, 808, 36, SUB, "against Bitcoin, scored automatically,")}
{txt(M, 856, 36, SUB, "in the repo, whether it flatters me or not.")}
{txt(M, 950, 44, TEXT, "It reads 1 for 1 today.", 700)}
{txt(M, 1010, 40, ORANGE, "Ask me at 30.", 700)}
""")


def slide5(d) -> str:
    days = d["daysElapsed"]
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "One last thing", 800)}
{txt(M, 360, 36, SUB, "The conversation that flagged it peaked at")}
{txt(M, 430, 64, TEXT, f'{d["spike"] / 1e6:.1f}M', 800)}
{txt(M, 480, 32, SUB, "interactions on the spike day")}
{txt(M, 570, 36, SUB, f'{days} days later:')}
{txt(M, 640, 64, ORANGE, f'{d["latest"] / 1e6:.1f}M', 800)}
{txt(M, 690, 32, SUB, f'about {d["retained"] * 100:.0f}% of it left')}
{txt(M, 780, 40, TEXT, "The price held. The talk did not.", 700)}
{txt(M, 840, 34, SUB, "Which is why I score these at 3 days,")}
{txt(M, 886, 34, SUB, "not 30.")}
{txt(M, 970, 34, GREEN, "Always publish the benchmark next to", 700)}
{txt(M, 1014, 34, GREEN, "the return. Always publish the losses.", 700)}
{txt(M, 1082, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    track = json.loads((HERE / "out" / "track.json").read_text())
    r = track["rows"][-1]
    decay = r.get("decay")
    if not decay:
        raise SystemExit("no decay figures in track.json; run `npm run track` first")

    OUT.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([slide1(r), slide2(r), slide3(r), slide4(), slide5(decay)], 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}  (${r['symbol']} {pct(r['coinReturn'])} vs BTC {pct(r['btcReturn'])})")


if __name__ == "__main__":
    main()
