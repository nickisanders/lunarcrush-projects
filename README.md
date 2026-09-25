# LunarCrush Projects

Example projects built on the [LunarCrush API](https://lunarcrush.com/developers/api/endpoints), a social + market intelligence API for crypto and stocks.

Each project is self-contained under `projects/` with its own README, dependencies, and instructions.

## Projects

| # | Project | What it does |
|---|---------|--------------|
| 01 | [altrank-movers](projects/altrank-movers/) | Daily bot that posts the biggest AltRank climbers and fallers with a chart |
| 02 | [social-price-backtest](projects/social-price-backtest/) | Backtest of whether social interaction spikes lead price, on 6+ years of daily data |
| 03 | [hype-detector](projects/hype-detector/) | Daily scanner classifying social spikes as organic or manufactured, with evidence |
| 04 | [narrative-rotation](projects/narrative-rotation/) | Weekly report on which crypto narratives gained or lost social attention share |
| 05 | [attention-halflife](projects/attention-halflife/) | Decay study: crypto attention has a one-day half-life, organic or not |
| 06 | [attention-breadth](projects/attention-breadth/) | Attention Breadth Index: how many coins crypto is actually talking about |
| 07 | [organic-watchlist](projects/organic-watchlist/) | Daily watchlist of genuine attention spikes where price hasn't moved yet |
| 08 | [attention-cascade](projects/attention-cascade/) | Tests the BTC-to-alts attention cascade folklore. It does not exist |
| 09 | [attention-death](projects/attention-death/) | Dying conversations predict nothing, and the altcoin base rate that fell out of it |
| 10 | [bot-share](projects/bot-share/) | How much of each major coin's conversation is flagged spam. The median is about 40% |
| 11 | [attention-clock](projects/attention-clock/) | Crypto conversation runs on a 2.1x daily cycle, and every major coin keeps the same Western hours |
| 12 | [crowd-size](projects/crowd-size/) | How many accounts it takes to make half a coin's conversation. Bitcoin needs hundreds, some coins need three |
| 13 | [name-collision](projects/name-collision/) | Coins whose social volume is mostly about something else, because the ticker is an ordinary word |
| 14 | [influencer-scorecard](projects/influencer-scorecard/) | Scores named crypto accounts on whether the coins they post about beat Bitcoin. They do not |
| 15 | [launch-check](projects/launch-check/) | How many contracts share a trending ticker, and whether the volume is plausible or churn |
| 16 | [weekend-crowd](projects/weekend-crowd/) | The weekend crowd is 7% smaller, the spike detector misses 19.5% more, and fixing it buys nothing |
| 17 | [attention-premium](projects/attention-premium/) | Coins talked about more than they are worth are not punished. How stablecoins nearly made them look punished |
| 18 | [top-ten](projects/top-ten/) | Seven coins own crypto's top-ten conversation. A visitor's median stay in the other three seats is one day |
| 19 | [polygon](projects/polygon/) | Polygon held a top-20 seat in crypto conversation for four years, then fell to #110. So did every Ethereum L2 |
| 20 | [narrative-shift](projects/narrative-shift/) | Half of crypto is talking about three coins. Every altcoin narrative lost share between 2024 and 2026 |
| 21 | [headcount](projects/headcount/) | The median top-1,000 coin has 24 people posting about it a day. 82% have fewer than 100 |
| 22 | [who-moved-first](projects/who-moved-first/) | For a coin pumping right now, hour by hour: did the crowd arrive before the price move or after it |
| 23 | [mood](projects/mood/) | The more people talk about a coin, the less they like it. Bitcoin is the least-liked coin in the top ten |
| 24 | [where-are-they-now](projects/where-are-they-now/) | 130 coins have held a top-20 conversation seat since 2020. 17 still do. Of the class of 2021, only DOGE |
| 25 | [pumps-not-dumps](projects/pumps-not-dumps/) | A +5% day is 2.4x as likely to trigger an attention spike as a -5% day. A -5% day barely beats a flat one |
| 26 | [loud-dumps](projects/loud-dumps/) | A 10% dump the crowd talks about beats BTC 39% of the time afterwards. One nobody mentions, 49% |
| 27 | [comeback](projects/comeback/) | Zcash was #126 in crypto conversation in January 2025 and $20 in mid-2024. Today #4, $1,439, #9 by market cap |
| 28 | [graveyard](projects/graveyard/) | 9 of this week's 20 biggest gainers sit 80%+ below their peak. ICON was once #4 in all of crypto conversation |
| 29 | [incident-watch](projects/incident-watch/) | Watches falling coins for hacks and freezes being discussed. The aggregate metrics miss these; the post text does not |

## The scoreboard

`python3 tools/scoreboard.py` prints every headline result across the repo,
sorted into what held up, what was tested and buried, and where the data
misleads. 20 recorded findings across 28 projects: 10 hold, 6 are nulls, 4
are measurement traps. `tools/scoreboard_chart.py` renders it.

## What the backtest found

The founding question was whether social attention leads price. The short answer, from [project 02](projects/social-price-backtest/):

- About **85% of social spikes are spam-heavy**, and those carry no positive signal. Filtering them is the difference between a signal and an anti-signal.
- The organic minority improves the odds of **beating Bitcoin** over 3 days from 41.9% to 49.0% (+7.1pp, p = 0.002). It is the only comparison that survives multiple-testing correction.
- That edge is **relative, not directional**. Scored on whether the price simply rose, it disappears (+1.5pp, p = 0.54).
- It requires the price to **not have moved yet**. The same spike after a 5%+ run is worth nothing.
- It **does not need a bull market**, and it fires 1.7x more often in a downturn.
- It **does not work on stocks**: 4,063 tickers, 9,073 events, no effect.

Most of what is in here is a null result, and the nulls are published with the same care as the finding.

## Getting an API key

All projects authenticate with a LunarCrush API key passed as a Bearer token. Sign up and grab a key at [lunarcrush.com](https://lunarcrush.com/) under Settings > API.

## License

MIT
