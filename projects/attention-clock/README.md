# Attention Clock

"Crypto never sleeps" is the most repeated line in this industry. The market doesn't. The people do.

For every coin over $1B, this measures posting volume by hour of the day across the last 30 days, and asks two questions: how deep is the daily trough, and do different coins keep different hours?

```bash
python3 pull.py        # one request per coin, resumable
python3 analysis.py    # writes out/report.json and out/profiles.csv
python3 make_chart.py  # writes out/clock.svg
```

Needs `LUNARCRUSH_API_KEY` in `.env` (falls back to `../altrank-movers/.env`).

## Result

Crypto conversation runs on a 2.1x daily cycle, and every major coin runs on the same one.

| | |
|---|---|
| Busiest hour | 13:00 UTC, 1.40x an average hour |
| Quietest hour | 04:00 UTC, 0.68x |
| Swing | 2.07x |
| Coins peaking 11:00-17:00 UTC | 19 of 22 |
| Coins troughing 01:00-07:00 UTC | 18 of 22 |
| Median correlation between two coins' clocks | 0.78 |
| Share of posting in 12:00-20:00 UTC | 46% (33% if flat) |

The clock is Western. 04:00 UTC, the quietest hour of the crypto day, is 1pm in Tokyo. The busiest, 13:00 UTC, is 9am in New York and 10pm in Tokyo. Whatever crypto's self-image as a borderless 24/7 market, the conversation about it keeps London-to-New-York office hours.

The uniformity is the part worth sitting with. There is no "Asian coin" and no "European coin" in this data: any two coins' hourly shapes correlate at 0.78, so BNB, Monero, Pump.fun and Bitcoin are all being discussed by what behaves like one crowd on one clock.

## Why the median, not the mean

Per clock hour this takes the **median** across the 30 days. On means, BNB appeared to peak at 01:00 UTC, which would have been a lovely story about an Asia-hours community. It was one overnight event. On medians BNB peaks at 13:00 like everything else and the story evaporates.

Any single listing, hack or liquidation cascade can otherwise invent a peak out of one hour, which is exactly the failure mode that makes hour-of-day analysis look more interesting than it is.

## Robustness

Coins are held to a floor of median posts per hour, because below it the per-hour median quantizes onto small integers and the shape becomes rounding noise. The conclusion does not depend on where that floor sits:

| Floor | Coins | Swing | Peak 11-17 UTC | Correlation |
|---|---|---|---|---|
| 5 | 31 | 2.09x | 26/31 | 0.73 |
| 10 | 22 | 2.07x | 19/22 | 0.78 |
| 20 | 15 | 2.00x | 14/15 | 0.83 |
| 40 | 10 | 1.91x | 9/10 | 0.78 |

The hour in progress is dropped, since it is partial by construction.

## Limits

This counts posts created, not people. A prolific account and a quiet one weigh the same, and automated posting is included: roughly a third of major-coin posting is flagged spam ([bot-share](../bot-share/)), and this study makes no attempt to strip it out. The honest reading is "when does posting happen", not "when are humans awake". Note the hourly `spam` field cannot separate the two here: it exceeds `posts_created` in 710 of 735 hours, so it is not an hourly count and no clean-versus-spam split is possible at this resolution.

Stablecoins and wrapped assets are excluded; their conversation is plumbing rather than a community.

Related: [attention-halflife/office_hours.py](../attention-halflife/office_hours.py) asks whether manufactured spikes peak at different hours than organic ones (they don't). This measures the underlying rhythm both sit on.
