# loud-dumps

A dump people talk about keeps falling. A dump nobody mentions recovers.

[pumps-not-dumps](../pumps-not-dumps/) found a 10% drop triggers an
attention spike only 2.2% of the time. This asks what happens next in that
2.2%.

## After a 10%+ dump

Every eligible coin-day where the price fell 10% or more, split by whether
the day also carried an attention spike. Beats-BTC rate over the following
days:

| | +1d | +3d | +7d | median BTC-adj +7d |
|---|---:|---:|---:|---:|
| loud dump (n=293) | 38.2% | 38.9% | 36.9% | -3.9% |
| quiet dump (n=13,015) | 50.8% | 49.2% | 43.1% | -2.0% |
| **loud minus quiet** | **-12.6pp** | **-10.3pp** | -6.3pp | |
| p | <0.001 | 0.002 | 0.051 | |

A quiet 10% dump is followed by roughly coin-flip odds against Bitcoin, which
is better than an ordinary coin-day's 42%. A loud one is followed by 39%.

## After a 10%+ pump, for contrast

| | +1d | +3d | +7d |
|---|---:|---:|---:|
| loud pump (n=1,297) | 37.9% | 38.6% | 37.5% |
| quiet pump (n=17,771) | 41.6% | 39.6% | 38.0% |
| loud minus quiet | -3.7pp | -1.0pp | -0.5pp |
| p | 0.044 | 0.538 | 0.709 |

Whether the crowd noticed a pump makes almost no difference to what follows.
Whether it noticed a dump makes a large one.

## Where the effect lives

Loud minus quiet dump, beats-BTC at +3d:

| subset | loud n | diff | 95% CI | p |
|---|---:|---:|---|---:|
| smaller half of coins, under $279M | 175 | -15.4pp | [-22.1, -8.3] | <0.001 |
| larger half, over $279M | 118 | -2.7pp | [-15.1, +8.6] | 0.642 |
| 2023 to 2026 | 271 | -10.7pp | [-17.2, -3.7] | 0.008 |
| 2020 to 2022 | 22 | -0.9pp | [-21.2, +23.7] | 0.926 |
| 20%+ dumps | 56 | -15.2pp | [-29.5, +1.1] | 0.068 |
| 5%+ dumps | 930 | -2.3pp | [-6.0, +1.0] | 0.186 |
| organic spikes only (spam ≤ 50%) | 54 | -8.4pp | [-22.3, +5.3] | 0.228 |

The effect is concentrated in the smaller half of eligible coins and is not
detectable in the larger half. It is present in 2023 to 2026, where 92% of
loud dumps occur; 2020 to 2022 has 22 events and says nothing either way. It
weakens at 5% (a 5% move is often just the market) and is directionally
stronger at 20% but underpowered there.

237 of the 293 loud dumps carry a spam-heavy spike. The 54 organic ones point
the same way at -8.4pp but the sample is too small to confirm.

## Reading it

A coin falling 10% on a day nobody is talking about it is usually falling
with the market, and it tends to bounce with the market. A coin falling 10%
on a day everyone is talking about it usually has a reason: an exploit, a
delisting, an unlock, a founder doing something. The reason does not resolve
in a day, and the price keeps going.

That reading fits the size split. A $100M coin with a loud dump has a
coin-specific problem. A $5B coin with a loud dump is more often just in the
news.

## Method

Spike: interactions 3+ standard deviations above the coin's own trailing 30
days, the backtest definition. Forward returns BTC-adjusted and winsorized at
the 1st/99th percentile. Significance from the calendar-month cluster
bootstrap in [social-price-backtest](../social-price-backtest/). Eligible:
$50M+ market cap, $1M+ volume, trailing median interactions ≥ 2,000, BTC
excluded.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 loud_dumps.py   # out/loud_dumps.json
python3 chart.py        # out/loud_dumps.svg
```
