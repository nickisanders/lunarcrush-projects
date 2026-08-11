# Social vs. Price Backtest

Does social attention lead price? This project tests the core claim behind social intelligence data: that a spike in social activity precedes price movement.

## Method in one paragraph

For the top 1,000 coins by market cap, pull full daily history from the LunarCrush time-series API (social interactions, contributors, sentiment, spam counts, and OHLC in the same rows, back to 2020). Define a spike as: interactions z-score >= 3 versus the trailing 30 days, on a day when price stayed flat (abs 24h return <= 2%), for coins with $50M+ market cap and $1M+ volume at the time. Split spikes into organic versus spam-heavy using the API's per-day spam counts, then measure BTC-adjusted forward returns at +1, +3, and +7 days against all comparable non-spike coin-days, with a calendar-month cluster bootstrap for significance.

Headline result: about 85% of social spikes are spam-heavy, and those carry no positive signal (directionally negative). The organic minority improves the odds of beating BTC over the next 3 days from 41.9% to 49.0% (p = 0.003, the only comparison that survives multiple-testing correction). See [DRAFT.md](DRAFT.md) for the full write-up.

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
```

Requires a LunarCrush API key in `.env` (or reuses `../altrank-movers/.env`). The pull needs a plan tier that includes the time-series endpoint.

## Out-of-sample: it does not work on stocks

The same setup, the same code, run against 385 equities over the same period (`pull_stocks.py`, `stocks_check.py`):

| Group | n | Hit rate vs the average stock |
|---|---|---|
| Ordinary stock-day | 249,677 | 48.8% |
| Organic attention spike | 1,455 | 48.7% |
| Spam-heavy spike | 1,093 | 48.8% |

Difference between organic spikes and ordinary days: **-0.1 points, p = 0.998**, with a confidence interval of [-2.5, +2.2]. That rules out anything close to the +7.2 point effect measured in crypto. The spam split, which is what carries the crypto signal, does nothing at all here.

So the finding is about crypto specifically, not about attention in general. The plausible reason: equities have analysts, earnings calendars, institutional coverage and market makers, so by the time retail attention spikes the information is already priced. Crypto has none of that machinery, which leaves social attention closer to the leading edge of information.

Three adjustments were needed and each is in the code: weekend rows carry the Friday close and would pass a "price is flat" filter for free, so only trading days count; the stocks feed has no `posts_created`, so spam share uses `posts_active` as the denominator and is not strictly comparable to the crypto threshold; and with no BTC to measure against, excess return is against the equal-weighted mean of eligible stocks that day.

One process note worth recording: at 69 stocks this test showed a *significant inversion* (-6.0 points, p = 0.033). It was noise, and it disappeared entirely at full sample. Partial data produced a publishable-looking result twice in this repo now.
