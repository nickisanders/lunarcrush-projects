#!/usr/bin/env python3
"""A bigger allocation costs a share of the odds, not a number of points.

Both panels are the same 50 tokens against the same x-axis: how often the
smallest tenth of a token's recipients still holds what it was given, which
is where that token's ladder starts.

Left is the fall in points per tenfold rise in the allocation. It tracks the
starting level at r = -0.81, and it has to: a token whose smallest group
sits at 5% cannot lose ten points, and one starting at 60% has room to lose
forty. Most of what looks like one token decaying faster than another is the
height it began at.

Right is the same fit in proportions, the share of its chances a wallet
loses per tenfold rather than the points. Against the same starting level it
reads r = +0.02, with a jackknife that sits on zero. Dividing the fall by
the level leaves something that does not know what the level was, and that
is the version of the rule worth carrying between tokens.

Groups at zero cannot be logged and are dropped rather than floored, because
any floor chosen here would set the slope of the tokens that most need one.
A token with fewer than seven groups left is not fitted.

Reads out/receipt-deciles.json.

Usage: python3 allocation_proportion.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path.home() / "proof-of-crowd-tools" / "out"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"

W = 1240
L, R = 60, 1180


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Per-character widths read back off a render: Charter sets at about 0.415 of
# its point size and 0.53 bold. A line that will not fit says so at render
# time instead of being drawn clipped.
def fits(x, size, s, weight=400):
    width = len(str(s)) * size * (0.53 if weight >= 700 else 0.415)
    if width > R - x:
        over = int((width - (R - x)) / (size * 0.415))
        print(f"  WARNING: {size}px line runs ~{over} characters past the "
              f"margin: {str(s)[:60]}...", flush=True)


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None):
    if anchor == "start" and font is None:
        fits(x, size, s, weight)
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


doc = json.loads((ROOT / "receipt-deciles.json").read_text())
st = doc["rate"]["elasticity"]
rows = [r for r in doc["per_token"] if r["elasticity_kept"] is not None]
if len(rows) < 20:
    raise SystemExit(f"  only {len(rows)} tokens carry a proportional fit; "
                     f"the chart compares two fits across a field")
mult = st["median_multiplier"]
q = st["quartiles"]

# Named by rule: the two ends of the x-axis, which are the tokens the left
# panel is most and least able to flatter.
hi_lvl = max(rows, key=lambda r: r["level_kept"])
lo_lvl = min(rows, key=lambda r: r["level_kept"])
NAMED = {hi_lvl["sym"], lo_lvl["sym"]}

PW, PH, PGAP = 486, 470, 118
PX1, PX2 = L + 54, L + 54 + PW + PGAP
TOP = 314
xs = [r["level_kept"] for r in rows]
xlo, xhi = 0.0, max(xs) * 1.05
ylo1 = min(r["rate_kept"] for r in rows)
yhi1 = max(0.0, max(r["rate_kept"] for r in rows))
ylo2 = min(r["elasticity_kept"] for r in rows)
yhi2 = max(0.0, max(r["elasticity_kept"] for r in rows))

b = [txt(L, 58, 37, INK, "A bigger allocation costs a share of the odds,", 700),
     txt(L, 98, 37, INK, "not a number of points.", 700),
     txt(L, 138, 20, SUB,
         f"Both panels are the same {len(rows)} tokens against the same "
         f"x-axis: how often the smallest tenth of a token's recipients "
         f"still holds"),
     txt(L, 164, 20, SUB,
         "what it was given, which is where that token's ladder starts. "
         "Left: the fall in points for each tenfold rise in the allocation."),
     txt(L, 190, 20, SUB,
         "Right: the same fit in proportions, the share of its chances a "
         "wallet loses per tenfold rather than the points.")]


def panel(px, ylo, yhi, key, title, rcorr, jk, unit):
    out = [txt(px, TOP - 46, 19, INK, title, 700)]

    def gy(v):
        return TOP + PH * (yhi - v) / (yhi - ylo)

    def gx(v):
        return px + PW * (v - xlo) / (xhi - xlo)

    for i in range(5):
        v = ylo + (yhi - ylo) * i / 4
        y = gy(v)
        out.append(f'<line x1="{px}" y1="{y:.0f}" x2="{px+PW}" y2="{y:.0f}" '
                   f'stroke="{RULE}" stroke-width="1"/>')
        out.append(txt(px - 10, y + 6, 15, SUB, unit(v), 400, "end"))
    for r in rows:
        named = r["sym"] in NAMED
        cx, cy = gx(r["level_kept"]), gy(r[key])
        out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" '
                   f'r="{7 if named else 5}" '
                   f'fill="{HOT if named else BRAND}" '
                   f'opacity="{1 if named else 0.5}"/>')
        if named:
            half = len(r["sym"]) * 5 + 6
            lx = min(max(cx, px + half), px + PW - half)
            out.append(txt(lx, max(cy - 13, TOP + 14), 15, HOT,
                           "$" + r["sym"], 700, "middle", MONO))
    for i in range(4):
        v = xlo + (xhi - xlo) * i / 3
        out.append(txt(gx(v), TOP + PH + 26, 15, SUB, f"{v*100:.0f}%",
                       400, "middle"))
    out.append(txt(px, TOP + PH + 54, 17, SUB,
                   "where the token's ladder starts"))
    out.append(txt(px, TOP + PH + 80, 17, INK,
                   f"r = {rcorr:.2f}, jackknife {jk[0]:.2f} to {jk[1]:.2f}",
                   700))
    return out


b += panel(PX1, ylo1, yhi1, "rate_kept", "points lost per tenfold",
           st["level_vs_points"], st["level_vs_points_jackknife"],
           lambda v: f"{v:.0f}")
b += panel(PX2, ylo2, yhi2, "elasticity_kept", "proportion lost per tenfold",
           st["level_vs_elasticity"], st["level_vs_elasticity_jackknife"],
           lambda v: f"{(1-10**v)*-100:+.0f}%")

y = TOP + PH + 118
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"Every tenfold rise in the allocation takes "
             f"{(1-mult)*100:.1f}% of the chances the wallet already had.",
             700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Median across the {st['tokens']} tokens, and it falls on "
             f"{st['negative']} of them. Half the field sits between "
             f"{(1-10**q[2])*100:.0f}% and {(1-10**q[0])*100:.0f}%."))
b.append(txt(L + 26, y + 96, 20, SUB,
             f"The points version cannot travel. Against the level it "
             f"starts from it reads r = {st['level_vs_points']:.2f}, so most "
             f"of it is height rather than decay."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"The proportional version does not know the level: "
             f"r = {st['level_vs_elasticity']:.2f}, with a jackknife from "
             f"{st['level_vs_elasticity_jackknife'][0]:.2f} to "
             f"{st['level_vs_elasticity_jackknife'][1]:.2f}."))

y += 184
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             f"${hi_lvl['sym']} starts at "
             f"{hi_lvl['level_kept']*100:.1f}% and ${lo_lvl['sym']} at "
             f"{lo_lvl['level_kept']*100:.1f}%, which is the whole of the "
             f"left panel's range and none of the right panel's."))
b.append(txt(L, y + 58, 19, SUB,
             f"Groups at zero cannot be logged and are dropped rather than "
             f"floored, since any floor would set the slope of the tokens "
             f"that most need one."))
b.append(txt(L, y + 84, 19, SUB,
             f"A token with fewer than {st['min_live_groups']} groups left "
             f"is not fitted. Both fits are against the log of what the "
             f"wallet received, so neither is priced."))
b.append(txt(L, y + 110, 19, SUB,
             "Why a position shrank is not visible from the chain. Selling, "
             "trimming and forgetting are the same event from here."))
b.append(txt(R, y + 138, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))

H = y + 170
render("allocation_proportion", W, H, "".join(b))
print(f"  {len(rows)} tokens, x{mult:.3f} a tenfold "
      f"({(1-mult)*100:.1f}% off), level vs points "
      f"r={st['level_vs_points']:.2f}, vs proportion "
      f"r={st['level_vs_elasticity']:.2f}")
