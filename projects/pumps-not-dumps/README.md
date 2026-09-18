# pumps-not-dumps

Crypto talks about pumps, not dumps.

Days when a coin rises 5%+ and days when it falls 5%+ are equally common:
12.2% and 12.6% of eligible coin-days. The crowd does not treat them
equally.

## The chance a price move triggers a spike

P(attention spike | what the price did that day), 452,402 coin-days, 2020 to
2026:

| move | days up | days down | P(spike / up) | P(spike / down) | ratio |
|---|---:|---:|---:|---:|---:|
| ±5% | 55,107 | 56,930 | 3.86% | 1.63% | 2.4x |
| ±10% | 19,111 | 13,325 | 6.81% | 2.20% | 3.1x |
| ±20% | 4,710 | 1,365 | 13.42% | 4.10% | 3.3x |

Flat day (within ±2%): 1.34%.

A coin falling 5% is barely more interesting to the crowd than a coin doing
nothing. A coin rising 5% is 2.4x as interesting as one falling 5%. Month-block
bootstrap 95% CI on the 5% ratio: [2.05, 2.69].

The asymmetry grows with the size of the move. A 20% pump has a 13% chance of
a spike; a 20% dump has a 4% chance.

## What spike days look like

| | up 5%+ | in between | down 5%+ |
|---|---:|---:|---:|
| all coin-days | 12% | 75% | 13% |
| spike days | 27% | 61% | 12% |

Green candles are over-represented among spike days by 2.2x. Red candles are
represented at exactly their base rate.

## Why this is the right way to measure it

The measure is P(spike | move), read off every eligible coin-day. It does not
depend on how spikes are distributed across years, on how many coins are
covered, or on LunarCrush's 2023 change to interaction counting, because a
spike is defined within each coin against its own trailing 30 days.

The inverse framing, "what share of spikes land on up days", is shown in the
composition table and gives the same answer, but it is sensitive to how many
flat-day spikes there are.

## What this says about the backtest

[social-price-backtest](../social-price-backtest/) found the only edge in
attention is a spike on a flat price. This is a partial explanation of why:
the spikes that land on big up days are the crowd noticing a pump, and there
are a lot of them. The spikes on flat days are something else.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 asymmetry.py   # out/asymmetry.json
python3 chart.py       # out/asymmetry.svg
```
