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
