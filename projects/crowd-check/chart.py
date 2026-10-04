#!/usr/bin/env python3
"""Chart: the week's gainers, split by whether a crowd showed up.

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
    coins = d["coins"]
    W, H = 1300, 300 + len(coins) * 62 + 190
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    # The headline is derived, not written: the split changes every day and a
    # hardcoded finding goes stale the moment the screen is re-run.
    flagged = [c for c in coins if (c["growth"] or 0) < 0 or (c["spamLift"] or 0) >= d["freshWave"]]
    n, k = len(coins), len(flagged)
    if k == 0:
        title = f"All {n} of this week's biggest gainers had people show up."
    elif k == 1:
        title = f"{n} coins are up big. {k} has nobody new behind it."
    else:
        title = f"{n} coins are up big. {k} have nobody new behind them."
    o.append(txt(60, 74, 37, TEXT, title, 700))
    o.append(txt(60, 112, 20, SUB,
                 "This week's biggest gainers, against how many people are actually posting about each one."))

    y0 = 190
    o.append(txt(60, y0, 15, SUB, "COIN", 700))
    o.append(txt(300, y0, 15, SUB, "7 DAYS", 700, "end"))
    o.append(txt(380, y0, 15, SUB, "PEOPLE A DAY, NOW vs A MONTH AGO", 700))
    o.append(txt(700, y0, 15, SUB, "CHANGE", 700, "end"))
    o.append(txt(900, y0, 15, SUB, "SPAM vs ITS OWN NORM", 700, "end"))
    o.append(txt(960, y0, 15, SUB, "WHAT THAT LOOKS LIKE", 700))

    for i, c in enumerate(coins):
        y = y0 + 40 + i * 62
        clean = c["growth"] is not None and c["growth"] > 0 and (c["spamLift"] or 0) < d["freshWave"]
        accent = GREEN if clean else RED
        o.append(f'<rect x="60" y="{y - 26}" width="1180" height="48" fill="{PANEL}" rx="5"/>')
        o.append(f'<rect x="60" y="{y - 26}" width="4" height="48" fill="{accent}" rx="2"/>')
        o.append(txt(84, y, 21, TEXT, f"${c['symbol']}", 700))
        o.append(txt(300, y, 19, ORANGE, f"+{c['pct7d']:.0f}%", 700, "end"))
        o.append(txt(470, y, 17, GREY, f"{c['crowdBase']:,.0f}", 400, "end"))
        o.append(txt(492, y, 15, GREY, "→"))
        o.append(txt(560, y, 18, TEXT, f"{c['crowdNow']:,.0f}", 700, "end"))
        g = c["growth"]
        o.append(txt(700, y, 18, GREEN if g and g > 0 else RED, f"{g * 100:+.0f}%" if g is not None else "n/a", 700, "end"))
        sl = c["spamLift"]
        o.append(txt(900, y, 18, RED if sl and sl >= d["freshWave"] else SUB,
                     f"{sl:.2f}x" if sl is not None else "n/a", 700, "end"))
        o.append(txt(960, y, 16, accent if not clean else SUB, c["read"]))

    by = y0 + 40 + len(coins) * 62 + 16
    o.append(f'<rect x="60" y="{by}" width="1180" height="150" fill="{PANEL}" rx="6"/>')
    best = max(coins, key=lambda c: c["growth"] if c["growth"] is not None else -9)
    lean = min((c for c in coins if c["crowdNow"] > 0), key=lambda c: c["crowdNow"])
    o.append(txt(84, by + 38, 19, TEXT,
                 f"${lean['symbol']} rose {lean['pct7d']:.0f}% on {lean['crowdNow']:,.0f} people a day. "
                 f"${best['symbol']} went from {best['crowdBase']:,.0f} people to {best['crowdNow']:,.0f}.", 700))
    if flagged:
        f0 = flagged[0]
        detail = (f"a crowd {abs(f0['growth']) * 100:.0f}% smaller than a month ago"
                  if (f0["growth"] or 0) < 0 else f"spam at {f0['spamLift']:.2f}x its own norm")
        o.append(txt(84, by + 70, 19, TEXT,
                     f"${f0['symbol']} rose {f0['pct7d']:.0f}% with {detail}.", 700))
    else:
        o.append(txt(84, by + 70, 19, TEXT,
                     "Nothing on the list had a shrinking crowd, which is not the usual result.", 700))
    o.append(txt(84, by + 108, 16, SUB,
                 "Spam share on its own says little: some tokens run high chronically. The ratio against the coin's"))
    o.append(txt(84, by + 130, 16, SUB,
                 "own 30-day baseline is what separates a fresh wave from a noisy neighbourhood."))

    o.append(txt(60, H - 46, 18, TEXT,
                 "None of this identifies who is behind anything. It says which of these had somebody show up.", 700))
    o.append(txt(60, H - 16, 14, GREY, f"Source: LunarCrush, {d['asOf']}. Daily active contributors, last 7 days against the 30 before."))
    o.append(txt(1240, H - 16, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "crowd_check.json").read_text())
    out = HERE / "out" / "crowd_check.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
