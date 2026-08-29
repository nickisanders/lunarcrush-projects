# Name Collision

Some coins look enormously popular because their ticker is an ordinary word.

```bash
npm install
npm run daily     # writes out/report.json, chart.svg, chart.png
npm test
```

Needs `LUNARCRUSH_API_KEY` in `.env` (falls back to `../altrank-movers/.env`).

## The measure

Social interactions per dollar of market cap, compared to the median coin.

The ratio matters more than either number alone. Big coins have big conversations and small coins have small ones, so raw interaction counts say nothing about whether a conversation is really about the coin. A token carrying more daily engagement than its entire market capitalisation in dollars is not being discussed by its holders.

Across ~3,000 coins the median sits at 0.0033 interactions per dollar. Bitcoin sits at 0.00008. Two dozen coins sit at 100x the median or more.

## Two different things get caught, and only one is a collision

A high ratio alone does not prove contamination, so every suspect is checked against its bare ticker as a topic:

- **Collision** — the bare word carries at least 3x the coin's traffic, so most of that conversation is not the coin's. `$AM`'s ticker as a topic drew **712 million interactions from 346,000 people** in 24 hours. That is the English word "am", and roughly 5.6x Bitcoin's entire daily conversation, attached to a $279k token.
- **Loud, not colliding** — the topic's traffic *is* the coin's. `$TITCOIN` and `$LILAI` sit far above the median but their topic traffic is entirely their own. That is a real conversation, or real bots, and calling it a naming accident would be wrong.

The distinction is the whole point of the tool. Flagging on the ratio alone would have condemned half a dozen coins that are simply small and loud.

## What showed up

| Coin | Market cap | Interactions 24h | vs median | The bare ticker as a topic |
|---|---|---|---|---|
| $DONS | $141,794 | 632,693 | 1,323x | "dons" = 7.3M interactions |
| $47 | $100,433 | 400,580 | 1,183x | "47" = 75.5M, and it is a political number |
| $AM | $279,063 | 1,099,882 | 1,169x | "am" = 712M from 346k people |
| $ALVA | $276,671 | 210,718 | 226x | "alva" = 2.7M |
| $OTC | $654,507 | 448,123 | 203x | "otc" = 3.3M, a finance acronym |
| $DINO | $118,993 | 74,437 | 186x | "dino" = 70M |

`$OPTIMUS` (Digital Optimus, Solana) is the case that prompted this: a $158k token whose topic inherits traffic from Tesla's humanoid robot.

## Limits

This is a naming problem, not an accusation. Nothing here says a project did anything wrong; a team that picked a short ticker in 2021 did not choose to collide with a robot or an election. What it says is that **ranking coins by social volume puts these near the top**, and any screen built on that number will surface them first.

Topic attribution is the mechanism: a post naming a ticker counts toward that topic, and a ticker that is also a word gets counted for every unrelated use of it. The same effect in miniature affects any coin whose ticker is short or generic.

Two suspects each run (`$BIFI2`, `$POLY` on the first pass) have topic strings that do not resolve to a topic at all. They are reported as unchecked rather than assumed either way.

Related: [crowd-size](../crowd-size/) measures how few accounts carry a coin's conversation; this measures whether the conversation is about the coin at all.
