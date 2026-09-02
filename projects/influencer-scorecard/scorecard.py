#!/usr/bin/env python3
"""When a named crypto account posts about a coin, what does the coin do next?

Reads the cache written by pull.py and scores each creator on the coins they
name, against Bitcoin, at 3, 7 and 30 days.

Read the result narrowly. This measures what happened after a mention, not
whether anyone was right. Four reasons a good score is not a good call:

- **A mention is not a recommendation.** `lookonchain` mostly reports whale
  movements, so its `$ETH` posts are frequently "somebody just dumped 40,000
  ETH". Posts are split by sentiment so a bearish report is not scored as a
  bullish call, but sentiment is a blunt instrument.
- **Causation is not on the table.** An account that posts about whatever is
  already moving will score like an account that moves things. This cannot
  separate them and does not try.
- **Small samples are not scores.** A creator needs MIN_EVENTS distinct
  coin-days before a number is published at all. On the first run several
  well-known accounts had fewer than ten.
- **The universe is current.** Creators come from today's topic lists, so
  accounts that were influential in 2024 and have since gone quiet are absent.

Usage:
    python3 scorecard.py [--min-events 20] [--horizon 7]
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "out"
HORIZONS = (3, 7, 30)
MIN_EVENTS = 20
DAY = 86_400

# Tickers that are also ordinary words. A post saying "I am bullish" or "it's
# hot" would otherwise be scored as a call on $AM or $HOT. Seeded from the
# name-collision project, which found these by measuring interactions per
# dollar of market cap across the whole market.
COLLIDING = {
    "AM", "HOT", "47", "DONS", "OTC", "DINO", "ALVA", "ALL", "ANY", "ARE", "BE",
    "BEST", "BIG", "BUY", "CAN", "DO", "FOR", "GET", "GO", "HAS", "HIGH", "IN",
    "IS", "IT", "JUST", "LIKE", "LOW", "ME", "MY", "NEW", "NEXT", "NO", "NOT",
    "NOW", "ON", "ONE", "OR", "OUT", "OWN", "PAY", "PUMP", "REAL", "RUN", "SO",
    "SUM", "TOP", "UP", "US", "WE", "WIN", "YOU",
}

TICKER_RE = re.compile(r"\$([A-Za-z0-9]{2,10})\b")


def load_prices() -> dict[str, pd.Series]:
    """Daily closes per symbol, indexed by UTC date."""
    out = {}
    for f in (DATA / "prices").glob("*.json"):
        blob = json.loads(f.read_text())
        rows = [(datetime.fromtimestamp(r["time"], timezone.utc).date(), r["close"])
                for r in blob["rows"] if r.get("close")]
        if rows:
            # Some closes arrive as strings; coerce or the comparisons below
            # raise on the first offender.
            s = pd.to_numeric(pd.Series(dict(rows)), errors="coerce").dropna()
            # A DatetimeIndex, not date objects: asof compares against
            # Timestamps and silently matches nothing on a plain date index.
            s.index = pd.to_datetime(list(s.index))
            s = s.sort_index()
            out[blob["symbol"]] = s[~s.index.duplicated(keep="last")]
    return out


def extract_events(symbols: set[str]) -> pd.DataFrame:
    """One row per (creator, coin, day) a coin was named.

    Deduplicated: five posts about $SOL in one day is one call, not five, and
    counting them separately would let a prolific poster dominate the sample.
    """
    rows = []
    for f in sorted((DATA / "creators").glob("*.json")):
        blob = json.loads(f.read_text())
        for p in blob["posts"]:
            created = p.get("post_created")
            if not created:
                continue
            day = datetime.fromtimestamp(created, timezone.utc).date()
            found = {t.upper() for t in TICKER_RE.findall(str(p.get("post_title") or ""))}
            for sym in found & symbols:
                if sym in COLLIDING:
                    continue
                rows.append({"creator": blob["creator_name"], "symbol": sym, "date": day,
                             "sentiment": p.get("post_sentiment"),
                             "interactions": p.get("interactions_total") or 0})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return (df.sort_values("interactions", ascending=False)
              .drop_duplicates(subset=["creator", "symbol", "date"], keep="first"))


def score_events(events: pd.DataFrame, prices: dict[str, pd.Series]) -> pd.DataFrame:
    """Forward return after each mention, minus Bitcoin over the same window."""
    btc = prices.get("BTC")
    if btc is None:
        raise SystemExit("no BTC prices cached; run pull.py")

    def fwd(series: pd.Series, day, h: int):
        entry_at = pd.Timestamp(day)
        exit_at = entry_at + pd.Timedelta(days=h)
        # asof carries the last known value forward, so an exit date that has
        # not happened yet would silently read as a flat return. Require the
        # series to actually reach past it.
        if series.index.max() < exit_at or series.index.min() > entry_at:
            return None
        entry, exit_ = series.asof(entry_at), series.asof(exit_at)
        if pd.isna(entry) or pd.isna(exit_) or entry <= 0:
            return None
        return exit_ / entry - 1

    out = []
    for r in events.itertuples():
        s = prices.get(r.symbol)
        if s is None:
            continue
        row = {"creator": r.creator, "symbol": r.symbol, "date": r.date, "sentiment": r.sentiment}
        ok = False
        for h in HORIZONS:
            c, b = fwd(s, r.date, h), fwd(btc, r.date, h)
            row[f"a{h}"] = (c - b) if (c is not None and b is not None) else np.nan
            ok = ok or not np.isnan(row[f"a{h}"])
        if ok:
            out.append(row)
    return pd.DataFrame(out)


def matched_baseline(prices: dict[str, pd.Series], events: pd.DataFrame, horizon: int,
                     seed: int = 7) -> pd.Series:
    """What an UNMENTIONED coin did, over the same dates.

    "36% beat Bitcoin" means nothing without knowing what an arbitrary coin did
    over the same weeks. This resamples the SAME dates the mentions fall on,
    pairing each with a random coin from the control set: 150 coins in the top
    600 that nobody in the creator sample named. Drawing from the mentioned
    coins instead would compare a mention against a different mention and could
    not answer whether being mentioned matters at all.
    """
    rng = np.random.default_rng(seed)
    btc = prices["BTC"]
    control_file = DATA / "control.json"
    if not control_file.exists():
        raise SystemExit("no control set cached; re-run pull.py")
    symbols = [s for s in json.loads(control_file.read_text()) if s in prices and s != "BTC"]
    if not symbols:
        raise SystemExit("control set has no cached prices")
    out, kept = [], []
    for day in events["date"]:
        sym = symbols[rng.integers(0, len(symbols))]
        s = prices[sym]
        entry_at = pd.Timestamp(day)
        exit_at = entry_at + pd.Timedelta(days=horizon)
        if s.index.max() < exit_at or s.index.min() > entry_at:
            continue
        if btc.index.max() < exit_at:
            continue
        e, x = s.asof(entry_at), s.asof(exit_at)
        be, bx = btc.asof(entry_at), btc.asof(exit_at)
        if pd.isna(e) or pd.isna(x) or e <= 0 or pd.isna(be) or be <= 0:
            continue
        out.append((x / e - 1) - (bx / be - 1))
        kept.append(day)
    return pd.Series(out), pd.Series(kept)


def block_bootstrap_rate_gap(mentioned: pd.Series, dates_m: pd.Series,
                             control: pd.Series, dates_c: pd.Series,
                             iters: int = 3000, seed: int = 7):
    """Month-block bootstrap of the gap in beats-BTC rate.

    Blocked by calendar month because mentions cluster: a hundred accounts
    naming the same coin in one week are not a hundred independent draws, and
    an unclustered test would report a confidence interval several times too
    tight.
    """
    dm = pd.DataFrame({"v": (mentioned > 0).astype(float), "b": pd.to_datetime(dates_m).dt.to_period("M")})
    dc = pd.DataFrame({"v": (control > 0).astype(float), "b": pd.to_datetime(dates_c).dt.to_period("M")})
    gm = {k: v["v"].values for k, v in dm.groupby("b")}
    gc = {k: v["v"].values for k, v in dc.groupby("b")}
    blocks = sorted(set(gm) & set(gc))
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(iters):
        pick = rng.choice(blocks, len(blocks), replace=True)
        draws.append(np.concatenate([gm[k] for k in pick]).mean()
                     - np.concatenate([gc[k] for k in pick]).mean())
    draws = np.array(draws)
    observed = (mentioned > 0).mean() - (control > 0).mean()
    return (observed, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
            float(2 * min((draws <= 0).mean(), (draws >= 0).mean())))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-events", type=int, default=MIN_EVENTS)
    ap.add_argument("--horizon", type=int, default=7, choices=HORIZONS)
    args = ap.parse_args()

    coins = json.loads((DATA / "coins.json").read_text())
    symbols = {c["symbol"].upper() for c in coins}
    prices = load_prices()
    print(f"{len(symbols)} known symbols, {len(prices)} with cached prices")

    events = extract_events(symbols)
    if events.empty:
        raise SystemExit("no events; run pull.py first")
    print(f"{len(events):,} distinct (creator, coin, day) mentions "
          f"from {events.creator.nunique()} creators")

    scored = score_events(events, prices)
    print(f"{len(scored):,} scoreable after joining prices\n")

    col = f"a{args.horizon}"
    d = scored.dropna(subset=[col])
    g = d.groupby("creator")[col]
    board = pd.DataFrame({"events": g.size(), "beat_btc": g.apply(lambda x: (x > 0).mean()),
                          "median": g.median()}).sort_values("median", ascending=False)
    board = board[board.events >= args.min_events]
    base, base_dates = matched_baseline(prices, d, args.horizon)
    print(f"Creators with at least {args.min_events} scoreable mentions: {len(board)}\n")
    print(f"Over {args.horizon} days, against Bitcoin:")
    print(f"  a coin that got mentioned:  beat BTC {(d[col] > 0).mean():.1%}  median {d[col].median() * 100:+.1f}%")
    print(f"  an UNMENTIONED coin, same dates: beat BTC {(base > 0).mean():.1%}  median {base.median() * 100:+.1f}%")
    print(f"  n={len(d):,} mentions vs {len(base):,} matched draws")
    gap, lo, hi, pv = block_bootstrap_rate_gap(d[col], d["date"], base, base_dates)
    print(f"  gap in beats-BTC rate: {gap * 100:+.1f}pp  CI [{lo * 100:+.1f}, {hi * 100:+.1f}]  p={pv:.3f}\n")
    print(f"{'creator':<22}{'events':>8}{'beats BTC':>11}{'median':>10}")
    for name, r in board.head(12).iterrows():
        print(f"{name:<22}{int(r.events):>8}{r.beat_btc:>10.0%}{r['median'] * 100:>9.1f}%")
    if len(board) > 12:
        print("  ...")
        for name, r in board.tail(5).iterrows():
            print(f"{name:<22}{int(r.events):>8}{r.beat_btc:>10.0%}{r['median'] * 100:>9.1f}%")

    OUT.mkdir(exist_ok=True)
    scored.to_csv(OUT / "events.csv", index=False)
    board.to_csv(OUT / "scorecard.csv")
    print(f"\nWrote out/events.csv ({len(scored):,} rows) and out/scorecard.csv")


if __name__ == "__main__":
    main()
