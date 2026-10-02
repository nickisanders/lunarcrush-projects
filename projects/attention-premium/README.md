# attention-premium

Are coins talked about more than they are worth punished for it?

LunarCrush reports two shares per coin: social dominance, its slice of all
crypto conversation, and market dominance, its slice of all crypto market cap.
The ratio is an attention premium. This tests whether a high premium predicts
underperformance.

The answer is no. Getting to no took throwing out a result that looked strong.

## The result that looked strong

Ranked within market-cap decile on each day, so a $60M coin is only compared
against other $60M coins that same day. 600,426 coin-days, 2020 to 2026, forward
returns BTC-adjusted and winsorized, month-block cluster bootstrap.

| bucket | median premium | median market cap | n |
|---|---:|---:|---:|
| quietest | 0.7x | $278M | 127,992 |
| quiet | 2.8x | $275M | 116,105 |
| middle | 5.3x | $273M | 116,069 |
| loud | 8.9x | $273M | 116,105 |
| loudest | 19.1x | $272M | 124,155 |

Size control worked: median market cap is within $6M across all five buckets.
The result was monotonic, and quietest minus loudest came to **+3.1pp at +7d,
p = 0.004**.

## Six checks it passed

| check | result |
|---|---|
| 2020-2022 only | +1.6pp, p = 0.018 |
| 2023-2026 only | +3.6pp, p = 0.010 |
| drop the 20 most-present symbols | +3.2pp, p = 0.004 |
| larger half by market cap | +4.7pp, p < 0.001 |
| smaller half by market cap | +1.5pp, p = 0.146 |
| volume floor raised 10x | +3.3pp, p = 0.002 |

Stronger in the larger half, which appeared to rule out an illiquidity story.
At this point the finding looked ready.

## What was actually in the bucket

The quietest bucket was 29.6% stablecoins and wrapped assets.

| part | share of bucket | beat BTC at +7d |
|---|---:|---:|
| stablecoins | 18.2% | 47.9% |
| wrapped and staked | 11.4% | 43.9% |
| actual coins | 70.4% | 40.6% |
| **whole bucket** | | **42.3%** |
| loudest bucket | | 39.2% |

Nobody discusses USDT, and a wrapper's conversation belongs to the asset it
wraps, so both sort into the quiet bucket by construction. A stablecoin then
beats Bitcoin on the BTC-adjusted measure every day Bitcoin falls. In the
contaminated bucket, 26.5% of coin-days moved less than 0.5%, against 8.7% in
the loudest.

The entire spread was those two groups. Real quiet coins beat BTC 40.6% of the
time against the loudest bucket's 39.2%, a gap of 1.4pp.

## The result after cleaning

Two exclusions, applied before any ranking. Pegged assets are detected by
behaviour rather than a hand-kept list: median absolute daily return under 1%
across the coin's history, which caught 114 symbols. Wrapped and liquid-staked
assets are excluded by name.

| comparison | +7d | 95% CI | p |
|---|---:|---|---:|
| quietest vs middle | +1.6pp | [+0.3, +2.9] | 0.012 |
| quiet vs middle | +0.4pp | [-0.3, +1.1] | 0.182 |
| loud vs middle | -0.1pp | [-0.7, +0.5] | 0.814 |
| loudest vs middle | +0.2pp | [-0.8, +1.2] | 0.742 |
| **quietest minus loudest** | **+1.5pp** | [-0.0, +3.0] | **0.053** |

Two conclusions:

- **There is no hype penalty.** The loudest coins are indistinguishable from
  the middle at every horizon. Whatever remains sits on the quiet side.
- **The residual does not survive.** +1.6pp at p = 0.012 is one of 12
  comparisons; a Bonferroni threshold here is 0.0042.

## What this is really about

Every robustness check in the table above ran on the same contaminated sample,
and every one passed. Splitting by era, dropping frequent symbols, raising the
volume floor and controlling for size all test whether a result is *stable*.
None of them test whether the thing being measured is what you think it is.

A contaminated sample is stably contaminated.

The check that killed it was not statistical. It was printing the ten most
common symbols in each bucket and reading them.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 premium.py       # the original, contaminated result
python3 robustness.py    # the six checks it passed
python3 clean.py         # pegged and wrapped removed, and the null
python3 chart.py         # out/premium.svg
LUNARCRUSH_API_KEY=... python3 today.py   # today's loudest and quietest names
```

`premium.py` and `robustness.py` are kept deliberately. The wrong version is
part of the record.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
