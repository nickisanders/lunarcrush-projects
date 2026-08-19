import type { CoinRow, CoinScore, SeriesRow } from "./types.js";

export const WINDOW_DAYS = 30;

/** Coins whose "conversation" is not a community talking about a project.
 * Stablecoins and wrapped assets get discussed as plumbing (transfer alerts,
 * exchange listings, yield mechanics), so their spam profile measures
 * something different from what this leaderboard is about. */
export const STABLECOINS = new Set([
  "USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE",
  "XAUT", "PAXG", "BUSD", "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD",
]);
export const WRAPPED = new Set([
  "WBTC", "WETH", "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC",
]);

/** Below this, the ratio is dominated by rounding: a coin with 4 posts a day
 * swings from 0 to 3.0 on a single flagged post. Every coin whose ratio blew
 * past 1.0 in testing sat in this range, except PEPE and UNI. */
export const MIN_POSTS_PER_DAY = 100;

export function isEligible(coin: CoinRow, postsPerDay: number): boolean {
  return (
    coin.market_cap_rank > 0 &&
    !STABLECOINS.has(coin.symbol) &&
    !WRAPPED.has(coin.symbol) &&
    postsPerDay >= MIN_POSTS_PER_DAY
  );
}

/** Trailing complete days with posting activity, newest last.
 *
 * The final row of any time series is the day in progress. `spam` and
 * `posts_created` accumulate at different rates through a day, so including it
 * biases the ratio high (the bug this repo hit in organic-watchlist and
 * hype-detector). It is dropped before the window is taken. */
export function completeWindow(series: SeriesRow[], days = WINDOW_DAYS): SeriesRow[] {
  return series
    .slice(0, -1)
    .filter((r) => (r.posts_created ?? 0) > 0)
    .slice(-days);
}

export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Unclipped spam-to-created-posts ratio for one day.
 *
 * Deliberately NOT clipped to 1. The clip is right when the number feeds a
 * score, but here the overshoot is the diagnostic: `spam` counts a wider post
 * universe than `posts_created`, so a ratio above 1 is proof that the two
 * fields are not measuring the same denominator for that coin. Clipping would
 * hide exactly the coins whose figure must not be quoted as a percentage. */
export function dayRatio(row: SeriesRow): number {
  const posts = row.posts_created ?? 0;
  if (posts <= 0) return 0;
  return (row.spam ?? 0) / posts;
}

export function scoreCoin(coin: CoinRow, series: SeriesRow[]): CoinScore | null {
  const window = completeWindow(series);
  // Require most of the window; a coin listed mid-window has no stable profile.
  if (window.length < WINDOW_DAYS - 5) return null;
  const postsPerDay = median(window.map((r) => r.posts_created ?? 0));
  if (!isEligible(coin, postsPerDay)) return null;

  const ratios = window.map(dayRatio);
  const daysOverOne = ratios.filter((r) => r > 1).length;
  return {
    symbol: coin.symbol,
    name: coin.name,
    marketCapRank: coin.market_cap_rank,
    spamShare: median(ratios),
    daysOverOne,
    quotable: daysOverOne === 0,
    postsPerDay,
  };
}

export function rankScores(scores: CoinScore[]): CoinScore[] {
  return [...scores].sort((a, b) => b.spamShare - a.spamShare);
}
