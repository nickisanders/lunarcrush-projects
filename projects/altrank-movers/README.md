# AltRank Movers Bot

Daily bot that finds the biggest [AltRank](https://lunarcrush.com/) climbers and fallers among the top 500 coins and produces a ready-to-post update: text plus a dark-mode chart image. Optionally posts straight to Telegram.

AltRank is LunarCrush's relative performance score combining market and social activity. It is a rank, so lower is better. A coin moving from #250 to #40 overnight usually means something is happening socially before most people notice.

## How it works

One API call per run:

```
GET https://lunarcrush.com/api4/public/coins/list/v2?sort=market_cap_rank&limit=1000
```

The response includes each coin's current `alt_rank` and its `alt_rank_previous` from 24 hours ago, so a single request is enough to compute movers. The bot also saves a daily snapshot to `data/` as a fallback source of yesterday's ranks and raw material for longer-horizon charts.

Junk filtering: only coins inside the top 500 by market cap with at least 5,000 social interactions in the last 24h are considered. On top of that, a relevance cap (default 200) keeps the tail out: climbers must currently sit inside the AltRank top 200, and fallers must have been inside it yesterday. Without this, the leaderboard is pure noise, since coins ranked #3000 routinely swing by thousands of places on negligible social volume. The story worth posting is "what arrived into relevance and what dropped out," not "what bounced around the tail."

## Setup

```bash
npm install
cp .env.example .env   # add your LunarCrush API key
```

## Usage

```bash
# Try it without an API key (bundled fixture data)
npm run daily -- --mock

# Real run: prints the post, writes out/post.txt, out/chart.svg, out/chart.png
npm run daily

# Post to Telegram (needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env)
npm run daily -- --send

# Options
npm run daily -- --top 300 --min-interactions 10000 --count 5 --altrank-cap 150
```

## Automate it

The repo ships a GitHub Actions workflow (`.github/workflows/altrank-movers.yml`) that runs the bot daily at 13:00 UTC. Add these repository secrets to enable it:

- `LUNARCRUSH_API_KEY` (required)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional, enables auto-posting)
- `POST_LINK_URL` (optional, link appended to each post)

Without Telegram secrets the workflow still runs and uploads the post text and chart as a build artifact.

## Sample output

```
🌙 AltRank movers, Jul 28

📈 Climbers
1. $ZIL +1044 (#1081 to #37)
2. $UMA +1345 (#1454 to #109)
...

📉 Fallers
1. $XVG -3060 (#53 to #3113)
...
```

## Rate limit budget

One request per day. Every LunarCrush plan tier covers this, including the free Hobby tier's 100 requests/day.
