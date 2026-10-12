export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  topic: string;
  market_cap: number;
  market_cap_rank: number;
  volume_24h: number;
  interactions_24h: number;
  alt_rank: number;
  alt_rank_previous?: number;
  sentiment: number;
}

export interface SeriesRow {
  time: number;
  interactions: number;
  posts_created?: number;
  spam?: number;
  sentiment?: number;
  close?: number;
}

export interface Creator {
  creator_id?: string;
  creator_name?: string;
  creator_followers?: number;
  interactions_24h?: number;
}

export interface Evidence {
  /** z-score of log interactions vs trailing 30d */
  zScore: number;
  /** share of created posts labeled spam today, clipped 0-1 */
  spamRatio: number;
  /** unclipped spam/posts ratio today (can exceed 1) */
  spamRatioRaw: number;
  /** coin's own trailing 30d median unclipped spam ratio */
  spamBaseline: number;
  /** share of creator interactions from the top 3 accounts (0-1) */
  top3CreatorShare: number;
  /** where top3CreatorShare sits among SAME-SIZE peers (0-1).
   *
   * Concentration falls with size for arithmetic reasons: a token with forty
   * people talking will always have its loudest three owning more of the
   * conversation than one with four thousand. Scoring the raw share therefore
   * charges small tokens for being small. Measured over 123 tokens, the median
   * band-3 token (under $280M) sits at 64.4% against 53.6% for band 1, which is
   * 3.2 points of score before any spam exists.
   *
   * Supply this and the score uses it. Omit it and the score falls back to the
   * raw share, which is the old behaviour and is wrong in the same way. */
  concentrationPercentile?: number;
  /** share held by the single largest account (0-1) */
  top1CreatorShare?: number;
  /** handle of that largest account, for source classification */
  topCreatorName?: string;
  /** 0-100 sentiment; near-unanimous positivity is a manufacturing tell */
  sentiment: number;
  /** top-3 hours' share of the last 24h interactions; organic crowds are
   * burstier (display-only lead, not scored, pending prospective validation) */
  burstShare24h?: number | null;
}

export type Verdict = "manufactured" | "mixed" | "organic";

export interface CoinVerdict {
  symbol: string;
  name: string;
  topic: string;
  marketCapRank: number;
  interactions24h: number;
  evidence: Evidence;
  /** 0-100, higher = more manufactured */
  score: number;
  verdict: Verdict;
  /** one account (or a tight few) IS the conversation: announcement/KOL
   * pattern, distinct from botnet-style manufacturing */
  megaphone: boolean;
  /** an exchange or automated alert feed is the spike: marketing and transfer
   * bots inflate interactions without anyone forming an opinion */
  institutionalBroadcast?: boolean;
  /** top creators behind the spike, persisted so cross-spike patterns
   * (repeat accounts across flagged coins) become measurable over time */
  topCreators?: Array<{
    id?: string;
    name?: string;
    followers?: number;
    interactions?: number;
  }>;
}

export interface DetectorReport {
  generatedAt: string;
  scanned: number;
  spiking: number;
  verdicts: CoinVerdict[];
}
