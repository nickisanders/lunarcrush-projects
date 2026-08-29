import type { CoinRow, Suspect } from "./types.js";

/** Below this the ratio is noise: a coin with a $30k market cap and one viral
 * post looks identical to a permanent collision. */
export const MIN_MARKET_CAP = 50_000;
export const MIN_INTERACTIONS = 10_000;

/** How many times the market median counts as implausible. Set high on
 * purpose. A genuinely beloved microcap might run 20x the median; nothing
 * legitimately runs 1,000x, and the worst offenders here run 13,000x. */
export const SUSPECT_MULTIPLE = 100;

export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Social engagement per dollar of market cap.
 *
 * The ratio matters more than either number alone. Big coins have big
 * conversations and small coins have small ones, so raw interactions say
 * nothing about whether a conversation is really about the coin. A token
 * carrying more daily engagement than its entire market capitalisation in
 * dollars is not being discussed by its holders. */
export function perDollar(coin: CoinRow): number {
  if (!coin.market_cap || coin.market_cap <= 0) return 0;
  return coin.interactions_24h / coin.market_cap;
}

export function isEligible(coin: CoinRow): boolean {
  return (
    coin.market_cap >= MIN_MARKET_CAP &&
    coin.interactions_24h >= MIN_INTERACTIONS &&
    coin.market_cap_rank > 0
  );
}

/** The first word of a topic string, which is the part that collides.
 *
 * LunarCrush topics read "am aston martin cognizant fan token": the ticker
 * followed by the name. The ticker alone is what a generic word matches, so
 * that is what gets checked against the wider platform. */
export function bareTopic(topic: string): string {
  return (topic || "").trim().split(/\s+/)[0] || "";
}

export function findSuspects(coins: CoinRow[], multiple = SUSPECT_MULTIPLE): {
  suspects: Suspect[];
  medianPerDollar: number;
} {
  const eligible = coins.filter(isEligible);
  const med = median(eligible.map(perDollar).filter((v) => v > 0));
  if (med <= 0) return { suspects: [], medianPerDollar: 0 };

  const suspects = eligible
    .map((c) => {
      const pd = perDollar(c);
      return {
        symbol: c.symbol, name: c.name, topic: c.topic,
        marketCap: c.market_cap, interactions24h: c.interactions_24h,
        perDollar: pd, vsMedian: pd / med,
      };
    })
    .filter((s) => s.vsMedian >= multiple)
    .sort((a, b) => b.vsMedian - a.vsMedian);
  return { suspects, medianPerDollar: med };
}


/** How much bigger the bare word's traffic must be before the coin's number is
 * mostly somebody else's conversation. At 3x, two thirds of the topic's
 * activity is unaccounted for by the coin. */
export const COLLISION_MULTIPLE = 3;

/** Distinguish a naming accident from a genuinely loud microcap.
 *
 * A high interactions-per-dollar ratio alone does not prove contamination. It
 * catches two different things: $AM, whose ticker is a common English word
 * carrying 631 million daily interactions, and $TITCOIN, whose topic traffic
 * is entirely its own. Only the first is a measurement problem; the second is
 * a real (if strange) conversation, and calling it a collision would be wrong.
 */
export function classify(coinInteractions: number, bareInteractions?: number):
  "collision" | "loud" | "unchecked" {
  if (bareInteractions === undefined || bareInteractions <= 0) return "unchecked";
  return bareInteractions >= coinInteractions * COLLISION_MULTIPLE ? "collision" : "loud";
}
