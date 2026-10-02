# graveyard

This week's biggest winners are coins that were left for dead.

Takes the largest 7-day gainers live, then looks each one up in six years of
cached history: how far below its own peak market cap it still sits, and the
best seat it ever held in crypto conversation.

## 2026-09-22

Nine of the top twenty gainers sit 80%+ below their own peak market cap. They
were not always nobodies:

| coin | name | best seat ever | off peak | this week |
|---|---|---:|---:|---:|
| $ICX | ICON | **#4** | -99% | +63% |
| $MINA | Mina Protocol | #11 | -90% | +68% |
| $ONE | Harmony | #12 | -99% | +450% |
| $PHA | PHALA | #12 | -91% | +68% |
| $AR | Arweave | #15 | -93% | +64% |
| $ZETA | ZetaChain | #17 | -86% | +58% |
| $AIOZ | AIOZ Network | #24 | -89% | +87% |
| $SYN | Synapse | #28 | -85% | +197% |
| $AURORA | Aurora | #34 | -83% | +561% |

$ARB misses the 80% bar at -69% and belongs on the list anyway: Arbitrum held
**#1**, the most-discussed coin in all of crypto, on its best day. It is up
56% this week.

Of the remaining names in the top twenty, $DRV, $AKE, $ZAMA, $SN53 and
$PIEVERSE are at or near their own highs, and $RHEA has no history in the
cache. The split is roughly half old names, half new ones.

## What this is not

The cohort as a whole is not outperforming. The median 7-day return across
the 24 named fallers from [where-are-they-now](../where-are-they-now/) is
+15.8% against a market median of +14.5% and Bitcoin at +12.4%. That was the
first thing tested and it is a null.

What is true is narrower and sits in the tail: when you sort by the biggest
moves rather than by the average, old names are heavily over-represented. A
coin 99% below its peak needs very little buying to move 450%, which is most
of the mechanism.

## One day later

Grading the list, 2026-09-23:

| coin | the run | next day |
|---|---:|---:|
| $AURORA | +561% | -24.7% |
| $ONE | +450% | -19.9% |
| $SYN | +197% | -10.8% |
| $AIOZ | +87% | -2.5% |
| $MINA | +68% | +4.4% |
| $PHA | +68% | +5.5% |
| $AR | +64% | +1.5% |
| $ICX | +63% | -22.6% |
| $ZETA | +58% | -6.8% |

Median -6.8% against a market median of +0.2% and Bitcoin at -0.5%. Six of the
nine fell.

The split by size of the prior run is the part worth keeping:

| | median next day |
|---|---:|
| runs over +150% (AURORA, ONE, SYN) | **-18.0%** |
| the other six | -0.5% |
| the market | +0.2% |

Spearman between the size of the run and the next day's return: -0.37. $ICX is
the exception, down 22.6% on a +63% run.

This is nine coins over one day, which is far too small to conclude anything
on its own. It points the same way as
[after_the_run.py](../social-price-backtest/after_the_run.py), which measured
382,644 coin-days: the 90-day median after a week up 50-100% is -25.0%, after
100-200% is -35.5%, and after 200%+ is -42.8%.

## Method

Seat is a coin's best-ever rank by daily active contributors against every
other coin on the same day, 2020 to now, with pegged and wrapped assets and
single-character tickers removed, as in [top-ten](../top-ten/). Peak market
cap is the highest daily value in the cached history, so a coin whose peak
predates 2020 has an understated fall.

The universe is today's top 1,000 by market cap, so coins that fell out of it
entirely cannot appear here at all.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
LUNARCRUSH_API_KEY=... python3 graveyard.py   # out/graveyard.json
python3 chart.py                              # out/graveyard.svg
```

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
