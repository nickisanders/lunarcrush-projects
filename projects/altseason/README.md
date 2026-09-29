# altseason

Is it altseason? A number instead of a vibe.

```bash
LUNARCRUSH_API_KEY=... python3 altseason.py
python3 chart.py
```

## 2026-09-29

**80% of the top 100 coins are beating Bitcoin over the last 30 days.**

| | |
|---|---:|
| today | **80%** |
| six-year median | 33% |
| percentile of today | **97th** of 2,372 days |
| days above 50%, ever | 28% |
| Bitcoin over the window | +7% |

Bitcoin is up and losing to four coins in five anyway, which is the part that
makes it unusual. Breadth this wide normally shows up when Bitcoin is flat or
falling and money rotates out; here it is rotating out of something that is
working.

By year, the share of days with more than half the top 100 beating Bitcoin:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---:|---:|---:|---:|---:|---:|---:|
| 36% | 45% | 28% | 24% | 16% | 19% | 27% |

2021 is the reference point everybody uses, and it only cleared half on 45%
of its days.

Leading the top 100 over 30 days: $QNT +302%, $AKE +282%, $NEAR +167%,
$DRV +144%, $ARB +135%, $AR +107%, $ZEC +69%.

## The measure

Take the top 100 by market cap as of 30 days ago, excluding Bitcoin itself,
pegged assets and wrapped assets. Count how many beat Bitcoin's 30-day return.
That is the whole thing. No index, no weighting, no threshold anybody picked,
so there is nothing to tune and nothing to argue with except the window and
the universe size, both of which are flags.

History to 2026-07-29 comes from the cached daily files; today's reading comes
from the live API, so the series runs to the current day.

## Limits

The universe is the top 1,000 coins by market cap today, so a coin that was
top-100 in 2021 and has since fallen out of the top 1,000 is missing from the
historical rankings. That biases the old readings, not today's.

A single day's reading is noisy: the series crosses 50% often and falls back
within days. What is unusual here is the level, not the direction.

This says nothing about what happens next. [graveyard](../graveyard/) and
[after_the_run.py](../social-price-backtest/after_the_run.py) both cover that,
and neither is encouraging about chasing it.
