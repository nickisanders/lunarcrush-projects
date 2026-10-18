# chain-hype

**Which chains are used, and which are only talked about.**

Measured 2026-10-18. Usage is fees paid over 30 days from DeFiLlama. Attention
is interactions on posts verifiably about the chain. Both as a share of the 14
chains measured, so the ratio is what matters rather than either column alone.

Measured 2026-10-18 across 14 chains. Usage is taken three ways, because a
result that holds on only the metric you happened to choose is not a result.

| Chain | Attention | Fees 30d | DEX 30d | TVL |
|---|---|---|---|---|
| Solana | 41.3% | 37.7% | 34.1% | 7.7% |
| Ethereum | 31.6% | 28.8% | 20.2% | 64.3% |
| Hyperliquid L1 | 12.2% | 13.7% | 4.5% | 1.3% |
| Base | 3.3% | 4.5% | 15.0% | 7.9% |
| Near | 2.3% | 0.8% | 2.6% | 0.3% |
| Tron | 1.8% | 0.7% | 0.9% | 7.2% |
| Sui | 1.8% | 0.4% | 0.8% | 0.6% |
| BSC | 1.5% | 7.1% | 13.4% | 7.1% |
| Sei | 0.9% | 0.1% | 0.1% | 0.0% |
| Aptos | 0.9% | 0.1% | 0.1% | 0.1% |
| Arbitrum | 0.9% | 1.7% | 2.6% | 1.8% |
| Avalanche | 0.7% | 0.9% | 2.0% | 0.8% |
| Optimism | 0.6% | 0.5% | 0.7% | 0.0% |
| Polygon | 0.2% | 3.1% | 2.9% | 0.9% |

Every column is a share of the 14 chains measured, so the comparison between
columns is the point rather than any figure on its own.

## What it found

Three usage measures, not one, because a finding that only holds on the metric
you happened to pick is not a finding. Ratios are attention share divided by
usage share, so above 1 means talked about more than used.

| Chain | vs fees | vs DEX | vs TVL |
|---|---|---|---|
| Sei | 8.3x | 7.1x | 22.9x |
| Aptos | 8.2x | 10.2x | 16.0x |
| Sui | 4.9x | 2.2x | 2.8x |
| Near | 3.0x | 0.9x | 8.1x |
| Tron | 2.7x | 2.0x | 0.3x |
| Optimism | 1.2x | 0.8x | n/a |
| Ethereum | 1.1x | 1.6x | 0.5x |
| Solana | 1.1x | 1.2x | 5.4x |
| Hyperliquid L1 | 0.9x | 2.7x | 9.3x |
| Avalanche | 0.8x | 0.4x | 0.9x |
| Base | 0.7x | 0.2x | 0.4x |
| Arbitrum | 0.5x | 0.3x | 0.5x |
| BSC | 0.2x | 0.1x | 0.2x |
| Polygon | 0.03x | 0.1x | 0.2x |

**What survives all three.** Sei, Aptos and Sui are talked about more than they
are used on every measure. BSC, Polygon and Arbitrum are used more than they
are talked about on every measure. Those are the findings worth repeating.

**Avalanche is not over-hyped, it is small.** Matched or slightly under on all
three, and 0.7% of all the attention measured. A chain can feel everywhere
while being a rounding error, and that is a property of a feed rather than of a
market. This was the question that started the work and the answer is no.

**Solana depends on what you think a chain is for.** Matched on fees and DEX
volume, 5.4x on TVL: 41% of the attention against 7.7% of the capital.
Ethereum is the mirror, holding 64.3% of TVL on 32% of the attention, which
makes it under-hyped by that measure and matched by the others. Anyone claiming
either chain is over or under-hyped is choosing a metric, and should say which.

**The bottom of the table wants care rather than a headline.** BSC pays 7.1% of
the fees on 1.5% of the attention and Polygon 3.1% on 0.2%. This reads
English-language social data, and a chain whose users talk somewhere else looks
quiet whatever it processes.

## Why the attention measure is built this way

Chain names collide with ordinary language worse than tickers do. `avalanche`
returns snow videos, `base` is a common word, `tron` is a film, `near` returns
an obituary. Counting a topic's raw posts ranks chains by how ordinary their
name is.

A ticker test alone does not fix it. It reads 13% on `ethereum` and 5% on
`solana`, because those communities write the chain's name rather than its
cashtag, while a trading-heavy community writes `$SEI` constantly. That ranks
chains by cashtag habit instead.

So one filter is applied identically to all 14: a post counts when it names the
chain or its ticker **and** carries a crypto term from a fixed vocabulary.
Attention is the interactions on what survives. The topics themselves were
verified first, which is why this uses `avax` rather than `avalanche` and
`polygon-ecosystem-token` rather than `polygon`.

## Why fees

Fees are what someone actually handed over for blockspace. Transaction counts
are cheap on purpose for many chains, active addresses are farmable, and TVL is
capital parked rather than used. DEX volume and TVL are collected alongside so
the choice can be argued with.

## What this cannot say

One snapshot, not a long window. The three metrics disagree for four of the
fourteen chains, and where they disagree there is no answer here, only a choice
of definition. TVL is the weakest of the three, since parked capital is not
usage and it structurally favours the chain holding most DeFi collateral. English-language social data only. A fee-share
comparison flatters chains with expensive blockspace and penalises those that
made it cheap deliberately, which is a design choice rather than a failure.
Nothing here says a chain is good or bad, only whether the talk and the paying
are in proportion.

Run: `LUNARCRUSH_API_KEY=... python3 chain_hype.py`
