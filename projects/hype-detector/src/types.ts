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
  /** share of created posts labeled spam today (0-1) */
  spamRatio: number;
  /** share of creator interactions from the top 3 accounts (0-1) */
  top3CreatorShare: number;
  /** 0-100 sentiment; extreme uniform positivity is a manufacturing tell */
  sentiment: number;
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
}

export interface DetectorReport {
  generatedAt: string;
  scanned: number;
  spiking: number;
  verdicts: CoinVerdict[];
}
