#!/usr/bin/env python3
"""Chart one coin's crowd against its price, when the two stop agreeing.

The spotlight chart answers whether a crowd showed up. This answers what
happened next, which is the question a follow-up post needs and the one the
bar chart cannot show: a crowd can still be growing while the price rolls over,
and that divergence is the whole story.

Two lines on their own scales, because the point is the shape rather than any
shared unit. The price peak is marked, since the gap between it and the crowd
peak is the measurement.

Usage:
    LUNARCRUSH_API_KEY=... python3 divergence.py STRK --days 14
"""

import argparse
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BASE = "https://lunarcrush.com/api4"
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
GREEN, RED, AMBER = "#3fb950", "#f85149", "#d29922"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, monospace"
W, H = 1200, 870
# R stops well short of the edge: the series labels sit to the right of the
# last point and ran off the canvas at 1120.
L, R, TOP, BOT = 90, 980, 210, 560


def get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {os.environ['LUNARCRUSH_API_KEY']}",
                 "User-Agent": "lunarcrush-projects/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{body}</text>')


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def path_for(vals, lo, hi):
    """Each series is scaled to its own range: the comparison is of shape, and
    people-per-day and dollars share no axis worth drawing."""
    span = (hi - lo) or 1
    step = (R - L) / max(len(vals) - 1, 1)
    pts = [(L + i * step, BOT - (v - lo) / span * (BOT - TOP)) for i, v in enumerate(vals)]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts), pts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    ap.add_argument("--name")
    ap.add_argument("--days", type=int, default=14)
    a = ap.parse_args()
    sym = a.symbol.upper()

    rows = [r for r in (get(f"/public/coins/{sym}/time-series/v2?bucket=day&interval=1m")
                        .get("data") or []) if r.get("contributors_active") is not None]
    rows = rows[-(a.days + 1):-1]          # drop the partial current day
    coins = get("/public/coins/list/v2?limit=1000")["data"]
    coin = next((c for c in coins if str(c.get("symbol")).upper() == sym), {})
    name = a.name or coin.get("name") or sym
    live = num(coin.get("price"))

    people = [num(r["contributors_active"]) for r in rows]
    price = [num(r.get("close")) for r in rows]
    days = [datetime.fromtimestamp(r["time"], timezone.utc) for r in rows]
    peak_i = price.index(max(price))
    crowd_i = people.index(max(people))

    b = [txt(60, 60, 36, TEXT,
             f"{name}'s crowd kept growing. The price did not.", 700),
         txt(60, 94, 20, SUB,
             f"${sym}, daily. Each line on its own scale; the shape is the comparison.")]

    for vals, col, label in ((people, GREEN, "people posting"), (price, AMBER, "price")):
        d, pts = path_for(vals, min(vals), max(vals))
        b.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3.5" '
                 f'stroke-linejoin="round"/>')
        b.append(txt(R + 14, pts[-1][1] + 7, 19, col, label, 700))

    # Mark both peaks. The distance between them is the finding.
    _, ppts = path_for(price, min(price), max(price))
    _, cpts = path_for(people, min(people), max(people))
    # The two peaks are days apart, so their labels collide if both sit above
    # their point. Price goes above, crowd below, and both pull left near the
    # right edge so neither runs off.
    for i, pts, col, lab, dy in (
        (peak_i, ppts, AMBER, f"price peak ${price[peak_i]:.4f}", -22),
        (crowd_i, cpts, GREEN, f"crowd peak {people[crowd_i]:,.0f}", 62),
    ):
        x, y = pts[i]
        anchor = "end" if x > R - 150 else "middle"
        tx = x - 12 if anchor == "end" else x
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}"/>')
        b.append(txt(tx, y + dy, 18, col, f"{lab}  {days[i]:%b %-d}", 700, anchor))

    b.append(f'<rect x="{L}" y="{BOT}" width="{R-L}" height="1.5" fill="{TRACK}"/>')
    for i in (0, len(rows) // 2, len(rows) - 1):
        x = L + i * ((R - L) / max(len(rows) - 1, 1))
        b.append(txt(x, BOT + 30, 18, SUB, f"{days[i]:%b %-d}", 400, "middle"))

    drop = (live / price[peak_i] - 1) * 100
    y = BOT + 96
    b.append(f'<rect x="60" y="{y}" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, y + 48, 25, TEXT,
                 f"People posting rose from {people[0]:,.0f} a day to {people[-1]:,.0f}.", 700))
    b.append(txt(60, y + 86, 25, RED,
                 f"The price is {abs(drop):.0f}% below its peak.", 700))
    b.append(txt(60, y + 124, 19, SUB,
                 "A real crowd is not the same thing as a good entry."))
    b.append(txt(60, y + 150, 19, SUB,
                 "People arrive after the move, not before it."))
    b.append(txt(60, H - 26, 16, SUB, "Source: LunarCrush"))
    b.append(txt(1140, H - 26, 16, SUB,
                 "github.com/nickisanders/lunarcrush-projects", 400, "end"))

    # Saved so a carousel reads the same numbers rather than having them
    # retyped, which is how slides drift from the chart they illustrate.
    facts = {
        "symbol": sym, "name": name,
        "days": [d.strftime("%Y-%m-%d") for d in days],
        "people": [round(v) for v in people],
        "price": price,
        "live_price": live,
        "price_peak": {"value": price[peak_i], "day": days[peak_i].strftime("%Y-%m-%d")},
        "crowd_peak": {"value": round(people[crowd_i]),
                       "day": days[crowd_i].strftime("%Y-%m-%d")},
        "from_peak_pct": round((live / price[peak_i] - 1) * 100, 1),
        # The gap between the two peaks is the whole point of this chart.
        "crowd_peaked_days_after_price": crowd_i - peak_i,
    }
    out0 = HERE / "out"
    out0.mkdir(exist_ok=True)
    (out0 / f"divergence-{sym.lower()}.json").write_text(json.dumps(facts, indent=2))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / f"divergence-{sym.lower()}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{out}/divergence-{sym.lower()}.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{out}/divergence-{sym.lower()}.png')"
        f".then(i=>console.log('out/divergence-{sym.lower()}.png',i.width+'x'+i.height));"],
        check=True)


if __name__ == "__main__":
    main()
