# Crowd Size

How many accounts does it take to make half of everything said about a coin?

Everyone treats social volume as a proxy for how many people care. This measures whether there are actually people there. For every coin over $1B, it counts how many individual accounts you need before you have covered half of the coin's total 24h interactions.

```bash
npm install
npm run daily     # writes out/report.json, chart.svg, chart.png
npm test
```

Needs `LUNARCRUSH_API_KEY` in `.env` (falls back to `../altrank-movers/.env`).

## Result

The answer ranges over two orders of magnitude, and it does not track market cap.

| Coin | Accounts to half | Top 10 hold |
|---|---|---|
| $BTC | 235 | 11% |
| $SOL | 154 | 20% |
| $ETH | 133 | 18% |
| $XRP | 37 | 28% |
| $LINK | 34 | 31% |
| $DOT | 10 | 51% |
| $XLM | 6 | 65% |
| $TRX | 3 | 70% |
| $UNI | 3 | 63% |

Median across 34 measured coins: **21 accounts** cover half, and the top 10 hold **38%**.

Two coins, $XMR and $BCH, have crowds wider than the API will enumerate. They are excluded rather than assigned a number, since "more than the list shows" is the only honest reading.

$TRX is the sharpest case. One account carries 34% of all Tron conversation and three carry 58%. For Bitcoin the single loudest account is 2%.

## The same voices, over and over

42 accounts sit in the top 10 of more than one coin simultaneously. `BSCNews` is in seven. `CryptoMichNL` is the single loudest voice on three different coins at once ($TAO, $ONDO, $MORPHO), and `digishahed` on two ($UNI, $DOT).

So the tail of the market is not 30 separate communities. It is substantially the same rotating cast.

## What the denominator is, and why it matters

Shares divide by the coin's own 24h interaction total, **not** by the sum of the returned creators.

The creators endpoint returns the head of the distribution and drops the tail. Dividing by the creator sum would silently assume the tail does not exist and would inflate every share, most for the coins with the widest crowds, which is exactly backwards. Across 52 major coins the creator sum is a median 72% of the coin total, so a substantial real tail is there and the denominator has to include it.

Three thin coins showed a creator sum *above* the coin total, meaning the two fields count differently at low volume. Those sit below the eligibility floor, and `topShare` clamps at 1 regardless.

## Who the loud accounts are

`npm run reach` asks a second question of the same data: does follower count predict who ends up driving a coin's conversation?

Barely. Across the 340 accounts sitting in some major coin's top 10, follower count explains **24%** of the variation in impact (log-log correlation 0.48). A quarter of them have under 10,000 followers, and only 14% have over a million. The median is about 65,000.

Read the population carefully. These are accounts that already landed, so a small account only appears here if it worked. That makes this a statement about *who the loud accounts are*, not a claim that small accounts get more reach in general. Per-follower engagement across these bands would be pure survivorship and is deliberately not reported.

## Limits

This counts posts and the engagement they draw, not people. One account can be a team, a scheduler, or a bot, and roughly a third of major-coin posting is flagged spam ([bot-share](../bot-share/)). A narrow crowd is evidence that few accounts carry the conversation; whether those accounts are paid, automated, or simply prolific is a separate question this does not answer.

Interactions are attributed per topic, and a post that mentions several tickers counts toward all of them. Most accounts show genuinely different numbers per coin (88% of those appearing on more than one), but a few post identical figures across a dozen coins, which is the signature of an account listing many tickers in one post. For a coin whose top voices are ticker-sprayers, the crowd will read narrower than it is.

It is also a 24-hour snapshot. A coin mid-announcement will look narrower than its normal week.

Related: [hype-detector](../hype-detector/) uses top-3 creator concentration as one input to its manufactured score, and treats near-total concentration with low spam as a megaphone rather than a botnet. This measures the same property across the whole market instead of only on spike days.
