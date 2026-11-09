#!/usr/bin/env python3
"""The top 1% holds nearly all the supply, and that says nothing about whales.

"The top 1% of addresses holds 95% of the supply" is the most quoted number in
token analysis and it is quoted as evidence of whale capture. On all forty
tokens here it reads between 92% and 100%, so as a way of telling tokens apart
it has already failed before anyone interprets it.

Each bar asks the chain what those addresses are. eth_getCode on every address
in the top 1% splits the supply they hold into code and wallets. A contract is
not a person: it is a pool, a bridge, a vesting escrow or an exchange's
omnibus. The red share runs from 0.2% to 99.1% across tokens whose headline
concentration is indistinguishable.

Three things this chart has to carry honestly.

Code is not the same as absence of people. An exchange omnibus holds for
thousands of people and a staking pool holds for its depositors, so a red bar
does not mean the holders are not there. It means this measure cannot see
them. The chain says there is code at the address and does not say what the
code does, which is the reason the number cannot be read in either direction.

A blue bar is not a crowd either. One person can hold through forty wallets,
and nothing here would tell.

Since EIP-7702 an ordinary wallet can carry a delegation, so code alone would
misclassify it. Code of exactly 23 bytes beginning ef0100 is a delegation
pointer and is counted as a wallet, which is what it is.

Reads out/top-code.json from proof-of-crowd-tools, written by top_code.py.

Usage: python3 top_percent.py
"""

