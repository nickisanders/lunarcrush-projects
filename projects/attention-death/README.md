# Attention Death, and the Altcoin Base Rate

## What this started as

Every other study here looks at attention spiking. This looked at the opposite: coins whose conversation collapses while their market cap is still intact. A death event is a coin whose interactions fall to 35% or less of its own trailing 90-day median, sustained five days running, on a coin with real size and a real conversation to lose.

7,067 such events across 456 coins. And they tell you nothing.

| Group | n | median vs BTC, 90d |
|---|---|---|
| Attention death | 7,067 | -17.11% |
| Everything else | 403,487 | -19.88% |

Death events actually did marginally *better* (+2.77% at 90 days, p = 0.13), which is not significant. So a dying community is not a sell signal. Whatever kills a coin's conversation does not appear to be what kills its price.

## The finding that was hiding in the comparison group

Look at that second row again. The typical eligible altcoin-day loses roughly 20% against Bitcoin over 90 days. That number was the control, not the result, and it is far more interesting than what was being tested.

Measured properly across 661,800 coin-days on 838 coins, all with $50M+ market cap and $1M+ daily volume:

| Hold for | Beats BTC | Median vs BTC | Median raw return |
|---|---|---|---|
| 1 day | 44.7% | -0.4% | -0.1% |
| 1 week | 40.4% | -1.9% | -0.6% |
| 1 month | 34.9% | -6.7% | -4.5% |
| 3 months | 28.2% | -17.2% | -12.9% |
| 6 months | 23.1% | -30.2% | -24.1% |

Pick a liquid, real altcoin at a random moment and hold it six months, and there is a 77% chance you would have done better simply holding Bitcoin, with a median shortfall of 30%.

Size helps but does not rescue you, and no band gets close to even:

| Market cap | Beats BTC over 90d | Median |
|---|---|---|
| $50-250M | 27.4% | -18.2% |
| $250M-1B | 26.8% | -19.1% |
| $1-10B | 30.8% | -14.0% |
| $10B+ | 35.6% | -7.8% |

It is not one bad cycle either. Every era is under half: 37.2% in 2020-2022, 23.3% in 2023-2025, 32.2% in 2026.

**And every number here understates the problem.** The universe is coins that survived to be in today's top 1,000. Coins that went to zero are not in the sample.

## Why this matters for the rest of this repo

It reframes every edge measured here. The [organic spike setup](../organic-watchlist/) beats BTC 49% of the time against a baseline of 42%. Both numbers sit below a coin flip, and now it is clear why: the baseline experience of holding an altcoin is losing to Bitcoin, and a good signal moves you from losing badly to losing slightly less often. That is what an edge looks like in this asset class. Anyone quoting a win rate against a "market" benchmark without stating the base rate is hiding the most important number.

## Reproduce

```bash
../social-price-backtest/.venv/bin/python analysis.py     # the death-signal null
../social-price-backtest/.venv/bin/python base_rate.py    # the base rate
```
