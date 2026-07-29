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

## What I take from this

1. The social-leads-price claim is real but narrow: it lives in organic attention, at short horizons, as an odds-shift rather than a money printer.
2. Spam filtering is not a nice-to-have. It is the difference between a signal and an anti-signal. Raw mention counts without spam labels are worse than useless, because 85% of what they count is manufactured.
3. If you use social data for anything, trading, research, or investigations, the first question to ask of any spike is "who is actually talking."

## Caveats, honestly

Survivorship bias in the universe (today's top 1,000, mitigated by the at-the-time size filters). Retroactive data revisions: spam labels are reprocessed historically, so live spam classification is noisier than what this backtest saw, and that caveat applies most strongly to exactly the finding that matters. Close-to-close returns, no execution costs. Daily granularity hides intraday lead-lag. This is a data study, not a strategy.

## Reproduce it

Everything is open source: [github.com/nickisanders/lunarcrush-projects](https://github.com/nickisanders/lunarcrush-projects), project 02. The pull is about 1,000 API requests and the analysis runs in a couple of minutes. You'll need a LunarCrush API key; affiliate code NICKI gets 15% off if you want to dig in yourself.
