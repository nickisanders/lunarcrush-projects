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
