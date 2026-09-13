#!/usr/bin/env python3
"""Chart: crypto's conversation consolidating into a few coins, 2024 to 2026.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER, ORANGE = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922", "#f7931a"
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
    W, H = 1300, 900
    c = d["concentration"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "Half of crypto is talking about three coins.", 700))
    o.append(txt(60, 112, 20, SUB,
                 "Share of everyone posting about crypto each day, by which coin. Early 2024 against mid 2026."))

    # Two stacked bars: then / now.
    bx, bw = 60, 1180
    for i, (lab, key) in enumerate((("EARLY 2024", "then"), ("MID 2026", "now"))):
        y = 180 + i * 150
        btc, eth, sol = c["btc"][key], c["eth"][key], c["sol"][key]
        t10 = c["top10"][key]
        segs = [("BTC", btc, ORANGE), ("ETH", eth, BLUE), ("SOL", sol, "#9945ff"),
                ("coins 4 to 10", t10 - btc - eth - sol, GREY), ("everything else", 1 - t10, PANEL)]
        o.append(txt(bx, y - 14, 17, SUB, lab, 700))
        o.append(txt(bx + bw, y - 14, 17, TEXT, f"top 3 = {c['top3'][key] * 100:.0f}%", 700, "end"))
        x = bx
        for name, v, col in segs:
            w = bw * v
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="90" fill="{col}"/>')
            if w > 70:
                o.append(txt(x + 14, y + 40, 16, TEXT if col == PANEL else "#ffffff", name, 700))
                o.append(txt(x + 14, y + 68, 20, TEXT if col == PANEL else "#ffffff", f"{v * 100:.0f}%", 700))
            x += w
        o.append(f'<rect x="{bx}" y="{y}" width="{bw}" height="90" fill="none" stroke="{GRID}" stroke-width="1"/>')

    # Narratives: every one lost except three.
    ny = 496
    o.append(txt(60, ny, 18, TEXT, "WHAT EACH NARRATIVE'S SHARE OF THE CROWD DID", 700))
    o.append(txt(60, ny + 24, 15, SUB, "coins tagged with each category by LunarCrush; a coin can carry several tags"))
    nar = [n for n in d["narratives"] if n["tag"] not in ("layer-1", "bitcoin-ecosystem")]
    nar = sorted(nar, key=lambda n: n["changeRel"])
    cols = 2
    per = (len(nar) + 1) // cols
    for i, n in enumerate(nar):
        col, row = divmod(i, per)
        x = 60 + col * 600
        y = ny + 66 + row * 34
        rel = n["changeRel"] * 100
        colr = GREEN if rel > 5 else RED if rel < -5 else SUB
        o.append(txt(x, y, 16, TEXT, n["label"]))
        o.append(txt(x + 250, y, 16, SUB, f"{n['then'] * 100:.1f}% → {n['now'] * 100:.1f}%"))
        lab = "new" if n["then"] == 0 else f"{rel:+.0f}%"
        o.append(txt(x + 540, y, 16, colr, lab, 700, "end"))

    o.append(txt(60, 838, 19, TEXT,
                 "Fewer people, on fewer coins. The crowd shrank 37% and the share outside the top ten fell from 59% to 36%.", 700))
    o.append(txt(60, 872, 15, GREY,
                 "Daily active contributors, 1,000 coins, pegged assets and name collisions removed. Source: LunarCrush."))
    o.append(txt(1240, 872, 15, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "shift.json").read_text())
    out = HERE / "out" / "shift.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
