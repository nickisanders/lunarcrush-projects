export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  topic: string;
  market_cap: number;
  market_cap_rank: number;
  interactions_24h: number;
}

export interface Creator {
  creator_name?: string;
  creator_followers?: number;
  interactions_24h?: number;
}

export interface CoinCrowd {
  symbol: string;
  name: string;
  marketCapRank: number;
  totalInteractions: number;
  creatorsReturned: number;
  /** Accounts needed to cover half of ALL interactions about the coin.
   * Null when the returned creator list never reaches half, which is itself
   * informative: the crowd is wider than the endpoint can show. */
  accountsToHalf: number | null;
  top1Share: number;
  top3Share: number;
  top10Share: number;
  topCreator?: string;
}

export interface CrowdReport {
  generatedAt: string;
  scanned: number;
  coins: CoinCrowd[];
}
