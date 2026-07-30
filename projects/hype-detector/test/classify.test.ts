import assert from "node:assert/strict";
import { test } from "node:test";
import {
  interactionZScore,
  manufacturedScore,
  pickCandidates,
  spamRatio,
  top3CreatorShare,
  verdictFor,
} from "../src/classify.js";
import type { CoinRow, SeriesRow } from "../src/types.js";

function flatSeries(days: number, base: number, todayMult = 1): SeriesRow[] {
  return Array.from({ length: days }, (_, i) => ({
    time: i,
    interactions: i === days - 1 ? base * todayMult : base,
    posts_created: 100,
    spam: 20,
  }));
}

test("z-score is high for a genuine spike and ~0 for flat activity", () => {
  // Slight noise so the trailing window has nonzero variance
  const noisy = flatSeries(35, 1000).map((r, i) => ({
    ...r,
    interactions: r.interactions + (i % 2 === 0 ? 50 : -50),
  }));
  const spiked = [...noisy.slice(0, -1), { ...noisy.at(-1)!, interactions: 40_000 }];
  assert.ok(interactionZScore(spiked) > 3);
  assert.ok(Math.abs(interactionZScore(noisy)) < 1.5);
});

test("z-score returns 0 when history is too short", () => {
  assert.equal(interactionZScore(flatSeries(10, 1000, 50)), 0);
});

test("spam ratio reads the latest day", () => {
  const s = flatSeries(35, 1000);
  s[s.length - 1] = { time: 99, interactions: 5000, posts_created: 200, spam: 150 };
  assert.equal(spamRatio(s), 0.75);
});

test("creator concentration: botnet vs broad crowd", () => {
  const botnet = [
    { interactions_24h: 60_000 },
    { interactions_24h: 20_000 },
    { interactions_24h: 10_000 },
    ...Array.from({ length: 20 }, () => ({ interactions_24h: 500 })),
  ];
  const crowd = Array.from({ length: 40 }, () => ({ interactions_24h: 2500 }));
  assert.ok(top3CreatorShare(botnet) > 0.85);
  assert.ok(top3CreatorShare(crowd) < 0.2);
});

test("manufactured score separates the archetypes", () => {
  const manufactured = manufacturedScore({
    zScore: 5,
    spamRatio: 0.85,
    top3CreatorShare: 0.8,
    sentiment: 92,
  });
  const organic = manufacturedScore({
    zScore: 5,
    spamRatio: 0.1,
    top3CreatorShare: 0.15,
    sentiment: 65,
  });
  assert.ok(manufactured >= 60, `expected manufactured >= 60, got ${manufactured}`);
  assert.ok(organic < 40, `expected organic < 40, got ${organic}`);
  assert.equal(verdictFor(manufactured), "manufactured");
  assert.equal(verdictFor(organic), "organic");
});

test("candidate picker enforces eligibility floors", () => {
  const coin = (over: Partial<CoinRow>): CoinRow => ({
    id: 1,
    symbol: "T",
    name: "T",
    topic: "t",
    market_cap: 1e9,
    market_cap_rank: 50,
    volume_24h: 1e8,
    interactions_24h: 100_000,
    alt_rank: 100,
    alt_rank_previous: 500,
    sentiment: 60,
    ...over,
  });
  const rows = [
    coin({ id: 1, symbol: "OK" }),
    coin({ id: 2, symbol: "TINY", market_cap: 1e6 }),
    coin({ id: 3, symbol: "ILLIQUID", volume_24h: 1000 }),
    coin({ id: 4, symbol: "QUIET", interactions_24h: 10 }),
  ];
  const picked = pickCandidates(rows, 10).map((r) => r.symbol);
  assert.deepEqual(picked, ["OK"]);
});
