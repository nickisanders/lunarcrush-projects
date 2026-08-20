#!/usr/bin/env python3
"""When does crypto actually talk?

The market runs 24/7. The people do not. This measures the hour-of-day shape
of posting volume for every major coin and asks two things: how deep is the
daily trough, and do different coins keep different hours?

Method notes that matter:

- MEDIAN posts per clock hour, not mean. One overnight listing or exchange
  hack otherwise invents a peak out of a single hour. Using the mean, BNB
  appeared to peak at 01:00 UTC on an Asia-hours schedule; on the median it
  peaks at 13:00 like everything else, and the "Asian coin" story evaporates.
- The final row is the hour in progress and is dropped.
- Coins are held to a posting floor, because below it the per-hour median
  quantizes onto small integers and the shape is rounding noise. The
  conclusions are stable from 5 to 40 posts/hour (see --floor).

Related: ../attention-halflife/office_hours.py asks whether manufactured
spikes peak at different hours than organic ones (they do not). This measures
the underlying rhythm both of them sit on.

Usage:
    python3 analysis.py [--floor 10]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "out"
DAY_WINDOW = (12, 20)  # the eight loudest consecutive UTC hours


def profiles(floor: int) -> pd.DataFrame:
    """Per-coin hour-of-day profile, normalized so 1.0 is an average hour."""
    out = {}
    for path in sorted(DATA.glob("*.json")):
        blob = json.loads(path.read_text())
        df = pd.DataFrame(blob["rows"])
        if "posts" not in df.columns:
            continue
        df = df.dropna(subset=["posts"]).iloc[:-1]  # drop the hour in progress
        if len(df) < 600 or df["posts"].median() < floor:
            continue
        df["h"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.hour
        p = df.groupby("h")["posts"].median()
        if len(p) < 24 or p.min() <= 0:
            continue
        out[blob["symbol"]] = p / p.sum() * 24
    return pd.DataFrame(out)


def summarize(t: pd.DataFrame) -> dict:
    agg = t.mean(axis=1)
    peaks, troughs = t.idxmax(), t.idxmin()
    corr = t.corr().values
    iu = np.triu_indices_from(corr, 1)
    lo, hi = DAY_WINDOW
    return {
        "coins": len(t.columns),
        "loudestHour": int(agg.idxmax()),
        "quietestHour": int(agg.idxmin()),
        "loudest": float(agg.max()),
        "quietest": float(agg.min()),
        "ratio": float(agg.max() / agg.min()),
        "peakInAfternoon": int(peaks.between(11, 17).sum()),
        "troughAtNight": int(troughs.between(1, 7).sum()),
        "medianCoinRatio": float((t.max() / t.min()).median()),
        "medianPairwiseCorr": float(np.median(corr[iu])),
        "dayWindowShare": float(agg.loc[lo:hi].sum() / 24),
        "hours": [float(agg[h]) for h in range(24)],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=int, default=10, help="min median posts per hour")
    args = ap.parse_args()

    t = profiles(args.floor)
    if t.empty:
        raise SystemExit("no usable profiles; run pull.py first")
    s = summarize(t)

    print(f"{s['coins']} coins with a usable hourly profile (floor {args.floor} posts/hr)\n")
    print(f"loudest hour   {s['loudestHour']:02d}:00 UTC   {s['loudest']:.2f}x an average hour")
    print(f"quietest hour  {s['quietestHour']:02d}:00 UTC   {s['quietest']:.2f}x")
    print(f"swing          {s['ratio']:.2f}x")
    print(f"\n{s['peakInAfternoon']} of {s['coins']} coins peak between 11:00 and 17:00 UTC")
    print(f"{s['troughAtNight']} of {s['coins']} coins bottom out between 01:00 and 07:00 UTC")
    print(f"median coin's own peak/trough swing: {s['medianCoinRatio']:.2f}x")
    print(f"median correlation between two coins' clocks: {s['medianPairwiseCorr']:.2f}")
    print(f"share of all posting in {DAY_WINDOW[0]:02d}:00-{DAY_WINDOW[1]:02d}:00 UTC: "
          f"{s['dayWindowShare']:.0%}  (flat would be 33%)\n")
    for h in range(24):
        v = s["hours"][h]
        print(f"  {h:02d}:00 UTC  {v:.2f}  {'█' * int(v * 30)}")

    OUT.mkdir(exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(s, indent=1))
    t.to_csv(OUT / "profiles.csv")

    print("\nSensitivity to the posting floor:")
    for f in (5, 10, 20, 40):
        tt = profiles(f)
        if tt.empty:
            continue
        ss = summarize(tt)
        print(f"  floor {f:>2}: {ss['coins']:>2} coins | swing {ss['ratio']:.2f}x | "
              f"peak 11-17 UTC {ss['peakInAfternoon']}/{ss['coins']} | corr {ss['medianPairwiseCorr']:.2f}")
    print("\nWrote out/report.json and out/profiles.csv")


if __name__ == "__main__":
    main()
