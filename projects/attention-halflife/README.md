# Attention Half-Life

How fast do crypto social spikes decay, and does authenticity matter? This study measures the post-spike trajectory of every clean spike in the [backtest](../social-price-backtest/) dataset: 5,255 spikes across 997 coins, 2020 to 2026.

## Result: decay does not distinguish organic from spam-heavy spikes, at daily or hourly resolution

At daily resolution, crypto attention has a one-day half-life regardless of who's talking. The hourly follow-up (2,372 spike windows: every organic spike plus a 2x spam sample) sharpens that further: median half-life from the peak hour is one hour for both groups, and roughly 90% of spikes are half-dead within 6 hours of peaking. Post-peak cliff and 24h retention show no significant group difference either.

The one suggestive hourly difference runs opposite to the decay hypothesis: organic spikes are burstier, concentrating a larger share of spike-day interactions in their top 3 hours (37% vs 31% median, p = 0.02 by month-cluster bootstrap, uncorrected for the multiple comparisons across these studies). A plausible read: real crowds react to events simultaneously, while scheduled campaigns spread posts across the day. Treat as a hypothesis for future detector work, not a confirmed signal.

- Median spike loses about two thirds of its height in one day (organic and spam-heavy alike)
- 83% of spikes are below half strength by day two
- Roughly 1% are still elevated at day 14
- Spikes leave a residue: the post-spike attention floor settles ~30% above the pre-spike baseline, identically for both groups
- No comparison (retention at 1/3/7 days, half-life, baseline residue) is statistically distinguishable between organic and spam-heavy spikes, by month-cluster bootstrap, including with sharper group cuts (spam <= 20% vs >= 80%)

At this resolution, what distinguishes manufactured hype is not how it dies. Everything dies in about a day. The distinguishing signals remain composition (who is talking: spam share, creator concentration) and price response (the backtest: organic spikes shift the odds of beating BTC, spam spikes don't).

## Method

For each spike day (interactions z >= 3 vs the coin's trailing 30 days; coin at $50M+ market cap, $1M+ volume, established social baseline):

- baseline = trailing 30-day median interactions
- retention at day k = (interactions[t+k] - baseline) / (interactions[t] - baseline), floored at 0
- half-life = first day retention falls below 50% (censored at 14 days)
- baseline residue = median interactions over days 8..14, relative to the pre-spike baseline

Spikes followed by another spike within 7 days are excluded (contaminated decay window), as are spikes without 14 days of subsequent history. Groups split by spam share of created posts at 50% (sensitivity cut at 20%/80%).

## Hourly follow-up

```bash
../social-price-backtest/.venv/bin/python pull_hourly.py   # ~2,400 API requests, resumable
../social-price-backtest/.venv/bin/python hourly_analysis.py
```

## Reproduce

Requires the backtest's cached data (`../social-price-backtest/data/raw`, ~1,000 API requests to rebuild) and its venv:

```bash
../social-price-backtest/.venv/bin/python analysis.py
```

Writes `out/spikes.csv`, `out/summary.csv`, `out/curves.json`, and the decay-curve chart source.

## Caveats

Daily buckets hide intraday decay shape. The overlap exclusion removes sustained multi-spike attention waves, which is conservative for measuring single-spike decay but means "campaigns that keep spending" are underrepresented. Spam labels are LunarCrush's classification, reprocessed historically. And the one-day half-life is a crypto-social fact, not a universal one; other domains likely differ.
