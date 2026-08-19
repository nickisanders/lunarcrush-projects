import type { CoinRow, SeriesRow } from "./types.js";

const BASE = "https://lunarcrush.com/api4";
const UA = "lunarcrush-projects-bot-share/0.1";

async function get<T>(path: string, apiKey: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${apiKey}`, "User-Agent": UA },
  });
  if (res.status === 429) {
    await new Promise((r) => setTimeout(r, 65_000));
    return get(path, apiKey);
  }
  if (!res.ok) throw new Error(`LunarCrush ${path}: HTTP ${res.status} ${await res.text()}`);
  const body = (await res.json()) as { data: T };
  await new Promise((r) => setTimeout(r, 650)); // stay under 100/min
  return body.data;
}

export function fetchCoinsList(apiKey: string, limit = 1000): Promise<CoinRow[]> {
  return get(`/public/coins/list/v2?sort=market_cap_rank&limit=${limit}&page=0`, apiKey);
}

export function fetchDailySeries(apiKey: string, coinId: number): Promise<SeriesRow[]> {
  return get(`/public/coins/${coinId}/time-series/v2?bucket=day&interval=3m`, apiKey);
}
