#!/usr/bin/env python3
"""Every finding in the repo, graded: what held, what died, where the data lies.

The point of the chart is the two categories nobody publishes. Ten findings
survived, eight were tested and came back empty, and seven are places where
the data hands you a confident wrong answer. Grouping them together and
sizing the bar by how many are in each is the whole argument: the empty
results and the traps outnumber the findings two to one, and a portfolio that
showed only the top group would be a record of its own luck.

The three counts and the project total are read from tools/out/scoreboard.json,
so they cannot drift from what the script last recorded. The finding text in
that file is transcribed by hand from each project, which is noted in the
footer rather than left for a reader to assume otherwise.

Run tools/scoreboard.py first to refresh the JSON.

Usage: python3 tools/scoreboard_chart.py
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "out" / "scoreboard.json"
SHARP = ROOT / "projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"

W = 1240
L, R = 60, 1180
TAG = 224                      # project-name column
X0 = L + TAG                   # finding text starts here
TEXTW = R - X0
LINE = 26


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None, op=1.0):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="{op}" '
            f'font-family="{font or FONT}">{esc(s)}</text>')


def wrap(s, px, size, em=0.455):
    """Wrap to a pixel width rather than a character count.

    The findings run from eight words to forty and mix prose with figures
    like "p = 0.003", so a single character limit either wasted a third of
    the column or pushed the longest lines past the margin.
    """
    per = size * em
    out, line = [], ""
    for word in s.split():
        trial = f"{line} {word}".strip()
        if len(trial) * per > px and line:
            out.append(line)
            line = word
        else:
            line = trial
    if line:
        out.append(line)
    return out


def render(name, w, h, body, scale=2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{GROUND}"/>'
           f'{body}</svg>')
    out = ROOT / "tools" / "out"
    out.mkdir(exist_ok=True)
    (out / f"{name}.svg").write_text(svg)
    subprocess.run(["node", "-e",
        f"const s=require('{SHARP}');s('{out}/{name}.svg',{{density:144}})"
        f".resize({w*scale},{h*scale}).png().toFile('{out}/{name}.png')"
        f".then(i=>console.log('  {name}.png',i.width+'x'+i.height));"], check=True)


doc = json.loads(SRC.read_text())
counts = doc["counts"]
total = sum(counts.values())
GROUPS = (("works", "HOLDS UP", BRAND, 1.0),
          ("null", "TESTED, CAME BACK EMPTY", SUB, 1.0),
          ("caution", "THE DATA WILL LIE TO YOU HERE", HOT, 1.0))

b = [txt(L, 58, 37, INK,
         f"{total} findings from {doc['projects']} studies on one crypto API.", 700),
     txt(L, 98, 37, INK, "Ten of them survived.", 700),
     txt(L, 140, 20, SUB,
         "Eight were tested and came back with nothing. Seven are places where "
         "the data hands you a confident wrong answer."),
     txt(L, 166, 20, SUB,
         "The bar is sized by how many findings are in each group, which is the "
         "part worth looking at.")]

# One bar across the top, because the ratio is the argument and a reader who
# goes no further than the first six inches should still leave with it.
y = 206
BH = 54
x = L
for key, label, col, op in GROUPS:
    seg = (R - L) * counts[key] / total
    b.append(f'<rect x="{x:.1f}" y="{y}" width="{seg:.1f}" height="{BH}" '
             f'fill="{col}" fill-opacity="{op}"/>')
    b.append(txt(x + seg / 2, y + BH / 2 + 8, 22, "#ffffff",
                 f"{counts[key]}", 700, "middle", MONO))
    x += seg
y += BH + 8
x = L
for key, label, col, op in GROUPS:
    seg = (R - L) * counts[key] / total
    b.append(txt(x, y + 14, 17, col, label, 700, "start", MONO))
    x += seg
y += 76

for key, label, col, op in GROUPS:
    items = [f for f in doc["findings"] if f["verdict"] == key]
    b.append(f'<line x1="{L}" y1="{y-26}" x2="{R}" y2="{y-26}" '
             f'stroke="{RULE}" stroke-width="2"/>')
    b.append(txt(L, y, 23, col, f"{label}  ({len(items)})", 700))
    y += 34
    for f in items:
        lines = wrap(f["text"], TEXTW, 19)
        # The marker is a rule down the whole entry rather than a bullet, so a
        # finding that runs to three lines still reads as one item.
        b.append(f'<rect x="{X0-20}" y="{y-14}" width="3" '
                 f'height="{len(lines)*LINE-6}" fill="{col}" fill-opacity="0.5"/>')
        b.append(txt(L, y, 15, SUB, f["project"], 400, "start", MONO))
        for ln in lines:
            b.append(txt(X0, y, 19, INK, ln))
            y += LINE
        y += 8
    y += 38

y -= 20
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="142" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="142" fill="{HOT}"/>')
b.append(txt(L + 26, y + 38, 23, INK,
             "Publishing only the top group is how a research portfolio becomes "
             "a record of its own luck.", 700))
b.append(txt(L + 26, y + 72, 20, SUB,
             "$ONE borrowed 5.0 billion interactions from the English word. The "
             "attention premium result was 30%"))
b.append(txt(L + 26, y + 98, 20, SUB,
             "stablecoins before it was anything. $LINK scored worst on a metric "
             "that measured which venue it trades on."))
b.append(txt(L + 26, y + 128, 20, SUB,
             "Each of those read as a finding first. None of them is in the top "
             "group now."))
y += 182

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
missing = doc["projects"] - len({f["project"] for f in doc["findings"]})
b.append(txt(L, y + 32, 19, SUB,
             f"{missing} of the {doc['projects']} projects have no headline "
             f"recorded here, the holder-count work among them."))
b.append(txt(L, y + 58, 19, SUB,
             "Counts are computed from the repo. The finding text is "
             "transcribed by hand, so a project's own output is the authority."))
b.append(txt(R, y + 84, 19, SUB,
             "github.com/nickisanders/lunarcrush-projects  ·  @nickisanders",
             400, "end"))
H = y + 112

render("scoreboard", W, H, "".join(b))
for key, label, _, _ in GROUPS:
    print(f"  {label:<32}{counts[key]:>3}")
print(f"  {'projects':<32}{doc['projects']:>3}   no headline: {missing}")
