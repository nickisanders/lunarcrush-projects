export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  topic: string;
  price: number;
  percent_change_24h: number;
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
  interactions?: number;
  posts_created?: number;
  spam?: number;
  close?: number;
  /** Unique accounts posting that day. Used to sanity-check a spike: a real
   * crowd produces a plausible number of interactions each. */
  contributors_active?: number;
}

export interface Candidate {
  row: CoinRow;
  heat: number;
}

export interface WatchEntry {
  symbol: string;
  name: string;
  marketCapRank: number;
  /** interactions z-score vs the coin's own trailing 30 days */
  z: number;
  /** spam share of created posts, 0-1 */
  spam: number;
  /** 24h price change, percent; near zero by construction */
  percentChange24h: number;
  interactions24h: number;
  medianInteractions: number;
  /** how many times its own normal day this is */
  multiple: number;
}

export interface NearMiss {
  symbol: string;
  z: number;
  spam: number;
  percentChange24h: number;
  /** which leg of the setup it failed */
  failed: string;
}

export interface WatchlistReport {
  generatedAt: string;
  scanned: number;
  checked: number;
  entries: WatchEntry[];
  /** shown so an empty list still proves the scan ran; these do NOT carry
   * the backtested edge, which applies only to the full setup */
  nearMisses: NearMiss[];
}
