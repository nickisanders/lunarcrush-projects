export interface CoinRow {
  id: number;
  symbol: string;
  name: string;
  topic: string;
  market_cap: number;
  market_cap_rank: number;
  interactions_24h: number;
  volume_24h: number;
}

export interface Suspect {
  symbol: string;
  name: string;
  topic: string;
  marketCap: number;
  interactions24h: number;
  /** Interactions per dollar of market cap. */
  perDollar: number;
  /** How many times the market median this coin sits at. */
  vsMedian: number;
  /** Traffic on the bare first word of the topic, when checked. */
  bareTopic?: string;
  bareInteractions?: number;
  bareContributors?: number;
  /** Coin interactions as a share of the bare word's traffic. */
  shareOfBare?: number;
  /** "collision" when the bare word carries traffic the coin cannot account
   * for. "loud" when the topic's traffic IS the coin's, so the ratio is real
   * engagement (or real bots) rather than a naming accident. */
  verdict?: "collision" | "loud" | "unchecked";
}

export interface CollisionReport {
  generatedAt: string;
  scanned: number;
  medianPerDollar: number;
  btcPerDollar: number;
  /** BTC's own 24h interactions, for scale comparisons. */
  btcInteractions: number;
  suspects: Suspect[];
}
