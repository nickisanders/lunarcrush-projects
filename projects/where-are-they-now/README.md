# where-are-they-now

Every coin that ever held a seat in crypto's top-20 conversation, and where
it sits today.

## 130 made it. 17 are still there.

Rank every coin by daily active contributors, take each month's median rank,
and find each coin's best month. 130 coins have held a top-20 seat in some
month since January 2020.

| | coins | share |
|---|---:|---:|
| still top 20 | 17 | 13% |
| slipped to 21–50 | 21 | 16% |
| slipped to 51–100 | 29 | 22% |
| fell past #100 | 63 | 48% |

Median seat today for a coin that was once top 20: #95.

## The ones you remember

| coin | peak | month | people a day then | now | seat now |
|---|---:|---|---:|---:|---:|
| YFI | #7 | Sep 2020 | 256 | 42 | #435 |
| SUSHI | #10 | Sep 2020 | 206 | 56 | #346 |
| 1INCH | #16 | Dec 2020 | 142 | 27 | #478 |
| MANA | #16 | Nov 2021 | 420 | 43 | #350 |
| SLP | #15 | Feb 2022 | 219 | 45 | #349 |
| GMT | #13 | Apr 2022 | 278 | 36 | #437 |
| GMX | #17 | Dec 2022 | 234 | 37 | #409 |
| AGIX | #16 | Feb 2023 | 1,052 | 27 | #505 |
| BLUR | #7 | Feb 2023 | 1,669 | 39 | #412 |
| MEME | #6 | Nov 2023 | 3,643 | 41 | #450 |
| DYM | #19 | Feb 2024 | 2,268 | 49 | #367 |

MEME had 3,643 people a day posting about it at its peak. It has 41 now.

## By the year they peaked

| peaked in | coins | still top 20 | fell past #100 |
|---|---:|---:|---:|
| 2020 | 32 | 6 | 19 |
| 2021 | 20 | 1 | 10 |
| 2022 | 15 | 1 | 7 |
| 2023 | 24 | 2 | 12 |
| 2024 | 20 | 2 | 10 |
| 2025 | 15 | 2 | 5 |
| 2026 | 4 | 3 | 0 |

The 2020 survivors are BTC, ETH, XRP, ADA, LINK and LTC. The single 2021
survivor is DOGE. The 2022 survivor is CRO.

## The 17 still holding a seat

BTC, ETH, SOL, PUMP, HYPE, XRP, ADA, DOGE, ZEC, MON, LINK, TIA, CRO, KAS,
TAO, LTC, PEPE. Seven of these are the fixtures from [top-ten](../top-ten/);
the rest peaked within the last two years and have not had time to fall yet.

## Survivorship, stated plainly

The universe is the top 1,000 coins by market cap at pull time. A coin that
held a top-20 seat in 2021 and has since dropped out of the top 1,000
entirely is not in this data. Every attrition number here is therefore a
floor: the real count of fallen coins is higher, and the real share still
holding a seat is lower than 13%.

## Method

Same universe hygiene as [top-ten](../top-ten/): pegged and wrapped assets
excluded, single-character tickers dropped, per-day name collisions removed
using the interactions-per-dollar test from
[name-collision](../name-collision/). Contributors rather than interactions,
for the reason in [polygon](../polygon/). "Now" is the median rank across
May to July 2026.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 fallen.py   # out/fallen.json
python3 chart.py    # out/fallen.svg
```
