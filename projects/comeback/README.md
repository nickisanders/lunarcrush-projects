# comeback

A coin that was written off, month by month, until it wasn't.

[where-are-they-now](../where-are-they-now/) found that of 130 coins that
ever held a top-20 seat in crypto conversation, 17 still do. This is the
mirror: a coin that had a seat, lost it completely, and took it back.

## $ZEC

Zcash launched in 2016 and was a top-ten coin by 2018. Then:

| month | price | market cap | people posting/day | seat in the conversation |
|---|---:|---:|---:|---:|
| Jun 2020 | $52.52 | $0.5B | 61 | #17 |
| Jun 2022 | $57.40 | $0.7B | 70 | #34 |
| Jun 2023 | $33.72 | $0.3B | 198 | #57 |
| **Jun 2024** | **$20.84** | **$0.3B** | 561 | #107 |
| **Jan 2025** | $43.15 | $0.7B | 686 | **#126** |
| Sep 2025 | $73.71 | $1.2B | 836 | #66 |
| Oct 2025 | $406.29 | $6.6B | 4,260 | #9 |
| Nov 2025 | $427.72 | $7.0B | 8,902 | #4 |
| Jul 2026 | $462.50 | $7.8B | 1,252 | #14 |
| **today** | **$1,439** | **$24.3B** | ~5,700 | **#4** |

69x from the June 2024 low. #126 to #4 in the conversation. $0.3B to $24B.
#9 by market cap today.

## The crowd came after the price

September to October 2025: the price went $73 to $406, 5.5x in a month. The
crowd went 836 to 4,260 a day, 5x. Both moved together in the same month,
and the daily data in the cache says the price led by a few days. This is
the pattern from [who-moved-first](../who-moved-first/) at the scale of a
$20B coin rather than a $600M one.

Nothing in the crowd data foreshadowed October. The seat was #66 in
September, roughly where it had been for a year.

## Why a rank and not a count

Contributor counts on this coin run 61 a day in 2020 and 8,902 in November
2025, and the whole market's contributor counts moved over the same period.
The seat, its rank against every other coin on the same day, is comparable
across six years in a way the raw count is not. Pegged assets and
single-character tickers are removed from the ranking as in
[top-ten](../top-ten/).

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
LUNARCRUSH_API_KEY=... python3 comeback.py ZEC   # out/zec.json
python3 chart.py out/zec.json                    # out/zec.svg
```

Works on any ticker in the cache. The live numbers come from the API.
