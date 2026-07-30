# Hype Detector

Daily scanner that finds coins in a social spike and classifies each spike as organic or manufactured, with the evidence shown. Sequel to [social-price-backtest](../social-price-backtest/), which found that 85% of social spikes are spam-heavy and carry no positive signal, while organic spikes shift the odds. This tool runs that distinction live, every day.

## How it works

Two stages to stay cheap on API quota (~80 requests/day):

1. One coins-list call. Candidates are coins inside the top 1000 with $50M+ market cap, $1M+ volume, and real social activity, ranked by a heat heuristic (AltRank jump plus outsized interactions for their size). Top ~40 move on.
2. Per candidate: a daily time-series call (30-day interaction baseline, spam share) and a creators call (who is driving the conversation). Only coins with an interaction z-score >= 2 get a verdict.

The manufactured score (0-100) weighs:

- **Spam share of created posts (55%)**: the load-bearing signal, validated by the backtest
- **Creator concentration (30%)**: share of interactions from the top 3 accounts; botnets are concentrated, crowds are not
- **Sentiment uniformity (15%)**: unanimous positivity above 75 is a tell; real crowds disagree

Verdicts: 60+ manufactured, 30-59 mixed, under 30 organic. Every verdict ships with its evidence: this is a measurement, not an accusation.

## Usage

```bash
npm install

# Try it without an API key
npm run daily -- --mock

# Real run (key in .env here or reused from ../altrank-movers/.env)
npm run daily

# Fewer expensive per-coin calls
npm run daily -- --max-candidates 20
```

Outputs `out/post.txt`, `out/chart.png` (leaderboard), and `out/report.json` (full evidence per coin).

## Honest limitations

- Creator concentration uses the top-creators endpoint, which reflects measurable interactions; sock-puppet networks that spread activity across many small accounts will read as less concentrated than they are.
- Spam labels are LunarCrush's classification; the backtest showed they carry signal, but they are not ground truth.
- A manufactured-looking spike is not proof of a coordinated campaign, and an organic-looking one is not an endorsement. The score summarizes evidence; it does not read minds.
