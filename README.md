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
