import type { CoinRow } from "./types.js";

const BASE = "https://lunarcrush.com/api4";
const UA = "lunarcrush-projects-name-collision/0.1";

async function get<T>(path: string, apiKey: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Authorization: `Bearer ${apiKey}`, "User-Agent": UA },
  });
  if (res.status === 429) {
    await new Promise((r) => setTimeout(r, 65_000));
    return get(path, apiKey);
  }
  if (!res.ok) throw new Error(`LunarCrush ${path}: HTTP ${res.status}`);
  const body = (await res.json()) as { data: T };
  await new Promise((r) => setTimeout(r, 650));
  return body.data;
}

/** The coins list is paged at 1,000. The collisions live in the tail, so all
 * three pages are needed; scanning only the top 1,000 would miss every one. */
export async function fetchAllCoins(apiKey: string, pages = 3): Promise<CoinRow[]> {
  const out: CoinRow[] = [];
  for (let page = 0; page < pages; page++) {
    const rows = await get<CoinRow[]>(
      `/public/coins/list/v2?sort=market_cap_rank&limit=1000&page=${page}`, apiKey
    );
    if (!rows.length) break;
    out.push(...rows);
  }
  return out;
}

export function fetchTopic(
  apiKey: string, topic: string
): Promise<{ interactions_24h?: number; num_contributors?: number }> {
  return get(`/public/topic/${encodeURIComponent(topic)}/v1`, apiKey);
}
