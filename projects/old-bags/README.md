# old-bags

The 2021 bags are beating the memecoins.

```bash
LUNARCRUSH_API_KEY=... python3 old_bags.py
python3 chart.py
```

## 2026-09-28

313 coins over $50M. Market median for the week: **+0.0%**.

| cohort | n | median 7d | beat the market |
|---|---:|---:|---:|
| 2021 bags, still 50%+ below their peak | 75 | **+1.4%** | **63%** |
| memecoins | 32 | **-4.0%** | 28% |

Best of the bags:

| coin | 7d | off its 2021 peak |
|---|---:|---:|
| $AMP | +36% | -99% |
| $GRT (The Graph) | +32% | -94% |
| $PROM | +29% | -85% |
| $RUNE (THORChain) | +21% | -95% |
| $NMR (Numeraire) | +20% | -84% |
| $ALGO | +18% | -91% |
| $BCH | +18% | -79% |
| $XDC | +14% | -70% |
| $SC (Siacoin) | +14% | -98% |

Worst of the memes: $DOG -23%, $SPX6900 -19%, $NPC -17%, $USELESS -12%,
$PEPE -12%, $ARC -12%.

$QNT peaked in 2021 and, after +242% this week, sits only 37% below that
peak. It no longer clears the 50%-down bar, so it dropped out of the cohort
it would have headlined. See [comeback](../comeback/).

## Both cohorts are defined from data

**The 2021 bags**: a coin whose all-time-high market cap across six years of
cached daily history landed in 2021 or earlier, and which still sits more
than 50% below it. No hand-picking, no narrative label, no judgment about
what kind of project it is.

**Memecoins**: LunarCrush's own `meme` category, unedited.

This matters because "old coins are pumping" is the easiest story in crypto
to tell badly. Pick nine names that went up and you can prove anything. The
cohort here is every coin that meets a rule written before the returns were
looked at, and it is 75 coins, not nine.

## What this is not

One week. The same test on a different week will say something else, and the
cohort medians are +1.4% against -4.0%, which is a real gap and a small one.
[graveyard](../graveyard/) made a narrower version of this point on 2026-09-22
and the same cohort fell a median 6.8% the next day.

Nothing here says old coins are better. It says that in the week ending
2026-09-28, capital moved toward names that have been down for four years and
away from names invented in the last two.

## Method

Universe: coins over $50M market cap and $1M daily volume, tickers of two
characters or more, deduplicated by symbol because LunarCrush lists twelve
tickers twice under different ids. Peak market cap and peak year come from
`../social-price-backtest/data/raw`, so a coin whose true peak predates 2020
has an understated drawdown.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
