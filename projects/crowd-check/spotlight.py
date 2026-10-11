#!/usr/bin/env python3
"""Chart one coin from the screen: did the crowd arrive with the price?

The table answers the question across ten coins. This answers it for one, which
is what a post needs. Three measures before and after, plus the spam share,
because the spam direction is what separates a crowd that showed up from a wave
that was bought: a purchased run has junk crowding in as the price goes, and the
share rises.

Last 7 days against the 30 before, from the coin's own daily series. The
partial current day is dropped; reading it understates everything.

Usage:
    LUNARCRUSH_API_KEY=... python3 spotlight.py STRK
"""

import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BASE = "https://lunarcrush.com/api4"
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
GREEN, GREY, RED = "#3fb950", "#6e7681", "#f85149"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, monospace"
W, H = 1200, 760


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
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font or FONT}">{body}</text>')


def avg(rows, key):
    v = [r.get(key) for r in rows if r.get(key) is not None]
    return sum(v) / len(v) if v else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("symbol")
    ap.add_argument("--name")
    a = ap.parse_args()
    sym = a.symbol.upper()

    rows = (get(f"/public/coins/{sym}/time-series/v2?bucket=day&interval=3m")
            .get("data") or [])[:-1]
    if len(rows) < 37:
        raise SystemExit(f"{sym}: only {len(rows)} complete days, need 37")
    last, prior = rows[-7:], rows[-37:-7]
    coins = get("/public/coins/list/v2?limit=1000")["data"]
    coin = next((c for c in coins if str(c.get("symbol")).upper() == sym), {})
    name = a.name or coin.get("name") or sym
    pct = float(coin.get("percent_change_7d") or 0)

    metrics = [("people posting, per day", "contributors_active"),
               ("posts, per day", "posts_created"),
               ("interactions, per day", "interactions")]
    data = [(label, avg(prior, k), avg(last, k)) for label, k in metrics]
    s_before = avg(prior, "spam") / max(avg(prior, "posts_created"), 1)
    s_after = avg(last, "spam") / max(avg(last, "posts_created"), 1)

    b = [txt(60, 60, 36, TEXT,
             f"{name} is up {pct:.0f}% and the crowd came with it", 700),
         txt(60, 94, 20, SUB,
             f"${sym}, the last 7 days against the 30 days before")]

    TOP, ROW, X0, BARW = 150, 150, 330, 560
    for i, (label, before, after) in enumerate(data):
        y = TOP + i * ROW
        peak = max(before, after) or 1
        b.append(txt(X0 - 22, y + 36, 21, TEXT, label, 700, "end"))
        for j, (tag, val, col) in enumerate((("before", before, GREY),
                                             ("now", after, GREEN))):
            by = y + j * 42
            w = BARW * (val / peak)
            b.append(txt(X0 - 22, by + 20, 17, SUB, tag, 400, "end"))
            b.append(f'<rect x="{X0}" y="{by}" width="{max(w,4):.0f}" height="30" '
                     f'rx="4" fill="{col}"/>')
            shown = f"{val:,.0f}" if val < 10_000 else f"{val/1000:,.0f}k"
            b.append(txt(X0 + max(w, 4) + 14, by + 22, 22, TEXT, shown, 700, "start", MONO))

    y = TOP + len(data) * ROW - 10
    b.append(f'<rect x="60" y="{y}" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, y + 44, 24, TEXT,
                 f"Spam fell as a share of posts while that happened, "
                 f"{s_before*100:.0f}% to {s_after*100:.0f}%.", 700))
    b.append(txt(60, y + 78, 20, SUB,
                 "A bought wave runs the other way, with junk crowding in as the price goes."))
    b.append(txt(60, H - 20, 16, SUB, "Source: LunarCrush"))
    b.append(txt(1140, H - 20, 16, SUB,
                 "github.com/nickisanders/lunarcrush-projects", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / f"spotlight-{sym.lower()}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{out}/spotlight-{sym.lower()}.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{out}/spotlight-{sym.lower()}.png')"
        f".then(i=>console.log('out/spotlight-{sym.lower()}.png',i.width+'x'+i.height));"],
        check=True)


if __name__ == "__main__":
    main()
