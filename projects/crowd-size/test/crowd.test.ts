import assert from "node:assert/strict";
import { test } from "node:test";
import {
  accountsToHalf,
  isEligible,
  measure,
  median,
  rankByCrowd,
  ranked,
  repeatVoices,
  topShare,
} from "../src/crowd.js";
import { logCorrelation, summarize, topVoices } from "../src/reach.js";
import type { CoinRow, Creator } from "../src/types.js";

function coin(over: Partial<CoinRow> = {}): CoinRow {
  return { id: 1, symbol: "T", name: "T", topic: "t", market_cap: 5e9,
    market_cap_rank: 20, interactions_24h: 1_000_000, ...over };
}
const creators = (...amounts: number[]): Creator[] =>
  amounts.map((n, i) => ({ creator_name: `acct${i}`, interactions_24h: n }));

test("shares divide by the coin total, not by the creator sum", () => {
  // The endpoint returns the head of the distribution: these five accounts are
  // 300k of a 1M conversation, so the top 3 are 25% of everything, not 83% of
  // what happens to have been returned.
  const s = ranked(creators(100_000, 90_000, 60_000, 30_000, 20_000));
  assert.equal(topShare(s, 3, 1_000_000), 0.25);
  assert.equal(topShare(s, 1, 1_000_000), 0.1);
  assert.equal(topShare(s, 99, 1_000_000), 0.3, "asking for more accounts than exist is fine");
});

test("accounts-to-half counts down the sorted list", () => {
  assert.equal(accountsToHalf(ranked(creators(600_000, 100_000)), 1_000_000), 1);
  assert.equal(accountsToHalf(ranked(creators(300_000, 200_000, 90_000)), 1_000_000), 2);
});

test("a crowd wider than the endpoint reads null, not a wrong number", () => {
  // 20 accounts covering 20% of a huge conversation: the honest answer is
  // "more than 20", and null is how that is carried without inventing one.
  const wide = creators(...Array.from({ length: 20 }, () => 10_000));
  assert.equal(accountsToHalf(ranked(wide), 1_000_000), null);
  const m = measure(coin(), wide)!;
  assert.equal(m.accountsToHalf, null);
  assert.equal(m.top10Share, 0.1);
});

test("null crowds sort to the front, as the widest of all", () => {
  const mk = (symbol: string, accountsToHalf: number | null) =>
    ({ symbol, accountsToHalf } as never);
  assert.deepEqual(
    rankByCrowd([mk("NARROW", 3), mk("WIDEST", null), mk("WIDE", 200)]).map((c: any) => c.symbol),
    ["WIDEST", "WIDE", "NARROW"]
  );
});

test("thin, quiet and pegged coins are excluded", () => {
  assert.equal(isEligible(coin(), 19), false, "too few creators returned to rank");
  assert.equal(isEligible(coin(), 20), true);
  assert.equal(isEligible(coin({ interactions_24h: 5_000 }), 500), false, "too quiet");
  assert.equal(isEligible(coin({ symbol: "USDT" }), 500), false);
  assert.equal(isEligible(coin({ symbol: "WBTC" }), 500), false);
  assert.equal(measure(coin({ symbol: "USDT" }), creators(1, 2, 3)), null);
});

test("a share can never exceed 1, even if the fields disagree", () => {
  // Thin coins have been observed where the creator sum exceeds the coin's own
  // total. That means the two fields are counting differently, and a share
  // above 100% would be nonsense on its face.
  assert.equal(topShare(ranked(creators(900, 800)), 2, 1_000), 1);
});

test("repeat voices catch one account dominating several coins at once", () => {
  const found = repeatVoices([
    { symbol: "TAO", creators: creators(500, 100).map((c, i) => ({ ...c, creator_name: i === 0 ? "mich" : "a" })) },
    { symbol: "ONDO", creators: creators(500, 100).map((c, i) => ({ ...c, creator_name: i === 0 ? "mich" : "b" })) },
    { symbol: "BTC", creators: creators(500, 100).map((c, i) => ({ ...c, creator_name: i === 0 ? "c" : "mich" })) },
  ]);
  assert.deepEqual(found[0], { name: "mich", coins: ["TAO", "ONDO", "BTC"] });
  assert.ok(!found.some((v) => v.name === "a"), "accounts on one coin are not repeats");
});

test("median handles even and odd", () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([4, 1, 2, 3]), 2.5);
  assert.equal(median([]), 0);
});

test("top voices need a usable follower count to be scored", () => {
  const raw = [{
    symbol: "X",
    creators: [
      { creator_name: "big", creator_followers: 1_000_000, interactions_24h: 500 },
      { creator_name: "small", creator_followers: 152, interactions_24h: 900 },
      { creator_name: "nofollowers", interactions_24h: 400 },
      { creator_name: "zero", creator_followers: 0, interactions_24h: 300 },
      { creator_name: "silent", creator_followers: 5000, interactions_24h: 0 },
    ],
  }];
  const v = topVoices(raw);
  assert.deepEqual(v.map((x) => x.name), ["small", "big"], "ranked by impact, not by followers");
  assert.equal(v[0].rank, 1, "the 152-follower account is the loudest voice here");
  assert.ok(!v.some((x) => x.name === "nofollowers"), "no follower count, no point on the chart");
  assert.ok(!v.some((x) => x.name === "zero"));
  assert.ok(!v.some((x) => x.name === "silent"), "zero interactions is not a voice");
});

test("correlation is computed in log space", () => {
  // Perfectly proportional in log space: 10x followers, 10x interactions.
  const perfect = [
    { coin: "X", rank: 1, name: "a", followers: 100, interactions: 100 },
    { coin: "X", rank: 2, name: "b", followers: 1_000, interactions: 1_000 },
    { coin: "X", rank: 3, name: "c", followers: 10_000, interactions: 10_000 },
  ];
  assert.ok(Math.abs(logCorrelation(perfect) - 1) < 1e-9);
  // Exactly inverted: the biggest account lands least.
  const inverted = perfect.map((v, i) => ({ ...v, interactions: [10_000, 1_000, 100][i] }));
  assert.ok(Math.abs(logCorrelation(inverted) + 1) < 1e-9);
  assert.equal(logCorrelation([]), 0, "too few points to claim a relationship");
});

test("the summary counts the follower bands it reports", () => {
  const v = [152, 900, 5_000, 50_000, 2_000_000].map((followers, i) => ({
    coin: "X", rank: i + 1, name: `a${i}`, followers, interactions: 1000,
  }));
  const s = summarize(v);
  assert.equal(s.voices, 5);
  assert.equal(s.underOneThousand, 2);
  assert.equal(s.underTenThousand, 3);
  assert.equal(s.overOneMillion, 1);
  assert.equal(s.medianFollowers, 5_000);
});
