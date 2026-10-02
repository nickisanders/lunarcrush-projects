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

## The threshold missed a big one

On 2026-09-22, Harmony ($ONE) was up 446% in a week and one of the largest
movers on the board. The scanner did not flag it.

| | |
|---|---:|
| market cap | $55M, #395 |
| the coin's own interactions, 24h | 321,024 |
| people posting about the coin, per day | 504 |
| the bare word "one", 24h | **5,046,904,079** |
| people using the word | **1,312,815** |
| word over coin | 15,727x |
| word over Bitcoin's entire daily conversation | 22.5x |

The ratio leg is why it was missed. $ONE sits at 24x the median interactions
per dollar, under the 100x bar, because a $55M coin needs far less borrowed
traffic to look normal per dollar than a $150k one does. The threshold was
tuned on microcaps and silently misses this whole class.

`loudest()` now returns the top 25 coins by raw interactions for a topic check
that does not depend on the ratio, and a test plants the Harmony numbers so
the gap cannot reopen. The cost is 25 extra topic calls a day.

None of this says the 446% is fake. 504 people a day posting about the coin is
a real crowd, five times what it was before the run. It says that anyone
ranking coins by social volume cannot see this one clearly, because the
measurement is competing with the most common word in the language.

## Limits

This is a naming problem, not an accusation. Nothing here says a project did anything wrong; a team that picked a short ticker in 2021 did not choose to collide with a robot or an election. What it says is that **ranking coins by social volume puts these near the top**, and any screen built on that number will surface them first.

Topic attribution is the mechanism: a post naming a ticker counts toward that topic, and a ticker that is also a word gets counted for every unrelated use of it. The same effect in miniature affects any coin whose ticker is short or generic.

Two suspects each run (`$BIFI2`, `$POLY` on the first pass) have topic strings that do not resolve to a topic at all. They are reported as unchecked rather than assumed either way.

Related: [crowd-size](../crowd-size/) measures how few accounts carry a coin's conversation; this measures whether the conversation is about the coin at all.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
