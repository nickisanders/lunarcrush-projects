#!/usr/bin/env python3
"""A 60% fall in advertised reward spend that is a calendar, not a decision.

The daily snapshot of Polymarket's live board carried about 15,000/day of
advertised maker rewards through mid-October, climbed to 51,898/day by
3 November and was back at 15,318/day three days later. Read as a time
series that is a platform cutting its liquidity budget by seventy percent
in a week.

It is the US midterms resolving. Of the 349 markets that left the board
between those two snapshots, 338 were election markets and they carried
42,802 of the 42,808/day that went with them, and 328 had already passed
their end date. The markets present in both snapshots went the other way,
from 9,090 to 14,151/day, a 56% rise.

That is the whole point of the chart. An aggregate over a population that
turns over does not measure the thing its units suggest. Every number on the
line is real and the line still describes the election calendar rather than
anybody's budget.

Two things the chart has to say out loud. Gamma's offset paging refuses an
offset past 2,000, so each snapshot is the first 2,100 open markets it will
serve and a lower bound on the board rather than a census. And the 4 November
run returned nothing, so that day is drawn as a gap rather than as a zero,
which is what a failed collection looks like when it is plotted carelessly.

Reads out/history/markets-live-*.json.

Usage: python3 reward_calendar.py
"""

import datetime as dt
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
HIST = HERE / "out" / "history"
SHARP = Path.home() / "lunarcrush-projects/projects/crowd-size/node_modules/sharp"
FONT = "Charter, Georgia, serif"
MONO = "Menlo, ui-monospace, monospace"
GROUND, INK, SUB, RULE = "#ffffff", "#15171c", "#6e6a60", "#ded8cd"
TRACK, BRAND, HOT = "#f2efe8", "#1b3a6b", "#a33228"
PEAK, AFTER = "2026-11-03", "2026-11-06"
# A small count reads as prose in a serif headline and as data in the
# callout, so the headline spells it and everything else does not.
WORD = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, size, fill, s, weight=400, anchor="start", font=None, op=1.0):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="{op}" '
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


def load(path):
    d = json.loads(path.read_text())
    return d.get("markets") or {}


snaps = {}
for p in sorted(HIST.glob("markets-live-*.json")):
    m = load(p)
    # A run that came back with nothing is a failed collection, not a board
    # with no markets on it. Dropping it leaves a gap in the line, which is
    # the truthful shape; plotting it as zero would invent the steepest move
    # in the series.
    if not m:
        continue
    day = p.name.split("markets-live-")[1][:10]
    snaps[day] = {"budget": sum(v["daily_rate"] for v in m.values()),
                  "paying": sum(1 for v in m.values() if v["paid"]),
                  "markets": len(m), "src": p}

days = sorted(snaps)
first, last = days[0], days[-1]

a = load(snaps[PEAK]["src"])
b = load(snaps[AFTER]["src"])
both = set(a) & set(b)
gone = {k: a[k] for k in set(a) - both}
came = {k: b[k] for k in set(b) - both}
KW = ("election", "senate", "governor", "house seat", "mayor", "midterm",
      "congress", "ballot", "proposition")
el = [v for v in gone.values()
      if any(w in (str(v.get("question")) + str(v.get("slug"))).lower() for w in KW)]
cut = dt.datetime.fromisoformat(AFTER).replace(tzinfo=dt.timezone.utc)


def ended(v):
    e = v.get("end")
    if not e:
        return False
    try:
        d = dt.datetime.fromisoformat(str(e).replace("Z", "+00:00"))
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d <= cut


past = [v for v in gone.values() if ended(v)]
stay_a = sum(a[k]["daily_rate"] for k in both)
stay_b = sum(b[k]["daily_rate"] for k in both)
gone_r = sum(v["daily_rate"] for v in gone.values())
el_r = sum(v["daily_rate"] for v in el)
came_r = sum(v["daily_rate"] for v in came.values())

