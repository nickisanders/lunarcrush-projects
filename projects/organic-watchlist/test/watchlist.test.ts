import assert from "node:assert/strict";
import { test } from "node:test";
import {
  CRITERIA,
  eligibleCandidates,
  interactionZScore,
  medianInteractions,
  qualifies,
  rankEntries,
  spamRatio,
} from "../src/watchlist.js";
import { addDays, attentionDecay, closeOn, collectPicks, summarize } from "../src/track.js";
import type { CoinRow, SeriesRow, WatchEntry } from "../src/types.js";

function coin(over: Partial<CoinRow>): CoinRow {
  return {
    id: 1, symbol: "T", name: "T", topic: "t", price: 1,
    percent_change_24h: 0.5, market_cap: 1e9, market_cap_rank: 50,
    volume_24h: 5e7, interactions_24h: 500_000, alt_rank: 100,
    alt_rank_previous: 400, sentiment: 60, ...over,
  };
}

function series(base: number, todayMult: number, spamShare = 0.1): SeriesRow[] {
  return Array.from({ length: 60 }, (_, i) => {
    const interactions = i === 59 ? base * todayMult : base + (i % 2 ? 40 : -40);
    const posts_created = 100;
    return { time: i, interactions, posts_created, spam: posts_created * spamShare };
  });
}

test("candidates require flat price and real size", () => {
  const rows = [
    coin({ id: 1, symbol: "FLAT", percent_change_24h: 1.2 }),
    coin({ id: 2, symbol: "PUMPED", percent_change_24h: 9.0 }),
    coin({ id: 3, symbol: "DUMPED", percent_change_24h: -8.0 }),
    coin({ id: 4, symbol: "TINY", market_cap: 1e6 }),
    coin({ id: 5, symbol: "ILLIQUID", volume_24h: 1000 }),
  ];
  assert.deepEqual(
    eligibleCandidates(rows, 10).map((c) => c.row.symbol),
    ["FLAT"]
  );
});

test("pegged assets are excluded, since they are flat by construction", () => {
  const rows = [
    coin({ id: 1, symbol: "REAL", percent_change_24h: 0.5 }),
    coin({ id: 2, symbol: "USDE", percent_change_24h: 0.0 }),
    coin({ id: 3, symbol: "WBTC", percent_change_24h: 0.5 }),
  ];
  assert.deepEqual(
    eligibleCandidates(rows, 10).map((c) => c.row.symbol),
    ["REAL"],
    "a stablecoin passes the flat-price leg every day and means nothing by it"
  );
});

test("price flatness boundary matches the backtest's 2%", () => {
  const inside = coin({ symbol: "IN", percent_change_24h: 1.99 });
  const outside = coin({ symbol: "OUT", percent_change_24h: 2.01 });
  const picked = eligibleCandidates([inside, outside], 10).map((c) => c.row.symbol);
  assert.deepEqual(picked, ["IN"]);
});

test("z-score fires on a genuine spike, not on ordinary variation", () => {
  assert.ok(interactionZScore(series(1000, 20)) >= CRITERIA.zMin);
  assert.ok(interactionZScore(series(1000, 1)) < CRITERIA.zMin);
});

test("median reads the trailing window", () => {
  assert.equal(medianInteractions(series(2000, 10, 0.25)), 2040);
});

test("spam ratio ignores today's partial row and reads the last complete day", () => {
  const s = series(2000, 10, 0.25);
  // Today's row is mid-accumulation and reads far higher than reality.
  s[s.length - 1] = { time: 999, interactions: 5000, posts_created: 100, spam: 90 };
  assert.equal(spamRatio(s), 0.25, "should use yesterday, not the 0.90 partial day");
});

test("spam ratio is clipped at 1, since the raw field can exceed it", () => {
  const s = series(1000, 5);
  s[s.length - 2] = { time: 98, interactions: 5000, posts_created: 100, spam: 900 };
  assert.equal(spamRatio(s), 1);
});

