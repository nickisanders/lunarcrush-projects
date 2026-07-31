export interface SeriesRow {
  time: number;
  interactions: number;
  contributors_active?: number;
  posts_active?: number;
  sentiment?: number;
}

export interface NarrativeWeek {
  key: string;
  title: string;
  /** total interactions, last 7 complete days */
  thisWeek: number;
  /** total interactions, the 7 days before that */
  prevWeek: number;
  /** week-over-week change in the narrative's own volume, percent */
  wowPct: number;
  /** share of tracked-narrative attention this week / last week, percent */
  shareNow: number;
  sharePrev: number;
  /** shareNow - sharePrev, percentage points */
  shareDeltaPp: number;
  /** interaction-weighted average sentiment, this week vs last */
  sentimentNow: number;
  sentimentPrev: number;
}

export interface HotCoin {
  symbol: string;
  name: string;
  interactions_24h: number;
}

export interface RotationReport {
  generatedAt: string;
  weekEnding: string;
  narratives: NarrativeWeek[];
  /** most talked-about coins right now */
  hotCoins: HotCoin[];
}
