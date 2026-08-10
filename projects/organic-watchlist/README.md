# Organic Attention Watchlist

Coins where the conversation genuinely spiked and the price hasn't reacted yet.

This is the one setup in this repo with a measured edge. The [social-price backtest](../social-price-backtest/) tested it across 6.5 years and 997 coins: organic spikes on flat-price days beat BTC over the following 3 days **49.0%** of the time, against **41.9%** for an ordinary coin-day (p = 0.003 by month-cluster bootstrap, and it survived a [within-era audit](../social-price-backtest/era_check.py)).

That is an odds shift, not a prediction, and the difference matters. Roughly half of these still lose to BTC.

## The setup is fixed, not tunable

The thresholds in `src/watchlist.ts` are the backtest's exact event definition:

| Leg | Threshold | Why |
|---|---|---|
| Attention spike | interactions z-score >= 3.0 vs the coin's own trailing 30 days | the event |
| Price hasn't moved | abs(24h change) <= 2% | separates "social moved first" from "everyone is talking about the pump" |
| Organic | spam <= 50% of created posts | the [spam split](../hype-detector/) is what carries the signal |
| Real coin | $50M+ market cap, $1M+ volume | |
| Real baseline | trailing median interactions >= 2,000 | so z-scores aren't computed on noise |

Change any of them and the 49% no longer describes the output. If you want to experiment, fork the criteria and re-run the backtest against your version.

## Most days are empty, by design

The backtest found 402 qualifying events in 450,790 eligible coin-days: about one day in six. An empty list is the normal state and is reported as such, along with the closest near-misses and which leg each one failed, so you can see the scan ran rather than silently broke. **Near-misses do not carry the measured edge.**

## Usage

```bash
npm install
npm run daily -- --mock      # no API key needed
npm run daily                # live
npm run daily -- --max-candidates 120
```

Outputs `out/post.txt`, `out/chart.png`, and `out/report.json`. Live runs append to `data/history.jsonl` so the realised hit rate can eventually be measured against the backtest's claim instead of assumed.

Cost: one coins-list call plus one history call per candidate, about 80 requests a day.

## Automate it

`.github/workflows/organic-watchlist.yml` runs daily at 13:15 UTC and uploads the outputs as an artifact. Needs the `LUNARCRUSH_API_KEY` secret.

## Honest limits

Candidates are ranked by social volume and AltRank movement before the expensive history call, so a very small coin spiking from a low base could fall outside the top 80 and be missed. Raising `--max-candidates` widens the net at the cost of more requests.

The backtest measured relative performance against BTC, not absolute returns, and ignores fees and slippage. Nothing here is financial advice.
