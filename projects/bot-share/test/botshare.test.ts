import assert from "node:assert/strict";
import { test } from "node:test";
import {
  completeWindow,
  dayRatio,
  isEligible,
  median,
  rankScores,
  scoreCoin,
} from "../src/botshare.js";
import type { CoinRow, SeriesRow } from "../src/types.js";

function coin(over: Partial<CoinRow> = {}): CoinRow {
  return { id: 1, symbol: "T", name: "T", market_cap: 5e9, market_cap_rank: 20, ...over };
}

function series(days: number, posts: number, spam: number): SeriesRow[] {
  return Array.from({ length: days }, (_, i) => ({ time: i, posts_created: posts, spam }));
}

test("the day in progress is excluded from the window", () => {
  const s = series(31, 100, 20);
  s[s.length - 1] = { time: 99, posts_created: 10, spam: 9 }; // partial, reads 0.90
  const w = completeWindow(s);
  assert.equal(w.length, 30);
  assert.ok(!w.some((r) => r.time === 99), "today must not appear in the window");
});

test("days with no posting drop out rather than counting as zero spam", () => {
  const s: SeriesRow[] = [...series(5, 100, 50), { time: 90, posts_created: 0, spam: 0 }, ...series(2, 100, 50)];
  assert.ok(completeWindow(s).every((r) => (r.posts_created ?? 0) > 0));
});

test("day ratio is left unclipped, since overshoot is the diagnostic", () => {
  assert.equal(dayRatio({ time: 1, posts_created: 100, spam: 170 }), 1.7);
  assert.equal(dayRatio({ time: 1, posts_created: 0, spam: 50 }), 0, "no posts means no ratio");
});

test("a coin whose spam exceeds its post count is scored but not quotable", () => {
  const s = series(31, 100, 50);
  for (let i = 5; i < 15; i++) s[i] = { time: i, posts_created: 100, spam: 170 };
  const score = scoreCoin(coin(), s)!;
  assert.equal(score.daysOverOne, 10);
  assert.equal(score.quotable, false, "10 days above 1.0 means the ratio is not a share");

  const clean = scoreCoin(coin(), series(31, 100, 50))!;
  assert.equal(clean.daysOverOne, 0);
  assert.equal(clean.quotable, true);
  assert.equal(clean.spamShare, 0.5);
});

test("thin, stablecoin and wrapped conversations are excluded", () => {
  assert.equal(isEligible(coin(), 99), false, "below the posting floor");
  assert.equal(isEligible(coin(), 100), true);
  assert.equal(isEligible(coin({ symbol: "USDT" }), 5000), false);
  assert.equal(isEligible(coin({ symbol: "WBTC" }), 5000), false);
  assert.equal(isEligible(coin({ market_cap_rank: 0 }), 5000), false, "unranked");
});

test("a coin listed mid-window has no stable profile", () => {
  assert.equal(scoreCoin(coin(), series(12, 500, 100)), null);
  assert.ok(scoreCoin(coin(), series(26, 500, 100)));
});

test("median handles even and odd windows", () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([4, 1, 2, 3]), 2.5);
  assert.equal(median([]), 0);
});

test("ranking runs dirtiest first", () => {
  const mk = (symbol: string, spamShare: number) => ({
    symbol, name: symbol, marketCapRank: 1, spamShare, daysOverOne: 0, quotable: true, postsPerDay: 500,
  });
  assert.deepEqual(
    rankScores([mk("B", 0.2), mk("A", 0.9), mk("C", 0.5)]).map((s) => s.symbol),
    ["A", "C", "B"]
  );
});
