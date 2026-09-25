#!/usr/bin/env python3
"""Chart the scoreboard: what held, what died, and where the data lies.

Usage: python3 tools/scoreboard_chart.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
WRAP = 108


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


def wrap(s: str, n: int = WRAP) -> list[str]:
    out, line = [], ""
    for w in s.split():
        if len(line) + len(w) + 1 > n:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def render(d: dict) -> str:
    groups = [("works", "WHAT HELD UP", GREEN), ("null", "WHAT I TESTED AND BURIED", GREY),
              ("caution", "WHERE THE DATA WILL LIE TO YOU", AMBER)]
    lines = 0
    for key, _, _ in groups:
        for f in d["findings"]:
            if f["verdict"] == key:
                lines += len(wrap(f["text"]))
    W = 1300
    H = 210 + lines * 26 + len(groups) * 62 + 130
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, f"{d['projects']} projects on one crypto API. Here's the scoreboard.", 700))
    o.append(txt(60, 112, 20, SUB,
                 "Everything I could establish, everything that turned out to be nothing, and the traps in between."))

    y = 190
    for key, label, col in groups:
        items = [f for f in d["findings"] if f["verdict"] == key]
        o.append(txt(60, y, 17, col, f"{label}   ({len(items)})", 700))
        y += 30
        for f in items:
            for i, ln in enumerate(wrap(f["text"])):
                if i == 0:
                    o.append(f'<rect x="60" y="{y - 12}" width="4" height="16" fill="{col}" rx="2"/>')
                o.append(txt(78, y, 17, TEXT if i == 0 else SUB, ln))
                y += 26
            y += 4
        y += 28

    n_null = sum(1 for f in d["findings"] if f["verdict"] == "null")
    o.append(txt(60, H - 74, 19, TEXT,
                 f"{n_null} of these are nulls, and they are in the repo with the same care as the findings. "
                 "Publishing only the wins is how you end up believing your own noise.", 700))
    o.append(txt(60, H - 44, 15, GREY,
                 "Every number reproducible. Data: LunarCrush. Six years of daily history across 1,000 coins."))
    o.append(txt(1240, H - 44, 15, GREEN, "github.com/nickisanders/lunarcrush-projects", 700, "end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((ROOT / "tools" / "out" / "scoreboard.json").read_text())
    out = ROOT / "tools" / "out" / "scoreboard.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
