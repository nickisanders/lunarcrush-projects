#!/usr/bin/env python3
"""Chart: price and crowd, hour by hour, for a coin that is pumping.

Usage: python3 chart.py out/ake.json
"""

import json
import sys
from pathlib import Path

import pandas as pd

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
    W, H = 1300, 860
    s = pd.DataFrame(d["series"])
    s["t"] = pd.to_datetime(s["t"])
    ev = {(e["what"], e["level"]): (pd.Timestamp(e["t"]) if e["t"] else None) for e in d["events"]}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    peak_i = int(s["close"].idxmax())
    hours_since_peak = len(s) - 1 - peak_i
    crowd_since_peak = s["contributors"].iloc[-1] / s["contributors"].iloc[peak_i] - 1
    if hours_since_peak >= 12 and crowd_since_peak > 0.15:
        title = f"${d['symbol']} stopped moving {hours_since_peak}h ago. The crowd is still arriving."
    else:
        title = f"${d['symbol']} is up {s['priceRel'].iloc[-1] * 100:.0f}%. The crowd showed up after."
    o.append(txt(60, 74, 38, TEXT, title, 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Price and distinct accounts posting, hour by hour, last {d['hours']} hours. Each relative to where it started."))

    # Plot area.
    px0, px1, py0, py1 = 90, 1240, 180, 560
    n = len(s)
    ymax = max(s["priceRel"].max(), s["crowdRel"].max()) * 1.12
    ymin = min(0, s["priceRel"].min(), s["crowdRel"].min()) - 0.05

    def X(i): return px0 + (px1 - px0) * i / (n - 1)
    def Y(v): return py1 - (py1 - py0) * (v - ymin) / (ymax - ymin)

    grid = [0, 0.25, 0.5, 0.75, 1.0] if ymax < 1.5 else [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    for lv in grid:
        if ymin <= lv <= ymax:
            o.append(f'<line x1="{px0}" y1="{Y(lv):.1f}" x2="{px1}" y2="{Y(lv):.1f}" stroke="{GRID}" stroke-width="1"/>')
            o.append(txt(px0 - 10, Y(lv) + 5, 14, SUB, f"{lv * 100:+.0f}%", 400, "end"))
    for i, t in enumerate(s["t"]):
        if t.hour in (0, 12):
            o.append(txt(X(i), py1 + 24, 13, SUB, t.strftime("%a %H:%M"), 400, "middle"))
            o.append(f'<line x1="{X(i):.1f}" y1="{py1}" x2="{X(i):.1f}" y2="{py1 + 6}" stroke="{GRID}"/>')

    def path(col):
        return "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s[col]))
    o.append(f'<path d="{path("crowdRel")}" fill="none" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>')
    o.append(f'<path d="{path("priceRel")}" fill="none" stroke="{ORANGE}" stroke-width="3.5" stroke-linejoin="round"/>')

    # Event markers.
    def mark(t, v, col, label, above=True):
        i = int((s["t"] == t).idxmax())
        x, y = X(i), Y(v)
        # A label near the right edge is anchored to its end so it stays on canvas.
        anchor = "end" if x > px1 - 120 else "middle"
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}" stroke="{BG}" stroke-width="2"/>')
        o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y - 34 if above else y + 34:.1f}" stroke="{col}" stroke-width="1.5"/>')
        o.append(txt(x, y - 42 if above else y + 52, 15, col, label, 700, anchor))

    tp = ev[("price", 0.25)]
    # The +100% crowd crossing is the clearer marker when it exists, and sits
    # further from the price marker on the canvas.
    tc = ev[("crowd", 1.0)] if ev.get(("crowd", 1.0)) is not None else ev[("crowd", 0.5)]
    tc_level = 1.0 if ev.get(("crowd", 1.0)) is not None else 0.5
    if hours_since_peak >= 12:
        tpk = s["t"].iloc[peak_i]
        mark(tpk, float(s["priceRel"].iloc[peak_i]), ORANGE, f"price peak  {tpk:%a %H:%M}")
    if tp is not None:
        mark(tp, float(s.loc[s["t"] == tp, "priceRel"].iloc[0]), ORANGE, f"price +25%  {tp:%H:%M}")
    if tc is not None:
        mark(tc, float(s.loc[s["t"] == tc, "crowdRel"].iloc[0]), BLUE, f"crowd +{tc_level * 100:.0f}%  {tc:%H:%M}", above=(tc_level >= 1.0))

    o.append(f'<rect x="{px0}" y="{py0 - 30}" width="14" height="14" fill="{ORANGE}" rx="2"/>')
    o.append(txt(px0 + 22, py0 - 18, 15, TEXT, "price"))
    o.append(f'<rect x="{px0 + 90}" y="{py0 - 30}" width="14" height="14" fill="{BLUE}" rx="2"/>')
    o.append(txt(px0 + 112, py0 - 18, 15, TEXT, "accounts posting per hour"))

    # Verdict and backtest context.
    vy = 640
    o.append(f'<rect x="60" y="{vy}" width="1180" height="120" fill="{PANEL}" rx="6"/>')
    verdict = d["verdict"].capitalize() + "."
    if hours_since_peak >= 12 and crowd_since_peak > 0.15:
        verdict += f" Since the price peaked, the crowd has grown another {crowd_since_peak * 100:.0f}%."
    o.append(txt(84, vy + 40, 22, TEXT, verdict, 700))
    o.append(txt(84, vy + 74, 17, SUB,
                 "Six years of backtest: an attention spike that lands on a flat price beats Bitcoin 49% of the time over 3 days,"))
    o.append(txt(84, vy + 100, 17, SUB,
                 "against a 42% baseline. The same spike after the price has already run 5%+ is 41.7%. No edge, p = 0.85."))

    o.append(txt(60, 806, 19, TEXT, "Attention that arrives after the move is people noticing it.", 700))
    o.append(txt(60, 838, 15, GREY, f"Source: LunarCrush hourly, {pd.Timestamp(d['start']):%Y-%m-%d} to {pd.Timestamp(d['end']):%Y-%m-%d %H:%M} UTC. Last partial hour dropped."))
    o.append(txt(1240, 838, 15, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "out/ake.json")
    d = json.loads(src.read_text())
    out = src.with_suffix(".svg")
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
