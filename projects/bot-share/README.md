# Bot Share

How much of each major coin's social conversation is flagged as spam.

Everyone knows crypto Twitter has a bot problem. Nobody publishes the number per coin. This does: for every coin over $1B, it takes the median share of created posts flagged as spam over the last 30 complete days, and ranks them.

```bash
npm install
npm run daily      # writes out/report.json, post.txt, chart.svg, chart.png
npm test
```

Needs `LUNARCRUSH_API_KEY` in `.env` (it falls back to `../altrank-movers/.env`).

## What the number is

`spam / posts_created` per day, median across the window. The median rather than the mean, because a single coordinated day would otherwise drag a coin's whole profile.

Three things are deliberately excluded:

- **The day in progress.** `spam` and `posts_created` fill at different rates through a day, so a partial day reads biased high. This repo shipped that bug twice before catching it, so `completeWindow` drops the final row.
- **Stablecoins and wrapped assets.** They get discussed as plumbing rather than as projects, so their spam profile answers a different question.
- **Coins under 100 posts a day.** Below that the ratio is rounding noise: a coin with four posts a day swings from 0 to 3.0 on a single flagged post.

## The honesty flag

`spam` can exceed `posts_created`. When it does, the two fields are counting different post universes for that coin, and the ratio is not a share of anything. Any coin with even one such day in the window is marked `quotable: false` and kept out of the chart and the percentage claims. It is still scored and still named, because "so far past the others that the measure breaks" is real information, just not a percentage.

On the first live run that flagged 10 of 33 coins, including the two highest.

`dayRatio` is deliberately left unclipped for this reason. Clipping to 1, which is right when the number feeds a score, would hide exactly the coins whose figure must not be quoted.

## What it does not measure

Posts, not reach. One bot post and one viral thread weigh the same here, so a high share means a lot of junk was written, not that a lot of people saw junk.

The labels are LunarCrush's classifier, not ground truth. A high share is also not a verdict on a project: airdrops, incentive campaigns and large retail communities all attract automated posting without anyone at the project asking for it.