test("qualifies enforces every leg of the published setup", () => {
  const ok = { z: 3.5, spam: 0.2, medianInteractions: 5000, percentChange24h: 1.0 };
  assert.equal(qualifies(ok), true);
  assert.equal(qualifies({ ...ok, z: 2.9 }), false, "weak spike");
  assert.equal(qualifies({ ...ok, spam: 0.6 }), false, "too spammy to be organic");
  assert.equal(qualifies({ ...ok, medianInteractions: 500 }), false, "no social baseline");
  assert.equal(qualifies({ ...ok, percentChange24h: 5 }), false, "price already moved");
});

test("entries rank by spike strength, ties to the cleaner conversation", () => {
  const e = (symbol: string, z: number, spam: number): WatchEntry => ({
    symbol, name: symbol, marketCapRank: 10, z, spam, percentChange24h: 0,
    interactions24h: 1000, medianInteractions: 100, multiple: 10,
  });
  assert.deepEqual(
    rankEntries([e("B", 3.2, 0.1), e("A", 5.0, 0.4), e("C", 3.2, 0.05)]).map((x) => x.symbol),
    ["A", "C", "B"]
  );
});

test("picks are deduplicated per day and pegged assets never count", () => {
  const line = (date: string, symbols: string[]) =>
    JSON.stringify({
      generatedAt: `${date}T13:00:00.000Z`,
      entries: symbols.map((symbol) => ({ symbol, z: 3.2, spam: 0.2 })),
    });
  const picks = collectPicks([
    line("2026-08-18", ["LINK"]),
    line("2026-08-18", ["LINK"]), // bot run twice that day; still one pick
    line("2026-08-21", ["USDE"]), // flat by construction, never a real pick
    line("2026-08-19", []),
    "",
  ]);
  assert.deepEqual(
    picks.map((p) => `${p.date}:${p.symbol}`),
    ["2026-08-18:LINK"]
  );
});

test("closes are looked up by exact UTC day, and a missing day reads open", () => {
  const day = (d: string, close: number) => ({ time: Date.parse(`${d}T00:00:00Z`) / 1000, close });
  const series = [day("2026-08-18", 9.5351), day("2026-08-21", 11.9929)];
  assert.equal(closeOn(series, "2026-08-18"), 9.5351);
  assert.equal(closeOn(series, "2026-08-21"), 11.9929);
  assert.equal(closeOn(series, "2026-08-20"), undefined, "an unresolved pick must not silently score");
  assert.equal(addDays("2026-08-18", 3), "2026-08-21");
  assert.equal(addDays("2026-08-30", 3), "2026-09-02", "month boundaries");
});

test("the track record scores against BTC, not against zero", () => {
  const mk = (coinReturn: number, btcReturn: number) => ({
    date: "2026-08-18", symbol: "T", z: 3, spam: 0.2, entry: 1, exit: 1 + coinReturn,
    coinReturn, btcReturn, spread: coinReturn - btcReturn, beatBtc: coinReturn > btcReturn,
  });
  // A coin up 10% in a market up 20% is a loss, however green the candle looks.
  const s = summarize([mk(0.258, 0.192), mk(0.1, 0.2)]);
  assert.equal(s.n, 2);
  assert.equal(s.wins, 1);
  assert.ok(Math.abs(s.meanSpread - (0.066 + -0.1) / 2) < 1e-9);
});

test("attention decay never reads the day in progress", () => {
  const day = (d: string, interactions: number) => ({
    time: Date.parse(`${d}T00:00:00Z`) / 1000, interactions,
  });
  const series = [
    day("2026-08-18", 6_808_499), // the spike that triggered the pick
    day("2026-08-22", 3_005_544),
    day("2026-08-23", 2_113_850), // last complete day
    day("2026-08-24", 1_366_052), // today, still filling: must be ignored
  ];
  const d = attentionDecay(series, "2026-08-18")!;
  assert.equal(d.latest, 2_113_850, "must not use the partial final row");
  assert.equal(d.latestDate, "2026-08-23");
  assert.equal(d.daysElapsed, 5, "elapsed days follow the complete day, not today");
  assert.ok(Math.abs(d.retained - 2_113_850 / 6_808_499) < 1e-9);

  assert.equal(attentionDecay(series, "2026-01-01"), undefined, "no spike row, no claim");
});
