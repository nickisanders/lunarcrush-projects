#!/usr/bin/env python3
"""One-off carousel: the chronic-vs-fresh spam lesson ($TRUMP vs $ZAMA).

Writes out/instagram-chronicfresh/slide-N.svg (1080x1350).
"""

from pathlib import Path

W, H, M = 1080, 1350, 90
BG, TEXT, SUB = "#0d1117", "#e6edf3", "#8b949e"
GREEN, RED, TRACK, DIM = "#3fb950", "#f85149", "#21262d", "#6e7681"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
OUT = Path(__file__).resolve().parent / "out" / "instagram-chronicfresh"
TOTAL = 5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    words = text.split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        factor = 0.45 if prev.endswith("%") else 0.30
        parts.append(f'<tspan dx="{size * factor:.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x: int, y: int, size: int, fill: str, content: str, weight: int = 400, anchor: str = "start") -> str:
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


def panel(days, vals, mults, color, hot_color_dim) -> str:
    """Six-bar mini chart with spam-multiple labels, sized for 4:5."""
    chart_top, chart_h, bw = 460, 480, 130
    gap = (W - 2 * M - 6 * bw) / 5
    maxv = max(vals)
    out = []
    for i, v in enumerate(vals):
        x = M + i * (bw + gap)
        h = max(10, v / maxv * chart_h)
        y = chart_top + chart_h - h
        c = color if i == 5 else hot_color_dim if i == 4 else DIM
        val = f"{v/1000:.1f}M" if v >= 1000 else f"{v}k"
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw}" height="{h:.0f}" rx="9" fill="{c}"/>')
        out.append(txt(int(x + bw / 2), int(y - 16), 26, TEXT if i >= 4 else SUB, val, 600, "middle"))
        out.append(txt(int(x + bw / 2), chart_top + chart_h + 42, 23, SUB, days[i], 400, "middle"))
        out.append(
            txt(int(x + bw / 2), chart_top + chart_h + 84, 28, color if i == 5 else SUB, mults[i], 700 if i == 5 else 400, "middle")
        )
    return "\n".join(out)


def slide1() -> str:
    return frame(
        1,
        f"""
{txt(M, 400, 100, TEXT, "My bot called an", 800)}
{txt(M, 520, 100, RED, "83% spam coin", 800)}
{txt(M, 640, 100, GREEN, "organic.", 800)}
{txt(M, 780, 52, TEXT, "It's right.", 700)}
{txt(M, 880, 42, SUB, "The reason is the most misunderstood")}
{txt(M, 935, 42, SUB, "thing about crypto spam data.")}
""",
        "swipe",
    )


def slide2() -> str:
    body = f"""
{txt(M, 250, 64, GREEN, "$TRUMP · today", 800)}
{txt(M, 320, 40, TEXT, "Attention 4x. Spam at 0.8x its own norm.")}
{txt(M, 372, 34, SUB, "daily interactions · number below = spam vs 30-day norm")}
{panel(["Jul 31","Aug 1","Aug 2","Aug 3","Aug 4","Aug 5"], [640, 661, 548, 518, 1760, 2328], ["1.0x","1.1x","1.4x","1.0x","0.9x","0.8x"], GREEN, "#2ea04366")}
{txt(M, 1160, 40, TEXT, "Always a spammy neighborhood.")}
{txt(M, 1212, 40, GREEN, "No fresh wave today. Verdict: organic.", 700)}
"""
    return frame(2, body)


def slide3() -> str:
    body = f"""
{txt(M, 250, 64, RED, "$ZAMA · last week", 800)}
{txt(M, 320, 40, TEXT, "Attention 6x. Spam at 2.0x its own norm.")}
{txt(M, 372, 34, SUB, "same metric, same scale, opposite story")}
{panel(["Jul 26","Jul 27","Jul 28","Jul 29","Jul 30","Jul 31"], [249, 325, 484, 359, 1089, 2115], ["1.1x","0.9x","0.9x","1.0x","1.0x","2.0x"], RED, "#f8514966")}
{txt(M, 1160, 40, TEXT, "A fresh spam wave riding the spike,")}
{txt(M, 1212, 40, RED, "3 accounts driving 98%. Manufactured.", 700)}
"""
    return frame(3, body)


def slide4() -> str:
    return frame(
        4,
        f"""
{txt(M, 300, 72, TEXT, "The lesson", 800)}
{txt(M, 430, 44, TEXT, "The absolute spam % tells you what a")}
{txt(M, 488, 44, TEXT, "coin's conversation is like every day.")}
{txt(M, 590, 44, GREEN, "The change against its own baseline", 700)}
{txt(M, 648, 44, GREEN, "tells you what's happening today.", 700)}
{txt(M, 760, 44, TEXT, "Score the change, not the level.")}
{txt(M, 880, 38, SUB, "That one calibration is the difference between")}
{txt(M, 930, 38, SUB, "a working detector and a broken one.")}
""",
        "the detector prints it right on the verdict: chronic baseline, no fresh wave",
    )


def slide5() -> str:
    return frame(
        5,
        f"""
{txt(M, 400, 92, TEXT, "The detector", 800)}
{txt(M, 510, 92, TEXT, "runs daily.", 800)}
{txt(M, 650, 42, SUB, "Open source, every verdict ships its evidence:")}
{txt(M, 720, 46, GREEN, "github.com/nickisanders/", 700)}
{txt(M, 780, 46, GREEN, "lunarcrush-projects", 700)}
{txt(M, 920, 42, SUB, "Data: LunarCrush")}
{txt(M, 985, 46, TEXT, "Code NICKI gets 15% off", 700)}
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4, slide5], 1):
        (OUT / f"slide-{i}.svg").write_text(fn())
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
