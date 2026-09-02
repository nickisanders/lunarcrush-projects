# Influencer Scorecard

When a named crypto account posts about a coin, what does the coin actually do next?

```bash
python3 pull.py          # creators, their posts, and prices. resumable.
python3 scorecard.py --horizon 7
```

Needs `LUNARCRUSH_API_KEY` in `.env` (falls back to `../altrank-movers/.env`).

## What it measures

137 creators, ~180 posts each going back months to over a year, 9,153 distinct (creator, coin, day) mentions, 6,685 of which have enough price history to score. Every mention is scored on the coin's return against Bitcoin at 3, 7 and 30 days.

## Result: being mentioned is not worth anything

| Horizon | A mentioned coin | An unmentioned coin | Gap | p |
|---|---|---|---|---|
| 3 days | 36.7% beat BTC | 42.2% | -5.5pp | 0.000 |
| 7 days | 35.9% | 37.6% | -1.7pp | 0.289 |
| 30 days | 31.4% | 35.6% | -4.2pp | 0.177 |

Only the 3-day gap clears its own interval, and it runs *against* the mentioned coins. At 7 and 30 days there is no detectable difference.

Note the two measures disagree in direction: mentioned coins beat Bitcoin **less often** but carry a **better median** (-0.5% vs -1.5% at 7 days). That is the signature of a liquidity difference rather than information. Coins people talk about are larger, so their outcomes are less dispersed: fewer big winners and fewer big losers. Nothing about the mention itself moves the middle of the distribution in a useful direction.

The blunt version: across 6,685 mentions by 137 named accounts, a coin they talked about did not beat Bitcoin more often than a coin nobody mentioned.

## What this does not measure

- **A mention is not a recommendation.** `lookonchain` mostly reports whale movements, so a `$ETH` post is frequently "somebody just dumped 40,000 ETH". `post_sentiment` is carried on every event so stance can be split out, but sentiment is a blunt instrument and this is the weakest joint in the study.
- **Causation is not on the table.** An account that posts about whatever is already moving scores like an account that moves things. This cannot separate them.
- **Creator rankings are noisier than they look.** 74 creators clear 20 events. Ranking 74 things on 20-90 observations each will produce an impressive-looking leader by chance alone, which is why the headline is the market-wide comparison and not the leaderboard.
- **The universe is current.** Creators come from today's topic lists, so accounts that were influential in 2024 and have gone quiet are absent.

## Details that decide the result

**The control set is coins nobody mentioned.** 150 coins in the top 600 that no creator in the sample named. The obvious baseline, drawing another coin from the cache, compares a mention against a different mention and cannot answer whether mentions matter. That mistake was in the first working version.

**Mentions are deduplicated per creator, coin and day.** Five posts about `$SOL` in one afternoon is one call. Without this a prolific poster dominates the sample.

**Tickers that are ordinary words are dropped.** "I am bullish" and "it's hot" would otherwise register as calls on `$AM` and `$HOT`. The stoplist is seeded from [name-collision](../name-collision/).

**The bootstrap is blocked by calendar month.** Mentions cluster hard: a hundred accounts naming the same coin in one week are not a hundred independent draws, and an unclustered test reports an interval several times too tight.

**Creator universe comes from topic creator lists, not `/public/creators/list/v1`.** That endpoint is LunarCrush's whole-platform ranking and returns Netflix, ESPN and Red Bull. The network is parsed from the `creator_id` prefix, since topic creator records carry no `creator_network` field.
