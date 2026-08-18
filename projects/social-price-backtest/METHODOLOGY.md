# Methodology

## Question

When a coin's social activity spikes while its price has not yet moved, what happens to price over the next 1, 3, and 7 days, compared to ordinary days?

## Data

- Source: LunarCrush `/public/coins/:id/time-series/v2`, daily bucket, full history (earliest data 2020-01-01).
- Universe: top 1,000 coins by market cap rank as of the pull date.
- Fields used: `interactions`, `posts_created`, `spam`, `close`, `market_cap`.
- Deliberately unused for the signal: `alt_rank`, `galaxy_score`, `sentiment`. AltRank and Galaxy Score are composites that already include price, so using them to predict price would be circular. Sentiment is reserved for a follow-up cut.

## Event definition

A coin-day is an event when all of the following hold:

1. Social spike: z-score of log(1 + interactions) versus the trailing 30 days (excluding the current day) is at least 3.
2. Price flat: absolute close-to-close return that day is at most 2%. This isolates "social moved first" from "everyone is talking about the pump."
3. Eligible: market cap at least $50M on that day, $1M+ daily volume, trailing median interactions at least 2,000.

Spike days are split by the spam share of created posts: organic (spam <= 50%) versus spam-heavy (spam > 50%). The baseline is every eligible coin-day without a spike. Forward returns are winsorized at the 1st/99th percentile of the eligible set, since raw crypto price data contains redenomination and near-zero-price glitches that otherwise destroy means.

## Outcome measures

Close-to-close forward returns at +1d, +3d, +7d:

- Raw.
- BTC-adjusted (minus BTC's return over the same window), since crypto returns share a large market factor and event clustering in bull weeks would otherwise flatter the signal.
- Hit rate: share of events with positive BTC-adjusted return.
- Up-rate: share of events with positive *raw* return. This is the directional
  question and it is deliberately kept separate from the hit rate, because the
  headline result is a hit rate and reads as a directional claim if you are not
  careful. `uprate.py` runs both metrics over the same events and the same
  bootstrap draws so the two gaps are directly comparable. They are not: the
  +3d beats-BTC gap is +7.2pp (p = 0.003) and the +3d up-rate gap is +1.5pp
  (p = 0.54). The signal is relative strength, not direction.

## Significance

Group-vs-baseline differences (mean BTC-adjusted return and hit rate, per horizon) are tested with a cluster bootstrap on calendar-month blocks: months are resampled with replacement and the difference recomputed 2,000 times. Month-level clustering respects both the overlap of multi-day forward windows and the cross-sectional correlation of coins within the same market regime, which naive per-observation tests ignore. Reported p-values are two-sided; with 12 comparisons, a Bonferroni-adjusted threshold is roughly p < 0.004.

## Known limitations

1. Survivorship bias. The universe is today's top 1,000, which over-represents coins that survived and grew. The per-day market cap filter mitigates this at event time (events only count when the coin was already at $50M+ on that day) but cannot fully cure universe selection. A fair reading: results describe "coins that were at some point large," not "all coins ever."
2. Retroactive data revisions. LunarCrush reprocesses historical time series (their Changes endpoint documents this). Interaction counts and especially spam classification for past dates may be cleaner than what was observable live. Any live implementation of this signal should expect noisier inputs than the backtest saw.
3. Close-to-close returns understate execution reality. No fees, slippage, or fill assumptions. This is a data study, not a strategy P&L.
4. Multiple comparisons. Thresholds (z >= 3, 2% flat, $50M) were chosen a priori and reported alongside sensitivity runs at other thresholds, but any backtest with tunable knobs deserves skepticism. The sensitivity table in the write-up shows how conclusions move with the knobs.
5. Daily granularity. A spike and a price move inside the same 24h bucket are invisible to this design. An hourly-bucket follow-up can resolve intraday lead-lag.

## What this can and cannot claim

If event forward returns beat baseline after BTC adjustment, that supports "social activity contains information not yet in price" at daily resolution, for large coins, in-sample. It does not prove a tradeable edge, and it specifically does not support a directional claim: the same events show no significant lift in the raw up-rate, so the finding is about performance relative to BTC and must be stated that way. If they do not beat baseline, that is evidence against the simplest version of the social-leads-price claim, within this design's limits.
