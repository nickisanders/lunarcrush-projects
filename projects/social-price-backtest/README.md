# Social vs. Price Backtest

Does social attention lead price? This project tests the core claim behind social intelligence data: that a spike in social activity precedes price movement.

## Method in one paragraph

For the top 1,000 coins by market cap, pull full daily history from the LunarCrush time-series API (social interactions, contributors, sentiment, spam counts, and OHLC in the same rows, back to 2020). Define a spike as: interactions z-score >= 3 versus the trailing 30 days, on a day when price stayed flat (abs 24h return <= 2%), for coins with $50M+ market cap and $1M+ volume at the time. Split spikes into organic versus spam-heavy using the API's per-day spam counts, then measure BTC-adjusted forward returns at +1, +3, and +7 days against all comparable non-spike coin-days, with a calendar-month cluster bootstrap for significance.

Headline result: about 85% of social spikes are spam-heavy, and those carry no positive signal (directionally negative). The organic minority improves the odds of beating BTC over the next 3 days from 41.9% to 49.0% (p = 0.003, the only comparison that survives multiple-testing correction). See [DRAFT.md](DRAFT.md) for the full write-up.

**The threshold does the work; clearing it by more does not.** Qualifying spikes beat BTC 49.0% of the time against 41.9% (+7.1pp, p = 0.002), but within that set neither a larger spike nor a cleaner conversation predicts a better outcome: biggest z vs smallest is +5.9pp (p = 0.068) and cleanest spam vs dirtiest is +2.0pp (p = 0.991). Correlations with the 3-day excess return are +0.056 and -0.048. A tool that sorts its picks strongest-first is showing a hierarchy that is not there. `threshold_check.py` runs it.

**Buying the dip is not the mirror image.** The pump side is a clean gradient; the crash side has no structure, and the only dip bucket that clears its own interval runs against dip buyers. A modest 10-30% dip returns a median -20.4% over 90 days against -9.2% for a quiet week, a gap of -11.2pp at p < 0.001. Deeper falls are indistinguishable from doing nothing (50-70%: +3.6%, p = 0.69). What separates a crash from a pump is the median, not the spread: after a 200%+ pump the median is -43% and 45% lose another half, after a 50%+ crash the median is -2% and 21% do. `buy_the_dip.py` runs it.

**Chasing a pump is the worst trade in the dataset.** Bucketing every coin-day by how much the coin had risen over the previous seven days gives a clean monotonic gradient in what happens next. Median return over the following 90 days: -9.2% after a quiet week, -25.0% after a 50-100% run, -35.5% after 100-200%, and -42.8% after 200%+. Of the 355 resolvable 200%+ episodes, 68% were lower 90 days later and 45% had lost half. Gap versus a quiet week is -33.6pp, CI [-42.1, -16.3], p < 0.001. Consecutive qualifying days collapse to one episode, and survivorship makes the figures generous rather than harsh: coins that pumped and died out of the top 1,000 are absent. `after_the_run.py` runs it.

**Two thirds of a spike is the same crowd, louder.** Applying the interaction z-score construction to unique contributors splits the 402 organic spikes: only 33% involve an actual influx of new contributors. On a normal day the median coin draws 296 interactions per active contributor; on a spike day, 1,577. The distinction does not pay, though: the beats-BTC rate is 48.5% versus 49.3%, medians identical, and the mean-return gap is +1.0pp with a CI of [-0.4, +3.0] (p = 0.15). `crowd_growth.py` runs it.

**Sentiment is not an indicator.** Across 449,640 coin-days it is net positive 97.6% of the time, median 86 out of 100, and the monthly median has never left the 77-94 band in six and a half years. It read 90 through the COVID crash, 86 through the LUNA collapse and 86 through the failure of FTX. It also predicts nothing: quintile-sorted, the 3-day beats-BTC rate runs 41.0% to 42.4% (gap +1.4pp, p = 0.12), and its correlation with forward BTC-adjusted return is +0.005. `sentiment_check.py` runs it.

**An early lead means nothing.** Among organic spikes, those ahead of BTC after day 1 beat BTC at day 3 72.8% of the time versus 28.9% for those behind. That 44 point spread is an artifact: day 1 sits inside day 3, so the measure and the outcome share a term. Scored on the non-overlapping remainder, days 2-3 alone, the two groups come in at 46.2% and 46.3% (gap -0.1pp, p = 0.99). `day1_check.py` runs it both ways.

