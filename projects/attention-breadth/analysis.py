#!/usr/bin/env python3
"""Attention Breadth Index: how many coins is crypto actually talking about?

Equity markets have had breadth indicators for a century (advance/decline,
percent above moving average). Crypto attention has none. This builds one.

For each day, take every eligible coin's share of that day's total social
interactions and compute the Herfindahl index. Its reciprocal is the
"effective number of coins" — if attention were split evenly among N coins,
the index reads N. In practice Bitcoin dominates, so the number is small, and
its movement is the signal: rising means attention is dispersing into alts,
falling means it is collapsing back toward the majors.

Then the question worth asking: does breadth widening precede alt-season?

Usage:
    python3 analysis.py [--min-mcap 50e6] [--json out/breadth.json]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR.parent / "social-price-backtest" / "data" / "raw"
OUT_DIR = PROJECT_DIR / "out"
NUMERIC = ["time", "close", "interactions", "market_cap", "volume_24h"]


def load_panel() -> pd.DataFrame:
    """One row per coin-day: date, symbol, interactions, market cap, close."""
    frames = []
    for p in sorted(RAW_DIR.glob("*.json")):
        blob = json.loads(p.read_text())
        rows = blob.get("rows") or []
        if len(rows) < 60:
            continue
        df = pd.DataFrame(rows)
        for c in NUMERIC:
            df[c] = pd.to_numeric(df.get(c), errors="coerce") if c in df.columns else np.nan
        df = df.dropna(subset=["time", "interactions"])
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
        df["symbol"] = blob["coin"]["symbol"]
        frames.append(df[["date", "symbol", "interactions", "market_cap", "volume_24h", "close"]])
    panel = pd.concat(frames, ignore_index=True)
    return panel.drop_duplicates(["date", "symbol"])


def daily_breadth(panel: pd.DataFrame, min_mcap: float, min_volume: float) -> pd.DataFrame:
    eligible = panel[
        (panel["market_cap"].fillna(0) >= min_mcap)
        & (panel["volume_24h"].fillna(0) >= min_volume)
        & (panel["interactions"] > 0)
    ].copy()

    out = []
    for date, day in eligible.groupby("date"):
        total = day["interactions"].sum()
        if total <= 0 or len(day) < 20:
            continue
        shares = day["interactions"] / total
        hhi = float((shares ** 2).sum())
        btc = day.loc[day["symbol"] == "BTC", "interactions"].sum() / total
        out.append(
            {
                "date": date,
                "coins": len(day),
                "effective_n": 1.0 / hhi,
                "hhi": hhi,
                "btc_share": float(btc),
                "top10_share": float(shares.nlargest(10).sum()),
            }
        )
    return pd.DataFrame(out).sort_values("date").reset_index(drop=True)


def alt_outperformance(panel: pd.DataFrame, min_mcap: float, min_volume: float,
                       horizons=(7, 30)) -> pd.DataFrame:
    """Equal-weighted forward return of eligible non-BTC coins, minus BTC's."""
    wide = panel.pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
    mcap = panel.pivot_table(index="date", columns="symbol", values="market_cap", aggfunc="last")
    vol = panel.pivot_table(index="date", columns="symbol", values="volume_24h", aggfunc="last")
    eligible = (mcap.fillna(0) >= min_mcap) & (vol.fillna(0) >= min_volume)

    rows = {}
    for h in horizons:
        fwd = wide.shift(-h) / wide - 1.0
        # winsorize: raw crypto price data carries redenominations
        lo, hi = fwd.stack().quantile([0.01, 0.99])
        fwd = fwd.clip(lo, hi)
        alts = fwd.where(eligible & (fwd.columns != "BTC"))
        rows[f"alt_{h}d"] = alts.mean(axis=1)
        rows[f"btc_{h}d"] = fwd["BTC"] if "BTC" in fwd.columns else np.nan
        rows[f"excess_{h}d"] = rows[f"alt_{h}d"] - rows[f"btc_{h}d"]
    return pd.DataFrame(rows).rename_axis("date").reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mcap", type=float, default=50e6)
    ap.add_argument("--min-volume", type=float, default=1e6)
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    panel = load_panel()
    print(f"panel: {len(panel):,} coin-days, {panel['symbol'].nunique()} coins, "
          f"{panel['date'].min().date()} to {panel['date'].max().date()}")

    breadth = daily_breadth(panel, args.min_mcap, args.min_volume)
    print(f"breadth series: {len(breadth):,} days")

    cur = breadth.iloc[-1]
    print(f"\nlatest ({cur['date'].date()}): effective N = {cur['effective_n']:.1f} coins "
          f"| BTC share {cur['btc_share']:.1%} | top-10 share {cur['top10_share']:.1%} "
          f"| {int(cur['coins'])} eligible coins")

    q = breadth["effective_n"].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    print("effective N distribution: " + " ".join(f"p{int(k*100)}={v:.1f}" for k, v in q.items()))

    # 30-day change in breadth, and where today sits historically
    breadth["eff_n_30d_chg"] = breadth["effective_n"] - breadth["effective_n"].shift(30)
    pct_rank = (breadth["effective_n"] <= cur["effective_n"]).mean()
    print(f"today's breadth is at the {pct_rank:.0%} percentile of its own history")

    # Does breadth predict alt outperformance?
    alts = alt_outperformance(panel, args.min_mcap, args.min_volume)
    merged = breadth.merge(alts, on="date", how="inner").dropna(
        subset=["excess_7d", "excess_30d", "eff_n_30d_chg"]
    )
    print(f"\npredictive test on {len(merged):,} overlapping days")
    print(f"{'signal':28} {'vs excess_7d':>14} {'vs excess_30d':>14}")
    for label, col in [("breadth level", "effective_n"),
                       ("breadth 30d change", "eff_n_30d_chg"),
                       ("BTC attention share", "btc_share")]:
        # Spearman without scipy: Pearson on ranks
        r7 = merged[col].rank().corr(merged["excess_7d"].rank())
        r30 = merged[col].rank().corr(merged["excess_30d"].rank())
        print(f"{label:28} {r7:>14.3f} {r30:>14.3f}")

    # The raw level is unusable for prediction: the eligible universe grows
    # over time, so effective_n drifts upward and its quintiles collapse onto
    # calendar eras (every "narrow" day lands in 2020-2022, every "wide" day in
    # 2023-2025). Comparing them compares market regimes, not breadth. Rank
    # each day against its own trailing year instead, which removes the drift.
    merged["breadth_rank"] = (
        merged["effective_n"]
        .rolling(365, min_periods=180)
        .apply(lambda w: (w.iloc[-1] >= w).mean(), raw=False)
    )
    merged = merged.dropna(subset=["breadth_rank"])
    merged["quintile"] = pd.qcut(
        merged["breadth_rank"], 5, labels=["Q1 narrow", "Q2", "Q3", "Q4", "Q5 wide"]
    )
    print(f"\n(detrended: breadth ranked against its own trailing year, "
          f"{len(merged):,} days)")
    print("\nforward alt-minus-BTC return by breadth quintile:")
    tab = merged.groupby("quintile", observed=True)[["excess_7d", "excess_30d"]].median()
    for name, row in tab.iterrows():
        print(f"  {name:10} 7d {row['excess_7d']:+7.2%}   30d {row['excess_30d']:+7.2%}")

    # Significance. Daily observations with 30-day forward windows overlap
    # heavily, so naive tests are meaningless; resample whole months instead.
    print(f"\nmonth-cluster bootstrap ({args.bootstrap} draws), Q5 wide minus Q1 narrow:")
    merged["block"] = merged["date"].dt.to_period("M")
    blocks = sorted(merged["block"].unique())
    by_block = {b: g for b, g in merged.groupby("block")}
    rng = np.random.default_rng(7)
    for h in (7, 30):
        col = f"excess_{h}d"

        def stat(sample: pd.DataFrame) -> float:
            wide = sample.loc[sample["quintile"] == "Q5 wide", col].median()
            narrow = sample.loc[sample["quintile"] == "Q1 narrow", col].median()
            return wide - narrow

        observed = stat(merged)
        draws = []
        for _ in range(args.bootstrap):
            picked = rng.choice(len(blocks), len(blocks))
            sample = pd.concat([by_block[blocks[i]] for i in picked])
            v = stat(sample)
            if np.isfinite(v):
                draws.append(v)
        d = np.array(draws)
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        print(f"  {h:>2}d: diff {observed:+.2%}  CI [{np.percentile(d, 2.5):+.2%}, "
              f"{np.percentile(d, 97.5):+.2%}]  p={p:.4f}")

    # Era stability: one regime shouldn't be carrying the whole result.
    print("\nby era (median 30d alt-minus-BTC, narrow vs wide):")
    merged["year"] = merged["date"].dt.year
    for era, (y0, y1) in {"2020-2022": (2020, 2022), "2023-2025": (2023, 2025),
                          "2026": (2026, 2026)}.items():
        sub = merged[(merged["year"] >= y0) & (merged["year"] <= y1)]
        if len(sub) < 60:
            print(f"  {era:10} too few days")
            continue
        narrow = sub.loc[sub["quintile"] == "Q1 narrow", "excess_30d"].median()
        wide = sub.loc[sub["quintile"] == "Q5 wide", "excess_30d"].median()
        n_n = (sub["quintile"] == "Q1 narrow").sum()
        n_w = (sub["quintile"] == "Q5 wide").sum()
        print(f"  {era:10} narrow {narrow:+7.2%} (n={n_n:>4})   wide {wide:+7.2%} (n={n_w:>4})")

    OUT_DIR.mkdir(exist_ok=True)
    breadth.to_csv(OUT_DIR / "breadth.csv", index=False)
    if args.json_out:
        payload = {
            "latest": {
                "date": str(cur["date"].date()),
                "effective_n": round(float(cur["effective_n"]), 2),
                "btc_share": round(float(cur["btc_share"]), 4),
                "percentile": round(float(pct_rank), 3),
            },
            "series": [
                {"date": str(d.date()), "effective_n": round(float(n), 3)}
                for d, n in zip(breadth["date"], breadth["effective_n"])
            ],
        }
        Path(args.json_out).write_text(json.dumps(payload, indent=1))
        print(f"\nWrote {args.json_out}")
    print(f"Wrote {OUT_DIR / 'breadth.csv'}")


if __name__ == "__main__":
    main()
