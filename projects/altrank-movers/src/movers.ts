import type { CoinRow, Mover, MoversReport } from "./types.js";

export interface MoversOptions {
  /** Only consider coins within this market cap rank. */
  topN: number;
  /** Ignore coins with fewer 24h interactions than this (filters dead microcaps). */
  minInteractions: number;
  /** How many climbers/fallers to report. */
  count: number;
  /**
   * Relevance cap: climbers must currently be inside this AltRank, fallers must
   * have been inside it yesterday. Filters out meaningless rank swings deep in
   * the tail, where AltRank moves by thousands of places on tiny social volume.
   */
  altRankCap: number;
  /** Fallback map of symbol to yesterday's alt_rank, used when the API omits alt_rank_previous. */
  previousRanks?: Map<string, number>;
}

export const DEFAULT_OPTIONS: MoversOptions = {
  topN: 500,
  minInteractions: 5000,
  count: 5,
  altRankCap: 200,
};

export function computeMovers(rows: CoinRow[], opts: MoversOptions = DEFAULT_OPTIONS): MoversReport {
  const eligible = rows.filter(
    (r) =>
      r.market_cap_rank > 0 &&
      r.market_cap_rank <= opts.topN &&
      typeof r.alt_rank === "number" &&
      r.alt_rank > 0 &&
      r.interactions_24h >= opts.minInteractions
  );

  const movers: Mover[] = [];
  for (const r of eligible) {
    const prev = r.alt_rank_previous ?? opts.previousRanks?.get(r.symbol);
    if (typeof prev !== "number" || prev <= 0) continue;
    movers.push({
      symbol: r.symbol,
      name: r.name,
      altRank: r.alt_rank,
      altRankPrevious: prev,
      // AltRank is a rank, so lower is better. Positive delta = improved.
      delta: prev - r.alt_rank,
      percentChange24h: r.percent_change_24h,
      interactions24h: r.interactions_24h,
    });
  }

  const climbers = movers
    .filter((m) => m.delta > 0 && m.altRank <= opts.altRankCap)
    .sort((a, b) => b.delta - a.delta || a.altRank - b.altRank)
    .slice(0, opts.count);

  const fallers = movers
    .filter((m) => m.delta < 0 && m.altRankPrevious <= opts.altRankCap)
    .sort((a, b) => a.delta - b.delta || a.altRank - b.altRank)
    .slice(0, opts.count);

  return {
    generatedAt: new Date().toISOString(),
    universeSize: eligible.length,
    climbers,
    fallers,
  };
}
