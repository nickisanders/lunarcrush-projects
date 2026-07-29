# Social vs. Price Backtest

Does social attention lead price? This project tests the core claim behind social intelligence data: that a spike in social activity precedes price movement.

## Method in one paragraph

For the top 1,000 coins by market cap, pull full daily history from the LunarCrush time-series API (social interactions, contributors, sentiment, spam counts, and OHLC in the same rows, back to 2020). Define an event as: interactions z-score >= 3 versus the trailing 30 days, on a day when price stayed flat (abs 24h return <= 2%). Then measure forward returns at +1, +3, and +7 days against a baseline of all comparable coin-days without a spike, both raw and BTC-adjusted. Events are filtered to coins with at least $50M market cap at event time and a meaningful social baseline, with a spam-share cap.

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
.venv/bin/python analysis.py --spam-max 1.0   # include spammy events
```

Requires a LunarCrush API key in `.env` (or reuses `../altrank-movers/.env`). The pull needs a plan tier that includes the time-series endpoint.
