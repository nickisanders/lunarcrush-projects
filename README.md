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

## Getting an API key

All projects authenticate with a LunarCrush API key passed as a Bearer token. Sign up and grab a key at [lunarcrush.com](https://lunarcrush.com/) under Settings > API.

## License

MIT
