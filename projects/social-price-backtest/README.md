# Social vs. Price Backtest

Does social attention lead price? This project tests the core claim behind social intelligence data: that a spike in social activity precedes price movement.

## Method in one paragraph

For the top 1,000 coins by market cap, pull full daily history from the LunarCrush time-series API (social interactions, contributors, sentiment, spam counts, and OHLC in the same rows, back to 2020). Define a spike as: interactions z-score >= 3 versus the trailing 30 days, on a day when price stayed flat (abs 24h return <= 2%), for coins with $50M+ market cap and $1M+ volume at the time. Split spikes into organic versus spam-heavy using the API's per-day spam counts, then measure BTC-adjusted forward returns at +1, +3, and +7 days against all comparable non-spike coin-days, with a calendar-month cluster bootstrap for significance.

Headline result: about 85% of social spikes are spam-heavy, and those carry no positive signal (directionally negative). The organic minority improves the odds of beating BTC over the next 3 days from 41.9% to 49.0% (p = 0.003, the only comparison that survives multiple-testing correction). See [DRAFT.md](DRAFT.md) for the full write-up.

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

# Is the signal directional or only relative to BTC? (writes out/uprate*.csv)
.venv/bin/python uprate.py
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
