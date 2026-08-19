# I backtested "social attention leads price" on 6 years of crypto data. Here's what actually holds up.

*Draft. Numbers from the 2026-07-29 pull; regenerate before publishing.*

Every social intelligence platform sells some version of the same claim: the crowd starts talking before the price moves. I'm building a series of projects on the LunarCrush API, so before going further I wanted to know whether the core premise survives contact with data.

So I pulled full daily history for the top 1,000 coins by market cap: 6.5 years, 997 usable coins, 1.14 million coin-days, with social interactions, spam counts, and OHLC prices aligned on the same daily rows.

## The test

A "spike" is a day where a coin's social interactions jump at least 3 standard deviations above its own trailing 30 days, while price stays flat (within 2%). The flat-price condition matters: it separates "social moved first" from "everyone is talking about the pump that already happened."

I only counted spikes on coins that were already real at the time: $50M+ market cap, $1M+ daily volume, and an established social baseline. Then I measured BTC-adjusted forward returns at 1, 3, and 7 days against every comparable non-spike coin-day, with a month-block cluster bootstrap for significance. Full methodology, code, and caveats are in the repo.

One more split, and it turned out to be the whole story. LunarCrush labels spam at the post level, so every spike day has a spam share. I split spikes into organic (spam <= 50% of posts) and spam-heavy (spam > 50%).

## Finding 1: 85% of social spikes are manufactured

Of 2,599 spike days, 2,197 were spam-heavy. When you see "everyone is suddenly talking about this coin," five times out of six the crowd is mostly bots.

## Finding 2: manufactured hype carries no signal

Spam-heavy spikes underperformed the baseline at every horizon (directionally; not statistically significant on its own). Whatever the botnets are being paid for, it is not delivering alpha to the people watching the mentions go up.

## Finding 3: organic attention does lead price, modestly, at one horizon

Organic spikes beat the baseline everywhere directionally, but one number is solid: over the next 3 days, organic-spike coins beat BTC 49.0% of the time versus 41.9% for ordinary coin-days. That is a 7.2 point improvement, p = 0.003 by cluster bootstrap, and it is the only one of twelve comparisons that survives multiple-testing correction.

Worth being precise about what this is: altcoins bleed against BTC on a typical day. An organic social spike roughly stops the bleed and tilts the odds toward outperformance. It does not predict pumps. The medians are near zero; the payoff is carried by a minority of winners.

## Finding 4: the signal is relative, not directional

"Beat BTC 49% of the time" is easy to hear as "the price went up 49% of the time." Those are different claims and only one of them is supported, so I tested them separately (`uprate.py`, same events, same bootstrap, scored on raw return with no BTC subtracted).

| +3 days | n | Price simply rose | Beat BTC |
|---|---|---|---|
| Ordinary coin-day | 448,191 | 46.3% | 41.8% |
| Organic spike | 402 | 47.8% | 49.0% |
| Spam-heavy spike | 2,197 | 45.5% | 39.7% |

The beats-BTC gap is +7.2 points, CI [+2.5, +11.4], p = 0.003. The up-rate gap over the same events and the same bootstrap draws is +1.5 points, CI [-3.4, +6.2], p = 0.54. Nothing.

Notice both up-rates sit below 50%. The typical altcoin day is a slight loser in absolute terms and a worse one against BTC, and an organic spike closes most of the gap to BTC while barely touching absolute direction. The +3d return distribution for those 402 events is near-symmetric around zero (p25 -2.4%, median -0.02%, p75 +2.4%) with a slightly fatter left tail (p10 -8.1% vs p90 +7.4%).

The one horizon where a directional reading looks tempting is +1d, where the up-rate gap is +3.9 points (p = 0.09) while the beats-BTC gap there is nothing. Six comparisons, no correction applied, and it does not survive a Bonferroni threshold. I am not claiming it.

So the correct statement of the result is: an organic spike makes a coin less likely to bleed against Bitcoin over the next three days. It does not make the price more likely to rise. Every published version of this number should carry that sentence.

## Finding 5: an early lead is not a leading indicator

Once a 3-day signal is live, the tempting question after day 1 is whether being green already means something. Scored naively it looks emphatic: organic spikes that were ahead of BTC after day 1 went on to beat BTC at day 3 72.8% of the time, against 28.9% for the ones behind. A 44 point spread, p < 0.001.

It is an artifact. Day 1 sits inside day 3, so an early lead is already part of the 3-day return before you measure anything. The measure and the outcome share a term.

The clean test is the non-overlapping remainder: does the day-1 lead predict days 2 and 3 by themselves? Ahead group 46.2%, behind group 46.3%, gap -0.1 points, p = 0.99. Correlation between the day-1 lead and the days 2-3 excess return is 0.06.

So the early scoreboard carries no information about what is left. This is the third time in this repo a number has looked like a finding until I checked what it shared with itself: the leave-one-out demeaning in attention-cascade, the raw-level quintiles in attention-breadth, and now this one.

## What I take from this

1. The social-leads-price claim is real but narrow: it lives in organic attention, at short horizons, as a *relative* odds-shift rather than a money printer. It is a statement about performance against BTC, not about direction.
2. Spam filtering is not a nice-to-have. It is the difference between a signal and an anti-signal. Raw mention counts without spam labels are worse than useless, because 85% of what they count is manufactured.
3. If you use social data for anything, trading, research, or investigations, the first question to ask of any spike is "who is actually talking."

## Caveats, honestly

Survivorship bias in the universe (today's top 1,000, mitigated by the at-the-time size filters). Retroactive data revisions: spam labels are reprocessed historically, so live spam classification is noisier than what this backtest saw, and that caveat applies most strongly to exactly the finding that matters. Close-to-close returns, no execution costs. Daily granularity hides intraday lead-lag. This is a data study, not a strategy.

## Reproduce it

Everything is open source: [github.com/nickisanders/lunarcrush-projects](https://github.com/nickisanders/lunarcrush-projects), project 02. The pull is about 1,000 API requests and the analysis runs in a couple of minutes. You'll need a LunarCrush API key; affiliate code NICKI gets 15% off if you want to dig in yourself.
