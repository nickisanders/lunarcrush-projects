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

## The $LAPTOP case, 2026-09-07

The clearest possible demonstration: the ticker was circulating two days **before** the announced launch date of September 9. Every contract trading under the name on the 7th is therefore a copycat by definition, regardless of what launches later.

Run on that day:

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

## What happened next

Re-run 24 hours later (`compare.py` diffs two runs). Of the six biggest pools from the 7th:

| Chain | Liquidity then | Now | Change |
|---|---|---|---|
| bsc | $495k | $706k | +43% |
| bsc | $406k | delisted | gone |
| bsc | $1.2M | **$542** | -100% |
| base | $483k | delisted | gone |
| robinhood | $109k | $156k | +43% |
| solana | $36k | $36k | -1% |

Two delisted, one drained to $542, and the contract count rose from 37 to 38 as new ones kept arriving.

The pool that fell to $542 **still reports $320M of daily volume**: a turnover of 589,813x. There is no money left in it and the tape has not noticed. Volume is what screeners rank by; liquidity is what you get back when you sell.

## A guard the tool needed

The second run reported $3.39B of combined liquidity and a turnover of 0x. One Base pool was reporting **$3,349,853,387** of depth on $1,198 of daily volume, a bad reading that alone dwarfed the real total.

Contracts reporting more than 50x the median liquidity while doing negligible volume are now excluded from the totals and listed separately rather than silently dropped. Third time a guard against bad external data has been needed in this repo, after the thin-pool check and the partial-day check.

## What it cannot do

**It cannot tell you which contract is official.** Neither can a screener, and that is the finding rather than a limitation to apologise for. Verifying a launch means an announcement from the party involved, published somewhere they control, naming the contract address. Onchain data cannot substitute for that.

The $LAPTOP case shows why the timing check matters most: when a launch has an announced date, anything trading before it is settled without needing any other evidence.

It also says nothing about who deployed anything. High turnover is consistent with wash trading and with a genuine frenzy; the tool reports the ratio and leaves the inference where it belongs.
