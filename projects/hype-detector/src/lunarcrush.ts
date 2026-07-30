import type { CoinRow, Creator, SeriesRow } from "./types.js";

const BASE = "https://lunarcrush.com/api4";
const USER_AGENT = "lunarcrush-projects-hype-detector/0.1";

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
  // Stay under the per-minute limit without tracking headers precisely.
  await new Promise((r) => setTimeout(r, 700));
  return body.data;
}

export function fetchCoinsList(apiKey: string, limit = 1000): Promise<CoinRow[]> {
  return get(`/public/coins/list/v2?sort=market_cap_rank&limit=${limit}&page=0`, apiKey);
}

export function fetchDailySeries(apiKey: string, coinId: number): Promise<SeriesRow[]> {
  return get(`/public/coins/${coinId}/time-series/v2?bucket=day&interval=1m`, apiKey);
}

export function fetchTopicCreators(apiKey: string, topic: string): Promise<Creator[]> {
  return get(`/public/topic/${encodeURIComponent(topic)}/creators/v1`, apiKey);
}
