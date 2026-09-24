#!/usr/bin/env python3
"""Chart: price and crowd, hour by hour, for a coin that is pumping.

Usage: python3 chart.py out/ake.json ["optional title"]
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


def render(d: dict, title: str | None = None) -> str:
    """Two stacked panels, not one shared axis.

    A coin whose crowd grows 3,000% while its price doubles cannot share a
    y-axis with its own price: the smaller series flattens to a straight line
    and the chart says nothing. Each series gets its own panel and its own
    scale, and the shared x-axis carries the comparison.
    """
    W, H = 1300, 920
    s = pd.DataFrame(d["series"])
    s["t"] = pd.to_datetime(s["t"])
    n = len(s)
    peak_i = int(s["close"].idxmax())
    crowd_i = int(s["contributors"].idxmax())
    drop_pct = (s["close"].iloc[-1] / s["close"].iloc[peak_i] - 1) * 100
    crowd_since_peak = s["contributors"].iloc[-1] / s["contributors"].iloc[peak_i] - 1
    lag = (s["t"].iloc[crowd_i] - s["t"].iloc[peak_i]).total_seconds() / 3600

    if not title:
        if s["close"].iloc[-1] < s["close"].iloc[peak_i] * 0.6 and crowd_since_peak > -0.1:
            title = f"${d['symbol']} is {abs(drop_pct):.0f}% off its top. The crowd has never been bigger."
        elif lag >= 4:
            title = f"${d['symbol']}: the price peaked {lag:.0f}h before the crowd did."
        else:
            title = f"${d['symbol']} is up {s['priceRel'].iloc[-1] * 100:.0f}%. The crowd showed up after."

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 38, TEXT, title, 700))
    o.append(txt(60, 112, 20, SUB,
                 f"Price and distinct accounts posting, hour by hour, last {d['hours']} hours."))

    px0, px1 = 110, 1240
    def X(i): return px0 + (px1 - px0) * i / (n - 1)

    def panel(y0, y1, col, label, vals, fmt, marker_i, marker_label):
        lo, hi = min(vals) * 0.92, max(vals) * 1.08
        def Y(v): return y1 - (y1 - y0) * (v - lo) / (hi - lo)
        o.append(txt(px0, y0 - 14, 15, col, label, 700))
        for frac in (0.0, 0.5, 1.0):
            v = lo + (hi - lo) * frac
            o.append(f'<line x1="{px0}" y1="{Y(v):.1f}" x2="{px1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
            o.append(txt(px0 - 10, Y(v) + 5, 13, SUB, fmt(v), 400, "end"))
        path = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        o.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>')
        mx_, my = X(marker_i), Y(vals[marker_i])
        o.append(f'<circle cx="{mx_:.1f}" cy="{my:.1f}" r="7" fill="{col}" stroke="{BG}" stroke-width="2"/>')
        anchor = "end" if mx_ > px1 - 200 else "start"
        o.append(txt(mx_ + (-14 if anchor == "end" else 14), my - 14, 15, col, marker_label, 700, anchor))
        return Y

    closes = list(s["close"])
    crowds = list(s["contributors"])
    panel(190, 400, ORANGE, "PRICE", closes,
          lambda v: f"${v:,.4f}" if v < 1 else f"${v:,.2f}",
          peak_i, f"peak {s['t'].iloc[peak_i]:%a %H:%M}")
    panel(480, 690, BLUE, "ACCOUNTS POSTING PER HOUR", crowds,
          lambda v: f"{v:,.0f}", crowd_i, f"peak {s['t'].iloc[crowd_i]:%a %H:%M}")

    # Shared x-axis and a band marking the stretch after the price peak.
    o.append(f'<rect x="{X(peak_i):.1f}" y="180" width="{px1 - X(peak_i):.1f}" height="520" fill="{RED}" opacity="0.06"/>')
    for i, t in enumerate(s["t"]):
        if t.hour in (0, 12):
            o.append(txt(X(i), 720, 13, SUB, t.strftime("%a %H:%M"), 400, "middle"))
            o.append(f'<line x1="{X(i):.1f}" y1="690" x2="{X(i):.1f}" y2="698" stroke="{GRID}"/>')
    o.append(txt(X(peak_i) + 10, 700, 14, RED, "after the price peak", 700))

    vy = 760
    o.append(f'<rect x="60" y="{vy}" width="1180" height="100" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, vy + 38, 21, TEXT,
                 f"The crowd peaked {abs(lag):.0f} hours {'after' if lag > 0 else 'before'} the price did. "
                 f"Since the top: price {drop_pct:+.0f}%, crowd {crowd_since_peak * 100:+.0f}%.", 700))
    o.append(txt(84, vy + 74, 17, SUB,
                 "Six years of backtest: an attention spike on a flat price beats Bitcoin 49% of the time over 3 days. "
                 "After the price has already run 5%+, 41.7%, which is the baseline."))

    o.append(txt(60, 896, 14, GREY,
                 f"Source: LunarCrush hourly, {pd.Timestamp(d['start']):%Y-%m-%d} to {pd.Timestamp(d['end']):%Y-%m-%d %H:%M} UTC. Last partial hour dropped."))
    o.append(txt(1240, 896, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "out/ake.json")
    title = sys.argv[2] if len(sys.argv) > 2 else None
    d = json.loads(src.read_text())
    out = src.with_suffix(".svg")
    out.write_text(render(d, title))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
