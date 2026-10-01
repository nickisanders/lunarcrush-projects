# month-review

The month that just ended, ranked two ways: who gained price, and who gained
the crowd.

```bash
LUNARCRUSH_API_KEY=... python3 month_review.py
python3 chart.py
```

Most month-in-review posts rank by price. This ranks by both and puts them
side by side, because the overlap is the finding.

## September 2026

Bitcoin +7%, market median +23%. Only **3 of 10** coins appear on both lists.

**Biggest price gains**

| coin | price | crowd |
|---|---:|---:|
| $QNT | +350% | +1117% |
| $AKE | +268% | +65% |
| $DRV | +171% | +129% |
| $NEAR | +149% | +462% |
| $RAY | +134% | **+1%** |
| $MINA | +119% | +33% |
| $USELESS | +117% | +42% |
| $NIGHT | +114% | +41% |
| $AIOZ | +99% | +94% |
| $AR | +98% | +68% |

**Biggest crowd gains**

| coin | crowd | people a day | price |
|---|---:|---|---:|
| $QNT | +1117% | 213 → 2,593 | +350% |
| $NEAR | +462% | 394 → 2,216 | +149% |
| $ZAMA | +169% | 65 → 175 | +54% |
| $SEI | +165% | 155 → 410 | +60% |
| $ONDO | +146% | 357 → 878 | +43% |
| $ARB | +136% | 171 → 404 | +77% |
| $DRV | +129% | 49 → 112 | +171% |
| $PEAQ | +127% | 73 → 166 | +79% |
| $RUNE | +121% | 107 → 236 | +64% |
| $FIL | +116% | 96 → 207 | +44% |

The two ends of it:

- **$RAY rose 134% and its crowd grew 1%.** 
- **$QNT rose 350% and went from 213 to 2,593 people a day.**

A coin can double with no audience, and an audience can arrive without the
price doing much.

## Method

Price is the live rolling 30-day change, which is close to but not exactly the
calendar month. Crowd is daily active contributors over the last seven days of
the month against the seven days before the month began, so a single viral day
cannot carry it, and it is read by date rather than by row position so a gap in
a coin's history cannot silently shift the two windows against each other.

Universe: coins over $100M market cap and $2M daily volume, pegged and wrapped
assets excluded, deduplicated by ticker. History is pulled only for the top 40
by price change and the top 40 by raw interactions, since nothing outside those
can top either list.

## Limits

A coin that gained a large crowd while sitting outside both of those top-40
pools would be missed. Raising `--top` closes that at the cost of more
requests.

Crowd change is a ratio, so a coin going from 49 to 112 people a day shows as
+129% and one going from 394 to 2,216 shows as +462%, which are not comparable
amounts of attention. The people-a-day column is there to keep that visible.
