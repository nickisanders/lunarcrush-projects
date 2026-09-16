# who-moved-first

When a coin pumps, did the crowd show up before the move or after it?

The [backtest](../social-price-backtest/) found an attention spike only carries
an edge when the price has not moved yet. A spike on a flat price beats
Bitcoin 49.0% of the time over 3 days against a 41.9% baseline (p = 0.001).
The same spike after the price has already run 5%+ is 41.7%, p = 0.85 against
baseline. Attention that arrives after a move is worth nothing.

This tool takes a coin that is pumping right now and shows which order things
happened in, hour by hour, so the backtest can be applied to a live case.

## $AKE, 2026-09-15

Up 80% over 48 hours, nearly all of it in the eight hours before this was
written.

| event | time (UTC) |
|---|---|
| price first +10% | Tue 03:00 |
| price first +25% | Tue 06:00 |
| crowd first +50% | Tue 12:00 |
| crowd first +100% | never |

The crowd arrived nine hours after the price move, and at the end of the
window it was up 51% against a price up 80%. The conversation is the move
being noticed.

## $AKE, 24 hours later

Price peaked at 16:00 UTC on the 15th and has traded within 5% of that for
the 20 hours since. The crowd kept growing: 181 accounts an hour at the price
peak, 246 an hour at 12:00 on the 16th, up 36% while the price went nowhere,
and still rising at the last complete hour.

Since the first post, +13.9%. The claim was that a crowd arriving after the
move tells you nothing about what comes next, and a flat day is consistent
with that. It did not say the price would fall.

## Method

Two hourly series from `/public/coins/:symbol/time-series/v2?bucket=hour`,
each expressed relative to its own level at the start of a 48-hour window.
Price is relative to the first close; crowd is relative to the median of the
first six hours, since a single hour of contributors is noisy.

The final row is the hour in progress and is dropped. A partial hour of
contributors compared to complete hours is the same defect as a partial day
compared to complete days, which has bitten three projects in this repo.

## Running it

```bash
LUNARCRUSH_API_KEY=... python3 who_moved_first.py AKE
python3 chart.py out/ake.json
```
