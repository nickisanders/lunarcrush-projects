# Attention Cascade

Crypto folklore says attention flows downhill: Bitcoin lights up, then the majors a few days later, then large alts, then the long tail. If that were true it would be tradeable, because you could watch the tier above yours.

It isn't true. There is no cascade.

## Result

Attention moves across tiers **the same day**, with no measurable lead or lag between them.

| Pair | Peak correlation at | Lead-lag asymmetry | p |
|---|---|---|---|
| BTC → majors | k = 0 (+0.32) | +0.001 | 0.87 |
| BTC → large alts | k = -1 | +0.019 | 0.49 |
| BTC → mid alts | k = +1 | -0.045 | 0.06 |
| BTC → small alts | k = 0 | +0.013 | 0.47 |
| majors → large alts | k = +1 | -0.002 | 0.98 |
| majors → mid alts | k = +1 | -0.037 | 0.10 |
| large alts → mid alts | k = -7 | -0.013 | 0.93 |
| mid alts → small alts | k = 0 | -0.041 | 0.10 |

Every peak sits at lag 0 or ±1 day, never at the multi-day lag the folklore implies. The asymmetry measure (correlation at positive lags minus negative lags, which is what a directional cascade would produce) is near zero for every pair and significant for none. Several of the small readings are actually *negative*, meaning the lower tier moved marginally first, which is the opposite of the story.

The one strong relationship is BTC and the majors at lag 0 (+0.32). They move together, within the same day, not in sequence.

## Two methodology notes worth reading

**The lag-0 column is contaminated and should not be interpreted.** Removing the cross-tier mean to strip out market-wide news days forces the residuals to sum to zero each day, which manufactures negative correlation between every pair at lag 0. With five tiers that is roughly -0.25 before any real relationship exists. It explains the large negative same-day figures against the small-alts tier.

**Leave-one-out demeaning does not fix it, and I checked.** Subtracting the mean of the *other* tiers produces exactly `n/(n-1)` times the plain demeaned residual, and correlation is scale invariant, so the output is byte-identical. It looked like a fix and was mathematically vacuous.

What the constraint does not affect is the asymmetry between positive and negative lags, since it applies symmetrically to each day. That is why the verdict rests on the asymmetry test, and why the whole analysis is also run with no common-factor removal at all as a robustness check. The conclusion is identical both ways: largest asymmetry anywhere is +0.043.

## Method

- Tiers by same-day market cap rank, not today's rank, so a coin that was a major in 2021 and a minnow in 2026 counts correctly in each period: BTC alone, majors (2-10), large alts (11-50), mid alts (51-200), small alts (201+).
- Eligibility: $50M market cap, $1M daily volume, nonzero interactions.
- Series are day-over-day log changes, since attention levels drift upward as the market grows and levels-based tests sort by calendar (see [attention-breadth](../attention-breadth/)).
- Significance by month-block bootstrap, since daily observations of a multi-day relationship overlap.

## Reproduce

Needs the backtest's cached data (`../social-price-backtest/data/raw`):

```bash
../social-price-backtest/.venv/bin/python analysis.py
```

## Does the cascade show up in price instead?

Attention arriving simultaneously does not by itself rule out the tradeable version of the myth: maybe Bitcoin's conversation spiking today still precedes altcoins outperforming a few days later, even if alt *attention* did not lag. `price_effect.py` tests that directly, across 39 combinations of tier, target and horizon.

Nothing. Every correlation falls between -0.035 and +0.035, every confidence interval spans zero, and none of the 39 tests clears the Bonferroni threshold (p < 0.0013).

The most direct test is the one people actually care about, whether BTC attention predicts alts *beating* BTC, which is what "alt season" means:

| Target tier | +1d | +3d | +7d |
|---|---|---|---|
| majors | +0.008 | +0.014 | +0.015 |
| large alts | +0.021 | +0.019 | +0.003 |
| mid alts | +0.002 | +0.004 | -0.007 |
| small alts | +0.005 | +0.005 | +0.001 |

Twelve readings, none distinguishable from zero, on 1,701 days.

One pattern is worth mentioning without overselling it. In the test of BTC attention against lower tiers' raw returns, all twelve readings came out mildly negative (-0.011 to -0.035). A run of twelve same-signed results looks striking, but these tests are not independent (overlapping horizons, correlated tiers), so the intuitive "one in four thousand" reading is wrong. Individually none is significant and every interval includes zero. It is consistent with Bitcoin's conversation spiking during market stress rather than before rallies, which would be a reasonable hypothesis for someone to test properly. It is not a finding here.

So the cascade fails twice: attention does not move down the tiers, and it does not move price down them either.
