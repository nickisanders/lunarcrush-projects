import assert from "node:assert/strict";
import { test } from "node:test";
import { computeMovers } from "../src/movers.js";
import type { CoinRow } from "../src/types.js";

function coin(overrides: Partial<CoinRow>): CoinRow {
  return {
    id: 1,
    symbol: "TEST",
    name: "Test Coin",
    price: 1,
    percent_change_24h: 0,
    market_cap: 1_000_000_000,
    market_cap_rank: 10,
    interactions_24h: 100_000,
    social_dominance: 1,
    galaxy_score: 50,
    alt_rank: 100,
    alt_rank_previous: 100,
    sentiment: 60,
    topic: "test coin",
    ...overrides,
  };
}

test("positive delta means the coin climbed (rank number went down)", () => {
  const rows = [coin({ symbol: "UP", alt_rank: 50, alt_rank_previous: 200 })];
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 5, altRankCap: 500 });
  assert.equal(report.climbers.length, 1);
  assert.equal(report.climbers[0].symbol, "UP");
  assert.equal(report.climbers[0].delta, 150);
  assert.equal(report.fallers.length, 0);
});

test("negative delta means the coin fell", () => {
  const rows = [coin({ symbol: "DOWN", alt_rank: 300, alt_rank_previous: 100 })];
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 5, altRankCap: 500 });
  assert.equal(report.fallers.length, 1);
  assert.equal(report.fallers[0].delta, -200);
});

test("filters by market cap rank and interactions", () => {
  const rows = [
    coin({ symbol: "MICROCAP", market_cap_rank: 900, alt_rank: 10, alt_rank_previous: 400 }),
    coin({ symbol: "DEAD", interactions_24h: 10, alt_rank: 10, alt_rank_previous: 400 }),
    coin({ symbol: "OK", alt_rank: 10, alt_rank_previous: 400 }),
  ];
  const report = computeMovers(rows, { topN: 500, minInteractions: 5000, count: 5, altRankCap: 500 });
  assert.deepEqual(
    report.climbers.map((m) => m.symbol),
    ["OK"]
  );
});

test("uses snapshot fallback when alt_rank_previous is missing", () => {
  const rows = [coin({ symbol: "SNAP", alt_rank: 40, alt_rank_previous: undefined })];
  const previousRanks = new Map([["SNAP", 90]]);
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 5, altRankCap: 500, previousRanks });
  assert.equal(report.climbers.length, 1);
  assert.equal(report.climbers[0].delta, 50);
});

test("coins with no previous rank from either source are skipped", () => {
  const rows = [coin({ symbol: "NEW", alt_rank: 40, alt_rank_previous: undefined })];
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 5, altRankCap: 500 });
  assert.equal(report.climbers.length + report.fallers.length, 0);
});

test("relevance cap: climbers must be inside the cap now, fallers must have been inside it", () => {
  const rows = [
    // Tail noise: jumped 2000 places but still ranked 2500. Not a climber.
    coin({ symbol: "TAILUP", alt_rank: 2500, alt_rank_previous: 4500 }),
    // Arrived into relevance: now #80. Climber.
    coin({ symbol: "ARRIVED", alt_rank: 80, alt_rank_previous: 900 }),
    // Tail noise: fell 2000 places, was never relevant. Not a faller.
    coin({ symbol: "TAILDOWN", alt_rank: 4500, alt_rank_previous: 2500 }),
    // Dropped out of relevance: was #60, now #700. Faller.
    coin({ symbol: "DROPPED", alt_rank: 700, alt_rank_previous: 60 }),
  ];
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 5, altRankCap: 200 });
  assert.deepEqual(report.climbers.map((m) => m.symbol), ["ARRIVED"]);
  assert.deepEqual(report.fallers.map((m) => m.symbol), ["DROPPED"]);
});

test("caps results at count, sorted by magnitude", () => {
  const rows = Array.from({ length: 10 }, (_, i) =>
    coin({ id: i, symbol: `C${i}`, alt_rank: 100, alt_rank_previous: 100 + (i + 1) * 10 })
  );
  const report = computeMovers(rows, { topN: 500, minInteractions: 0, count: 3, altRankCap: 500 });
  assert.deepEqual(
    report.climbers.map((m) => m.symbol),
    ["C9", "C8", "C7"]
  );
});
