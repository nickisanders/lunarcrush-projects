import type { HotCoin, SeriesRow } from "./types.js";

const BASE = "https://lunarcrush.com/api4";
const USER_AGENT = "lunarcrush-projects-narrative-rotation/0.1";

async function get<T>(path: string, apiKey: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${apiKey}`, "User-Agent": USER_AGENT },
  });
  if (res.status === 429) {
    await new Promise((r) => setTimeout(r, 65_000));
    return get(path, apiKey);
  }
  if (!res.ok) {
    throw new Error(`LunarCrush ${path}: HTTP ${res.status} ${await res.text()}`);
  }
  const body = (await res.json()) as { data: T };
  await new Promise((r) => setTimeout(r, 700));
  return body.data;
}

export function fetchTopicSeries(apiKey: string, topic: string): Promise<SeriesRow[]> {
  return get(
    `/public/topic/${encodeURIComponent(topic)}/time-series/v1?bucket=day&interval=1m`,
    apiKey
  );
}

export async function fetchTopCoins(apiKey: string): Promise<HotCoin[]> {
  // sort=interactions_24h already returns descending; the desc param REVERSES it
  const rows = await get<Array<HotCoin & { market_cap_rank?: number }>>(
    `/public/coins/list/v2?sort=interactions_24h&limit=50&page=0`,
    apiKey
  );
  // Keep recognizable assets: spam-inflated microcaps can fake interactions
  return rows.filter((r) => r.market_cap_rank && r.market_cap_rank <= 500);
}
