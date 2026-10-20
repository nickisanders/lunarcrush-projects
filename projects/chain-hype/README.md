# chain-hype

**Retracted in part, 2026-10-20.** This project set out to compare how much a
chain is talked about against how much it is used. The usage half is sound and
is kept below. The attention half does not survive checking and every ratio
built on it has been withdrawn.

## What went wrong

The attention measure counted interactions on posts that name a chain and
carry a crypto term, one filter applied identically to every chain. That
filter was built to keep out snow videos for `avalanche` and the film for
`tron`, and it does. It does nothing about a post that names eight chains at
once.

A TikTok captioned `8 Cryptos: Which Will Explode and Which Will Crash?
#Bitcoin #Solana #XRP #Cardano #pepe` names the chain and says "crypto", so it
counted in full toward Cardano, and toward Solana, and toward every other
chain it tagged. Measuring the share of each chain's interactions that came
from posts naming three or more chains:

| TON | Base | Polygon | Avalanche | Aptos | Optimism | Cardano |
|---|---|---|---|---|---|---|
| 90.1% | 77.3% | 56.8% | 54.6% | 48.5% | 42.6% | 23.2% |

Base and TON were mostly measuring hashtag dumps. Checking Cardano's loudest
posts directly, the top five were Wojak meme videos about obesity, gambling
addiction and bus drivers, which carried 38% of its interactions, and the
loudest post in the raw topic was a TikTok dance video that says "Cardano"
zero times.

The sample is also unstable. Two calls minutes apart put Cardano at 7.18M and
then 7.52M interactions, and Ethereum at 13.2M then 19.4M. The post endpoint
returns a different sample each time, so no ratio built on it is reproducible.

**So the headline finding is withdrawn.** Cardano was reported as over-talked
by 348x on fees, 669x on DEX volume and 185x on TVL. Those numbers divided a
contaminated numerator by a sound denominator. Nothing here now says which
chains are over or under-hyped, because this cannot currently measure the
hype.

## What the usage data shows

Unaffected, because it never touched social data. All from DeFiLlama, fees and
DEX volume as 30-day totals, TVL as of the measurement date.

The most useful thing in it is how much fee revenue each chain produces per
dollar of capital parked on it. Chains with under $100M TVL are left out, as
the ratio gets noisy when the denominator is small.

| Chain | TVL | Fees 30d | Fees per $1,000 of TVL |
|---|---|---|---|
| Hyperliquid L1 | $1.0B | $165.4M | $164.14 |
| Solana | $5.9B | $445.1M | $75.76 |
| Polygon | $0.7B | $36.6M | $53.71 |
| Near | $0.2B | $8.8M | $40.96 |
| Avalanche | $0.6B | $11.2M | $19.25 |
| BSC | $5.9B | $83.2M | $14.04 |
| Arbitrum | $1.4B | $19.6M | $13.92 |
| Base | $6.2B | $54.1M | $8.79 |
| Sui | $0.5B | $4.2M | $8.76 |
| Ethereum | $49.5B | $345.6M | $6.98 |
| Cronos | $0.1B | $0.6M | $4.11 |
| Tron | $5.5B | $8.1M | $1.47 |

Hyperliquid gets 111x out of a parked dollar what Tron does, and Solana 11x
what Ethereum does.

**"Biggest chain" has three answers.** By TVL it is Ethereum with 63.7% of all
capital measured. By fees it is Solana at 36.4%. By DEX volume Solana again at
33.9%, with Base third at 14.9% while paying 4.4% of the fees, because Base
made its blockspace cheap deliberately.

None of the three is wrong. They measure different things and a chain built
for one reads as weak on another, which is worth knowing before accepting
anyone's league table. Hyperliquid at $164 per $1,000 is a trading venue and
Tron at $1.47 is somewhere people park stablecoins, and both are reasonable
things to be.

## Why fees, and what fees cannot say

Fees are what someone actually handed over for blockspace. Transaction counts
are cheap on purpose for many chains, active addresses are farmable, and TVL
is capital parked rather than used. DEX volume and TVL are collected alongside
so the choice can be argued with.

A fee comparison flatters chains with expensive blockspace and penalizes those
that made it cheap on purpose, which is a design decision rather than a
failure. One snapshot, not a long window. Nothing here says a chain is good or
bad.

## What would make the attention half work

Not attempted yet, and the project claims nothing until it is. A post naming
several chains would need splitting between them rather than counted whole for
each, the sample would need to be fixed rather than redrawn per call, and the
result would need to reproduce across runs before any ratio gets published.

Run: `python3 chain_hype.py` for the full table, which still computes the
attention columns. Treat those columns as unreliable.
