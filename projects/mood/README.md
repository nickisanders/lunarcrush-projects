# mood

The more people talk about a coin, the less they like it.

LunarCrush scores every coin's daily conversation for sentiment, 0 to 100.
This ranks 504 coins by how many people post about them and looks at what
the score does as the crowd grows.

## Sentiment falls as the crowd grows

Median daily sentiment, April to July 2026, coins with at least 45 days of
at least 20 posters:

| people posting a day | median sentiment | n | examples |
|---|---:|---:|---|
| 20–50 | 84 | 183 | AUDIO, CARV, HASH |
| 50–100 | 82 | 147 | MORPHO, SUPER, HOT |
| 100–250 | 81 | 100 | UNI, AMP, GOMINING |
| 250–1,000 | 80 | 58 | RAY, PEPE, BNB |
| 1,000–5,000 | 79 | 12 | XRP, HYPE, ADA |
| 5,000+ | 74 | 4 | BTC, ETH, SOL |

Spearman correlation between log crowd size and sentiment: **-0.24**, 95%
bootstrap CI [-0.32, -0.15]. Every band is lower than the one before it.

The direction also holds inside a single coin, day to day: on days a coin's
own crowd is larger, its own sentiment tends to be lower. Median within-coin
Spearman -0.07, negative for 63% of coins. Weak, but the same sign.

## Bitcoin is the least-liked coin in the top ten

| coin | sentiment | people a day |
|---|---:|---:|
| BTC | 70 | 54,053 |
| ETH | 74 | 22,538 |
| XRP | 79 | 4,320 |
| BNB | 80 | 736 |
| SOL | 80 | 22,002 |
| TRX | 88 | 280 |

Four of the top ten are stablecoins or wrappers and are excluded.

## Why

A small crowd is mostly holders, and holders are cheerful. A large crowd
includes traders on both sides, critics, people who lost money, journalists,
and people arguing with all of the above. The score averages everyone in the
room, and a bigger room has more people in it who are not fans.

The alternative reading, that popular coins are genuinely disliked, does not
survive the within-coin result. The same coin scores lower on its busier days.

## One thing the score cannot do

The lowest-scoring coins in the data:

| coin | sentiment | name |
|---|---:|---|
| ASS | 16 | another stupid shitcoin |
| CLASH | 32 | GeorgePlaysClashRoyale |
| USELESS | 46 | USELESS COIN |
| TROLL | 50 | TROLL |

Those are their names. The model is reading the ticker, and it cannot tell a
coin called USELESS from a coin people think is useless. Anything built on
this score needs to know that, and so does anyone reading a "most hated
coins" list built from it. See [name-collision](../name-collision/) for the
same problem in the other direction.

The highest scorer is VET at 98, with 342 people a day. That one is probably
real.

## Method

Coin-days with fewer than 20 posters are dropped before the median is taken,
since a sentiment score from six posts is noise. A coin needs 45 such days in
the 90-day window to be included. Pegged, wrapped and single-character
tickers are excluded.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 mood.py    # out/mood.json
python3 chart.py   # out/mood.svg
```

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
