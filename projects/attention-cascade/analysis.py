#!/usr/bin/env python3
"""Does attention cascade from Bitcoin down to the long tail?

Crypto folklore says attention flows BTC -> majors -> alts -> memecoins, with
each tier lighting up a few days after the one above it. That is a testable
lead-lag structure, and this tests it.

Method, shaped by the traps hit in earlier studies in this repo:

  Stationarity. Attention levels drift upward as the market grows, and
  quintiles of a drifting series sort by calendar rather than by state (see
  attention-breadth). Everything here works on day-over-day log changes.

  Common factor. On big news days every tier lights up together, which would
  manufacture correlation at lag 0 and smear into neighbouring lags. Each
  tier's daily change has the cross-tier mean removed, so what remains is
  tier-specific movement.

  Overlapping windows. Significance comes from a month-block bootstrap rather
  than a naive test on daily observations.

Tiers are assigned by each coin's market cap rank ON THAT DAY, not today's, so
a coin that was a major in 2021 and a minnow in 2026 is counted correctly in
both periods.

Usage:
    python3 analysis.py [--max-lag 7] [--bootstrap 2000]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"
NUMERIC = ["time", "interactions", "market_cap", "volume_24h"]

# Rank bands, evaluated per day. BTC is its own tier because the folklore
# treats it as the source.
TIERS = [
    ("majors", 2, 10),
    ("large alts", 11, 50),
    ("mid alts", 51, 200),
    ("small alts", 201, 10_000),
]


def load_panel() -> pd.DataFrame:
    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        blob = json.loads(p.read_text())
        rows = blob.get("rows") or []
        if len(rows) < 120:
            continue
        df = pd.DataFrame(rows)
        for c in NUMERIC:
            df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
        df = df.dropna(subset=["time", "interactions"])
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
        df["symbol"] = blob["coin"]["symbol"]
        frames.append(df[["date", "symbol", "interactions", "market_cap", "volume_24h"]])
    return pd.concat(frames, ignore_index=True).drop_duplicates(["date", "symbol"])


def tier_series(panel: pd.DataFrame, min_mcap: float, min_vol: float) -> pd.DataFrame:
    """Daily total interactions per tier, tiers assigned by same-day rank."""
    eligible = panel[
        (panel["market_cap"].fillna(0) >= min_mcap)
        & (panel["volume_24h"].fillna(0) >= min_vol)
        & (panel["interactions"] > 0)
    ].copy()
    eligible["rank"] = eligible.groupby("date")["market_cap"].rank(
        ascending=False, method="first"
    )

    out = {}
    btc = eligible[eligible["symbol"] == "BTC"].set_index("date")["interactions"]
    out["BTC"] = btc
    for name, lo, hi in TIERS:
        sub = eligible[(eligible["rank"] >= lo) & (eligible["rank"] <= hi)
                       & (eligible["symbol"] != "BTC")]
        out[name] = sub.groupby("date")["interactions"].sum()
    wide = pd.DataFrame(out).sort_index()
    # Require every tier present, so the common-factor removal is comparable
    # across days.
    return wide.dropna()


def residual_changes(wide: pd.DataFrame, demean: bool = True) -> pd.DataFrame:
    """Day-over-day log change, optionally with the common market move removed.

    Two things to know about the demeaned version:

    Removing the cross-tier mean forces the residuals to sum to zero each day,
    which manufactures negative correlation between every pair AT LAG 0 (with
    five tiers, roughly -0.25 before any real relationship exists). The k=0
    column is therefore not interpretable and is reported only for context.

    Leave-one-out demeaning does not fix this. Subtracting the mean of the
    other tiers yields exactly n/(n-1) times the plain demeaned residual, and
    correlation is scale invariant, so the numbers are identical. Verified.

    What the constraint does not touch is the ASYMMETRY between positive and
    negative lags, since it applies to each day symmetrically. That is why the
    cascade verdict rests on the asymmetry test rather than on any single
    correlation, and why the undemeaned version is run as a robustness check.
    """
    chg = np.log(wide).diff()
    chg = chg.replace([np.inf, -np.inf], np.nan).dropna()
    return chg.sub(chg.mean(axis=1), axis=0) if demean else chg


def lead_lag(resid: pd.DataFrame, source: str, target: str, max_lag: int) -> pd.Series:
    """corr(source_t, target_{t+k}). Positive k means source leads target."""
    out = {}
    for k in range(-max_lag, max_lag + 1):
        out[k] = resid[source].corr(resid[target].shift(-k))
    return pd.Series(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-lag", type=int, default=7)
    ap.add_argument("--min-mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    panel = load_panel()
    wide = tier_series(panel, args.min_mcap, args.min_volume)
    print(f"tier series: {len(wide):,} days, {wide.index.min().date()} to {wide.index.max().date()}")
    print("median daily interactions per tier:")
    for c in wide.columns:
        print(f"  {c:12} {wide[c].median():>15,.0f}")

    resid = residual_changes(wide)
    print(f"\nresidual daily changes: {len(resid):,} days "
          f"(common market move removed)")

    order = ["BTC"] + [t[0] for t in TIERS]
    print(f"\nlead-lag correlation, corr(source_t, target_t+k)")
    print("positive k means the source moves first\n")
    header = "  ".join(f"k={k:+d}" for k in range(-3, 4))
    print(f"{'source -> target':28} {header}")
    pairs = [(order[i], order[j]) for i in range(len(order)) for j in range(len(order)) if i < j]
    results = {}
    for src, tgt in pairs:
        ll = lead_lag(resid, src, tgt, args.max_lag)
        results[(src, tgt)] = ll
        row = "  ".join(f"{ll[k]:+.3f}" for k in range(-3, 4))
        print(f"{src + ' -> ' + tgt:28} {row}")

    # If a cascade exists, the peak correlation should sit at positive k.
    print("\npeak correlation and where it sits:")
    rng = np.random.default_rng(7)
    resid_blocks = resid.copy()
    resid_blocks["block"] = resid_blocks.index.to_period("M")
    blocks = sorted(resid_blocks["block"].unique())
    by_block = {b: g for b, g in resid_blocks.groupby("block")}

    for (src, tgt), ll in results.items():
        peak_k = int(ll.abs().idxmax())
        peak_v = ll[peak_k]
        # Bootstrap the asymmetry that a cascade implies: correlation at
        # positive lags minus negative lags. A real cascade is directional.
        def asym(sample: pd.DataFrame) -> float:
            s, t = sample[src], sample[tgt]
            pos = np.mean([s.corr(t.shift(-k)) for k in range(1, 4)])
            neg = np.mean([s.corr(t.shift(k)) for k in range(1, 4)])
            return pos - neg

        observed = asym(resid)
        draws = []
        for _ in range(args.bootstrap):
            picked = rng.choice(len(blocks), len(blocks))
            sample = pd.concat([by_block[blocks[i]] for i in picked])
            v = asym(sample)
            if np.isfinite(v):
                draws.append(v)
        d = np.array(draws)
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        verdict = "leads" if observed > 0 else "lags"
        print(f"  {src + ' -> ' + tgt:28} peak at k={peak_k:+d} ({peak_v:+.3f})  "
              f"asymmetry {observed:+.3f} [{np.percentile(d,2.5):+.3f}, "
              f"{np.percentile(d,97.5):+.3f}] p={p:.3f}  source {verdict}")

    # Robustness: same asymmetry test on raw log changes, no common-factor
    # removal at all. If the verdict flips here, the demeaning was doing the
    # work rather than the data.
    raw = residual_changes(wide, demean=False)
    print("\nrobustness, no common-factor removal (asymmetry only):")
    for src, tgt in pairs:
        s, t_ = raw[src], raw[tgt]
        pos = np.mean([s.corr(t_.shift(-k)) for k in range(1, 4)])
        neg = np.mean([s.corr(t_.shift(k)) for k in range(1, 4)])
        print(f"  {src + ' -> ' + tgt:28} asymmetry {pos - neg:+.3f}")

    OUT_DIR.mkdir(exist_ok=True)
    pd.DataFrame({f"{s}->{t}": v for (s, t), v in results.items()}).to_csv(
        OUT_DIR / "lead_lag.csv"
    )
    wide.to_csv(OUT_DIR / "tier_attention.csv")
    print(f"\nWrote out/lead_lag.csv and out/tier_attention.csv")


if __name__ == "__main__":
    main()
