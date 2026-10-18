# chain-hype

**Which chains are used, and which are only talked about.**

Measured 2026-10-18. Usage is fees paid over 30 days from DeFiLlama. Attention
is interactions on posts verifiably about the chain. Both as a share of the 14
chains measured, so the ratio is what matters rather than either column alone.

| Chain | Attention | Fees | Ratio | |
|---|---|---|---|---|
| Sei | 0.9% | 0.1% | **8.3x** | talked about more than used |
| Aptos | 0.9% | 0.1% | **8.2x** | |
| Sui | 1.8% | 0.4% | **4.9x** | |
| Near | 2.3% | 0.8% | 3.0x | |
| Tron | 1.8% | 0.7% | 2.7x | |
| Optimism | 0.6% | 0.5% | 1.2x | roughly matched |
| Ethereum | 31.6% | 28.8% | 1.1x | |
| Solana | 41.3% | 37.7% | 1.1x | |
| Hyperliquid L1 | 12.2% | 13.7% | 0.9x | |
| Avalanche | 0.7% | 0.9% | 0.8x | |
| Base | 3.3% | 4.5% | 0.7x | |
| Arbitrum | 0.9% | 1.7% | 0.5x | used more than talked about |
| BSC | 1.5% | 7.1% | **0.2x** | |
| Polygon | 0.2% | 3.1% | **0.03x** | |

## What it found

**The loud chains are mostly earning it.** Solana takes 41% of the attention
and pays 38% of the fees. Ethereum is 32% against 29%. Hyperliquid is the third
largest on both. The intuition that Solana is over-hyped does not survive
contact with what people pay to use it.

**Avalanche is not over-hyped, it is small.** It reads 0.8x, which is matched.
What it is not is loud: 0.7% of all the attention measured here. A chain can
feel everywhere while being a rounding error, and that is a property of a feed
rather than of a market.

**The over-indexing is the newer L1s.** Sei, Aptos and Sui take five to eight
times more attention than their share of fees.

**The strangest column is the bottom.** BSC pays 7.1% of the fees on 1.5% of
the attention and Polygon pays 3.1% on 0.2%. Treat both carefully: this reads
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

One snapshot, not a long window. English-language social data only. A fee-share
comparison flatters chains with expensive blockspace and penalises those that
made it cheap deliberately, which is a design choice rather than a failure.
Nothing here says a chain is good or bad, only whether the talk and the paying
are in proportion.

Run: `LUNARCRUSH_API_KEY=... python3 chain_hype.py`
