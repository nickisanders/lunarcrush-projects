import type { CoinCrowd, CoinRow, Creator } from "./types.js";

/** Pegged and wrapped assets: their conversation is plumbing, not a community. */
export const EXCLUDED = new Set([
  "USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE",
  "BUSD", "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG",
  "SUSDE", "USYC", "WBETH",
  "WBTC", "WETH", "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC",
]);

export const MIN_CREATORS = 20;
export const MIN_INTERACTIONS = 100_000;

export function isEligible(coin: CoinRow, creatorsReturned: number): boolean {
  return (
    coin.market_cap_rank > 0 &&
    !EXCLUDED.has(coin.symbol) &&
    coin.interactions_24h >= MIN_INTERACTIONS &&
    creatorsReturned >= MIN_CREATORS
  );
}

/** Creator interactions, largest first, zeroes dropped. */
export function ranked(creators: Creator[]): number[] {
  return creators
    .map((c) => c.interactions_24h ?? 0)
    .filter((n) => n > 0)
    .sort((a, b) => b - a);
}

/** Share of the coin's TOTAL interactions held by the top n accounts.
 *
 * The denominator is the coin's own 24h interaction count, not the sum of the
 * returned creators. The endpoint returns the head of the distribution and
 * drops the tail, so dividing by the creator sum would quietly assume the tail
 * does not exist and inflate every share. Spot-checked across 52 major coins:
 * the creator sum is a median 72% of the coin total, so a real tail is there.
 */
export function topShare(sorted: number[], n: number, total: number): number {
  if (total <= 0) return 0;
  const head = sorted.slice(0, n).reduce((a, b) => a + b, 0);
  return Math.min(1, head / total);
}

/** How many accounts it takes to cover half of everything said about a coin.
 *
 * Null when the returned list never gets there. That is not a failure to
 * measure, it is the answer: the crowd is wider than the endpoint will show,
 * so all we can honestly say is "more than this many". */
export function accountsToHalf(sorted: number[], total: number): number | null {
  if (total <= 0) return null;
  let cum = 0;
  for (let i = 0; i < sorted.length; i++) {
    cum += sorted[i];
    if (cum >= total / 2) return i + 1;
  }
  return null;
}

export function measure(coin: CoinRow, creators: Creator[]): CoinCrowd | null {
  const sorted = ranked(creators);
  if (!isEligible(coin, sorted.length)) return null;
  const total = coin.interactions_24h;
  const named = [...creators]
    .filter((c) => (c.interactions_24h ?? 0) > 0)
    .sort((a, b) => (b.interactions_24h ?? 0) - (a.interactions_24h ?? 0));
  return {
    symbol: coin.symbol,
    name: coin.name,
    marketCapRank: coin.market_cap_rank,
    totalInteractions: total,
    creatorsReturned: sorted.length,
    accountsToHalf: accountsToHalf(sorted, total),
    top1Share: topShare(sorted, 1, total),
    top3Share: topShare(sorted, 3, total),
    top10Share: topShare(sorted, 10, total),
    topCreator: named[0]?.creator_name,
  };
}

/** Widest crowd first. Coins whose list never reached half are the widest of
 * all, so they sort to the front rather than being dropped. */
export function rankByCrowd(coins: CoinCrowd[]): CoinCrowd[] {
  return [...coins].sort(
    (a, b) => (b.accountsToHalf ?? Infinity) - (a.accountsToHalf ?? Infinity)
  );
}

export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Accounts that sit in the top 10 of more than one coin at the same time. */
export function repeatVoices(
  reports: { symbol: string; creators: Creator[] }[],
  depth = 10
): { name: string; coins: string[] }[] {
  const seen = new Map<string, string[]>();
  for (const r of reports) {
    const top = [...r.creators]
      .filter((c) => (c.interactions_24h ?? 0) > 0)
      .sort((a, b) => (b.interactions_24h ?? 0) - (a.interactions_24h ?? 0))
      .slice(0, depth);
    for (const c of top) {
      if (!c.creator_name) continue;
      const list = seen.get(c.creator_name) ?? [];
      list.push(r.symbol);
      seen.set(c.creator_name, list);
    }
  }
  return [...seen.entries()]
    .map(([name, coins]) => ({ name, coins }))
    .filter((v) => v.coins.length > 1)
    .sort((a, b) => b.coins.length - a.coins.length);
}
