# headcount

How many people are actually talking about your coin?

For each of the top 1,000 coins by market cap, the median number of distinct
accounts posting about it per day, April to July 2026.

## The median coin has 24 people

| percentile | people a day |
|---|---:|
| p10 | 1 |
| p25 | 5 |
| **p50** | **24** |
| p75 | 73 |
| p90 | 190 |

35% of coins have fewer than 10 people a day. 67% have fewer than 50. 82%
have fewer than 100.

## By market-cap rank

| rank band | median people a day | median posts a day |
|---|---:|---:|
| #1 to 10 | 13,161 | 28,965 |
| #11 to 50 | 532 | 1,120 |
| #51 to 100 | 128 | 379 |
| #101 to 250 | 62 | 116 |
| #251 to 500 | 29 | 51 |
| #501 to 1000 | 14 | 24 |

The drop from the top ten to the next forty is 25x. From there to the bottom
half of the list is another 38x.

To rank in the top 100 coins by crowd you need 183 people a day. The top 10
needs 1,836.

## Big coins with tiny crowds

Top-100 by market cap, fewer than 50 people a day:

| coin | rank | market cap | people a day |
|---|---:|---:|---:|
| $FTN | #47 | $1.8B | 3 |
| $BGB | #66 | $1.2B | 6 |
| $LEO | #15 | $9.0B | 7 |
| $KCS | #74 | $1.0B | 16 |
| $BEAT | #65 | $0.7B | 17 |
| $NEXO | #86 | $0.5B | 23 |
| $HASH | #95 | $0.5B | 38 |
| $FLR | #100 | $0.6B | 43 |
| $BDX | #92 | $0.6B | 44 |
| $HTX | #54 | $1.6B | 48 |

Five of the ten are exchange tokens. LEO is the fifteenth largest coin in
crypto and seven accounts a day post about it.

## What is excluded, and why

Pegged, wrapped, liquid-staked and yield-bearing tokens are removed before
anything is counted. Nobody discusses a wrapper, so without the exclusion the
"big coins, tiny crowds" list is WBETH, USDC.e and a dozen staked-ETH
derivatives, which is true and not interesting. What is left is projects with
a real ticker and almost no crowd. Single-character tickers are dropped too.

The window is a fixed 90 days back from the newest row in the cache, not each
coin's last 90 rows, because a sparsely covered coin's last 90 rows can reach
back a year.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 headcount.py   # out/headcount.json
python3 chart.py       # out/headcount.svg
```

Reads the cached daily history in `../social-price-backtest/data/raw`.
