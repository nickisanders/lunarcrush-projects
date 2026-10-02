# weekend-crowd

Crypto never closes. The people talking about it do.

Markets run 24/7, so a Saturday and a Tuesday are the same trading environment.
The conversation is not. This measures the gap, finds a real defect in the
standard attention-spike detector, fixes it, and then shows the fix was worth
nothing.

## 1. The weekend crowd is smaller

Median interactions per coin-day, 1,000 coins, 2020-01-01 to 2026-07-29:

| day | median interactions | vs weekday mean |
|---|---:|---:|
| Mon | 8,766 | -1.0% |
| Tue | 8,930 | +0.8% |
| Wed | 8,892 | +0.4% |
| Thu | 8,859 | 0.0% |
| Fri | 8,847 | -0.1% |
| **Sat** | **8,291** | **-6.4%** |
| **Sun** | **8,154** | **-8.0%** |

Weekend conversation runs 7.2% below weekday conversation.

## 2. A 7% smaller crowd produces 19.5% fewer spikes

The standard detector takes log interactions, subtracts a trailing 30-day mean
and divides by the trailing standard deviation. That window mixes weekdays and
weekends. Every Saturday and Sunday therefore starts below the mean it is
scored against and needs a larger real jump to clear the same threshold. The
weekly seasonal also inflates the denominator, raising the bar on every day.

Share of eligible coin-days registering a spike at z >= 3:

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---:|---:|---:|---:|---:|---:|---:|
| 1.90% | 1.83% | 1.90% | 1.76% | 1.80% | **1.51%** | **1.45%** |

Weekday 1.84%, weekend 1.48%. A 7.2% smaller crowd yields 19.5% fewer detected
events. The distortion is nearly three times the size of the thing causing it.

`projects/organic-watchlist/src/watchlist.ts` computes exactly this z-score, so
the live scanner has this blind spot.

## 3. The fix works

`deseason.py` subtracts each coin's own day-of-week offset before scoring,
estimated on a trailing 8-week window of the same weekday, shifted so it never
sees today. Using the coin's own history rather than a market-wide constant
keeps coins with genuinely different weekly rhythms from being forced onto one
shape.

| | weekend deficit | max-min spread across the week |
|---|---:|---:|
| standard z | -19.5% | 26.2% of mean |
| deseasoned z | **+1.3%** | **11.7% of mean** |

Weekend events found: 1,885 to 2,128, up 12.9%. Detection is now flat across
the week.

## 4. The fix is worth nothing

The only question that matters is whether the recovered events behave like real
ones. Scored against the same baseline, with the same organic-spike definition,
BTC adjustment and month-block bootstrap as the main backtest:

| group | n | beats BTC at +3d | 95% CI | p |
|---|---:|---:|---|---:|
| kept (both scorers agree) | 294 | **+7.8pp** | [+2.4, +12.8] | **0.005** |
| recovered (deseasoned only) | 68 | -0.7pp | [-12.3, +10.3] | 0.877 |
| dropped (standard only) | 92 | +3.8pp | [-6.3, +12.3] | 0.425 |

The events the blind spot was hiding are the ones that were never worth having.
The correction is real, the recovered events are marginal, and marginal events
carry no edge.

68 events cannot rule out a modest effect. What the interval does rule out is
the recovered events carrying anything like the +7.8pp the agreed events carry.

## 5. Weekend spikes themselves are fine

Separately: an organic spike that clears the bar on a weekend performs like one
that clears it on a weekday. Head-to-head, not read off two separate
comparisons against baseline:

| horizon | weekend minus weekday | 95% CI | p |
|---|---:|---|---:|
| +1d | +6.4pp | [-7.6, +20.6] | 0.392 |
| +3d | -0.6pp | [-12.3, +10.5] | 0.948 |
| +7d | -2.4pp | [-15.1, +9.8] | 0.707 |

87 weekend events, so this is underpowered: it rules out a difference larger
than roughly 12pp, not a smaller one. There is no reason to discount a weekend
signal, and no evidence weekends are noisier once an event clears the bar.

## What this changes

Nothing, deliberately. The live scanner keeps its plain z-score. Knowing a
defect is real is not sufficient reason to fix it; the fix has to buy something,
and this one does not.

## A data break worth knowing about

LunarCrush changed how `spam` is counted during 2023. The share of rows where
`spam` exceeds `posts_created` jumps from 4.7% in 2022 to 55.5% in 2023 and
stays high. Any series built from the spam field is comparing two different
measurement regimes across that boundary. Two candidate findings were discarded
here for that reason: a market-wide "bot share" trend, and a top-10 attention
concentration trend, both of which break at exactly 2023-01-01 rather than at
anything happening in crypto.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 weekend.py       # the crowd gap, spike rates, weekend vs weekday edge
python3 deseason.py      # the seasonal correction and what it recovers
python3 recovered.py     # whether the recovered events carry the edge
python3 chart.py         # out/weekend.svg
```

Reads the cached daily history in `../social-price-backtest/data/raw`.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
