# attention-floor

A spike is easy to see and nearly useless on its own. Did anyone stay?

```bash
LUNARCRUSH_API_KEY=... python3 floor.py FET
python3 chart.py
```

[project 05](../attention-halflife/) established that crypto attention dies fast
whatever its source, so the height of a bar says very little about whether the
crowd was real. The signature that separates adoption from a campaign is what
the ordinary days look like afterwards. Arrivals who stay leave a durably higher
floor, and a campaign leaves a crater once the budget stops.

So this throws the spikes away and measures what is left. Every day at or above
2x the coin's own 30-day median is excluded, and the quiet days that remain are
compared across three windows.

## $FET, 2026-10-05

Five spike days in three weeks, and the number of people posting rose at every
one of them.

| day | interactions | vs norm | people | price |
|---|---:|---:|---:|---:|
| 2026-09-21 | 1,317,530 | 2.8x | 421 | $0.2038 |
| 2026-09-24 | 1,044,228 | 2.2x | 465 | $0.2289 |
| 2026-09-25 | 1,602,991 | 3.4x | 538 | $0.2456 |
| 2026-09-26 | 1,003,405 | 2.1x | 591 | $0.2432 |
| 2026-10-04 | 1,680,804 | 3.5x | 691 | $0.2530 |

The floor, counting quiet days only:

| window | interactions | people |
|---|---:|---:|
| 90 to 42 days ago | 208,975 | 238 |
| 42 to 21 days ago | 274,140 | 211 |
| the last 21 days | 506,250 | 376 |

**The floor is 2.42x where it was, with 1.58x the people.** Each wave left more
behind it than the last, which is the residue of a crowd accumulating rather
than cycling through.

Supporting checks on the same token: zero near-identical posts across separate
accounts, so no copypasta campaign, and spam rose 2.3x against a crowd that
rose 2.2x, so no fresh wave running ahead of the people.

`python3 chart.py` draws it and `python3 carousel.py` builds the five-slide
Instagram version, both reading the same `out/floor.json` so neither can drift
from the numbers. Charts are not committed anywhere in this repo, so rerun the
scripts to regenerate them.

## What it does not say

It makes no claim about who is behind any spike. The same pattern is compatible
with coordinated promotion, an ordinary news cycle, and a genuinely growing
community.

It is also not a buy signal, and $FET is the case that shows why. Price is up
54% over the same 90 days, and [project 02](../social-price-backtest/) found
organic attention only shifts the odds while the price has **not** moved yet.
A rising floor next to a price that has already run is a description of what
happened, not an edge on what happens next.

## Notes

The final row of the series is dropped because it is today and still
accumulating, which is the partial-day bias that has bitten three projects here.
The 2x threshold is a convention rather than a discovery; the floor comparison
is not sensitive to it, since moving it mainly changes how many days get
excluded from windows that have dozens either way.

Both LunarCrush and most crypto data APIs sit behind Cloudflare, which rejects
the default `Python-urllib` User-Agent with a 403 that reads exactly like rate
limiting. Every request here sends one.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
