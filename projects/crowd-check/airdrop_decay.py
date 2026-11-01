#!/usr/bin/env python3
"""How long ago an airdrop happened barely predicts how much of it stayed.

Each dot is a token's largest single month of arrivals, placed by how long
ago that month was and by how much of that cohort still holds. The expected
shape is a decay curve, with old drops near the floor and recent ones near
the top. The data does not have one: the correlation between cohort age and
retention is weak, and it survives dropping any single token, so the weakness
is the finding rather than an artifact of one outlier.

The two oldest cohorts here are also among the better retained, and two
cohorts of the same age sit at opposite ends of the axis. Something decides
this and it is not the calendar.

Reads out/retention-baseline.json from proof-of-crowd-tools.

Usage: python3 airdrop_decay.py
"""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "retention-baseline.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
MIN_COHORT = 500
# Named on the chart: the big ones people recognize, and the pair that makes
# the point by sitting at opposite ends of the same age.
LABEL = {"ens", "ape", "blur", "drv", "soso", "edge", "ath", "plume", "fet"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>'
           f'{body}</svg>')
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{HERE}/out/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{HERE}/out/{name}.png')"
        f".then(i=>console.log('  {name}.png',i.width+'x'+i.height));"], check=True)


doc = json.loads(SRC.read_text())
rows = []
for sym, d in doc["tokens"].items():
    b = d.get("biggest_cohort") or {}
    if b.get("arrived", 0) < MIN_COHORT:
        continue
    rows.append({"sym": sym.upper(), "key": sym, "age": b["age_months"],
                 "ret": b["retention"], "n": b["arrived"]})
if len(rows) < 10:
    raise SystemExit(f"  only {len(rows)} cohorts above {MIN_COHORT}")


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return cov / den if den else 0.0


xs = [r["age"] for r in rows]
ys = [r["ret"] for r in rows]
r0 = corr(xs, ys)
# The standing check in this repo: every correlation here has been moved by
# one token at least once, so the range without any single one is reported
# beside the figure rather than after someone asks.
jack = [corr(xs[:i] + xs[i + 1:], ys[:i] + ys[i + 1:]) for i in range(len(rows))]

W, H_PLOT = 1240, 620
L, R = 60, 1180
PLOT_L, PLOT_R = L + 64, R - 20
PLOT_T = 226
PLOT_B = PLOT_T + H_PLOT
XMAX = max(xs) + 4
rmax = max(r["n"] for r in rows)


def px(age):
    return PLOT_L + (PLOT_R - PLOT_L) * age / XMAX


def py(ret):
    return PLOT_B - (PLOT_B - PLOT_T) * ret


b = [txt(L, 58, 37, INK, "How long ago an airdrop happened", 700),
     txt(L, 98, 37, INK, "barely predicts how much of it stayed.", 700),
     txt(L, 138, 20, SUB,
         "Each dot is a token's biggest month of arrivals, placed by how long "
         "ago it was and how much of that group still holds."),
     txt(L, 164, 20, SUB,
         f"{len(rows)} cohorts of at least {MIN_COHORT:,} wallets. Dot size is "
         f"the size of the cohort.")]

for frac in (0, 0.25, 0.5, 0.75, 1.0):
    yy = py(frac)
    b.append(f'<line x1="{PLOT_L}" y1="{yy:.0f}" x2="{PLOT_R}" y2="{yy:.0f}" '
             f'stroke="{RULE}" stroke-width="1" opacity="0.7"/>')
    b.append(txt(PLOT_L - 14, yy + 6, 17, SUB, f"{frac*100:.0f}%", 400, "end", MONO))
for age in range(0, int(XMAX) + 1, 12):
    xx = px(age)
    b.append(f'<line x1="{xx:.0f}" y1="{PLOT_B}" x2="{xx:.0f}" y2="{PLOT_B+6}" '
             f'stroke="{RULE}" stroke-width="2"/>')
    b.append(txt(xx, PLOT_B + 28, 17, SUB, f"{age}", 400, "middle", MONO))
b.append(txt((PLOT_L + PLOT_R) / 2, PLOT_B + 58, 19, SUB,
             "months since the cohort arrived", 400, "middle"))
b.append(txt(PLOT_L - 14, PLOT_T - 16, 17, SUB, "still holding", 400, "end"))

for r in sorted(rows, key=lambda r: -r["n"]):
    x, yy = px(r["age"]), py(r["ret"])
    rad = 6 + 16 * (r["n"] / rmax) ** 0.5
    hot = r["key"] in ("ens", "edge")
    b.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{rad:.1f}" '
             f'fill="{HOT if hot else BRAND}" fill-opacity="{0.8 if hot else 0.42}" '
             f'stroke="{HOT if hot else BRAND}" stroke-width="1.5"/>')
placed = []
for r in rows:
    if r["key"] not in LABEL:
        continue
    x, yy = px(r["age"]), py(r["ret"])
    rad = 6 + 16 * (r["n"] / rmax) ** 0.5
    ly = yy - rad - 9
    if any(abs(x - ox) < 76 and abs(ly - oy) < 22 for ox, oy in placed):
        ly = yy + rad + 22              # flip below the dot instead
    placed.append((x, ly))
    b.append(txt(x, ly, 17, INK, "$" + r["sym"], 700, "middle", MONO))

y = PLOT_B + 92
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="142" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="142" fill="{HOT}"/>')
ens = next(r for r in rows if r["key"] == "ens")
edge = next(r for r in rows if r["key"] == "edge")
b.append(txt(L + 26, y + 36, 23, INK,
             f"${ens['sym']} dropped {ens['n']:,} wallets {ens['age']} months "
             f"ago and kept {ens['ret']*100:.1f}%.", 700))
b.append(txt(L + 26, y + 66, 23, INK,
             f"${edge['sym']} dropped {edge['n']:,} wallets {edge['age']} months "
             f"ago and kept {edge['ret']*100:.1f}%.", 700))
b.append(txt(L + 26, y + 98, 20, SUB,
             f"Correlation between age and retention is {r0:+.2f}, and stays "
             f"between {min(jack):+.2f} and {max(jack):+.2f} with any single "
             f"token removed."))
b.append(txt(L + 26, y + 124, 20, SUB,
             "The weakness is the result. Age is not what decides this."))
y += 182

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Cohorts are read from Transfer logs, not from a dashboard: the "
             "month a token saw the most first-time recipients."))
b.append(txt(L, y + 58, 19, SUB,
             "Cohort size, concentration of arrival, token age and the share "
             "of holders who cannot pay gas were all tested. None reached 0.34."))
b.append(txt(R, y + 84, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 112

render("airdrop_decay", W, H, "".join(b))
print(f"  {len(rows)} cohorts, r={r0:+.3f}, jackknife [{min(jack):+.3f},{max(jack):+.3f}]")
