# Hype Detector

Daily scanner that finds coins in a social spike and classifies each spike as organic or manufactured, with the evidence shown. Sequel to [social-price-backtest](../social-price-backtest/), which found that 85% of social spikes are spam-heavy and carry no positive signal, while organic spikes shift the odds. This tool runs that distinction live, every day.

## How it works

Two stages to stay cheap on API quota (~80 requests/day):

1. One coins-list call. Candidates are coins inside the top 1000 with $50M+ market cap, $1M+ volume, and real social activity, ranked by a heat heuristic (AltRank jump plus outsized interactions for their size). Top ~40 move on.
2. Per candidate: a daily time-series call (30-day interaction baseline, spam share) and a creators call (who is driving the conversation). Only coins with an interaction z-score >= 2 get a verdict.

The manufactured score (0-100), calibrated on a burn-in week of live verdicts plus 6.5 years of historical distributions, weighs:

- **Spam lift vs the coin's own baseline (40%)**: today's raw spam/posts ratio relative to the coin's trailing 30-day median. This is the era-robust signal: the absolute spam field's scale has shifted over the years and some coins run chronically high, so a fresh spam wave counts more than a chronic level.
- **Absolute spam share (20%)**: chronic botting still matters, just not twice.
- **Creator concentration (30%)**: share of interactions from the top 3 accounts.
- **Sentiment uniformity (10%)**: re-centered at 90, because a majority of crypto spike days run 85+ sentiment; only near-unanimity discriminates.

Two v2 additions ride along as evidence without touching the score:

- **Burst share (display-only)**: the top-3 hours' share of the last 24h of interactions, from one hourly call per verdict coin. The half-life study found organic crowds are burstier than scheduled campaigns (p=0.02, a lead rather than a finding); it stays out of the score until a prospective validation window says otherwise.
- **Decay-watch**: any specimen that scored 80+ gets an automatic "what happened next" chart 3-5 days later (`out/decay-SYMBOL-DATE.png`), built from the verdict history (`data/history.jsonl`, persisted across CI runs via actions/cache).

Verdicts: 60+ manufactured, 30-59 mixed, under 30 organic. Two source labels sit alongside the score, because concentration on its own doesn't say what kind of concentration it is:

- **Institutional broadcast**: the single largest account holds 60%+ of interactions and is a known exchange or automated alert feed. Giveaways and transfer bots inflate interaction counts enormously without anyone forming an opinion. Found via $USDT on 2026-08-06, where MEXC alone was 89% of an 11.6M-interaction "spike"; the score was technically right and completely uninformative without this label. Handles match exactly (a substring rule would flag "stargate" as "gate"), so unknown accounts fall back to the generic case rather than claiming an institution the data can't identify.
- **Megaphone**: near-total concentration with low spam (top 3 >= 90%, spam < 40%), i.e. one account is the conversation but isn't a recognized institution: an announcement or a large KOL, not a botnet.

Neither label changes the score. Exchange marketing genuinely does inflate apparent attention, so the measurement stands; the label tells you who caused it. Every verdict ships with its evidence: this is a measurement of amplification, not an identification of who is behind it.

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
