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
