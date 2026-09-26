# incident-watch

Watch for hacks, exploits and freezes being discussed, per coin.

```bash
LUNARCRUSH_API_KEY=... python3 incident_watch.py --drop 10
```

Takes every coin down more than `--drop` percent in 24 hours, pulls each one's
topic posts, and surfaces any carrying security language, newest first, with
links.

## Three approaches that do not work

**Generic topics.** The bare topic `exploit` returns football results and a
Watch Dogs 2 review. `hack` is ordinary English carrying 199 million
interactions a day from 25,000 people. Same problem as
[name-collision](../name-collision/), pointed the other way.

**Security accounts.** `/public/creator/twitter/:name/posts/v1` resolves and
returns history, but on 2026-09-25 the newest post it held for a well-known
investigator with 1.09M followers was **148 hours old**. Useful for looking
backwards, not for a watch.

**Attention spikes.** This is the one worth knowing about. On 2026-09-25 $ZANO
fell 23% while a post reading "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO AND
fUSD IMMEDIATELY" circulated with 2,934 interactions. Its aggregate metrics
that hour:

| | |
|---|---|
| contributors | 47/hour, against a 50/hour two-day baseline |
| sentiment | 88 out of 100 |
| interactions | a single 2,071 spike, back to normal the next hour |

Nothing in the aggregates said anything was wrong. The
[loud-dumps](../loud-dumps/) signal, which needs a 3-sigma attention spike on
the day of a fall, would not have fired. The post text is the only place the
incident exists.

## What does work

Read the posts for coins that are already moving, and require two things of
each post:

1. **It names the coin.** The ticker with a `$`, the bare ticker as a
   standalone token, or the project's name. On the first run this was missing
   and $ELF surfaced a post about Stable Diffusion models while $LIT surfaced
   one about a neighbour's motion-sensor light, both flagged on security
   wording unrelated to either coin. Adding the check dropped both and kept
   $ZANO, whose warning names the coin twice.
2. **It carries incident language.** Specific phrases rather than single
   words: `drained`, `rug pull`, `postmortem`, `withdrawals suspended`,
   `rollback`, `depeg`, `cease all`, `do not buy`. A generic `hack` alone
   matches "growth hack", so the words that survive are the ones with no
   common non-crypto use.

## The timing, which is the point

The tool works. It also settles what it is for.

| time (UTC) | what happened |
|---|---|
| Fri 10:00 | $ZANO trading at $6.87 |
| **Fri 11:00** | **$5.83. A 20% fall in one hour** |
| Fri 17:16 | "CEASE ALL ECONOMIC ACTIVITY INVOLVING ZANO AND fUSD IMMEDIATELY" posted, 11,164 interactions |
| Fri 18:03 | 24-hour chain rollback listed publicly, impact 8/10 |
| Sat 11:40 | "We expect economic activity to be able to resume ... within the next 24 hours" |

The price moved **6 hours and 16 minutes** before the public warning. By the
time the most-shared post about the incident existed, the fall had already
happened and the price had been flat at the bottom for five hours.

This is the same ordering [who-moved-first](../who-moved-first/) finds on
pumps, on an incident rather than a rally. The tool tells you **why** a coin
is falling, hours faster than a news cycle and hours slower than the market.
It is an explanation, not a warning.

$ZANO closed the episode up 17.9% the next day.

## On 2026-09-25

Ten coins qualified. Nine were clean. $ZANO returned two posts, 1.3 and 2.1
hours old: a scheduled 24-hour chain rollback listed with an impact rating,
and the warning quoted above.

## What this does not do

It reports what is being said and who said it. It does not decide whether a
claim is true, and neither should you. A post saying a project was drained is
evidence that somebody said so, nothing more, and the fastest accounts in this
space are sometimes wrong and occasionally malicious.

Rate of false negatives is unmeasured. An incident discussed only in a Discord,
or announced by a project before the price moves, will not appear here at all,
because the scan starts from coins that are already falling.

## Cost and cadence

One coins-list call plus one topic-posts call per falling coin, so roughly 10
to 30 requests a run. Cheap enough to run every 15 minutes. Posts arrive in the
feed within one to two hours of being made, which is the real latency floor.

## Running it

```bash
python3 incident_watch.py                 # 10%+ fallers, posts from the last 24h
python3 incident_watch.py --drop 5        # wider net, more noise
python3 incident_watch.py --hours 6       # only very fresh posts
```

Writes `out/incidents.json`.
