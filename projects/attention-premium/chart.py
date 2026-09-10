#!/usr/bin/env python3
"""Chart the attention-premium result before and after cleaning.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL = "#0d1117", "#e6edf3", "#8b949e", "#161b22"
RED, GREEN, GREY, AMBER = "#f85149", "#3fb950", "#6e7681", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start") -> str:
    body = esc(s)
    if weight >= 700 and " " in str(s):
        words = str(s).split(" ")
        parts = [esc(words[0])]
        for prev, w in zip(words, words[1:]):
            dx = size * (0.45 if prev.endswith("%") else 0.30)
            parts.append(f'<tspan dx="{dx:.2f}">{esc(w)}</tspan>')
        body = "".join(parts)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def render(d: dict) -> str:
    W, H = 1300, 1046
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "I almost published this.", 700))
    o.append(txt(60, 112, 20, SUB,
                 "Do coins talked about more than they are worth underperform? "
                 "600,426 coin-days say no."))

    # Composition of the quietest bucket.
    o.append(txt(60, 178, 18, TEXT, "WHAT WAS IN THE “QUIET” BUCKET", 700))
    o.append(txt(60, 204, 16, SUB, "and how often each part beat Bitcoin over 7 days"))
    parts = [("Stablecoins", 18.2, 47.9, RED),
             ("Wrapped and staked assets", 11.4, 43.9, RED),
             ("Actual coins", 70.4, 40.6, GREY)]
    x0, y = 60, 236
    bw = 1180
    cx = x0
    for label, share, hit, col in parts:
        w = bw * share / 100
        o.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="70" fill="{col}" rx="4"/>')
        if w > 190:
            o.append(txt(cx + 18, y + 44, 26, "#ffffff" if col == GREY else "#ffffff",
                         f"{share:.1f}%", 700))
        cx += w
    o.append(txt(60, y + 108, 17, RED, "■", 700))
    o.append(txt(84, y + 108, 17, TEXT, "Stablecoins  18.2%", 700))
    o.append(txt(84, y + 134, 16, SUB, "beat BTC 47.9% of the time"))
    o.append(txt(440, y + 108, 17, RED, "■", 700))
    o.append(txt(464, y + 108, 17, TEXT, "Wrapped and staked  11.4%", 700))
    o.append(txt(464, y + 134, 16, SUB, "beat BTC 43.9% of the time"))
    o.append(txt(880, y + 108, 17, GREY, "■", 700))
    o.append(txt(904, y + 108, 17, TEXT, "Actual coins  70.4%", 700))
    o.append(txt(904, y + 134, 16, SUB, "beat BTC 40.6% of the time"))

    o.append(txt(60, y + 190, 19, TEXT,
                 "Nobody discusses USDT or WBETH. A wrapper's conversation belongs to the thing it wraps,", 700))
    o.append(txt(60, y + 218, 19, TEXT,
                 "so they sort into the quiet bucket, then beat Bitcoin every day Bitcoin falls.", 700))

    # The robustness checks that all passed on the contaminated sample.
    ry = 512
    o.append(txt(60, ry, 18, TEXT, "CHECKS THE CONTAMINATED VERSION PASSED", 700))
    o.append(txt(60, ry + 26, 16, SUB, "every one run on the same dirty sample"))
    checks = [("Held 2020-2022", "p = 0.018"), ("Held 2023-2026", "p = 0.010"),
              ("Dropped the 20 most common coins", "p = 0.004"),
              ("Larger half by market cap", "p < 0.001"),
              ("Volume floor raised 10x", "p = 0.002"),
              ("Size controlled within decile", "median cap equal")]
    cy = ry + 62
    for i, (label, note) in enumerate(checks):
        cx = 60 + (i % 2) * 600
        yy = cy + (i // 2) * 34
        o.append(txt(cx, yy, 16, GREEN, "✓", 700))
        o.append(txt(cx + 26, yy, 16, TEXT, label))
        o.append(txt(cx + 430, yy, 15, SUB, note, anchor="end"))
    o.append(txt(60, cy + 128, 18, AMBER,
                 "Robustness checks test whether a result is stable, not whether it is real.", 700))
    o.append(txt(60, cy + 154, 18, AMBER,
                 "A contaminated sample is stably contaminated.", 700))

    # Before / after.
    by = 776
    o.append(f'<rect x="60" y="{by}" width="1180" height="150" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, by + 40, 18, SUB, "QUIETEST MINUS LOUDEST, BEATS-BTC RATE AT +7d", 700))
    o.append(txt(84, by + 92, 17, TEXT, "With stablecoins and wrappers in", 400))
    o.append(txt(560, by + 96, 34, RED, "+3.1pp", 700))
    o.append(txt(690, by + 92, 17, SUB, "p = 0.004"))
    o.append(txt(84, by + 130, 17, TEXT, "With them removed", 400))
    o.append(txt(560, by + 134, 34, GREEN, "+1.5pp", 700))
    o.append(txt(690, by + 130, 17, SUB, "p = 0.053, and one of 12 comparisons"))

    o.append(txt(60, 976, 19, TEXT,
                 "The loudest coins do not underperform at all: +0.2pp against the middle, p = 0.74.", 700))
    o.append(txt(60, 1012, 16, GREY,
                 "Ranked within market-cap decile each day. Month-block bootstrap. Source: LunarCrush daily history."))
    o.append(txt(1240, 1012, 16, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "clean.json").read_text())
    out = HERE / "out" / "premium.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
