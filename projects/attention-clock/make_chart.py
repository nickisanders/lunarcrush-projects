#!/usr/bin/env python3
"""Radial clock of crypto's posting rhythm, from out/report.json.

Radial because the message is the SHAPE: a lit side and a dark side. The
exact magnitudes are labelled for the two hours that carry the argument.

Writes out/clock.svg. Rasterize with sharp:
    node -e "require('../hype-detector/node_modules/sharp')('out/clock.svg',{density:144}).png().toFile('out/clock.png')"
"""

import json
from math import cos, pi, sin
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 1200, 1420
CX, CY = 600, 660
R0, R1 = 155, 410
BG, TEXT, SUB, GRID = "#0d1117", "#e6edf3", "#8b949e", "#30363d"
NIGHT, DAY = (31, 111, 235), (247, 147, 26)  # blue -> orange
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def lerp(a: tuple, b: tuple, t: float) -> str:
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def polar(hour: float, r: float) -> tuple[float, float]:
    """00:00 at the top, clockwise, so it reads like a clock face."""
    ang = hour / 24 * 2 * pi - pi / 2
    return CX + r * cos(ang), CY + r * sin(ang)


def main() -> None:
    s = json.loads((HERE / "out" / "report.json").read_text())
    hours = s["hours"]
    lo, hi = min(hours), max(hours)
    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<text x="60" y="78" font-size="40" font-weight="700" fill="{TEXT}">Crypto sleeps</text>',
        f'<text x="60" y="124" font-size="24" fill="{SUB}">posts created per hour of the day, {s["coins"]} coins over $1B, last 30 days</text>',
        f'<text x="60" y="160" font-size="24" fill="{SUB}">each spoke is one UTC hour. 1.0 would be a perfectly even day.</text>',
    ]

    # Reference ring at 1.0 so the eye has a baseline for "average hour".
    r_avg = R0 + (1.0 - lo) / (hi - lo) * (R1 - R0)
    p.append(f'<circle cx="{CX}" cy="{CY}" r="{r_avg:.0f}" fill="none" stroke="{GRID}" '
             f'stroke-width="2" stroke-dasharray="5 7"/>')

    for h, v in enumerate(hours):
        t = (v - lo) / (hi - lo)
        r = R0 + t * (R1 - R0)
        x0, y0 = polar(h + 0.5, R0)
        x1, y1 = polar(h + 0.5, r)
        p.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                 f'stroke="{lerp(NIGHT, DAY, t)}" stroke-width="26" stroke-linecap="round"/>')

    for h in range(0, 24, 3):
        x, y = polar(h, R1 + 52)
        p.append(f'<text x="{x:.0f}" y="{y + 9:.0f}" font-size="25" fill="{SUB}" '
                 f'text-anchor="middle">{h:02d}</text>')

    p += [
        f'<text x="{CX}" y="{CY - 34}" font-size="88" font-weight="800" fill="{TEXT}" text-anchor="middle">{s["ratio"]:.1f}x</text>',
        f'<text x="{CX}" y="{CY + 12}" font-size="25" fill="{SUB}" text-anchor="middle">busiest hour vs</text>',
        f'<text x="{CX}" y="{CY + 46}" font-size="25" fill="{SUB}" text-anchor="middle">quietest hour</text>',
    ]

    # Callouts on the two hours the argument rests on. Anchor away from the
    # dial rather than at a fixed side, so the text never lies back over it.
    for hour, value, label, color in [
        (s["loudestHour"], s["loudest"], "busiest", "#f7931a"),
        (s["quietestHour"], s["quietest"], "quietest", "#58a6ff"),
    ]:
        x, y = polar(hour + 0.5, R1 + 78)
        # Centre the callout on its spoke, then clamp inside the canvas: the
        # peak and trough can land at any angle as the data changes, and a
        # callout that runs off the edge is worse than one nudged inward.
        x = min(max(x, 170), W - 170)
        p += [
            f'<text x="{x:.0f}" y="{y:.0f}" font-size="30" font-weight="700" fill="{color}" '
            f'text-anchor="middle">{hour:02d}:00 UTC</text>',
            f'<text x="{x:.0f}" y="{y + 34:.0f}" font-size="24" fill="{SUB}" '
            f'text-anchor="middle">{label} · {value:.2f}x</text>',
        ]

    p += [
        f'<text x="60" y="{H - 118}" font-size="23" fill="{TEXT}">The market runs 24/7. The people posting about it keep office hours, and they are Western office hours:</text>',
        f'<text x="60" y="{H - 86}" font-size="23" fill="{TEXT}">the quietest hour of the crypto day is lunchtime in Tokyo.</text>',
        f'<text x="60" y="{H - 50}" font-size="21" fill="{SUB}">{s["peakInAfternoon"]} of {s["coins"]} coins peak between 11:00 and 17:00 UTC. Median correlation between any two coins\' clocks: {s["medianPairwiseCorr"]:.2f}.</text>',
        f'<text x="60" y="{H - 20}" font-size="19" fill="{SUB}">Data: LunarCrush · median posts per clock hour · method and code in the repo</text>',
        "</svg>",
    ]
    (HERE / "out" / "clock.svg").write_text("\n".join(p))
    print(f"Wrote out/clock.svg  ({s['ratio']:.2f}x, peak {s['loudestHour']:02d}:00, trough {s['quietestHour']:02d}:00)")


if __name__ == "__main__":
    main()
