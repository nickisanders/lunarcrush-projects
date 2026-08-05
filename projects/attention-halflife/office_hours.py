#!/usr/bin/env python3
"""Does manufactured hype keep office hours?

Uses the cached hourly spike windows to compare WHEN spikes peak (UTC hour
of day) for organic vs spam-heavy groups. Both groups share crypto's global
diurnal rhythm, so the comparison is group-vs-group, not group-vs-uniform.

Significance: permutation test on the total variation distance between the
two hour-of-day distributions (group labels shuffled).

Usage:
    python3 office_hours.py [--permutations 5000]
"""

import argparse
import json
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent
HOURLY_DIR = PROJECT_DIR / "data" / "hourly"
OUT_DIR = PROJECT_DIR / "out"
DAY = 86400


def peak_hour(path: Path) -> tuple[str, int] | None:
    blob = json.loads(path.read_text())
    rows = blob["rows"]
    if len(rows) < 100:
        return None
    t0 = blob["spike_ts"]
    times = np.array([r["time"] for r in rows])
    inter = np.array([float(r.get("interactions") or 0) for r in rows])
    day = np.where((times >= t0) & (times < t0 + DAY))[0]
    if len(day) < 20:
        return None
    peak_ts = times[day[np.argmax(inter[day])]]
    return blob["group"], int((peak_ts % DAY) // 3600)


def hist24(hours: np.ndarray) -> np.ndarray:
    h = np.bincount(hours, minlength=24).astype(float)
    return h / h.sum()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--permutations", type=int, default=5000)
    args = ap.parse_args()

    groups: dict[str, list[int]] = {"organic": [], "spam": []}
    for p in sorted(HOURLY_DIR.glob("*.json")):
        r = peak_hour(p)
        if r:
            groups[r[0]].append(r[1])
    org = np.array(groups["organic"])
    spam = np.array(groups["spam"])
    print(f"{len(org)} organic, {len(spam)} spam-heavy spike peaks")

    h_org, h_spam = hist24(org), hist24(spam)
    tvd = 0.5 * np.abs(h_org - h_spam).sum()

    rng = np.random.default_rng(7)
    pooled = np.concatenate([org, spam])
    n_org = len(org)
    draws = []
    for _ in range(args.permutations):
        rng.shuffle(pooled)
        draws.append(0.5 * np.abs(hist24(pooled[:n_org]) - hist24(pooled[n_org:])).sum())
    p = float((np.array(draws) >= tvd).mean())

    print(f"\ntotal variation distance between hour-of-day distributions: {tvd:.3f}")
    print(f"permutation p-value ({args.permutations} shuffles): {p:.4f}")

    quads = [("00-06 UTC", 0, 6), ("06-12 UTC", 6, 12), ("12-18 UTC", 12, 18), ("18-24 UTC", 18, 24)]
    print("\nshare of peaks by UTC quadrant:")
    print(f"{'quadrant':10} {'organic':>9} {'spam':>9}")
    for name, a, b in quads:
        print(f"{name:10} {h_org[a:b].sum():>8.1%} {h_spam[a:b].sum():>8.1%}")

    top_org = int(np.argmax(h_org))
    top_spam = int(np.argmax(h_spam))
    print(f"\nmodal peak hour: organic {top_org:02d}:00 UTC ({h_org[top_org]:.1%}), "
          f"spam {top_spam:02d}:00 UTC ({h_spam[top_spam]:.1%})")

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "office_hours.json").write_text(
        json.dumps({"organic": h_org.tolist(), "spam": h_spam.tolist(), "tvd": tvd, "p": p}, indent=1)
    )
    print(f"\nWrote out/office_hours.json")


if __name__ == "__main__":
    main()
