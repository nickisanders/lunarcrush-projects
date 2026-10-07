# size-bias

Two signals that look like evidence about a community are partly measuring how
big the token is.

```bash
LUNARCRUSH_API_KEY=... python3 size_bias.py
python3 chart.py
```

## 2026-10-07

164 tokens from the top 200 by market cap, split into three equal-count bands.

| band | median market cap | creator concentration | cross-token accounts |
|---|---:|---:|---:|
| largest | $4,589M | 49% | 21% |
| middle | $813M | 57% | 10% |
| smallest | $267M | 66% | 8% |

Rank correlation with market cap: **-0.24** for concentration and **+0.12** for
cross-token overlap. Real, and noisy.

Neither gradient is manipulation. A token with forty people talking about it
will always have its loudest three owning more of the conversation than one with
four thousand, so concentration falls as tokens get larger. An account that
posts about twenty tokens posts about the big ones by definition, so the largest
tokens inherit those accounts whether or not anyone is paying them.

## Why it matters

A percentile built over a mixed-size population ranks a $267M token against a
$4.6B one on something neither of them chose. The fix is to rank within size
bands, which `--bands` does, and which the scan behind
[Proof of Crowd](https://proofofcrowd.com) now does by default.

Applying it moved 41% of a 196-token population across a flag boundary, in both
directions. Aggregate flag counts barely changed, which is the expected result:
banding redistributes rather than inflating or deflating.

## A caution about the first version of this

The first run of this analysis joined an existing scan to market caps and
reported a 23%-to-1% gradient on cross-token overlap with a +0.28 correlation.
This project, which fetches its own universe, gets 21%-to-8% and +0.12. Same
direction, different magnitude, and the second one is the number that gets
published because it is the one a reader can reproduce.

The ad-hoc version also made cross-token look like the dominant effect. On the
reproducible data concentration is the stronger one.

## Notes

The population is fetched fresh rather than read from a saved scan, so anyone
with a key can reproduce it. Topic pulls are cached in `out/cache`, so a second
run costs nothing.

Tokens with fewer than 25 posts are excluded: below that the signals are noise
rather than measurement.

Every token is every other token's basket for the cross-token figure, which is
what makes it comparable across the population at all. That also means the
figure depends on the size of the population, so it is not comparable between
runs of different sizes.

Both LunarCrush and most crypto data APIs sit behind Cloudflare, which rejects
the default `Python-urllib` User-Agent with a 403 that reads exactly like rate
limiting. Every request here sends one.

<!-- lunarcrush-referral -->
---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
