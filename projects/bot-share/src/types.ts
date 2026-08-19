export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  market_cap: number;
  market_cap_rank: number;
}

export interface SeriesRow {
  time: number;
  posts_created?: number | null;
  spam?: number | null;
}

export interface CoinScore {
  symbol: string;
  name: string;
  marketCapRank: number;
  /** Median of spam/posts_created over the trailing complete days. */
  spamShare: number;
  /** Days in the window where spam exceeded posts_created. Zero means the
   * ratio behaved as a share throughout and the figure can be quoted as a
   * percentage; anything above zero means it cannot. */
  daysOverOne: number;
  quotable: boolean;
  postsPerDay: number;
}

export interface BotShareReport {
  generatedAt: string;
  windowDays: number;
  scanned: number;
  scored: CoinScore[];
}
