import assert from "node:assert/strict";
import { test } from "node:test";
import { bareTopic, findSuspects, isEligible, median, perDollar } from "../src/collision.js";
import type { CoinRow } from "../src/types.js";

function coin(over: Partial<CoinRow> = {}): CoinRow {
  return { id: 1, symbol: "T", name: "T", topic: "t t", market_cap: 1_000_000,
    market_cap_rank: 500, interactions_24h: 300, volume_24h: 1000, ...over };
}

test("per-dollar is the ratio, not the raw count", () => {
  // Bitcoin has an enormous conversation and an enormous market cap, so it is
  // unremarkable on this measure. That is the point of dividing.
  const btc = coin({ market_cap: 1.5e12, interactions_24h: 220e6 });
  const tiny = coin({ market_cap: 279_072, interactions_24h: 1_006_764 });
  assert.ok(perDollar(btc) < 0.001);
  assert.ok(perDollar(tiny) > 3, "more engagement than dollars of market cap");
  assert.equal(perDollar(coin({ market_cap: 0 })), 0, "no market cap, no ratio");
});

test("the bare topic is the ticker, which is the part that collides", () => {
  assert.equal(bareTopic("am aston martin cognizant fan token"), "am");
  assert.equal(bareTopic("optimus digital optimus"), "optimus");
  assert.equal(bareTopic("  47 president trump "), "47");
  assert.equal(bareTopic(""), "");
});

test("thin and quiet coins are excluded before ranking", () => {
  assert.equal(isEligible(coin({ market_cap: 49_999, interactions_24h: 1e6 })), false);
  assert.equal(isEligible(coin({ interactions_24h: 9_999 })), false, "one viral post is not a collision");
  assert.equal(isEligible(coin({ market_cap_rank: 0 })), false);
  assert.equal(isEligible(coin({ market_cap: 100_000, interactions_24h: 20_000 })), true);
});

test("suspects are ranked by how far above the market median they sit", () => {
  // 40 ordinary coins set the median, then two outliers. They need to clear
  // the eligibility floor themselves, or they never reach the median at all.
  const ordinary = Array.from({ length: 40 }, (_, i) =>
    coin({ symbol: `N${i}`, market_cap: 100_000_000, interactions_24h: 30_000 }));
  const rows = [
    ...ordinary,
    coin({ symbol: "AM", market_cap: 279_072, interactions_24h: 1_006_764 }),
    coin({ symbol: "MILD", market_cap: 1_000_000, interactions_24h: 30_000 }),
  ];
  const { suspects, medianPerDollar } = findSuspects(rows);
  assert.ok(Math.abs(medianPerDollar - 0.0003) < 1e-9);
  assert.deepEqual(suspects.map((s) => s.symbol), ["AM", "MILD"], "worst first");
  assert.ok(suspects[0].vsMedian > 10_000);
  // A coin merely 100x the median is caught; an ordinary one is not.
  assert.ok(!suspects.some((s) => s.symbol.startsWith("N")));
});

test("an empty or flat universe yields no suspects rather than dividing by zero", () => {
  assert.deepEqual(findSuspects([]).suspects, []);
  assert.equal(findSuspects([]).medianPerDollar, 0);
  assert.deepEqual(findSuspects([coin({ interactions_24h: 0 })]).suspects, []);
});

test("median handles even and odd", () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([4, 1, 2, 3]), 2.5);
  assert.equal(median([]), 0);
});
