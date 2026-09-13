# narrative-shift

Where did the attention go? [polygon](../polygon/) found every Ethereum
scaling chain lost its seat in crypto's top-20 conversation between early 2024
and mid 2026. This asks what took the seats.

The answer is that nothing did. The crowd shrank and what remained moved to
Bitcoin.

## Half of crypto is talking about three coins

Share of all daily active contributors, early 2024 (Jan–Mar) against mid 2026
(May–Jul):

| | early 2024 | mid 2026 |
|---|---:|---:|
| BTC | 15.5% | 28.2% |
| ETH | 9.1% | 12.1% |
| SOL | 6.4% | 11.7% |
| **top 3 coins** | **31.0%** | **51.9%** |
| top 10 coins | 41.5% | 64.1% |
| everything outside the top 10 | 58.5% | 35.9% |

Total contributors a day fell from 310,677 to 196,115, down 37%, while the
number of coins in the universe with data rose from 485 to 850. Fewer people,
spread across fewer coins, with more coins to choose from.

Bitcoin's share by year: 39.6% in 2020, falling to a low of 14.9% in 2024,
back to 26.4% in 2026. Early 2024 was the most dispersed crypto conversation
has been in this data.

## Every narrative lost, except three

Share of the crowd touching a coin tagged with each category:

| narrative | early 2024 | mid 2026 | change |
|---|---:|---:|---:|
| NFT | 12.7% | 4.5% | -65% |
| Layer 2s | 5.7% | 2.3% | -59% |
| Gaming | 8.1% | 3.4% | -58% |
| DePIN | 8.3% | 3.5% | -58% |
| AI | 9.7% | 4.5% | -54% |
| RWA | 8.4% | 4.1% | -51% |
| AI agents | 4.8% | 2.9% | -40% |
| Exchange tokens | 5.8% | 3.6% | -39% |
| Privacy | 5.7% | 4.2% | -27% |
| DeFi | 32.3% | 25.6% | -21% |
| ZK | 4.8% | 3.8% | -20% |
| Memecoins | 10.2% | 10.6% | +4% |
| Perps | 1.6% | 3.6% | +131% |
| pump.fun | 0.0% | 3.9% | new |

Layer 1s (56% to 70%) and Bitcoin ecosystem (19% to 30%) rose, and both
contain BTC, which is the concentration finding again from a different angle.

The L2 decline in the Polygon post was not a story about L2s. Every altcoin
narrative fell by a comparable amount. The only things that grew were
memecoins (flat), perps and pump.fun, and those three together are 18% of the
crowd.

## Method

Every coin's daily active contributors are counted toward each category tag
it carries, then divided by the day's total across all coins. Tags are
LunarCrush's current categories, applied retroactively; all of these
narratives existed by early 2024, so the comparison holds. A coin can carry
several tags, so narrative shares are not exclusive and do not sum to 100%.
Each is read as "share of the crowd touching a coin tagged X".

Contributors rather than interactions, for the reason in the Polygon project:
interactions-per-contributor jumps 90x across LunarCrush's 2023 counting
change and contributor counts do not. Pegged assets, single-character tickers
and per-day name collisions are removed before anything is summed, as in
[top-ten](../top-ten/).

## Limits

The universe is the top 1,000 coins by market cap at pull time. A coin that
was heavily discussed in 2024 and has since fallen out of the top 1,000 is not
here, which understates early-2024 dispersion and therefore understates the
consolidation.

The 37% fall in total contributors is measured on this universe. It is not a
claim about how many people are in crypto; it is how many are posting about
these coins on a given day.

## Running it

```bash
source ../social-price-backtest/.venv/bin/activate
python3 shift.py     # out/shift.json
python3 chart.py     # out/shift.svg
```

`tags.json` is the symbol-to-categories map from `/public/coins/list/v2`.
Refresh it with a LunarCrush API key if the categories change.