**The flat-price condition is the finding, not a detail.** Split all 1,218 organic spikes by what price did on the spike day: the flat-price slice beats BTC 49.0% of the time (+7.2pp, p = 0.001), while the same quality of spike on a day price had already run 5%+ comes in at 41.7% against a 41.8% baseline (-0.2pp, p = 0.85). Attention arriving after the move is a reaction to it. `price_context.py` runs the split.

**The signal is relative, not directional.** That 49% is a hit rate against BTC. Scored on whether the price simply rose, the same 402 events give 47.8% against a 46.3% baseline: +1.5 points, CI [-3.4, +6.2], p = 0.54. So an organic spike makes a coin less likely to bleed against Bitcoin. It does not make the price more likely to go up. `uprate.py` runs both metrics over the same events and the same bootstrap draws, and exists so that distinction cannot quietly go missing from a summary.

See [METHODOLOGY.md](METHODOLOGY.md) for the full design, including known biases and what this backtest cannot claim.

## Reproduce it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# ~1,000 API requests, resumable, respects rate limit headers
python3 pull.py --top 1000

# Run the analysis (writes out/summary.csv and out/events.csv)
.venv/bin/python analysis.py

# Sensitivity checks
.venv/bin/python analysis.py --z 2.5 --flat 0.03
.venv/bin/python analysis.py --spam-split 0.3 --bootstrap 0   # stricter spam cut, skip bootstrap

# Does clearing the threshold by more help? (writes out/threshold.json)
.venv/bin/python threshold_check.py

# Does buying the dip work? (writes out/buy-the-dip.json)
.venv/bin/python buy_the_dip.py

# You missed the pump. Should you buy it anyway? (writes out/after-the-run.json)
.venv/bin/python after_the_run.py

# Is a spike new people or the same people louder? (writes out/crowd-growth.json)
.venv/bin/python crowd_growth.py

# Does sentiment ever say anything but "bullish"? (writes out/sentiment.json)
.venv/bin/python sentiment_check.py

# Is the signal directional or only relative to BTC? (writes out/uprate*.csv)
.venv/bin/python uprate.py

# Does an early lead predict the rest of the move? (writes out/day1.csv)
.venv/bin/python day1_check.py

# Does the spike matter once price already moved? (writes out/price-context.csv)
.venv/bin/python price_context.py
```

Requires a LunarCrush API key in `.env` (or reuses `../altrank-movers/.env`). The pull needs a plan tier that includes the time-series endpoint.

## Out-of-sample: it does not work on stocks

The same setup and the same code, run against the full LunarCrush equities universe: 4,063 stocks, 2.6M stock-days, 9,073 organic events. That is 22 times the crypto event sample.

| Group | n | Hit rate vs the average stock |
|---|---|---|
| Ordinary stock-day | 1,719,925 | 48.7% |
| Organic attention spike | 9,073 | 49.8% |
| Spam-heavy spike | 6,146 | 49.6% |

Organic spikes beat ordinary stock-days by **+1.1 points, CI [-0.2, +2.3], p = 0.09**. The interval excludes crypto's +7.2 points several times over. And the spam split, which is the entire source of the crypto signal, does nothing here: organic 49.8% versus spam-heavy 49.6%.

Broken out by size, in case the effect hid in the retail-driven corner of the market:

| Market cap band | Events | Effect |
|---|---|---|
| Small (<$2B) | 623 | +1.0 pts |
| Mid ($2-10B) | 3,015 | +1.1 pts |
| Large ($10-100B) | 3,454 | +0.3 pts |
| Mega (>$100B) | 1,313 | +1.8 pts |

It does not. Small caps look like everything else, and the largest reading sits in mega caps, which is the opposite of what a retail-attention story would predict and is almost certainly noise across four bands.

So the finding is specific to crypto, not a general property of attention. The plausible mechanism: equities have analysts, earnings calendars, institutional coverage and market makers, so by the time retail attention spikes the information is priced. Crypto has none of that machinery, which leaves social attention closer to the leading edge of information.

Three adjustments were needed and each is in the code: weekend rows carry the Friday close and would pass a "price is flat" filter for free, so only trading days count; the stocks feed has no `posts_created`, so spam share uses `posts_active` as the denominator and is not strictly comparable to the crypto threshold; and with no BTC to measure against, excess return is against the equal-weighted mean of eligible stocks that day.

Two process notes worth recording. At 69 stocks this test showed a *significant inversion* (-6.0 points, p = 0.033); at 385 stocks it read -0.1; at 4,063 it reads +1.1. All three are consistent with a true effect of about zero, and only the first looked publishable. Partial data has now produced a convincing-looking artifact twice in this repo.
