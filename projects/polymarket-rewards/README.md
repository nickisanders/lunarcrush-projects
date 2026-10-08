# polymarket-rewards

Does reciprocal trading concentrate in the Polymarket markets that pay makers
for liquidity?

```bash
python3 fills.py --days 3                                   # pass 1: collect tokens
python3 markets.py --from-fills out/fills-<A>-<B>.json.gz   # resolve + snapshot rewards
python3 fills.py --from-block <A> --to-block <B> \
        --token-map out/markets-latest.json                 # pass 2: segmented
python3 analyse.py
```

No API key, no account. Polygon RPC and Polymarket's public Gamma API.

## The question

Polymarket pays makers a daily rate for resting liquidity meeting a market's
`rewardsMinSize` within its `rewardsMaxSpread`. If a share of volume exists to
collect that rather than to express a view, it should show up as pairs of
addresses trading with each other repeatedly in both directions, concentrated in
the markets that pay.

The comparison is within-platform and within-period, which is what makes it
worth running: paying and non-paying markets sit on the same venue over the same
days with the same mechanics, so the only systematic difference is the
incentive. A ratio near 1 is the null, and the null is a publishable result.

## What this cannot say

Two addresses trading reciprocally are only self-dealing if one party controls
both, and fill events do not say who controls an address. A market maker quoting
both sides against a frequent counterparty produces reciprocity honestly. A gap
between the arms is evidence that the incentive shapes trading. It is not
evidence that any pair is wash trading, and nothing here prints that verdict.

Establishing control would mean linking proxy wallets to common funders, which
is a separate piece of work the scope calls stage 3.

## Three things that were measured rather than assumed

**Reward status does not survive a market closing.** Across 80 closed markets
sampled on 2026-10-07, not one retained `clobRewards` or `rewardsMinSize`, on
either the Gamma or the CLOB API. Reward status is unrecoverable after the fact.
That is why every resolution is written as a dated snapshot and never
overwritten, and why this study cannot be run retrospectively on an arbitrary
past window — only forward from a snapshot, or over a window whose markets are
still open.

**Enumerating the live universe does not work.** Gamma's offset paging stops
near 2,100 markets, well short of the live set. Attributing a one-hour sample
against that enumeration left **98.6% of notional unmatched**, nearly all of it
in sports markets that were live and simply absent from the enumeration.
Resolving the tokens that actually traded, by id, took attribution to 79% of
notional and 88% of tokens.

**Gamma's default query excludes closed markets, and that may sink the
comparison.** The top tokens by notional over a week are overwhelmingly sports
and esports markets that have since resolved, and they return nothing until
`closed=true` is asked for. Worse, a closed market has had its reward fields
stripped, so it comes back looking unpaid. Labelling those `False` would quietly
sweep most of the week's volume into the control arm and produce a confident,
meaningless ratio. Closed markets are therefore labelled `None`, never `False`,
and excluded from both arms.

The consequence is that **the paid-versus-unpaid comparison cannot be run
retrospectively on a venue whose volume closes within days.** It has to run
forward: snapshot reward status daily, then measure the window that follows.
Stages 1 and 2 are built and correct; the comparison itself is waiting on
prospective snapshots.

**Gamma silently drops batched ids.** A request carrying 50 `clob_token_ids`
returns markets covering 18 of them; a request carrying 5 covers all 5. Tokens
that fail in a batch resolve fine alone. The resolver therefore batches at 5 and
then retries every unmatched id individually, which is what moved coverage from
46% to 88%. A batch size chosen for speed would have quietly thrown away half
the data and the totals would still have looked plausible.

## Scale

A full week, blocks 94,832,989 to 95,137,189, streamed 2026-10-07:

| | |
|---|---|
| Fills | 13,805,772 |
| Notional | $594,886,604 |
| Distinct trader addresses | 68,174 |
| Distinct outcome tokens traded | 112,616 |

Full history is not reachable on free infrastructure. A week is, and the
Columbia study that put wash-trading estimates into the press looked at a single
week.

## Half the notional has no counterparty

**47.8% of fill notional has the exchange router as the counterparty, not
another trader** — 4,853,630 of 13,805,772 fills, $284,344,536. Those are not
matched orders. Every transaction carrying a router leg also fires a
`PositionSplit` on the conditional tokens contract: when nobody is selling the
side you want, the protocol mints a fresh complete set against collateral and
hands you the side you asked for.

That is real exposure through a different mechanism, not fake volume, and the
distinction matters for anyone building a counterparty graph from these events.
**Who-trades-with-whom analysis, wash-trading studies included, can see about
half the money.** The other half has no counterparty to analyse. Router legs are
excluded from pair analysis here and the excluded amount is reported.

Only one exchange contract emits fills today,
`0xe111180000d2663c0091e4f400237545b87b996b`. The two legacy exchanges were
checked on 2026-10-07 and are dormant; they stay in the query so a run over
older history is correct rather than silently empty.

## Daily snapshots

Reward status is unrecoverable once a market closes, so the paid-versus-unpaid
comparison cannot be run backwards over an arbitrary week. It has to be run
forward from snapshots taken while the markets were open.

`snapshot.sh` captures the live board once a day. Installed on this machine as a
LaunchAgent at 09:15 local:

```bash
cp com.proofofcrowd.polymarket-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.proofofcrowd.polymarket-snapshot.plist
launchctl start com.proofofcrowd.polymarket-snapshot   # force one run
launchctl list | grep polymarket                       # confirm it is registered
```

To stop it:

```bash
launchctl unload ~/Library/LaunchAgents/com.proofofcrowd.polymarket-snapshot.plist
```

Each snapshot is about 1.7MB and lands in `out/history/`, which is gitignored.
A year is kept and older ones are pruned. The log is `out/snapshot.log`.

First capture: 2026-10-08, 2,100 live markets, 752 paying rewards (35.8%),
$17,001 a day advertised across them. The comparison becomes runnable once there
are enough days to pair a snapshot against the fills in the window that follows
it, so roughly a week.

## Notes

Fills are aggregated as they stream and never retained raw, because the
questions here are about pairs and markets rather than individual trades.

Pairs are keyed by `maker|taker|segment`, which is why there are two passes.
Reward status is a property of the market and is only known once the traded
tokens have been resolved. Keying pairs by token instead would need one pass but
grows with the fill count rather than the pair count — millions of entries to
support a two-way comparison.

`rewardsMinSize` is set on markets that pay nothing, so a market counts as paid
only when it carries a funded `clobRewards` entry.

Polygon's public RPCs are uneven. `polygon-rpc.com` returns "tenant disabled",
`rpc.ankr.com/polygon` requires a key, and `polygon-bor-rpc.publicnode.com`
allows 10,000-block ranges but times out at that size against this density, so
the streamer asks for 2,000 and halves on failure. Override with `POLYGON_RPC`.
