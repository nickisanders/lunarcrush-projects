# Attention Breadth Index

How many coins is crypto actually talking about?

Equity markets have had breadth indicators for a century. Crypto attention has none. This builds one: for each day, take every eligible coin's share of that day's total social interactions, compute the Herfindahl index, and report its reciprocal — the **effective number of coins**. If attention were split evenly among N coins, the index reads N.

It rarely clears 8. As of the last full day measured it sits at **4.9**, with Bitcoin alone taking 41% of all crypto social attention and the top ten taking 82%.

## Result: it describes, it does not predict

The obvious hypothesis was that widening breadth precedes alt-season. It doesn't. After correcting for the confound below, forward alt-minus-BTC returns are statistically indistinguishable between the narrowest and widest quintiles (30-day difference -0.55%, p = 0.79 by month-cluster bootstrap; 7-day -0.83%, p = 0.22), and the quintile ordering is noise.

Treat this as a descriptive gauge of market attention structure, not a trading signal.

## The confound worth reading about

The first version of this analysis produced a beautiful result: a perfectly monotonic relationship across quintiles, narrow breadth predicting +2.0% alt outperformance and wide breadth -6.2%, with p = 0.001.

It was entirely an artifact. The eligible universe grows over time, so the raw index drifts upward, and its quintiles collapse onto calendar eras — of the days sorted into "narrow", 465 fell in 2020-2022 and 2 fell later; of the "wide" days, 469 fell in 2023-2025 and none earlier. The test wasn't comparing breadth regimes, it was comparing 2021 to 2024.

The fix is to rank each day's breadth against its own trailing year rather than against all history. That balances the eras (178 narrow / 174 wide in 2020-2022; 180 / 259 in 2023-2025) and the signal disappears completely.

Any indicator with a secular trend will do this to you. Quintiles of a drifting series are a time machine, not a signal.

## Method

- Universe: coins above $50M market cap and $1M daily volume with nonzero interactions, at least 20 per day.
- Breadth: `1 / sum(share_i^2)` over each day's interaction shares.
- Detrended breadth: percentile rank of the day's value within its trailing 365 days (minimum 180).
- Outcome: equal-weighted forward return of eligible non-BTC coins minus BTC's, at 7 and 30 days, winsorized at the 1st/99th percentile.
- Significance: month-cluster bootstrap, since daily observations of a 30-day forward window overlap almost completely.

## Caveats

Survivorship: the universe is the top 1,000 coins as of the pull date, so historical breadth is computed over coins that survived. This inflates the early-period index (dead coins that once held attention are missing) and is a further reason the raw level shouldn't be compared across eras.

## Reproduce

Needs the backtest's cached data (`../social-price-backtest/data/raw`):

```bash
../social-price-backtest/.venv/bin/python analysis.py --json out/breadth.json
```
