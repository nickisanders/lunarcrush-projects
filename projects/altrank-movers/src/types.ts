export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  price: number;
  percent_change_24h: number;
  market_cap: number;
  market_cap_rank: number;
  interactions_24h: number;
  social_dominance: number;
  galaxy_score: number;
  galaxy_score_previous?: number;
  alt_rank: number;
  alt_rank_previous?: number;
  sentiment: number;
  topic: string;
}

export interface Mover {
  symbol: string;
  name: string;
  altRank: number;
  altRankPrevious: number;
  delta: number;
  percentChange24h: number;
  interactions24h: number;
}

export interface MoversReport {
  generatedAt: string;
  universeSize: number;
  climbers: Mover[];
  fallers: Mover[];
}
