#!/usr/bin/env python3
"""Chart: loud dumps keep falling, quiet dumps recover.

Usage: python3 chart.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG, TEXT, SUB, PANEL, GRID = "#0d1117", "#e6edf3", "#8b949e", "#161b22", "#30363d"
RED, GREEN, GREY, BLUE, AMBER = "#f85149", "#3fb950", "#6e7681", "#58a6ff", "#d29922"
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
    dm, pm = d["dumps"], d["pumps"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, "A dump people talk about keeps falling.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Coins that fell {d['drop'] * 100:.0f}%+ in a day, split by whether the crowd noticed. "
                 f"{d['coinDays']:,} coin-days, 2020 to 2026."))

    # Two panels: dumps (left), pumps (right). Each: beats-BTC at +1/+3/+7d, loud vs quiet.
    def panel(x0, title, r, loud, quiet, sub):
        o.append(txt(x0, 190, 18, TEXT, title, 700))
        o.append(txt(x0, 214, 14, SUB, sub))
        by, bh, bw = 250, 240, 60
        for lv in (0.3, 0.4, 0.5):
            y = by + bh - (lv - 0.25) / 0.30 * bh
            o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + 520}" y2="{y:.1f}" stroke="{GRID}"/>')
            o.append(txt(x0 - 8, y + 5, 13, SUB, f"{lv * 100:.0f}%", 400, "end"))
        for i, h in enumerate(("+1d", "+3d", "+7d")):
            cx = x0 + 90 + i * 170
            hl = (r["hit"][loud][h] - 0.25) / 0.30 * bh
            hq = (r["hit"][quiet][h] - 0.25) / 0.30 * bh
            o.append(f'<rect x="{cx - bw - 5}" y="{by + bh - hl:.1f}" width="{bw}" height="{hl:.1f}" fill="{RED}" rx="4"/>')
            o.append(f'<rect x="{cx + 5}" y="{by + bh - hq:.1f}" width="{bw}" height="{hq:.1f}" fill="{GREY}" rx="4"/>')
            o.append(txt(cx - bw / 2 - 5, by + bh - hl - 10, 17, TEXT, f"{r['hit'][loud][h] * 100:.0f}%", 700, "middle"))
            o.append(txt(cx + bw / 2 + 5, by + bh - hq - 10, 17, TEXT, f"{r['hit'][quiet][h] * 100:.0f}%", 700, "middle"))
            o.append(txt(cx, by + bh + 24, 15, TEXT, h, 700, "middle"))
            dd = [x for x in r["diff"] if x["horizon"] == h][0]
            col = RED if dd["p"] < 0.05 else SUB
            o.append(txt(cx, by + bh + 46, 14, col, f"{dd['diff'] * 100:+.0f}pp  p={dd['p']:.3f}", 700, "middle"))
        o.append(f'<rect x="{x0}" y="{by + bh}" width="520" height="1" fill="{GRID}"/>')

    panel(100, f"AFTER A {d['drop'] * 100:.0f}%+ DUMP", dm, "loud_dump", "quiet_dump",
          f"beats Bitcoin over the next N days. loud n={dm['n']['loud_dump']:,}, quiet n={dm['n']['quiet_dump']:,}")
    panel(720, f"AFTER A {d['drop'] * 100:.0f}%+ PUMP, FOR CONTRAST", pm, "loud_pump", "quiet_pump",
          f"loud n={pm['n']['loud_pump']:,}, quiet n={pm['n']['quiet_pump']:,}")
    o.append(f'<rect x="100" y="570" width="14" height="14" fill="{RED}" rx="2"/>')
    o.append(txt(122, 582, 14, SUB, "loud: an attention spike landed on the move"))
    o.append(f'<rect x="420" y="570" width="14" height="14" fill="{GREY}" rx="2"/>')
    o.append(txt(442, 582, 14, SUB, "quiet: it did not"))

    # Where it lives.
    ry = 630
    o.append(f'<rect x="60" y="{ry}" width="1180" height="150" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, ry + 32, 15, SUB, "WHERE THE DUMP EFFECT LIVES  (loud minus quiet, beats-BTC at +3d)", 700))
    rob = {r["check"]: r for r in d["robustness"]}
    rows = [("smaller half of coins, under $279M", "smaller half by mcap"),
            ("larger half, over $279M", "larger half by mcap"),
            ("2023 to 2026, where 92% of the sample is", "2023-2026"),
            ("20%+ dumps", "20% dumps")]
    for i, (lab, key) in enumerate(rows):
        r = rob[key]
        col, row = divmod(i, 2)
        x = 84 + col * 590
        y = ry + 70 + row * 34
        c = RED if r["p"] < 0.05 else SUB
        o.append(txt(x, y, 15, TEXT, lab))
        o.append(txt(x + 400, y, 15, c, f"{r['diff'] * 100:+.0f}pp", 700))
        o.append(txt(x + 470, y, 14, SUB, f"p={r['p']:.3f}  n={r['nLoud']}"))

    o.append(txt(60, 822, 19, TEXT,
                 "A quiet dump is usually the market. A loud dump usually has a reason, and the reason is not finished.", 700))
    o.append(txt(60, 856, 14, GREY,
                 "Spike: interactions 3+ SD above the coin's trailing 30 days. BTC-adjusted, month-block bootstrap. Source: LunarCrush."))
    o.append(txt(1240, 856, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "loud_dumps.json").read_text())
    out = HERE / "out" / "loud_dumps.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
