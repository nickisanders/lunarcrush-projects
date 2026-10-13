#!/usr/bin/env python3
"""What spam share normally does, so a dated event can be tested against it.

Ukrainian strikes on Yandex data centres around 2026-10-08 collapsed that
network's traffic by roughly 94%, and people reported political bot accounts
going quiet. The obvious question is whether automated posting fell anywhere
measurable. This answers it for crypto conversation, which is the slice this
dataset can see.

Answering it needs a baseline first, because the raw series is misleading. Total
posts fell by a third between 8 and 11 October, which looks like a collapse and
is a weekend. **Spam share is systematically higher at weekends**: real people
post less on a Saturday and automated posting does not care what day it is, so
the share rises. Any event test that ignores the weekday compares a Saturday
against a Thursday and finds whatever it wants.

So this builds the weekday baseline, then compares each day of an event window
against the median of the same weekday earlier in the series.

An event date is optional. Without one this just reports the baseline.

Usage:
    LUNARCRUSH_API_KEY=... python3 spam_baseline.py
    python3 spam_baseline.py --event 2026-10-08 --window 5 --coins 60
"""

import argparse
import datetime as dt
import json
import os
import statistics as st
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
BASE = "https://lunarcrush.com/api4"
UA = "lunarcrush-projects/spam-baseline"
PEGGED = {"USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "BUSD",
          "USDS", "SUSDE", "USDTB", "XAUT", "PAXG", "STETH", "WSTETH", "WBTC", "WETH"}
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get(path, attempts=6, pace=0.2):
    time.sleep(pace)
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {os.environ['LUNARCRUSH_API_KEY']}",
                 "User-Agent": UA})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429, 529) and e.code < 500:
                return None
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(min(60, 1.5 * 2 ** attempt))
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coins", type=int, default=30, help="universe size by market cap")
    ap.add_argument("--event", help="YYYY-MM-DD to test against the baseline")
    ap.add_argument("--window", type=int, default=5, help="days from the event to test")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    coins = (get("/public/coins/list/v2?limit=1000") or {}).get("data") or []
    coins = [c for c in coins if str(c.get("symbol", "")).upper() not in PEGGED][:a.coins]

    # Aggregated across coins rather than averaged, so a token with four posts
    # does not weigh the same as one with four thousand.
    daily = defaultdict(lambda: [0.0, 0.0])
    used = 0
    for i, c in enumerate(coins, 1):
        d = get(f"/public/coins/{c['symbol']}/time-series/v2?bucket=day&interval=3m")
        rows = (d or {}).get("data") or []
        if not rows:
            continue
        used += 1
        for r in rows[:-1]:          # the current day is partial and reads low
            day = dt.datetime.fromtimestamp(r["time"], dt.timezone.utc).strftime("%Y-%m-%d")
            daily[day][0] += r.get("spam") or 0
            daily[day][1] += r.get("posts_created") or 0
        if i % 10 == 0:
            print(f"  {i}/{len(coins)} coins", flush=True)

    series = {d: {"spam": s, "posts": p, "share": (s / p if p else None)}
              for d, (s, p) in sorted(daily.items()) if p}
    by_dow = defaultdict(list)
    for day, v in series.items():
        by_dow[dt.datetime.strptime(day, "%Y-%m-%d").strftime("%a")].append((day, v))

    baseline = {d: {"n": len(rows),
                    "median_share": st.median([v["share"] for _, v in rows]),
                    "median_posts": st.median([v["posts"] for _, v in rows])}
                for d, rows in by_dow.items()}

    print(f"\n  {used} coins, {len(series)} days\n")
    print(f"  {'day':<5}{'n':>4}{'median share':>15}{'median posts':>15}")
    for d in DOW:
        if d in baseline:
            b = baseline[d]
            print(f"  {d:<5}{b['n']:>4}{b['median_share']*100:>14.1f}%{b['median_posts']:>15,.0f}")
    wk = [baseline[d]["median_share"] for d in DOW[:5] if d in baseline]
    we = [baseline[d]["median_share"] for d in DOW[5:] if d in baseline]
    gap = (st.mean(we) - st.mean(wk)) * 100 if wk and we else 0
    print(f"\n  weekend spam share runs {gap:+.1f} points above the working week")

    result = {"captured": dt.datetime.now(dt.timezone.utc).isoformat(),
              "coins": used, "days": len(series), "baseline": baseline,
              "weekend_gap_points": round(gap, 2), "series": series}

    if a.event:
        start = dt.datetime.strptime(a.event, "%Y-%m-%d")
        print(f"\n  event window from {a.event}, each day against its own weekday:\n")
        print(f"  {'day':<12}{'dow':<5}{'share':>8}{'baseline':>10}{'change':>9}")
        tested = []
        for k in range(a.window):
            day = (start + dt.timedelta(days=k)).strftime("%Y-%m-%d")
            if day not in series:
                continue
            dow = dt.datetime.strptime(day, "%Y-%m-%d").strftime("%a")
            # Compare only against earlier instances, so the event cannot sit
            # inside its own baseline.
            peers = [v["share"] for d2, v in by_dow[dow] if d2 < day]
            if not peers:
                continue
            med = st.median(peers)
            chg = (series[day]["share"] / med - 1) * 100
            tested.append({"day": day, "dow": dow, "share": series[day]["share"],
                           "baseline": med, "change_pct": round(chg, 1)})
            print(f"  {day:<12}{dow:<5}{series[day]['share']*100:>7.1f}%"
                  f"{med*100:>9.1f}%{chg:>8.1f}%")
        if tested:
            downs = sum(1 for t in tested if t["change_pct"] < 0)
            med_chg = st.median([t["change_pct"] for t in tested])
            print(f"\n  {downs} of {len(tested)} days below baseline, median change "
                  f"{med_chg:+.1f}%")
            print("  a drop would show as most days below baseline, not one")
            result["event"] = {"date": a.event, "days": tested,
                               "days_below": downs, "median_change_pct": med_chg}

    (OUT / "spam_baseline.json").write_text(json.dumps(result, indent=2))
    print(f"\n  wrote {(OUT/'spam_baseline.json').relative_to(HERE)}")


if __name__ == "__main__":
    main()
