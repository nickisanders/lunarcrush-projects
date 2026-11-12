#!/usr/bin/env python3
"""The ticker is the one field on a crypto chart nothing has to agree with.

Four tokens have been dropped from charts in this project for carrying a
symbol a reader would take for another asset, every one of them caught by
hand after it had already been rendered once. symbol_audit.py asks every
contract in the baseline what it calls itself, and this draws the answers
that do not match the label.

Two groups, and they are not the same kind of claim.

The top group is computed. A contract whose own name() contains wrapped,
bridged, staked, xStock or Ondo Tokenized is telling you it is a claim on
something that is not itself, and the string test is the whole rule. The
audit also found $ZANO trading in the baseline under a key the contract does
not use: its symbol is WZANO. That one is a label error in my own data rather
than anything the token did.

The bottom group is hand-labelled and the chart says so. These contracts say
nothing unusual about themselves. What gives them away is the recipient
count: an asset with millions of holders on its own chain does not have an
Ethereum contract that has paid 189 addresses in its entire life. The
judgment is mine, the counts are not.

What this cannot do is tell a wrapper from a fraud. A bridged token is a
normal thing and most of these are exactly what they say. The point is
narrower: holding one is not holding the asset the ticker names, and a chart
that prints only the ticker has no way to show the difference.

Reads out/symbol-audit.json from proof-of-crowd-tools.

Usage: python3 ticker_truth.py
"""

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "symbol-audit.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
# The whole rule for the computed group. A contract matching this is saying in
# its own name that it stands for something other than itself.
DECLARED = re.compile(r"wrapped|bridged|staked |xstock|ondo tokenized", re.I)
# Hand-labelled, and said so on the chart. Nothing on chain marks a contract
# as the Ethereum representation of an asset that lives elsewhere, so this is
# a judgment about what a reader would take each ticker for.
ELSEWHERE = {
    "GMX": "Arbitrum", "APT": "Aptos", "ATOM": "Cosmos",
    "AKT": "Cosmos", "DOT": "Polkadot", "ICP": "Internet Computer",
}


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


doc = json.loads(SRC.read_text())
all_rows = doc["tokens"]
declared = sorted((r for r in all_rows if r["name"] and DECLARED.search(r["name"])),
                  key=lambda r: r["arrived"])
elsewhere = sorted((r for r in all_rows if r["key"] in ELSEWHERE),
                   key=lambda r: r["arrived"])
missing = sorted(set(ELSEWHERE) - {r["key"] for r in elsewhere})
if missing:
    raise SystemExit(f"  {', '.join(missing)} named in the hand-labelled set "
                     f"but not in the audit; rerun symbol_audit.py")
mismatch = [r for r in all_rows if (r["symbol"] or "").upper() != r["key"]]
# Written in as "four" while only three of them appear on this chart. Counted
# against the rows actually drawn, so it cannot drift from them again.
DROPPED_BEFORE = {"APT", "DOT", "ICP", "SKY"}
shown = {r["key"] for r in declared} | {r["key"] for r in elsewhere}
already = sorted(DROPPED_BEFORE & shown)
smallest = min(all_rows, key=lambda r: r["arrived"])

W = 1240
L, R = 60, 1180
C_NAME = L + 148                # what the contract calls itself
C_RECV = R - 128                # lifetime recipients, right-aligned
C_WHEN = R                      # first block it moved on

b = [txt(L, 58, 37, INK,
         f"{len(declared)} of these {len(all_rows)} contracts say in their", 700),
     txt(L, 98, 37, INK,
         "own name that they stand for something else.", 700),
     txt(L, 138, 20, SUB,
         "Every chart prints the ticker, which is a string a contract chooses "
         "for itself and nothing has to agree with."),
     txt(L, 164, 20, SUB,
         # Typed as 94 while the audit reads however many contracts the
         # baseline holds, which is a count that grows on its own.
         f"These are the answers all {len(all_rows)} gave when asked for "
         "symbol() and name(), wherever the two tell different stories."),
     txt(L, 190, 20, SUB,
         "Recipients counts every address the contract has ever paid, which "
         "is the number that gives the rest away.")]

y = 246
b.append(txt(L, y, 23, INK, "It is in the name", 700))
b.append(txt(C_RECV, y, 16, SUB, "recipients", 400, "end"))
b.append(txt(C_WHEN, y, 16, SUB, "first moved", 400, "end"))
y += 14
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
y += 30

for r in declared:
    b.append(txt(L, y, 19, HOT, "$" + r["key"], 700, "start", MONO))
    b.append(txt(C_NAME, y, 20, INK, r["name"]))
    b.append(txt(C_RECV, y, 18, SUB, f"{r['arrived']:,}", 400, "end"))
    b.append(txt(C_WHEN, y, 18, SUB, r["first_seen"], 400, "end"))
    y += 34

y += 24
b.append(txt(L, y, 23, INK, "It is in the recipient count", 700))
# Set at C_NAME this printed straight through the section heading.
b.append(txt(C_WHEN, y, 18, SUB, "labeled by hand, everything else computed",
             400, "end"))
y += 14
b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
y += 30

for r in elsewhere:
    b.append(txt(L, y, 19, HOT, "$" + r["key"], 700, "start", MONO))
    b.append(txt(C_NAME, y, 20, INK,
                 f"{r['name']}, which lives on {ELSEWHERE[r['key']]}"))
    b.append(txt(C_RECV, y, 18, SUB, f"{r['arrived']:,}", 400, "end"))
    b.append(txt(C_WHEN, y, 18, SUB, r["first_seen"], 400, "end"))
    y += 34

y += 28
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${smallest['key']} has paid {smallest['arrived']} addresses in "
             f"{smallest['age_months']} months. The ticker is the same one the "
             f"exchanges print.", 700))
b.append(txt(L + 26, y + 68, 20, SUB,
             "A bridged token is ordinary and most of these are exactly what "
             "they claim. Holding one is still not holding what the ticker "
             "names."))
if mismatch:
    m = mismatch[0]
    b.append(txt(L + 26, y + 96, 20, SUB,
                 f"The audit also caught my own data: ${m['key']} is filed "
                 f"under that key and the contract's symbol is "
                 f"{m['symbol']}, {m['name']}."))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"{len(already)} of the rows above had already been dropped from "
             f"charts by hand, each one after it had been rendered once."))
y += 184

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "The top group is a string test on name() for wrapped, bridged, "
             "staked, xStock or Ondo Tokenized. No judgment in it."))
b.append(txt(L, y + 58, 19, SUB,
             "The bottom group says nothing unusual about itself. Which "
             "tickers a reader would take for a major asset is my call, and "
             "the counts are not."))
b.append(txt(L, y + 84, 19, SUB,
             "Recipients is every address ever paid by the contract, read "
             "from its Transfer history. Nothing here is priced."))
b.append(txt(R, y + 112, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 140

render("ticker_truth", W, H, "".join(b))
print(f"  {len(declared)} declared, {len(elsewhere)} hand-labeled, "
      f"smallest ${smallest['key']} at {smallest['arrived']} recipients")
