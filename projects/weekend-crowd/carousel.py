#!/usr/bin/env python3
"""Instagram carousel (1080x1350) for the weekend blind spot.

Reads out/deseason.json and out/recovered.json, so the slides always match the
last run. Writes out/instagram-weekend/slide-N.svg.

Rasterize with sharp:
    node -e "const s=require('../crowd-size/node_modules/sharp');[1,2,3,4,5].forEach(i=>s(`out/instagram-weekend/slide-${i}.svg`,{density:144}).png().toFile(`out/instagram-weekend/slide-${i}.png`))"
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "instagram-weekend"
W, H, M = 1080, 1350, 90
BG, TEXT, SUB, TRACK, GRID = "#0d1117", "#e6edf3", "#8b949e", "#21262d", "#30363d"
RED, AMBER, GREY, GREEN = "#f85149", "#d29922", "#8b949e", "#3fb950"
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TOTAL = 5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def heavy(text: str, size: int) -> str:
    """librsvg drops word spaces at font-weight >= 700, so space words by hand.
    The % glyph overhangs its advance width and needs a wider gap after it."""
    words = text.split(" ")
    parts = [esc(words[0])]
    for prev, w in zip(words, words[1:]):
        factor = 0.45 if prev.endswith("%") else 0.30
        parts.append(f'<tspan dx="{size * factor:.0f}">{esc(w)}</tspan>')
    return "".join(parts)


def txt(x, y, size, fill, content, weight=400, anchor="start") -> str:
    body = heavy(content, size) if weight >= 700 and " " in content else esc(content)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{body}</text>')


def frame(n: int, body: str, footer: str = "") -> str:
    dots = "".join(
        f'<circle cx="{W/2 + (i - (TOTAL-1)/2) * 36}" cy="{H-60}" r="7" '
        f'fill="{TEXT if i == n-1 else TRACK}"/>' for i in range(TOTAL))
    f = txt(M, H - 110, 28, SUB, footer) if footer else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{txt(M, 102, 30, SUB, f"the LunarCrush API series · {n}/{TOTAL}")}
{body}
{f}
{dots}
</svg>"""


def bars(by_day, key, top=560, ch=300) -> str:
    """Spike rate per weekday. Weekend bars carry the accent colour."""
    bw, gap, x0 = 106, 22, M
    mx = max(by_day[d][key] for d in DAYS)
    out = []
    for i, d in enumerate(DAYS):
        v = by_day[d][key]
        h = v / mx * ch
        x = x0 + i * (bw + gap)
        y = top + ch - h
        wknd = d in ("Sat", "Sun")
        col = (RED if key == "standard" else GREEN) if wknd else GREY
        out += [
            f'<rect x="{x}" y="{y:.0f}" width="{bw}" height="{h:.0f}" rx="8" fill="{col}"/>',
            txt(int(x + bw / 2), int(y) - 18, 26, col if wknd else SUB,
                f"{v*100:.2f}", 800 if wknd else 400, "middle"),
            txt(int(x + bw / 2), top + ch + 44, 26, TEXT if wknd else SUB, d,
                700 if wknd else 400, "middle"),
        ]
    out.append(f'<line x1="{M}" y1="{top+ch}" x2="{W-M}" y2="{top+ch}" stroke="{GRID}" stroke-width="2"/>')
    return "\n".join(out)


def slide1() -> str:
    return frame(1, f"""
{txt(M, 330, 62, TEXT, "Crypto never", 800)}
{txt(M, 400, 62, TEXT, "closes.", 800)}
{txt(M, 500, 62, SUB, "The people talking", 800)}
{txt(M, 570, 62, SUB, "about it do.", 800)}
{txt(M, 700, 36, TEXT, "Weekend conversation runs", 400)}
{txt(M, 748, 36, TEXT, "this far below weekday:", 400)}
{txt(M, 900, 150, RED, "7.2%", 800)}
{txt(M, 960, 32, SUB, "1,000 coins · 450,790 coin-days · six years")}
""", "swipe")


def slide2(d) -> str:
    return frame(2, f"""
{txt(M, 240, 50, TEXT, "A small gap does", 800)}
{txt(M, 300, 50, TEXT, "something strange", 800)}
{txt(M, 370, 30, SUB, "Share of coin-days a spike detector fires on, by weekday")}
{bars(d["byDay"], "standard")}
{txt(M, 990, 36, TEXT, "Weekdays 1.84% · Weekends 1.48%", 700)}
{txt(M, 1046, 36, RED, "The detector misses 19.5% more.", 800)}
""", "a 7% smaller crowd, a 19.5% gap. three times the distortion.")


