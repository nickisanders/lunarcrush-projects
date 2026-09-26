#!/usr/bin/env python3
"""Chart: the aggregates stayed flat through an incident. The posts did not.

Usage: python3 chart.py
"""

import json
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
    W, H = 1300, 940
    s = pd.DataFrame(d["series"])
    s["t"] = pd.to_datetime(s["t"])
    n = len(s)
    ev = [{**e, "t": pd.to_datetime(e["t"]).tz_localize(None)} for e in d["events"]]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    o.append(txt(60, 74, 37, TEXT, f"The price knew {d['gapHours']:.0f} hours before the warning post did.", 700))
    o.append(txt(60, 112, 20, SUB,
                 f"${d['symbol']} over 60 hours. Every attention metric stayed flat through the whole thing."))

    px0, px1 = 110, 1240
    def X(i): return px0 + (px1 - px0) * i / (n - 1)
    def nearest(t):
        return int((s["t"] - t).abs().idxmin()) - s.index[0]

    def panel(y0, y1, col, label, key, fmt, flat_note=None):
        vals = list(s[key])
        lo, hi = min(vals) * 0.92, max(vals) * 1.08
        def Y(v): return y1 - (y1 - y0) * (v - lo) / (hi - lo)
        o.append(txt(px0, y0 - 12, 15, col, label, 700))
        if flat_note:
            o.append(txt(px1, y0 - 12, 15, SUB, flat_note, 700, "end"))
        for frac in (0.0, 1.0):
            v = lo + (hi - lo) * frac
            o.append(f'<line x1="{px0}" y1="{Y(v):.1f}" x2="{px1}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
            o.append(txt(px0 - 10, Y(v) + 5, 13, SUB, fmt(v), 400, "end"))
        path = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        o.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>')
        return Y

    Yp = panel(190, 380, ORANGE, "PRICE", "close", lambda v: f"${v:,.2f}")
    panel(450, 560, BLUE, "ACCOUNTS POSTING PER HOUR", "crowd", lambda v: f"{v:,.0f}",
          f"never left {d['crowdMin']:.0f}–{d['crowdMax']:.0f}")
    panel(620, 710, GREEN, "SENTIMENT SCORE", "sent", lambda v: f"{v:,.0f}",
          f"never left {d['sentMin']:.0f}–{d['sentMax']:.0f}")

    # Event markers spanning all three panels. Labels alternate height and
    # flip anchor near the right edge so two close events cannot overprint.
    colours = {"price": ORANGE, "warn": RED, "ok": GREEN}
    for i, e in enumerate(ev):
        idx = nearest(e["t"])
        x = X(idx)
        col = colours[e["kind"]]
        o.append(f'<line x1="{x:.1f}" y1="185" x2="{x:.1f}" y2="712" stroke="{col}" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.85"/>')
        ly = 148 + (i % 2) * 24
        anchor = "end" if x > px1 - 260 else "start"
        dx = -8 if anchor == "end" else 8
        o.append(txt(x + dx, ly, 15, col, e["label"], 700, anchor))
        o.append(f'<circle cx="{x:.1f}" cy="{Yp(s["close"].iloc[idx]):.1f}" r="6" fill="{col}" stroke="{BG}" stroke-width="2"/>')

    # The gap between the price move and the warning.
    i0, i1 = nearest(ev[0]["t"]), nearest(ev[1]["t"])
    o.append(f'<rect x="{X(i0):.1f}" y="185" width="{X(i1) - X(i0):.1f}" height="527" fill="{AMBER}" opacity="0.07"/>')
    o.append(txt((X(i0) + X(i1)) / 2, 730, 15, AMBER, f"{d['gapHours']:.0f} hours", 700, "middle"))

    for i, t in enumerate(s["t"]):
        if t.hour in (0, 12):
            o.append(txt(X(i), 740, 13, SUB, t.strftime("%a %H:%M"), 400, "middle"))

    by = 780
    o.append(f'<rect x="60" y="{by}" width="1180" height="100" fill="{PANEL}" rx="6"/>')
    o.append(txt(84, by + 36, 19, TEXT,
                 f"The warning drew {d['warnInteractions']:,} interactions and still moved nothing: "
                 f"contributors stayed between {d['crowdMin']:.0f} and {d['crowdMax']:.0f} an hour all week.", 700))
    o.append(txt(84, by + 70, 17, SUB,
                 "A 3-sigma attention spike, the trigger every other tool in this repo uses, never came close to firing. "
                 "Reading the posts is the only thing that surfaced it."))

    o.append(txt(60, 912, 14, GREY,
                 f"Source: LunarCrush hourly and topic posts, as of {d['asOf']}. Post content is reported, not verified."))
    o.append(txt(1240, 912, 14, GREY, "github.com/nickisanders/lunarcrush-projects", anchor="end"))
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    d = json.loads((HERE / "out" / "zano.json").read_text())
    out = HERE / "out" / "zano.svg"
    out.write_text(render(d))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
