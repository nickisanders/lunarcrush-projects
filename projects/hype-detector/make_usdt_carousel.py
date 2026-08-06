#!/usr/bin/env python3
"""One-off carousel: the $USDT institutional-broadcast spike (Aug 6, 2026).

Writes out/instagram-usdt/slide-N.svg (1080x1350).
"""

from pathlib import Path

W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, YELLOW, TRACK, DIM = "#3fb950", "#f85149", "#d29922", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
OUT = Path(__file__).resolve().parent / "out" / "instagram-usdt"
TOTAL = 5

ROWS = [
    ("MEXC", "exchange", 10_400_570, "89%", RED),
    ("whale_alert", "transfer bot", 581_019, "5%", YELLOW),
    ("MEXC_ID", "same exchange", 223_800, "2%", RED),
    ("Gate", "exchange", 81_006, "1%", RED),
    ("everyone else", "all of crypto", 358_863, "3%", DIM),
]


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
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>'
    )


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W / 2 + (i - (TOTAL - 1) / 2) * 36}" cy="{H - 60}" r="7" '
        f'fill="{TEXT if i == n - 1 else TRACK}"/>'
        for i in range(TOTAL)
    )
    f = txt(M, H - 110, 28, SUB, footer) if footer else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{txt(M, 102, 30, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}
{body}
{f}
{dots}
</svg>"""


def slide1() -> str:
    return frame(
        1,
        f"""
{txt(M, 420, 96, TEXT, "Stablecoins", 800)}
{txt(M, 530, 96, TEXT, "aren't supposed", 800)}
{txt(M, 640, 96, TEXT, "to trend.", 800)}
{txt(M, 790, 46, RED, "$USDT spiked today.", 700)}
{txt(M, 856, 42, SUB, "11.6 million interactions in 24 hours.")}
{txt(M, 908, 42, SUB, "So I pulled the creator breakdown.")}
""",
        "swipe for who was actually posting",
    )


def slide2() -> str:
    top, rowh = 400, 150
    barmax = W - 2 * M - 210
    maxv = max(r[2] for r in ROWS)
    out = [
        txt(M, 250, 60, TEXT, "It's one account.", 800),
        txt(M, 310, 34, SUB, "interactions on $USDT, last 24h, by creator"),
    ]
    for i, (name, kind, v, pct, color) in enumerate(ROWS):
        y = top + i * rowh
        w = max(8, round(v / maxv * barmax))
        label = f"{v/1e6:.1f}M" if v >= 1e6 else f"{round(v/1000)}k"
        out.append(txt(M, y, 36, TEXT, name, 600))
        out.append(txt(M, y + 40, 26, SUB, kind))
        out.append(txt(W - M, y, 34, color, pct, 700, "middle" if False else "end"))
        out.append(f'<rect x="{M}" y="{y + 58}" width="{barmax}" height="30" rx="8" fill="{TRACK}"/>')
        out.append(f'<rect x="{M}" y="{y + 58}" width="{w}" height="30" rx="8" fill="{color}"/>')
        out.append(txt(M + barmax + 18, y + 82, 28, color, label, 700))
    return frame(2, "\n".join(out))


def slide3() -> str:
    return frame(
        3,
        f"""
{txt(M, 300, 66, TEXT, "Nothing shady", 800)}
{txt(M, 375, 66, TEXT, "happened here.", 800)}
{txt(M, 500, 42, TEXT, "Exchanges run giveaways.")}
{txt(M, 556, 42, TEXT, "whale_alert posts big transfers.")}
{txt(M, 612, 42, TEXT, "That's the job.")}
{txt(M, 730, 42, SUB, "But if you were watching social volume")}
{txt(M, 782, 42, SUB, "on USDT today, you'd have seen a spike")}
{txt(M, 834, 42, SUB, "and assumed something happened.")}
{txt(M, 930, 46, RED, "What happened was a", 700)}
{txt(M, 986, 46, RED, "marketing campaign.", 700)}
""",
    )


def slide4() -> str:
    return frame(
        4,
        f"""
{txt(M, 280, 64, TEXT, "My detector", 800)}
{txt(M, 352, 64, TEXT, "handled it badly.", 800)}
{txt(M, 470, 42, TEXT, "It scored 53/100 and filed it")}
{txt(M, 522, 42, TEXT, "under “mixed” — technically honest,")}
{txt(M, 574, 42, TEXT, "practically useless.")}
{txt(M, 680, 42, SUB, "This isn't a botnet. It isn't a crowd.")}
{txt(M, 732, 42, SUB, "It's a category I hadn't named.")}
{txt(M, 850, 50, GREEN, "So I shipped a label:", 700)}
{txt(M, 916, 50, GREEN, "institutional broadcast.", 700)}
{txt(M, 1000, 34, SUB, "live in the detector as of today")}
""",
    )


def slide5() -> str:
    return frame(
        5,
        f"""
{txt(M, 380, 62, TEXT, "The number never", 800)}
{txt(M, 452, 62, TEXT, "tells you who's", 800)}
{txt(M, 524, 62, RED, "behind it.", 800)}
{txt(M, 650, 42, SUB, "The detector runs daily and shows its")}
{txt(M, 702, 42, SUB, "evidence on every verdict.")}
{txt(M, 810, 46, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 866, 46, GREEN, "lunarcrush-projects", 700)}
{txt(M, 970, 42, SUB, "Data: LunarCrush")}
{txt(M, 1032, 46, TEXT, "Code NICKI gets 15% off", 700)}
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
