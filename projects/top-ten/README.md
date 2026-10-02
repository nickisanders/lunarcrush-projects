# top-ten

Crypto's ten most-discussed coins, every day for six and a half years: who
holds the seats, and how long anyone else gets to sit in one.

## Seven fixtures, three open seats

Rank every coin by daily social interactions and take the top ten. Seven coins
are there on more than half of all 2,402 days:

| coin | share of days |
|---|---:|
| BTC | 99.0% |
| ETH | 98.7% |
| XRP | 97.6% |
| ADA | 88.5% |
| LINK | 77.9% |
| SOL | 77.1% |
| DOGE | 71.6% |

That leaves roughly three seats. 212 other coins have held one at some point.

## How long a visitor lasts

2,279 stints in the top ten by a non-fixture:

| | |
|---|---:|
| median stay | 1 day |
| gone the next day | 51% |
| gone within 3 days | 75% |
| gone within a week | 88% |
| lasted a month | 1.4% |

The longest runs belong to LTC (226, 207, 202, 197 days across separate
stints), TON (125), VET (103) and SHIB (101). LTC is the one coin that behaves
like a fixture without quite being one, at 49.5% of days.

New entrants per day: 1.19.

## Two filters, and why

The raw list is not a list of coins people are discussing.

**Pegged and wrapped assets** are removed. USDT and USDC were in the raw top
ten on 22% and 37% of days. Their conversation belongs to what they track.

**Name collisions** are removed per coin-day: any coin carrying more than 100x
the day's median interactions per dollar of market cap, the same measure
[name-collision](../name-collision/) uses. Without it the raw fixtures include
$GIGA (60% of days), $S (47%), $SHELL (38%) and $NIGHT (30%), because those are
words. Single-character tickers are dropped outright, since $S is Sonic and
also the letter s, and a coin large enough passes the ratio test regardless.

Most-dropped by the ratio test: $TROLL (882 days), $BNX (863), $HOME (673),
$GIGA (624), $WHITE (453), $RARE (440).

## Limits

The universe is the top 1,000 coins by market cap at pull time. A coin that
held a seat in 2021 and has since died is not here, so the stint count is a
floor and the fixtures are the survivors among fixtures. Nothing in that
changes the shape of the result, since dead coins do not tend to have held
long stints.

Top-ten membership is a rank, so LunarCrush's 2023 change to how some social
fields are counted affects levels rather than ordering.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 top_ten.py    # out/top_ten.json
python3 chart.py      # out/top_ten.svg
```

Reads the cached daily history in `../social-price-backtest/data/raw`.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
