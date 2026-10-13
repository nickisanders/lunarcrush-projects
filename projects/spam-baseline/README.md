# spam-baseline

Spam share keeps office hours, which is what makes a dated event testable.

```bash
LUNARCRUSH_API_KEY=... python3 spam_baseline.py --coins 60 --event 2026-10-08
python3 chart.py
```

## 2026-10-13

60 coins, 90 days.

| weekday | median spam share | median posts |
|---|---:|---:|
| Mon | 27.0% | 138,324 |
| Tue | 27.5% | 139,968 |
| Wed | 26.4% | 138,632 |
| Thu | 26.8% | 142,736 |
| Fri | 27.3% | 137,261 |
| **Sat** | **31.1%** | 112,184 |
| **Sun** | **30.8%** | 113,706 |

**Weekend spam share runs 3.9 points above the working week.** Real people post
less on a Saturday and automated posting does not care what day it is, so its
share of a smaller total rises. The posts column is the mechanism: weekday
volume runs near 138,000 and weekend volume near 112,000, while spam volume
barely moves.

## The thing this was built to test

Ukrainian strikes on Yandex data centres around 2026-10-08 collapsed that
network's traffic by roughly 94%, and people reported political bot accounts
going quiet. The obvious question was whether automated posting fell anywhere
measurable.

| day | | spam share | baseline for that weekday | change |
|---|---|---:|---:|---:|
| 2026-10-08 | Thu | 24.9% | 27.2% | **-8.5%** |
| 2026-10-09 | Fri | 29.3% | 26.9% | +8.7% |
| 2026-10-10 | Sat | 31.2% | 30.7% | +1.8% |
| 2026-10-11 | Sun | 30.8% | 30.2% | +2.0% |
| 2026-10-12 | Mon | 29.1% | 26.8% | +8.7% |

**One of five days below baseline, median change +2.0%. No effect.** A real drop
would put most days below the line, not one.

## Why the weekday control is the whole method

The raw series looks like something happened. Total posts fell by a third
between 8 and 11 October, which reads as a collapse and is a weekend. Comparing
the days after an event against the days before it compares Saturdays against
Thursdays and finds whatever the calendar happens to supply.

Each day is therefore compared against the median of the same weekday earlier in
the series. Only earlier instances count, so an event cannot sit inside its own
baseline.

## What this does not show

LunarCrush's spam label is a classifier output, not ground truth about bots.

Crypto engagement spam and political influence operations are probably different
economies with different operators, so a null here says little about whether AfD
or MAGA accounts went quiet. It says automated posting in crypto conversation
did not move.

Nobody established the premise in the first place. Yandex's traffic collapse is
measured; what those systems were posting was never shown. This measures the one
slice of social data that is visible from here.

Sixty coins over ninety days can detect a large sudden shift. It cannot detect a
subtle one, and it has no control group, because every token in the window is
exposed to the same event.

## Notes

The current day is dropped from every series. It is partial and reads low, which
would manufacture a decline at the right-hand edge of any event window.

Counts are aggregated across coins rather than averaged, so a token with four
posts does not weigh the same as one with four thousand.

`--event` is optional. Without it the script just reports the baseline, which is
the reusable part: any dated claim about bot activity can be tested against it.

---

Needs a [LunarCrush](https://lunarcrush.com/) API key. Code `NICKI` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
