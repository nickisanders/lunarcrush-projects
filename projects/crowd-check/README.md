# crowd-check

Ten coins are up big. Which ones have a real crowd behind them?

```bash
LUNARCRUSH_API_KEY=... python3 crowd_check.py
python3 chart.py
```

Takes the week's biggest gainers and reports four things per coin. It is the
screen, not the audit: it says where to look.

## 2026-10-03

| coin | 7d | people a day | a month ago | change | spam vs own norm | read |
|---|---:|---:|---:|---:|---:|---|
| $QNT | +109% | 2,844 | 196 | +1347% | 1.24x | crowd more than doubled |
| $NIGHT | +91% | 399 | 188 | +112% | 1.04x | crowd more than doubled |
| $SHX | +83% | 167 | 86 | +93% | 1.04x | crowd grew with the price |
| $SAND | +63% | 63 | 43 | +47% | 0.34x | crowd grew with the price |
| $CARDS | +44% | 236 | 118 | +99% | **1.53x** | fresh spam wave |
| $OMI | +38% | 73 | 42 | +72% | 0.81x | crowd grew with the price |
| $PUMP | +36% | 93 | 50 | +84% | 0.73x | crowd grew with the price |
| $AGT | +36% | 14 | 10 | +47% | **2.05x** | fresh spam wave |
| $SUPER | +30% | 156 | 94 | +67% | 1.14x | crowd grew with the price |
| $PURR | +30% | 33 | 47 | **-30%** | **1.49x** | price up, fewer people talking |

Seven of ten had people arrive. Three did not.

- **$SAND rose 63% on 63 people a day**, with spam at a third of its own norm.
  A small crowd and a clean one.
- **$QNT went from 196 people a day to 2,844.** Whatever else is true, that is
  a genuine arrival.
- **$PURR rose 30% with fewer people talking about it than a month ago**, and
  spam at 1.49x its baseline. The only coin on the list whose crowd shrank
  while the price rose.
- **$AGT is 14 people a day** at 2.05x its spam norm, on a $83M token.

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