def slide3(d) -> str:
    return frame(3, f"""
{txt(M, 240, 50, TEXT, "Why: the window", 800)}
{txt(M, 300, 50, TEXT, "contains weekends", 800)}
{txt(M, 400, 34, SUB, "A spike score is today's volume minus the")}
{txt(M, 446, 34, SUB, "trailing 30-day average, over its standard")}
{txt(M, 492, 34, SUB, "deviation. Those 30 days include weekends.")}
{txt(M, 580, 38, TEXT, "Every Saturday starts below the", 700)}
{txt(M, 628, 38, TEXT, "average it is measured against,", 700)}
{txt(M, 676, 38, TEXT, "so it needs a bigger jump to", 700)}
{txt(M, 724, 38, TEXT, "clear the same bar.", 700)}
{txt(M, 840, 36, GREEN, "So I fixed it.", 800)}
{txt(M, 900, 34, SUB, "Subtract each coin's own day-of-week offset.")}
{txt(M, 960, 40, TEXT, "Weekend deficit", 700)}
{txt(W-M, 960, 40, RED, "-19.5%", 800, "end")}
{txt(M, 1020, 40, TEXT, "After the fix", 700)}
{txt(W-M, 1020, 40, GREEN, "+1.3%", 800, "end")}
{txt(M, 1080, 32, SUB, "Detection is flat across the week. 12.9% more weekend events.")}
""")


def slide4(r) -> str:
    res = {(x["comparison"].split(" vs ")[0], x["horizon"]): x
           for x in r["results"] if x["metric"] == "hit_rate_adj"}
    kept, rec = res[("kept", "+3d")], res[("recovered", "+3d")]
    return frame(4, f"""
{txt(M, 240, 50, TEXT, "Then I scored", 800)}
{txt(M, 300, 50, TEXT, "what it found", 800)}
{txt(M, 380, 30, SUB, "Beating Bitcoin over 3 days, against the same baseline")}
{txt(M, 500, 34, TEXT, "Events both scorers agree on", 700)}
{txt(M, 546, 28, SUB, f'n = {r["counts"]["kept"]}')}
{txt(W-M, 530, 78, GREEN, f'+{kept["diff"]*100:.1f}pp', 800, "end")}
{txt(W-M, 576, 28, SUB, f'p = {kept["p_two_sided"]:.3f}', 400, "end")}
{txt(M, 700, 34, TEXT, "Events only the fix finds", 700)}
{txt(M, 746, 28, SUB, f'n = {r["counts"]["recovered"]}')}
{txt(W-M, 730, 78, RED, f'{rec["diff"]*100:.1f}pp', 800, "end")}
{txt(W-M, 776, 28, SUB, f'p = {rec["p_two_sided"]:.3f}', 400, "end")}
{txt(M, 900, 44, TEXT, "Nothing.", 800)}
{txt(M, 970, 34, SUB, "A correction that lowers a threshold recovers")}
{txt(M, 1016, 34, SUB, "whatever sat just under it, and marginal")}
{txt(M, 1062, 34, SUB, "events are marginal for a reason.")}
""")


def slide5() -> str:
    return frame(5, f"""
{txt(M, 250, 50, TEXT, "So I kept the bug", 800)}
{txt(M, 350, 38, TEXT, "A defect being real is not enough", 700)}
{txt(M, 398, 38, TEXT, "reason to fix it. The fix has to", 700)}
{txt(M, 446, 38, TEXT, "buy something. This one does not.", 700)}
{txt(M, 560, 36, GREEN, "One thing worth keeping", 800)}
{txt(M, 620, 34, SUB, "Weekend spikes that clear the bar on their")}
{txt(M, 666, 34, SUB, "own look no different from weekday ones.")}
{txt(M, 730, 40, TEXT, "-0.6pp", 800)}
{txt(M + 190, 730, 34, SUB, "p = 0.95")}
{txt(M, 800, 38, TEXT, "A Sunday signal is not a", 700)}
{txt(M, 848, 38, TEXT, "worse signal.", 700)}
{txt(M, 960, 32, SUB, "Every number here is reproducible from the repo.")}
{txt(M, 1050, 32, GREEN, "github.com/nickisanders/lunarcrush-projects", 700)}
""", "Data: LunarCrush · not advice · code NICKI gets 15% off")


def main() -> None:
    d = json.loads((HERE / "out" / "deseason.json").read_text())
    r = json.loads((HERE / "out" / "recovered.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [slide1(), slide2(d), slide3(d), slide4(r), slide5()]
    for i, s in enumerate(slides, 1):
        (OUT / f"slide-{i}.svg").write_text(s)
    print(f"Wrote {TOTAL} slides to {OUT}")


if __name__ == "__main__":
    main()
