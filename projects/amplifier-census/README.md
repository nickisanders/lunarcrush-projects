# amplifier-census

One cross-token signal, produced by two unrelated behaviours.

```bash
LUNARCRUSH_API_KEY=... python3 amplifiers.py
python3 chart.py
```

## The question

"Does this account also post about everything else" is one of the three signals
behind a manufactured-attention verdict, and it sounds unambiguous. An account
appearing in fifty token conversations looks like an amplifier network.

It is not one thing. Two unrelated behaviours produce the identical number:

- **A list poster.** One post naming twenty-eight tickers places the account
  inside dozens of conversations at once. That is somebody writing a comparison.
- **A serial poster.** Fifty separate single-token posts, each on the same
  template. That is somebody working through a catalogue.

This counts the distinct tickers in every post from the accounts that reach the
most tokens, which is what separates them.

## 2026-10-13

200 coins screened, **112 topics verified**, 87 rejected.

**One account appears in 51 of the 112 verified conversations.** The median
account that appears in more than one appears in 2. There are
1,021 accounts in two or more.

That reads as an amplifier network until the posts are counted. Across 1,200
posts from the 40 accounts reaching the most tokens:

| tokens named in a post | posts | share |
|---|---:|---:|
| 1 | 526 | 44% |
| 2 | 48 | 4% |
| 3 to 7 | 208 | 17% |
| **8 or more** | **418** | **35%** |

Two populations, not one. **35% of these posts name eight tokens or more**, and a
single post of that kind places the account inside dozens of conversations at
once. Another 44% name exactly one, which is an account working through a
catalogue one post at a time.

Both register identically as "an account that also posts about other tokens".
Only one of them is doing anything that resembles a campaign, and the number
alone cannot say which.

## Why the topics are verified first

Short tickers collide with ordinary English, and the collisions are not subtle.
`near` returns an obituary, `sky` returns bedroom painting, `bat` returns a live
stream, `sand` returns ASMR, `ray` returns true crime. A census of who appears
across many tokens is worthless if the tokens are not the tokens.

Two tests, because one is not enough. A topic's posts have to be about a token,
using `$TICKER` notation or the project's own name, since an official account
writes the latter. And separately its loudest accounts have to be, because a
topic can look acceptable in aggregate while the accounts that dominate it are
somebody else entirely.

Candidates are tried most-specific first, so a colliding ticker gets a chance at
a longer name: `raydium` over `ray`, `starknet` over `strk`, `$near` over `near`.

## Notes

The universe is fetched fresh rather than read from a saved scan, so anyone with
a key can reproduce it. Topic pulls are cached in `out/cache`, so a second run
costs nothing.

A full pass is roughly two hours. Each coin costs up to three topic lookups
before a slug verifies or is dropped, and the API answers in one to three
seconds.

Accounts are counted by creator id, never named. One of the accounts reaching
the most tokens is a large crypto news outlet doing exactly what a news outlet
does, and characterising the others would be an assertion about real people that
this data does not support. The pattern is the finding.

---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