W = 1240
L, R = 60, 1180
PT, PB = 260, 700
# Rounded up to a whole 15k so the gridline labels are readable numbers
# rather than whatever 12% above the peak happens to be.
STEP = 15000
top = -(-max(s["budget"] for s in snaps.values()) * 1.08 // STEP) * STEP

drop = (1 - snaps[AFTER]["budget"] / snaps[PEAK]["budget"]) * 100
days_apart = (dt.date.fromisoformat(AFTER) - dt.date.fromisoformat(PEAK)).days
b_ = [txt(L, 58, 37, INK,
          f"Polymarket's advertised reward spend fell {drop:.0f}% in", 700),
      txt(L, 98, 37, INK,
          f"{WORD.get(days_apart, days_apart)} days, because the US midterms "
          f"resolved.", 700),
      txt(L, 140, 20, SUB,
          "Each point is one daily snapshot of the live board, summing every "
          "market's advertised maker-reward rate. The line is real and it is"),
      txt(L, 166, 20, SUB,
          "a picture of the US election calendar rather than of anyone's "
          "liquidity budget.")]

# grid
for i in range(int(top // STEP) + 1):
    val = i * STEP
    gy = PB - (PB - PT) * val / top
    b_.append(f'<line x1="{L}" y1="{gy:.0f}" x2="{R}" y2="{gy:.0f}" '
              f'stroke="{RULE}" stroke-width="1"/>')
    b_.append(txt(L - 10, gy + 6, 16, SUB, f"{val/1000:.0f}k", 400, "end", MONO))

span = (dt.date.fromisoformat(last) - dt.date.fromisoformat(first)).days


def px(day):
    d = (dt.date.fromisoformat(day) - dt.date.fromisoformat(first)).days
    return L + (R - L) * d / span


def py(v):
    return PB - (PB - PT) * v / top


# The series is drawn as runs of consecutive days, so the missing collection
# breaks the line instead of being bridged across.
run = []
runs = []
prev = None
for d in days:
    cur = dt.date.fromisoformat(d)
    if prev and (cur - prev).days > 1:
        runs.append(run)
        run = []
    run.append(d)
    prev = cur
runs.append(run)
for r in runs:
    pts = " ".join(f"{px(d):.1f},{py(snaps[d]['budget']):.1f}" for d in r)
    b_.append(f'<polyline points="{pts}" fill="none" stroke="{BRAND}" '
              f'stroke-width="3"/>')
for d in days:
    hot = d in (PEAK, AFTER)
    b_.append(f'<circle cx="{px(d):.1f}" cy="{py(snaps[d]["budget"]):.1f}" '
              f'r="{6 if hot else 4}" fill="{HOT if hot else BRAND}"/>')

b_.append(txt(px(PEAK) - 14, py(snaps[PEAK]["budget"]) - 16, 21, HOT,
              f"{snaps[PEAK]['budget']:,.0f}/day", 700, "end", MONO))
b_.append(txt(px(AFTER) - 14, py(snaps[AFTER]["budget"]) + 8, 21, HOT,
              f"{snaps[AFTER]['budget']:,.0f}", 700, "end", MONO))
b_.append(txt(px(PEAK) + 14, PT - 20, 19, SUB, "election day", 400, "end"))
b_.append(f'<line x1="{px(PEAK):.1f}" y1="{PT-12}" x2="{px(PEAK):.1f}" '
          f'y2="{py(snaps[PEAK]["budget"])-14:.1f}" stroke="{SUB}" '
          f'stroke-width="1.5" stroke-dasharray="4 4"/>')
miss = [d for d in ((dt.date.fromisoformat(first) + dt.timedelta(days=i)).isoformat()
                    for i in range(span + 1)) if d not in snaps]
for d in miss:
    b_.append(f'<line x1="{px(d):.1f}" y1="{PB-6}" x2="{px(d):.1f}" '
              f'y2="{PB-30}" stroke="{RULE}" stroke-width="2"/>')
    b_.append(txt(px(d), PB - 40, 16, SUB, "no run", 400, "middle", MONO))

for d in (first, days[len(days)//2], last):
    b_.append(txt(px(d), PB + 26, 17, SUB,
                  dt.date.fromisoformat(d).strftime("%b %-d"), 400, "middle", MONO))
b_.append(f'<line x1="{L}" y1="{PB}" x2="{R}" y2="{PB}" stroke="{INK}" stroke-width="2"/>')

y = PB + 86
b_.append(f'<rect x="{L}" y="{y}" width="{R-L}" height="176" fill="#fbf7ef"/>')
b_.append(f'<rect x="{L}" y="{y}" width="5" height="176" fill="{HOT}"/>')
b_.append(txt(L + 26, y + 40, 23, INK,
              f"The {len(both):,} markets on the board both days went up "
              f"{(stay_b/stay_a-1)*100:.0f}%, from {stay_a:,.0f} to "
              f"{stay_b:,.0f} a day.", 700))
b_.append(txt(L + 26, y + 72, 23, INK,
              f"All of the fall is {len(gone):,} markets leaving, and "
              f"{len(el):,} of those are elections.", 700))
b_.append(txt(L + 26, y + 106, 20, SUB,
              f"They carried {el_r:,.0f} of the {gone_r:,.0f} a day that went "
              f"with them, and {len(past):,} had already passed their end date. "
              f"The {len(came):,} markets"))
b_.append(txt(L + 26, y + 132, 20, SUB,
              f"that took their place carry {came_r:,.0f} a day between them. An "
              f"aggregate over a population that turns over measures the"))
b_.append(txt(L + 26, y + 158, 20, SUB,
              "turnover, whatever its units say."))
y += 216

b_.append(f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="{RULE}" stroke-width="2"/>')
b_.append(txt(L, y + 32, 19, SUB,
              f"Gamma's paging refuses an offset past 2,000, so a snapshot is the "
              f"first {snaps[last]['markets']:,} open markets it serves, a lower "
              f"bound and not a census."))
b_.append(txt(L, y + 58, 19, SUB,
              "The 4 November collection returned nothing and is drawn as a gap. "
              "A failed run plotted as a zero would be the steepest move here."))
b_.append(txt(R, y + 84, 19, SUB,
              f"{first} to {last}  ·  @nickisanders", 400, "end"))
H = y + 112

render("reward_calendar", W, H, "".join(b_))
print(f"  {len(days)} snapshots, {first} to {last}")
print(f"  peak {snaps[PEAK]['budget']:,.0f}/day -> {snaps[AFTER]['budget']:,.0f}/day")
print(f"  stayed {len(both):,}: {stay_a:,.0f} -> {stay_b:,.0f}")
print(f"  left {len(gone):,} carrying {gone_r:,.0f}; elections {len(el):,} carrying {el_r:,.0f}; ended {len(past):,}")
print(f"  entered {len(came):,} carrying {came_r:,.0f}")
