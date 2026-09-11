# polygon

Where did Polygon go? Its rank in crypto conversation, 2020 to 2026.

Polygon was one of the most discussed coins in crypto for four years. This
ranks it against every other coin on every day by daily active contributors,
then does the same for peer chains so the fall can be read as either
Polygon's or a narrative's.

## The shape

| period | median rank | days in top 20 | contributors/day |
|---|---:|---:|---:|
| 2021 H1 | 15 | 61% | 328 |
| 2021 H2 | 17 | 77% | 281 |
| 2022 H1 | 18 | 66% | 157 |
| 2022 H2 | 16 | 84% | 175 |
| 2023 H1 | 22 | 39% | 724 |
| 2023 H2 | **13** | **100%** | 1,383 |
| 2024 H1 | 22 | 35% | 2,147 |
| 2024 H2 | 26 | 17% | 1,870 |
| 2025 H1 | 39 | 0% | 1,132 |
| 2025 H2 | 49 | 0% | 1,020 |
| 2026 H1 | 62 | 0% | 510 |
| 2026 H2 (to July) | **110** | 0% | 143 |

Best single month: May 2021, rank 9. Most contributors: December 2023, 2,777 a
day. Its most consistent period was the second half of 2023, in the top 20 on
every single day. The first month with zero top-20 days was April 2024, five
months before the MATIC to POL rebrand, so the rebrand did not start the slide.
It did not stop it either.

## Polygon's fall is a narrative's fall

Same measure, median rank, first half of 2024 to July 2026:

| chain | from | to | places |
|---|---:|---:|---:|
| OP | 41 | 156 | +115 |
| **Polygon** | 22 | 110 | +88 |
| ARB | 23 | 80 | +57 |
| APT | 58 | 113 | +54 |
| AVAX | 22 | 31 | +9 |
| BNB | 20 | 20 | 0 |
| SOL | 3 | 2 | -1 |
| SUI | 34 | 25 | -9 |

Every Ethereum scaling chain fell, and OP fell further than Polygon. Solana and
BNB held their seats exactly. Sui rose. Whatever left Polygon left the whole
category.

## Three data decisions

Each was forced by the source, and each would have produced a wrong chart if
skipped.

**MATIC and POL are summed.** LunarCrush delisted MATIC as a coin at the
September 2024 rebrand and the conversation moved to POL. Either ticker alone
shows a cliff that month which is a ticker change, not an attention change.
MATIC still resolves at `/public/coins/MATIC/time-series/v2` with social
fields only; that is where the pre-rebrand history comes from.

**The "polygon" topic is not used.** It is a word. Its series *rises* through
2026 while MATIC+POL falls; correlation with the coin series since 2023 is
0.27. The topic belongs to geometry and a games website. See
[name-collision](../name-collision/).

**Rank by contributors, not interactions.** MATIC's 2020 interaction data has
bot spikes (2.4M interactions from 35 accounts on 2020-02-15), and
interactions per contributor jumps from 16 to 1,482 across LunarCrush's 2023
counting change, so absolute interactions are not comparable across eras.
Daily active contributors is stable across both, and rank against the market
is stable across everything.

Pegged assets and per-day name collisions are removed from the ranking
universe, as in [top-ten](../top-ten/). Peer ranks before each token's launch
are pre-launch topic noise (ARB at #156 in 2021 is the word "arb") and are
omitted from the chart.

## Limits

The ranking universe is the cached top-1,000 coins, which ends July 2026, so
"latest" here is July. The live MATIC and POL series run to today.

The universe grew from 683 coins with data in 2020 to 994 in 2026. That adds
competition at the bottom of the list, not the top, and cannot move a coin
from #13 to #110.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
LUNARCRUSH_API_KEY=... python3 pull.py   # refresh raw_coins.json
python3 polygon.py                        # out/polygon.json
python3 chart.py                          # out/polygon.svg
```
