import type { NarrativeWeek, SeriesRow } from "./types.js";

/** Crypto narratives tracked week over week. Keys are LunarCrush social
 * topics (NOT categories: categories like "gaming" span all of social media,
 * while topics like "defi" are the crypto-native conversations). A topic
 * with no data is skipped with a warning, so this list can be tuned freely. */
export const NARRATIVES: Array<{ key: string; title: string }> = [
  { key: "bitcoin", title: "Bitcoin" },
  { key: "ethereum", title: "Ethereum" },
  { key: "solana", title: "Solana" },
  { key: "memecoins", title: "Memecoins" },
  { key: "defi", title: "DeFi" },
  { key: "nfts", title: "NFTs" },
  { key: "stablecoins", title: "Stablecoins" },
  { key: "rwa", title: "RWA" },
  { key: "depin", title: "DePIN" },
  { key: "ai agents", title: "AI Agents" },
];

/** Drop the trailing partial day, keep the last 14 complete days. */
export function lastCompleteDays(series: SeriesRow[], days = 14): SeriesRow[] {
  if (series.length < days + 1) return [];
  return series.slice(-1 - days, -1);
}

function weightedSentiment(rows: SeriesRow[]): number {
  let weighted = 0;
  let total = 0;
  for (const r of rows) {
    if (typeof r.sentiment !== "number") continue;
    weighted += r.sentiment * r.interactions;
    total += r.interactions;
  }
  return total > 0 ? weighted / total : 0;
}

export function computeRotation(
  seriesByKey: Record<string, SeriesRow[]>,
  titles: Record<string, string>
): NarrativeWeek[] {
  const partial: Array<Omit<NarrativeWeek, "shareNow" | "sharePrev" | "shareDeltaPp">> = [];
  for (const [key, series] of Object.entries(seriesByKey)) {
    const window = lastCompleteDays(series);
    if (window.length < 14) continue;
    const prev = window.slice(0, 7);
    const cur = window.slice(7);
    const thisWeek = cur.reduce((a, r) => a + r.interactions, 0);
    const prevWeek = prev.reduce((a, r) => a + r.interactions, 0);
    partial.push({
      key,
      title: titles[key] ?? key,
      thisWeek,
      prevWeek,
      wowPct: prevWeek > 0 ? ((thisWeek - prevWeek) / prevWeek) * 100 : 0,
      sentimentNow: weightedSentiment(cur),
      sentimentPrev: weightedSentiment(prev),
    });
  }

  const totalNow = partial.reduce((a, n) => a + n.thisWeek, 0);
  const totalPrev = partial.reduce((a, n) => a + n.prevWeek, 0);
  return partial
    .map((n) => {
      const shareNow = totalNow > 0 ? (n.thisWeek / totalNow) * 100 : 0;
      const sharePrev = totalPrev > 0 ? (n.prevWeek / totalPrev) * 100 : 0;
      return { ...n, shareNow, sharePrev, shareDeltaPp: shareNow - sharePrev };
    })
    .sort((a, b) => b.shareDeltaPp - a.shareDeltaPp);
}
