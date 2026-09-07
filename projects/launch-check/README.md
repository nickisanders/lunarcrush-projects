# Launch Check

A ticker is trending. How many tokens actually carry that name, and is the volume real?

```bash
python3 launch_check.py LAPTOP
python3 chart.py out/laptop.json
```

No API key. Reads GeckoTerminal directly.

## Why it exists

Every celebrity or news-driven token launch produces the same situation: a name spreads faster than any way to verify it, and someone searching a screener finds several contracts that look identical. The tool answers two questions in one call.

**How many distinct contracts carry this name?** Pools are grouped by contract, because one token can have many pools and counting pools would overstate how many separate things share a ticker.

**Is the volume plausible?** Screeners rank by volume, and volume is the easiest number on a chart to manufacture. Two derived numbers do the work:

- **Turnover** = 24h volume divided by pool liquidity. A pool holding $495k that reports $325M of daily volume has traded its entire depth 657 times in a day. Healthy pools turn over a few times.
- **Volume per trading wallet** = 24h volume divided by distinct buyers plus sellers. Real retail does not average six figures on a token that is hours old.

## The $LAPTOP launch, 2026-09-07

Run on the day the name started circulating:

| | |
|---|---|
| Distinct contracts carrying the ticker | **37** |
| Networks | base, bsc, robinhood, solana |
| Combined liquidity | $7.6M |
| Combined reported 24h volume | **$1.01B** |
| Combined turnover | 133x |
| Contracts turning over more than 20x | 19 |

The three busiest, all on BSC and all created that day:

| Liquidity | 24h volume | Turnover | Volume per wallet |
|---|---|---|---|
| $495k | $325.1M | 657x | $113,873 |
| $406k | $320.7M | 790x | $138,224 |
| $1.2M | $317.2M | 267x | $174,553 |

## What it cannot do

**It cannot tell you which contract is official.** Neither can a screener, and that is the finding rather than a limitation to apologise for. Verifying a launch means a signed announcement from the party involved, published somewhere they control. On-chain data cannot substitute for that.

It also says nothing about who deployed anything. High turnover is consistent with wash trading and with a genuine frenzy; the tool reports the ratio and leaves the inference where it belongs.