import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "proof-of-crowd-tools" / "out" / "top-code.json"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
# The claim is about tokens whose headline concentration is the same, so the
# floor is what makes the set comparable rather than a way of picking winners.
MIN_TOP1, MIN_HOLDERS = 0.90, 1000
# Same reasoning as mobility_spread.py: a ticker is whatever a contract says
# its symbol is, and the label is what would mislead rather than the
# measurement. Keyed by address so a genuine token reusing a ticker survives.
AMBIGUOUS = {
    "0x8cdf7af57e4c8b930e1b23c477c22f076530585e": "symbol APT, not Aptos",
    "0x8d010bf9c26881788b4e6bf5fd1bdc358c8f90b8": "symbol DOT, not Polkadot",
    "0x00f3c42833c3170159af4e92dbb451fb3f708917": "symbol ICP, first seen 2025",
    "0x33e2c129ea670031659ac8852c01d0fe4b297954": "symbol SKY, not Sky's token",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Three drafts of this chart ran a line of prose past the right margin and the
# renderer drew it anyway, clipped. The per-character widths are read back off
# a render rather than guessed: Charter sets at about 0.40 of its point size
# and 0.52 bold. A line that will not fit now says so at render time instead
# of in the image.
def fits(x, size, s, weight=400):
    room = R - x
    width = len(str(s)) * size * (0.53 if weight >= 700 else 0.415)
    if width > room:
        over = int((width - room) / (size * 0.485))
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
base = json.loads((SRC.parent / "retention-baseline.json").read_text())
rows, dropped = [], []
for name, d in doc["tokens"].items():
    if d["top1pct_supply_share"] < MIN_TOP1 or d["holders"] < MIN_HOLDERS:
        continue
    addr = (base["tokens"].get(name) or {}).get("address", "").lower()
    if addr in AMBIGUOUS:
        dropped.append(name.upper())
        continue
    c = d["classes"]
    if c["unknown"]["n"]:
        # An address nobody answered for would be split between the two
        # segments by whichever one it was quietly filed under.
        raise SystemExit(f"  {name}: {c['unknown']['n']} addresses went "
                         f"unclassified; rerun top_code.py before charting")
    rows.append({"sym": name.upper(), "holders": d["holders"],
                 "n": d["top1pct_n"], "top1": d["top1pct_supply_share"],
                 # A 7702 delegation is a person's wallet carrying code, so it
                 # belongs with the wallets and not with the contracts.
                 "code": c["contract"]["supply_share"],
                 "own": c["wallet"]["supply_share"] + c["delegated"]["supply_share"],
                 "deleg": c["delegated"]["supply_share"],
                 "first": d["biggest_holder"]["supply_share"]})
if len(rows) < 10:
    raise SystemExit(f"  only {len(rows)} tokens clear {MIN_TOP1*100:.0f}% "
                     f"concentration and {MIN_HOLDERS} holders")
rows.sort(key=lambda r: -r["code"])
med = statistics.median(r["code"] for r in rows)
hi, lo = rows[0], rows[-1]
mostly_code = [r for r in rows if r["code"] > 0.5]
holders = sum(r["holders"] for r in rows)
big_own = max((r for r in rows if r["code"] <= 0.5),
              key=lambda r: r["holders"], default=rows[-1])
checked = sum(r["n"] for r in rows)
t_lo = min(r["top1"] for r in rows)

W = 1240
L, R = 60, 1180
LABEL = 112
RIGHT = 150                     # the top-1% column
BARW = R - L - LABEL - RIGHT
BH, GAP = 22, 4
X0 = L + LABEL

# The count of tokens was written into the headline as a word and the set
# grew to 44 while the chart still said forty. Nothing in the header is typed
# now: the headline carries no count and the subhead computes the ones it has.
b = [txt(L, 58, 37, INK, "The top 1% of addresses holds nearly all the", 700),
     txt(L, 98, 37, INK, "supply on every one of these tokens.", 700),
     txt(L, 138, 20, SUB,
         f"What that 1% is made of runs from {hi['code']*100:.1f}% smart "
         f"contracts on ${hi['sym']} to {lo['code']*100:.1f}% on ${lo['sym']}, "
         f"and the concentration"),
     txt(L, 164, 20, SUB,
         f"figure reads the same either way. {len(rows)} tokens, "
         f"{holders:,} holder positions, {checked:,} addresses asked."),
     txt(L, 190, 20, SUB,
         "Red is supply sitting in code. Blue is supply in wallets. The pale "
         "remainder is everything the other 99% holds.")]

y = 240
bars_top = y
for r in rows:
    wc, ww = BARW * r["code"], BARW * r["own"]
    b.append(txt(L, y + BH - 7, 17, INK, "$" + r["sym"], 700, "start", MONO))
    b.append(f'<rect x="{X0}" y="{y}" width="{BARW}" height="{BH}" fill="{TRACK}"/>')
    b.append(f'<rect x="{X0}" y="{y}" width="{wc:.1f}" height="{BH}" fill="{HOT}"/>')
    b.append(f'<rect x="{X0+wc:.1f}" y="{y}" width="{ww:.1f}" height="{BH}" '
             f'fill="{BRAND}"/>')
    label = f"{r['code']*100:.1f}%"
    # Under about a tenth of the track the segment is narrower than its own
    # label, so the figure moves outside rather than being squeezed or clipped.
    if wc > 76:
        b.append(txt(X0 + wc - 10, y + BH - 7, 17, "#ffffff", label, 700,
                     "end", MONO))
    else:
        b.append(txt(X0 + BARW + 12, y + BH - 7, 17, SUB, label, 400,
                     "start", MONO))
    b.append(txt(R, y + BH - 8, 16, SUB, f"{r['top1']*100:.1f}%", 400, "end"))
    y += BH + GAP

bars_bot = y - GAP
b.append(txt(R, bars_top - 10, 15, SUB, "top 1% holds", 400, "end"))

mx = X0 + BARW * med
b.append(f'<line x1="{mx:.1f}" y1="{bars_top-6}" x2="{mx:.1f}" y2="{bars_bot+6}" '
         f'stroke="{INK}" stroke-width="2" stroke-dasharray="3 4" opacity="0.55"/>')
b.append(txt(mx + 9, bars_bot + 26, 18, INK, f"median {med*100:.1f}% in code", 700))

y = bars_bot + 52
b.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="144" fill="#fbf7ef"/>')
b.append(f'<rect x="{L}" y="{y}" width="5" height="144" fill="{HOT}"/>')
b.append(txt(L + 26, y + 36, 23, INK,
             f"${hi['sym']} and ${lo['sym']} both read above "
             f"{min(hi['top1'], lo['top1'])*100:.0f}% concentration. One is "
             f"{hi['code']*100:.1f}% code, the other {lo['code']*100:.1f}%.",
             700))
b.append(txt(L + 26, y + 68, 20, SUB,
             f"Code holds more than half the supply on {len(mostly_code)} of "
             f"the {len(rows)}. The largest where it does not is "
             f"${big_own['sym']}, {big_own['code']*100:.1f}% code across "
             f"{big_own['holders']:,} holders."))
b.append(txt(L + 26, y + 96, 20, SUB,
             "A contract is not a person and it is not nobody. An exchange "
             "omnibus holds for thousands, a pool holds for its depositors, "
             "and the"))
b.append(txt(L + 26, y + 124, 20, SUB,
             f"chain says only that code is there. Blue is no safer: one wallet "
             f"holds {lo['first']*100:.1f}% of ${lo['sym']}, the token with "
             f"the least code on the chart."))
y += 184

b.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b.append(txt(L, y + 32, 19, SUB,
             "Supply is every token held at a positive balance, netted from "
             "every Transfer event since each contract's first block. Nothing "
             "here is priced."))
b.append(txt(L, y + 58, 19, SUB,
             f"The set is every baseline token above {MIN_HOLDERS:,} holders "
             f"whose top 1% holds {MIN_TOP1*100:.0f}% of supply or more, "
             f"{len(rows)} of them. The lowest reads {t_lo*100:.1f}%."))
b.append(txt(L, y + 84, 19, SUB,
             "A wallet carrying code as an EIP-7702 delegation counts as a "
             "wallet, not a contract. One person holding through forty "
             "wallets reads as blue."))
if dropped:
    names = ", ".join("$" + d for d in dropped)
    b.append(txt(L, y + 110, 19, SUB,
                 f"{names} {'is' if len(dropped) == 1 else 'are'} dropped for "
                 f"carrying a ticker a reader would take for another token."))
    y += 26
b.append(txt(R, y + 112, 19, SUB,
             f"measured {doc['measured']}  ·  @nickisanders", 400, "end"))
H = y + 140

render("top_percent", W, H, "".join(b))
print(f"  {len(rows)} tokens, {checked:,} addresses, median {med*100:.1f}% in "
      f"code, ${hi['sym']} {hi['code']*100:.1f}% to ${lo['sym']} "
      f"{lo['code']*100:.1f}%")
