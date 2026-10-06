#!/usr/bin/env python3
"""What happened after the last post: this run against an earlier snapshot.

The cohort's first appearance is rarely the interesting part. Whether the move
held is, and that question can only be answered against a reading taken at the
time, because market caps and crowd counts are point-in-time and the API will
not hand them back later.

Compares the two most recent files in out/history/ unless told otherwise.

Usage:
    python3 followup.py
    python3 followup.py --from 2026-10-02 --to 2026-10-06
"""

import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIST = HERE / "out" / "history"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
BG, TEXT, SUB, TRACK = "#0d1117", "#e6edf3", "#8b949e", "#21262d"
RED, GREEN, GREY = "#f85149", "#3fb950", "#30363d"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
W, H = 1200, 760


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start"):
    """librsvg drops word spaces at bold weights, so set them by hand."""
    body = esc(s)
    if weight >= 700 and " " in str(s):
        w = str(s).split(" ")
        body = esc(w[0]) + "".join(
            f'<tspan dx="{size*(0.45 if p.endswith("%") else 0.30):.0f}">{esc(n)}</tspan>'
            for p, n in zip(w, w[1:]))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{body}</text>')


def load(stamp: str | None, which: int) -> dict:
    files = sorted(HIST.glob("metaverse-*.json"))
    if not files:
        raise SystemExit("No snapshots in out/history/. Run metaverse.py first.")
    if stamp:
        hit = HIST / f"metaverse-{stamp}.json"
        if not hit.exists():
            raise SystemExit(f"No snapshot for {stamp}. Have: "
                             + ", ".join(f.stem[-10:] for f in files))
        return json.loads(hit.read_text())
    if len(files) < 2:
        raise SystemExit("Only one snapshot so far; nothing to compare against yet.")
    return json.loads(files[which].read_text())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    a = ap.parse_args()

    old, new = load(a.frm, -2), load(a.to, -1)
    o = {c["symbol"]: c for c in old["coins"]}
    n = {c["symbol"]: c for c in new["coins"]}
    moves = sorted(((s, n[s]["mcap"] / o[s]["mcap"] - 1)
                    for s in o if s in n and o[s].get("mcap")), key=lambda kv: -kv[1])
    med = sorted(c for _, c in moves)[len(moves) // 2] if moves else 0

    b = [txt(60, 62, 38, TEXT, f"Four days after the metaverse bags woke up", 700),
         txt(60, 96, 21, SUB, f"{new['n']} coins that peaked in 2021 and sit "
                              f"{abs(1-new['mcapNow']/new['mcapPeak'])*100:.0f}% below it")]
    pairs = [("beating the market", old["beat"], new["beat"], RED),
             ("crowd still growing", old["crowdGrew"], new["crowdGrew"], GREEN)]
    for i, (label, x, y, col) in enumerate(pairs):
        cx = 90 + i * 560
        b.append(txt(cx, 190, 26, TEXT, label, 700))
        for j, (when, val) in enumerate(((old["asOf"][5:], x), ("today", y))):
            bx = cx + j * 200
            h = 300 * val / max(new["n"], 1)
            b.append(f'<rect x="{bx}" y="{560-h:.0f}" width="140" height="{h:.0f}" rx="5" '
                     f'fill="{col if j else GREY}"/>')
            b.append(txt(bx + 70, 560 - h - 18, 44, col if j else SUB, str(val), 700, "middle"))
            b.append(txt(bx + 70, 592, 22, SUB, when, 400, "middle"))
        b.append(txt(cx, 626, 20, SUB, f"out of {new['n']}"))

    b.append(f'<rect x="60" y="664" width="1080" height="1.5" fill="{TRACK}"/>')
    b.append(txt(60, 704, 24, TEXT, "The price trade faded. The crowd did not.", 700))
    b.append(txt(60, 736, 19, SUB, f"Median coin is down {abs(med)*100:.1f}% since "
                                   f"{old['asOf'][5:]}, and {new['crowdGrew']} of {new['n']} "
                                   f"still have a growing crowd."))
    b.append(txt(1140, 736, 17, SUB, "Data: LunarCrush", 400, "end"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>'
           + "".join(b) + "</svg>")
    (HERE / "out" / "followup.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/followup.svg',{{density:144}})"
        f".resize({W*2},{H*2}).png().toFile('{HERE}/out/followup.png')"
        f".then(i=>console.log('out/followup.png',i.width+'x'+i.height));"], check=True)
    print(f"  {old['asOf']} -> {new['asOf']}: beat {old['beat']}->{new['beat']}, "
          f"crowd grew {old['crowdGrew']}->{new['crowdGrew']}, median {med:+.1%}")


if __name__ == "__main__":
    main()
