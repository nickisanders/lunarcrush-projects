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
