import type { CoinRow, Candidate, SeriesRow, WatchEntry } from "./types.js";

/** These thresholds are not adjustable knobs. They are the exact event
 * definition from the social-price-backtest, which measured what happens next:
 * organic spikes beat BTC over the following 3 days 49.0% of the time versus
 * 41.9% for ordinary coin-days (p=0.003, month-cluster bootstrap, 6.5 years).
 * Change any of them and that hit rate no longer describes this list. */
export const CRITERIA = {
  /** interactions z-score vs the coin's own trailing 30 days */
  zMin: 3.0,
  /** price must not have reacted yet: |24h close-to-close| <= 2% */
  flatPriceMax: 0.02,
  /** spam share of created posts; above this it is not organic */
  spamMax: 0.5,
  minMarketCap: 50e6,
  minVolume24h: 1e6,
  /** trailing median interactions, so z-scores are not computed on noise */
  minMedianInteractions: 2000,
} as const;

export const BASELINE = { organic: 0.49, ordinary: 0.419, horizonDays: 3 } as const;

const TRAILING = 30;

/** Coins that could qualify, before the expensive per-coin history call.
 * Price flatness and size are knowable from the list; the spike is not. */
/** Pegged assets, which pass the flat-price test every single day.
 *
 * The whole setup rests on "attention moved and price has not reacted YET",
 * which presumes a price free to react. A stablecoin's is not: it sits inside
 * the 2% band by design, so it satisfies the hardest-to-meet leg of the
 * criteria for free and is structurally over-represented among candidates.
 * $USDE surfaced this on 2026-08-21 at 23x its normal chatter and a 0.0% move,
 * which reads like a perfect signal and means nothing.
 *
 * Wrapped and liquid-staking assets are excluded for the neighbouring reason:
 * they track another asset's price, so their conversation and their chart
 * belong to something else. */
export const PEGGED = new Set([
  "USDT", "USDC", "USDE", "DAI", "FDUSD", "USD1", "RLUSD", "PYUSD", "USDCE",
  "BUSD", "TUSD", "USDS", "USDD", "BFUSD", "BSC-USD", "USDGO", "XAUT", "PAXG",
  "WBTC", "WETH", "WBNB", "STETH", "WSTETH", "WEETH", "CBBTC", "RETH", "SOLVBTC", "LBTC",
]);

export function eligibleCandidates(rows: CoinRow[], max = 80): Candidate[] {
  const eligible = rows.filter(
    (r) =>
      !PEGGED.has(r.symbol) &&
      r.market_cap >= CRITERIA.minMarketCap &&
      r.volume_24h >= CRITERIA.minVolume24h &&
      r.interactions_24h > 0 &&
      Number.isFinite(r.percent_change_24h) &&
      Math.abs(r.percent_change_24h) <= CRITERIA.flatPriceMax * 100
  );
  // Rank by how likely a spike is: raw social volume, plus a bonus for coins
  // whose AltRank jumped, which is the cheapest available spike proxy.
  return eligible
    .map((row) => {
      const altJump =
        typeof row.alt_rank_previous === "number" && row.alt_rank_previous > 0
          ? Math.max(0, row.alt_rank_previous - row.alt_rank)
          : 0;
      return { row, heat: Math.log1p(row.interactions_24h) + altJump / 200 };
    })
    .sort((a, b) => b.heat - a.heat)
    .slice(0, max);
}

/** z-score of log(1+interactions) for the latest complete day. The caller
 * substitutes the coins-list rolling 24h count for the final series row, which
 * is a partial day and would otherwise never register as a spike. */
export function interactionZScore(series: SeriesRow[]): number {
  if (series.length < TRAILING + 1) return 0;
  const li = series.map((r) => Math.log1p(r.interactions ?? 0));
  const today = li[li.length - 1];
  const window = li.slice(-1 - TRAILING, -1);
  const mean = window.reduce((a, b) => a + b, 0) / window.length;
  const sd = Math.sqrt(window.reduce((a, b) => a + (b - mean) ** 2, 0) / window.length);
  return sd === 0 ? 0 : (today - mean) / sd;
}

export function medianInteractions(series: SeriesRow[]): number {
  const window = series
    .slice(-1 - TRAILING, -1)
    .map((r) => r.interactions ?? 0)
    .sort((a, b) => a - b);
  return window.length === 0 ? 0 : window[Math.floor(window.length / 2)];
}

