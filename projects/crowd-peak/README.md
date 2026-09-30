# crowd-peak

A coin crashes into crypto's top 10 conversation. What happens next?

```bash
source ../social-price-backtest/.venv/bin/activate
python3 crowd_peak.py --top 10
python3 chart.py
```

## The result

Every time since 2020 that a coin entered the top 10 by daily active
contributors with no top-10 day in the prior year. 79 events.

| horizon | n | median return | median vs BTC | 95% CI on vs BTC | p | rose | beat BTC |
|---|---:|---:|---:|---|---:|---:|---:|
| +7d | 79 | -3.6% | -2.7% | [-6.3, +1.8] | 0.257 | 42% | 42% |
| +30d | 79 | -4.8% | **-8.2%** | [-13.5, -1.1] | **0.026** | 46% | 35% |
| +90d | 77 | -18.0% | **-21.1%** | [-29.2, -9.4] | **0.001** | 35% | 30% |

Nothing at a week. By 90 days the median event has lost 21% against Bitcoin
and only 30% of them beat it.

## The live case

$QNT sits at #7 by daily contributors today, 3,599 people, after being #90 in
April. It is the 80th event in this table and is not included in it.

## The exception

$ZEC entered the top 10 on 2025-10-02 and beat Bitcoin by 220% over the next
30 days. It is the reason the mean is not worth quoting and the median is.
[comeback](../comeback/) covers that arc in full.

Of the last twelve entries, ten are negative against Bitcoin at 30 days.
$ICP -51%, $DRIFT -47%, $BIO -43%, $XMR -22%, $VET -21%.

## Why the two return columns differ

The absolute median at 30 days is -4.8% and the Bitcoin-adjusted median is
-8.2%, so most of these events happened while Bitcoin was rising. Reading only
the absolute number understates the cost; reading only the adjusted one hides
that a third of them did go up.

## Limits

79 events over six years is not many, and they cluster: several arrive in the
same month during a broad rally, which is exactly why the bootstrap resamples
by calendar month rather than by event.

The universe is today's top 1,000 by market cap, so a coin that entered the
top 10 in 2021 and has since fallen out of the top 1,000 never appears. Those
are the worst outcomes, so the real numbers are likely worse than these.

Entry is defined on a single day's rank. A coin that touched #10 for one day
counts the same as one that sat at #4 for a month.
