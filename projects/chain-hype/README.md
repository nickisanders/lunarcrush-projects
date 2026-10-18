# chain-hype

**Which chains are used, and which are only talked about.**

Measured 2026-10-18 across 18 chains. Usage is taken three ways, because a
result that holds on only the metric you happened to choose is not a result.
Attention is interactions on posts verifiably about the chain.

| Chain | Attention | Fees 30d | DEX 30d | TVL |
|---|---|---|---|---|
| Ethereum | 27.2% | 28.0% | 20.2% | 63.8% |
| Solana | 24.4% | 36.6% | 34.0% | 7.6% |
| Cardano | 14.8% | 0.04% | 0.02% | 0.1% |
| Hyperliquid L1 | 11.6% | 13.3% | 4.5% | 1.3% |
| Base | 3.8% | 4.4% | 15.0% | 7.9% |
| Near | 2.7% | 0.7% | 2.6% | 0.3% |
| Tron | 2.4% | 0.7% | 0.9% | 7.2% |
| Sui | 2.1% | 0.3% | 0.8% | 0.6% |
| Cronos | 1.8% | 0.05% | 0.1% | 0.2% |
| BSC | 1.8% | 6.9% | 13.4% | 7.4% |
| Hedera | 1.5% | 0.02% | 0.1% | 0.0% |
| Aptos | 1.3% | 0.1% | 0.1% | 0.1% |
| Arbitrum | 1.2% | 1.6% | 2.6% | 1.8% |
| Sei | 1.1% | 0.1% | 0.1% | 0.0% |
| Optimism | 0.9% | 0.5% | 0.7% | 0.0% |
| Avalanche | 0.8% | 0.9% | 2.0% | 0.8% |
| TON | 0.3% | 2.7% | 0.1% | 0.1% |
| Polygon | 0.2% | 3.0% | 2.9% | 0.9% |

Every column is a share of the 18 chains measured, so the comparison between
columns is the point rather than any figure on its own.

## What it found

Ratios are attention share divided by usage share, so above 1 means talked
about more than used.

| Chain | vs fees | vs DEX | vs TVL |
|---|---|---|---|
| Cardano | 348x | 669x | 185x |
| Hedera | 70x | 26x | 34x |
| Cronos | 40x | 35x | 10x |
| Aptos | 12x | 14x | 22x |
| Sei | 10x | 8.5x | 28x |
| Sui | 6.1x | 2.7x | 3.4x |
| Near | 3.6x | 1.0x | 9.5x |
| Tron | 3.6x | 2.6x | 0.3x |
| Optimism | 1.8x | 1.2x | n/a |
| Ethereum | 1.0x | 1.3x | 0.4x |
| Avalanche | 0.9x | 0.4x | 1.1x |
| Hyperliquid L1 | 0.9x | 2.6x | 8.9x |
| Base | 0.9x | 0.3x | 0.5x |
| Arbitrum | 0.7x | 0.5x | 0.7x |
| Solana | 0.7x | 0.7x | 3.2x |
| BSC | 0.3x | 0.1x | 0.2x |
| TON | 0.1x | 4.4x | 4.9x |
| Polygon | 0.1x | 0.1x | 0.2x |

**Cardano is the largest gap in the set by two orders of magnitude.** It is the
third loudest chain measured, 7.2 million interactions on posts that name it
and talk about crypto, behind only Ethereum and Solana and ahead of
Hyperliquid. It collected $0.5 million in fees over the same 30 days, against
Solana's $456 million. That is 348x on fees, 669x on DEX volume and 185x on
TVL, and a chain being over-talked on every measure at once is rare. Everything
else at the top of this table is a small chain with a loud trading community.
Cardano is a top-three attention share attached to a rounding error of usage.

**Hedera and Cronos are the same shape, smaller.** Both run 10x to 70x over on
all three measures. Neither is close to Cardano's absolute volume, so these are
ordinary small-chain hype gaps rather than the outlier.

**TON is the clearest case of the metric choosing the answer.** It pays 2.7% of
all fees measured, more than Arbitrum and Avalanche combined, on 0.3% of the
attention, so by fees it is the most under-talked chain here at 0.1x. By DEX
volume and TVL it reads 4.4x and 4.9x the other way. Both are true: TON
processes a lot of cheap transfers and runs very little DeFi, so a fee measure
and a DeFi measure describe different chains. Anyone quoting a single number
for TON is picking the one that suits them.

**Avalanche is not over-hyped, it is small.** Matched or slightly under on all
three, and 0.8% of all the attention measured. A chain can feel everywhere
while being a rounding error, and that is a property of a feed rather than of a
market. This was the question that started the work and the answer is no.

**Solana depends on what you think a chain is for.** Under on fees and DEX
volume, 3.2x on TVL: 24% of the attention against 7.6% of the capital.
Ethereum is the mirror, holding 64% of TVL on 27% of the attention. Anyone
claiming either chain is over or under-hyped is choosing a metric, and should
say which.

**The bottom of the table wants care rather than a headline.** BSC pays 6.9% of
the fees on 1.8% of the attention and Polygon 3.0% on 0.2%. This reads
English-language social data, and a chain whose users talk somewhere else looks
quiet whatever it processes.

## Every number here depends on the basket

The 14-chain run published earlier the same day put Solana at 41.3% of
attention and 1.1x on fees. Adding four chains moved it to 24.4% and 0.7x,
because Cardano alone absorbed 15% of the attention share while adding
essentially no usage to the denominator. Nothing about Solana changed.

Shares are shares of whatever was measured, and the ratios inherit that. A
chain's position relative to its neighbours is stable, its absolute multiple is
not, and a figure from one run should not be quoted against a figure from
another. The sample moves too: Ethereum returned 146 on-topic posts in the
morning run and 110 in this one.

## Which chains are in, and why the rest are out

A chain is included when its verified topic carries enough on-topic posts for
the interaction figure to mean something. Berachain returned 1 post, Celo 4,
Mantle 8, Linea 20 and zkSync 44, which is too thin for one viral post not to
decide the answer, and Scroll has no usable topic at all. All six were checked
and left out on that basis.

TON is the thinnest chain included, at 28 on-topic posts against a floor of 67
for every other chain, so it moves more on a single post than the rest and its
0.3% attention share should be read loosely. It is in because the fee side of
its result is large and does not depend on the social sample being precise.

## Why the attention measure is built this way

Chain names collide with ordinary language worse than tickers do. `avalanche`
returns snow videos, `base` is a common word, `tron` is a film, `near` returns
an obituary, and `ton` appears in "a ton of" constantly, which is why TON is
matched on `toncoin`, the cashtag or "TON blockchain/network/chain" rather than
the bare word. Counting a topic's raw posts ranks chains by how ordinary their
name is.

A ticker test alone does not fix it. It reads 13% on `ethereum`, 5% on `solana`
and 13% on `cardano`, because those communities write the chain's name rather
than its cashtag, while a trading-heavy community writes `$SEI` constantly.
That ranks chains by cashtag habit instead.

So one filter is applied identically to all 18: a post counts when it names the
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

One snapshot, not a long window. The three metrics disagree for five of the
eighteen chains, and where they disagree there is no answer here, only a choice
of definition. TVL is the weakest of the three, since parked capital is not
usage and it structurally favours the chain holding most DeFi collateral.
English-language social data only. A fee-share comparison flatters chains with
expensive blockspace and penalises those that made it cheap deliberately, which
is a design choice rather than a failure. Nothing here says a chain is good or
bad, only whether the talk and the paying are in proportion.

Run: `LUNARCRUSH_API_KEY=... python3 chain_hype.py`