/** Spam share of created posts for the most recent COMPLETE day.
 *
 * Deliberately not today's row. `spam` and `posts_created` accumulate at
 * different rates through a day, so the ratio on a partial day is unstable and
 * biased high: on 2026-08-18 LINK read 0.32 at 13:33 UTC and 0.65 at 15:06,
 * while its completed days that week ran 0.15 to 0.27. That inflation was
 * rejecting qualifying coins for spam they did not have.
 *
 * The backtest measured complete days, so the published 49% only describes a
 * complete-day ratio. Using yesterday's figure costs up to a day of freshness
 * and keeps the threshold meaning what it meant when it was measured. There is
 * no rolling 24h spam figure available to do better; the hourly series reports
 * spam counts that routinely exceed its own posts_created, so it cannot
 * substitute.
 *
 * Clipped to 0-1 to match the backtest, since the raw field can exceed 1. */
export function spamRatio(series: SeriesRow[]): number {
  const lastComplete = series[series.length - 2];
  if (!lastComplete?.posts_created) return 0;
  return Math.min(1, (lastComplete.spam ?? 0) / Math.max(1, lastComplete.posts_created));
}

export function qualifies(e: {
  z: number;
  spam: number;
  medianInteractions: number;
  percentChange24h: number;
}): boolean {
  return (
    e.z >= CRITERIA.zMin &&
    e.spam <= CRITERIA.spamMax &&
    e.medianInteractions >= CRITERIA.minMedianInteractions &&
    Math.abs(e.percentChange24h) <= CRITERIA.flatPriceMax * 100
  );
}

export function rankEntries(entries: WatchEntry[]): WatchEntry[] {
  // Strongest spike first; ties to the cleaner conversation.
  return [...entries].sort((a, b) => b.z - a.z || a.spam - b.spam);
}

/** Which leg of the setup a candidate failed, for the near-miss list. */
export function failureReason(e: {
  z: number;
  spam: number;
  medianInteractions: number;
  percentChange24h: number;
}): string | null {
  if (e.medianInteractions < CRITERIA.minMedianInteractions) return "no social baseline";
  if (Math.abs(e.percentChange24h) > CRITERIA.flatPriceMax * 100) return "price already moved";
  if (e.spam > CRITERIA.spamMax) return `${Math.round(e.spam * 100)}% spam`;
  if (e.z < CRITERIA.zMin) return `spike only ${e.z.toFixed(1)} of ${CRITERIA.zMin.toFixed(1)}`;
  return null;
}

/** The first word of a LunarCrush topic string, which is the ticker.
 *
 * Topics read "hot holo": the ticker followed by the name. The ticker alone is
 * what a common word collides with, so that is what gets checked. */
export function bareTopic(topic: string): string {
  return (topic || "").trim().split(/\s+/)[0] || "";
}

/** How much bigger the bare ticker's own traffic must be before a coin's spike
 * is more plausibly the word than the coin. */
export const COLLISION_MULTIPLE = 3;

/** Interactions per active contributor above which a spike is not credible.
 *
 * Measured, not guessed: across the backtest the median coin draws 296
 * interactions per active contributor on an ordinary day and 1,577 on a spike
 * day. $HOT was flagged at 37x normal chatter on 2026-08-30 with 1.85M
 * interactions from 71 contributors, or 26,024 each, which is 16x the spike-day
 * norm. A real crowd does not do that; a name collision does. */
export const MAX_PER_CONTRIBUTOR = 8_000;

/** Is this spike more plausibly about the word than the coin?
 *
 * Two independent tests, either of which is disqualifying:
 *
 * 1. The bare ticker carries multiples of the coin's own traffic. A ticker that
 *    is also an ordinary word ("hot", "am", "47") collects every unrelated use
 *    of it.
 * 2. The interactions are spread over too few contributors to be real. This
 *    catches collisions the topic check misses, and needs no extra request.
 */
export function isNameCollision(input: {
  interactions24h: number;
  contributors?: number;
  bareInteractions?: number;
}): { collision: boolean; reason?: string } {
  const { interactions24h, contributors, bareInteractions } = input;
  if (bareInteractions !== undefined && bareInteractions >= interactions24h * COLLISION_MULTIPLE) {
    return { collision: true, reason: `the bare ticker draws ${Math.round(bareInteractions / interactions24h)}x the coin's traffic` };
  }
  if (contributors && contributors > 0) {
    const per = interactions24h / contributors;
    if (per > MAX_PER_CONTRIBUTOR) {
      return { collision: true, reason: `${Math.round(per).toLocaleString()} interactions per contributor, against a spike-day norm of ~1,600` };
    }
  }
  return { collision: false };
}
