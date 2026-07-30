import type { CoinRow, Creator, Evidence, SeriesRow, Verdict } from "./types.js";

export const ELIGIBILITY = {
  topN: 1000,
  minMarketCap: 50e6,
  minVolume: 1e6,
  minInteractions: 5000,
};

/** Cheap first-stage filter from the coins list alone: coins whose AltRank
 * jumped into relevance or whose social volume is outsized. The expensive
 * per-coin calls only run for these. */
export function pickCandidates(rows: CoinRow[], max = 40): CoinRow[] {
  const eligible = rows.filter(
    (r) =>
      r.market_cap_rank > 0 &&
      r.market_cap_rank <= ELIGIBILITY.topN &&
      r.market_cap >= ELIGIBILITY.minMarketCap &&
      r.volume_24h >= ELIGIBILITY.minVolume &&
      r.interactions_24h >= ELIGIBILITY.minInteractions
  );
  const scored = eligible.map((r) => {
    const altJump =
      typeof r.alt_rank_previous === "number" && r.alt_rank_previous > 0
        ? Math.max(0, r.alt_rank_previous - r.alt_rank)
        : 0;
    // Outsized social volume for the coin's size: interactions above what its
    // market cap rank would suggest.
    const socialOutsize = r.interactions_24h / (1 + Math.sqrt(r.market_cap_rank));
    return { row: r, heat: altJump * 50 + socialOutsize };
  });
  return scored
    .sort((a, b) => b.heat - a.heat)
    .slice(0, max)
    .map((s) => s.row);
}

/** z-score of log(1+interactions) for the latest day vs the trailing window. */
export function interactionZScore(series: SeriesRow[], trailing = 30): number {
  if (series.length < trailing + 1) return 0;
  const li = series.map((r) => Math.log1p(r.interactions ?? 0));
  const today = li[li.length - 1];
  const window = li.slice(-1 - trailing, -1);
  const mean = window.reduce((a, b) => a + b, 0) / window.length;
  const sd = Math.sqrt(window.reduce((a, b) => a + (b - mean) ** 2, 0) / window.length);
  if (sd === 0) return 0;
  return (today - mean) / sd;
}

export function spamRatio(series: SeriesRow[]): number {
  const today = series[series.length - 1];
  if (!today || !today.posts_created) return 0;
  return Math.min(1, (today.spam ?? 0) / Math.max(1, today.posts_created));
}

export function top3CreatorShare(creators: Creator[]): number {
  const interactions = creators
    .map((c) => c.interactions_24h ?? 0)
    .filter((n) => n > 0)
    .sort((a, b) => b - a);
  const total = interactions.reduce((a, b) => a + b, 0);
  if (total === 0) return 0;
  const top3 = interactions.slice(0, 3).reduce((a, b) => a + b, 0);
  return top3 / total;
}

/** 0-100 manufactured score. Weights follow what the backtest validated:
 * spam share is the load-bearing signal, concentration and sentiment
 * uniformity are supporting tells. */
export function manufacturedScore(e: Evidence): number {
  const spam = e.spamRatio; // 0-1
  const concentration = e.top3CreatorShare; // 0-1
  // Sentiment uniformity: 50 = balanced crowd, 100 = suspiciously unanimous.
  // Only extreme positivity counts; organic fear is not manufacturing.
  const uniformity = Math.max(0, (e.sentiment - 75) / 25); // 0-1 above 75
  return Math.round(100 * (0.55 * spam + 0.3 * concentration + 0.15 * uniformity));
}

export function verdictFor(score: number): Verdict {
  if (score >= 60) return "manufactured";
  if (score >= 30) return "mixed";
  return "organic";
}

/** Only coins genuinely spiking get a verdict at all. */
export const SPIKE_Z_MIN = 2.0;
