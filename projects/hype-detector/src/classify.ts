import type { CoinRow, Creator, Evidence, SeriesRow, Verdict } from "./types.js";
export type { SeriesRow };

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

/** Spam share of created posts for the most recent COMPLETE day.
 *
 * Never today's row. `spam` and `posts_created` accumulate at different rates
 * through a day, so a partial-day ratio is unstable and biased high: LINK read
 * 0.32 at 13:33 UTC on 2026-08-18 and 0.65 at 15:06 the same day, against
 * completed days that week of 0.15 to 0.27. Reading the partial day inflates
 * spam and makes clean conversations look manufactured. */
export function spamRatio(series: SeriesRow[]): number {
  const lastComplete = lastCompleteRow(series);
  if (!lastComplete || !lastComplete.posts_created) return 0;
  return Math.min(1, (lastComplete.spam ?? 0) / Math.max(1, lastComplete.posts_created));
}

/** The most recent row that represents a finished day. The final row of any
 * time series is the day in progress and must not be used for ratios between
 * two fields that fill at different rates. */
export function lastCompleteRow(series: SeriesRow[]): SeriesRow | undefined {
  return series.length >= 2 ? series[series.length - 2] : undefined;
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

/** Share of creator interactions held by the single largest account. The
 * top-3 share can't tell "one account is the whole conversation" apart from
 * "three accounts split it", and those are different phenomena. */
export function top1CreatorShare(creators: Creator[]): number {
  const interactions = creators.map((c) => c.interactions_24h ?? 0).filter((n) => n > 0);
  const total = interactions.reduce((a, b) => a + b, 0);
  if (total === 0) return 0;
  return Math.max(...interactions) / total;
}

export function topCreatorName(creators: Creator[]): string | undefined {
  let best: Creator | undefined;
  for (const c of creators) {
    if ((c.interactions_24h ?? 0) > (best?.interactions_24h ?? 0)) best = c;
  }
  return best?.creator_name;
}

/** Accounts whose posting is institutional broadcast rather than opinion:
 * exchange marketing accounts and automated alert/data feeds. Matched on the
 * normalized handle, exact only — a substring match would catch unrelated
 * accounts ("gate" in "stargate"), and a false institutional label is worse
 * than falling back to the generic megaphone case. Extend as they turn up. */
const INSTITUTIONAL_ACCOUNTS = new Set([
  // exchanges
  "binance", "binanceus", "coinbase", "coinbaseexchange", "kraken", "krakenfx",
  "okx", "bybit", "bybitofficial", "mexc", "mexcid", "mexcglobal", "gate", "gateio",
  "kucoin", "kucoincom", "htx", "htxofficial", "bitget", "bitgetglobal", "bingx",
  "cryptocom", "upbit", "bitfinex", "gemini", "bitstamp", "bitmart", "lbank", "phemex",
  // automated alert and data feeds
  "whalealert", "arkham", "arkhamintel", "spotonchain", "dexscreener",
  "coingecko", "coinmarketcap", "tokenunlocks", "defillama",
]);

function normalizeHandle(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export function isInstitutionalAccount(name?: string): boolean {
  return name ? INSTITUTIONAL_ACCOUNTS.has(normalizeHandle(name)) : false;
}

/** One account carrying most of the conversation is only interesting once you
 * know what kind of account it is. */
export const BROADCAST_MIN_TOP1 = 0.6;

/** Institutional broadcast: an exchange or alert feed IS the spike. Not a
 * botnet (nobody is hiding), not a crowd (nobody is talking). Giveaways and
 * transfer alerts inflate interaction counts without anyone forming an
 * opinion, so the score stays as measured and this label explains it. */
export function isInstitutionalBroadcast(e: Evidence): boolean {
  return (e.top1CreatorShare ?? 0) >= BROADCAST_MIN_TOP1 && isInstitutionalAccount(e.topCreatorName);
}

/** Unclipped spam/posts ratio for a single row. Can exceed 1: the spam count
 * covers a broader post universe than posts_created, and its scale has shifted
 * across eras, which is why the score leans on the LIFT vs the coin's own
 * baseline rather than the absolute level alone. */
export function rowSpamRatio(row: SeriesRow | undefined): number {
  if (!row || !row.posts_created) return 0;
  return (row.spam ?? 0) / Math.max(1, row.posts_created);
}

/** Unclipped spam ratio for the most recent COMPLETE day. */
export function spamRatioRaw(series: SeriesRow[]): number {
  return rowSpamRatio(lastCompleteRow(series));
}

/** Median unclipped spam ratio over the trailing complete days. The slice
 * already stops before the final row, so the day in progress never enters the
 * baseline either. */
export function spamBaseline(series: SeriesRow[], trailing = 30): number {
  const window = series.slice(-1 - trailing, -1).map(rowSpamRatio).sort((a, b) => a - b);
  if (window.length === 0) return 0;
  return window[Math.floor(window.length / 2)];
}

/** How elevated today's spam ratio is vs the coin's own norm, mapped to 0-1
 * (2x baseline -> 0.5, 3x or more -> 1). Chronically botted coins aren't
 * penalized twice for their baseline; fresh spam waves are. */
export function spamLift(rawToday: number, baseline: number): number {
  const lift = rawToday / Math.max(baseline, 0.05);
  return Math.min(1, Math.max(0, (lift - 1) / 2));
}

/** 0-100 manufactured score, calibrated on the burn-in week + 6.5y of
 * historical distributions:
 * - spam lift vs own baseline (0.40): the era-robust spam signal
 * - absolute spam share (0.20): chronic botting still counts
 * - creator concentration (0.30)
 * - sentiment uniformity (0.10): re-centered at 90 because crypto spike
 *   sentiment is >=85 on a majority of spike days; only near-unanimity
 *   discriminates */
export function manufacturedScore(e: Evidence): number {
  const uniformity = Math.max(0, (e.sentiment - 90) / 10);
  return Math.round(
    100 *
      (0.4 * spamLift(e.spamRatioRaw, e.spamBaseline) +
        0.2 * e.spamRatio +
        0.3 * e.top3CreatorShare +
        0.1 * uniformity)
  );
}

export function verdictFor(score: number): Verdict {
  if (score >= 60) return "manufactured";
  if (score >= 30) return "mixed";
  return "organic";
}

/** Burst share over the last 24 complete hours: the top-3 hours' share of
 * interactions. The half-life study found organic spikes are BURSTIER (real
 * crowds pile in together; scheduled campaigns spread through the day).
 * Display-only evidence until prospectively validated: NOT in the score. */
export function burstShare24h(hourly: SeriesRow[]): number | null {
  const complete = hourly.slice(0, -1); // trailing hour is partial
  const window = complete.slice(-24).map((r) => r.interactions ?? 0);
  if (window.length < 24) return null;
  const total = window.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;
  const top3 = [...window].sort((a, b) => b - a).slice(0, 3).reduce((a, b) => a + b, 0);
  return top3 / total;
}

/** Burn-in showed a recurring pattern the score alone muddles: near-total
 * concentration with LOW spam, i.e. one account is the entire conversation
 * (a project announcement, an exchange, a big KOL). That's a megaphone, not
 * a botnet, and it gets labeled instead of misread as manufacturing. */
export function isMegaphone(e: Evidence): boolean {
  return e.top3CreatorShare >= 0.9 && e.spamRatio < 0.4;
}

/** Only coins genuinely spiking get a verdict at all. */
export const SPIKE_Z_MIN = 2.0;
