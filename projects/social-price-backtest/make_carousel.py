#!/usr/bin/env python3
"""Generate Instagram carousel slides (1080x1350 SVG) for the backtest write-up.

Writes out/instagram/slide-N.svg. Rasterize with sharp (see README):
    cd ../altrank-movers && node -e "..."
"""

from pathlib import Path

W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, TRACK = "#3fb950", "#f85149", "#21262d"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
OUT = Path(__file__).resolve().parent / "out" / "instagram"

TOTAL = 6


def esc(s: str) -> str:
    # librsvg collapses a regular space after "%" at heavy weights; use nbsp
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("% ", "% ")
    )


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W / 2 + (i - (TOTAL - 1) / 2) * 36}" cy="{H - 60}" r="7" '
        f'fill="{TEXT if i == n - 1 else TRACK}"/>'
        for i in range(TOTAL)
    )
    footer_el = (
        f'<text x="{M}" y="{H - 110}" font-size="28" fill="{SUB}">{esc(footer)}</text>'
        if footer
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
<text x="{M}" y="102" font-size="30" fill="{SUB}">the LunarCrush API series · {n}/{TOTAL}</text>
{body}
{footer_el}
{dots}
</svg>"""


def lines(items: list[tuple[str, int, str, int, str]], x: int = M) -> str:
    """items: (text, font_size, fill, y, weight)"""
    out = []
    for text, size, fill, y, weight in items:
        # At heavy weights librsvg renders word gaps near zero and ignores
        # word-spacing, so add explicit per-word dx offsets via tspans.
        if int(weight) >= 700 and " " in text:
            # librsvg collapses spaces at tspan boundaries, so the dx must
            # carry the entire word gap itself.
            words = text.split(" ")
            parts = [esc(words[0])]
            for prev, w in zip(words, words[1:]):
                # the % glyph has a large right overhang in the fallback font
                dx = size * (0.45 if prev.endswith("%") else 0.30)
                parts.append(f'<tspan dx="{dx:.0f}">{esc(w)}</tspan>')
            content = "".join(parts)
        else:
            content = esc(text)
        out.append(
            f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}">{content}</text>'
        )
    return "\n".join(out)


def bullet_block(entries: list[list[str]], start_y: int, gap: int = 66, group_gap: int = 46) -> str:
    out = []
    y = start_y
    for group in entries:
        out.append(f'<circle cx="{M + 10}" cy="{y - 15}" r="9" fill="{GREEN}"/>')
        for line in group:
            out.append(f'<text x="{M + 48}" y="{y}" font-size="42" fill="{TEXT}">{esc(line)}</text>')
            y += gap
        y += group_gap
    return "\n".join(out)


def slide1() -> str:
    body = lines(
        [
            ("85% of crypto", 108, TEXT, 420, 800),
            ("hype is bots.", 108, TEXT, 545, 800),
            ("I checked.", 108, GREEN, 700, 800),
            ("6.5 years of data. 997 coins.", 44, SUB, 850, 400),
            ("1.1 million coin-days.", 44, SUB, 910, 400),
        ]
    )
    return frame(1, body, "swipe for what actually predicts price")


def slide2() -> str:
    bars = [("Ordinary day", 41.9, SUB), ("Spam spike", 39.7, RED), ("Organic spike", 49.0, GREEN)]
    title = lines(
        [
            ("Odds of beating BTC", 62, TEXT, 260, 700),
            ("over the next 3 days", 62, TEXT, 335, 700),
        ]
    )
    top, chart_h, bw = 480, 520, 260
    gap = (W - 2 * M - 3 * bw) / 2
    maxv = 55.0
    y50 = top + chart_h - 50.0 / maxv * chart_h
    parts = [title]
    parts.append(
        f'<line x1="{M}" y1="{y50:.0f}" x2="{W - M}" y2="{y50:.0f}" stroke="#30363d" stroke-width="2" stroke-dasharray="8 8"/>'
    )
    parts.append(f'<text x="{M}" y="{y50 - 12:.0f}" font-size="26" fill="{SUB}">coin flip (50%)</text>')
    for i, (label, v, color) in enumerate(bars):
        x = M + i * (bw + gap)
        h = v / maxv * chart_h
        y = top + chart_h - h
        parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw}" height="{h:.0f}" rx="12" fill="{color}"/>')
        parts.append(
            f'<text x="{x + bw / 2:.0f}" y="{y - 20:.0f}" font-size="52" font-weight="700" fill="{color}" text-anchor="middle">{v}%</text>'
        )
        parts.append(
            f'<text x="{x + bw / 2:.0f}" y="{top + chart_h + 56}" font-size="30" fill="{TEXT}" text-anchor="middle">{esc(label)}</text>'
        )
    return frame(2, "\n".join(parts), "997 coins, 2020 to 2026, $50M+ market cap")


def slide3() -> str:
    title = lines([("The test", 72, TEXT, 280, 800)])
    bullets = bullet_block(
        [
            ["Social interactions jump 3+ standard", "deviations above the coin's 30-day norm"],
            ["Price stays flat that day (within 2%)"],
            ["Social moved. Price hadn't."],
            ["2,599 spike days among $50M+", "coins since 2020"],
        ],
        420,
    )
    return frame(3, title + bullets, "then measure returns over the next 1, 3, 7 days")


def slide4() -> str:
    title = lines([("Split by who's talking", 72, TEXT, 280, 800)])
    parts = [title]
    parts.append(f'<rect x="{M}" y="360" width="{W - 2 * M}" height="290" rx="18" fill="{TRACK}"/>')
    parts.append(
        lines(
            [
                ("Spam-heavy spikes (85%)", 46, RED, 440, 700),
                ("No signal. Directionally negative.", 40, TEXT, 510, 400),
                ("Manufactured hype does not pay.", 40, TEXT, 570, 400),
            ],
            x=M + 44,
        )
    )
    parts.append(f'<rect x="{M}" y="700" width="{W - 2 * M}" height="350" rx="18" fill="{TRACK}"/>')
    parts.append(
        lines(
            [
                ("Organic spikes (15%)", 46, GREEN, 780, 700),
                ("Odds of beating BTC in 3 days:", 40, TEXT, 850, 400),
                ("41.9% on ordinary days", 40, SUB, 910, 400),
                ("49.0% after an organic spike", 40, GREEN, 970, 700),
                ("p = 0.003, cluster bootstrap", 34, SUB, 1025, 400),
            ],
            x=M + 44,
        )
    )
    return frame(4, "\n".join(parts))


def slide5() -> str:
    title = lines([("The fine print", 72, TEXT, 280, 800)])
    bullets = bullet_block(
        [
            ["An odds shift, not a money printer"],
            ["Medians near zero. A minority of", "winners carries the average."],
            ["No execution costs. Daily data.", "Survivorship bias in the universe."],
            ["Every caveat documented in the repo"],
        ],
        420,
    )
    return frame(5, title + bullets, "if a backtest has no fine print, distrust it")


def slide6() -> str:
    body = lines(
        [
            ("Reproduce it", 92, TEXT, 420, 800),
            ("yourself", 92, TEXT, 530, 800),
            ("All code + methodology:", 42, SUB, 680, 400),
            ("github.com/nickisanders/", 46, GREEN, 750, 700),
            ("lunarcrush-projects", 46, GREEN, 810, 700),
            ("Data: LunarCrush", 42, SUB, 950, 400),
            ("Code NICKI gets 15% off", 46, TEXT, 1015, 700),
        ]
    )
    return frame(6, body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5, slide6], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
