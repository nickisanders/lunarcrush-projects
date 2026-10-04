# crowd-check

Ten coins are up big. Which ones have a real crowd behind them?

```bash
LUNARCRUSH_API_KEY=... python3 crowd_check.py
python3 chart.py
```

Takes the week's biggest gainers and reports four things per coin. It is the
screen, not the audit: it says where to look.

## 2026-10-04

| coin | 7d | people a day | a month ago | change | spam vs own norm | read |
|---|---:|---:|---:|---:|---:|---|
| $NIGHT | +86% | 529 | 188 | +181% | 1.11x | crowd more than doubled |
| $SAND | +76% | 63 | 43 | +47% | 0.45x | crowd grew with the price |
| $NOS | +65% | 83 | 34 | +148% | 1.20x | crowd more than doubled |
| $QNT | +44% | 2,846 | 196 | +1348% | 1.33x | crowd more than doubled |
| $STRK | +42% | 129 | 100 | +30% | 0.98x | crowd grew with the price |
| $OMI | +42% | 94 | 42 | +121% | 0.59x | crowd more than doubled |
| $QUBIC | +38% | 232 | 146 | +58% | 0.92x | crowd grew with the price |
| $PUMP | +35% | 93 | 50 | +88% | 0.78x | crowd grew with the price |
| $MUBARAK | +34% | 149 | 60 | +146% | 1.30x | crowd more than doubled |
| $CARDS | +29% | 245 | 120 | +104% | **2.04x** | fresh spam wave |

Nine of ten had people arrive, and nobody's crowd shrank. That is not the
usual result.

- **$SAND rose 76% on 63 people a day**, with spam at 0.45x its own norm. The
  leanest crowd on the list and the cleanest.
- **$QNT sits at 2,846 people a day** against 196 a month ago.
- **$CARDS is the one exception**, at 2.04x its spam baseline. It was 1.53x
  the day before, so the wave is getting louder rather than fading.

The day before, three of ten were flagged and $PURR's crowd had shrunk 30%
while its price rose. It fell off the gainers list entirely the next day.

## Spam lift, not spam share

The absolute share is close to useless. Some tokens run chronically high, and
LunarCrush's own counting changed during 2023, so `spam` can exceed
`posts_created` outright — see the data break documented in
[weekend-crowd](../weekend-crowd/).

What carries information is the ratio against the coin's own 30-day norm.
$PUMP sits at 59% spam and a 0.73x lift: high, and lower than usual for it.
That is a noisy neighbourhood, not a new campaign. $AGT at 2.05x is the
opposite case.

## What this does not do

It does not identify who is behind anything, and it cannot. Amplification
patterns are compatible with bot campaigns, coordinated advocacy, algorithmic
reach and unusually tight real communities alike. The output says which of
these coins had somebody show up, and nothing about anyone's intent.

Crowd change is a ratio, so $AGT going from 10 to 14 people reads as +47% and
is still 14 people. The absolute column is there to keep that visible.

Seven days is a short window and one week does not establish a pattern. A
coin can have a thin crowd and a perfectly good reason for it.

## Method

Daily active contributors over the last seven complete days against the thirty
before them. The final row is dropped because it is today, still accumulating,
which is the partial-day bias that has bitten three projects in this repo.
Pegged and wrapped assets excluded, tickers deduplicated.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
