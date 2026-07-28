import type { CoinRow } from "./types.js";

const BASE_URL = "https://lunarcrush.com/api4";

export async function fetchCoinsList(apiKey: string, limit = 1000): Promise<CoinRow[]> {
  const url = `${BASE_URL}/public/coins/list/v2?sort=market_cap_rank&limit=${limit}&page=0`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });

  if (res.status === 401 || res.status === 403) {
    throw new Error(
      `LunarCrush rejected the API key (HTTP ${res.status}). Check LUNARCRUSH_API_KEY in your .env.`
    );
  }
  if (res.status === 429) {
    throw new Error(
      "Rate limited by LunarCrush (HTTP 429). The bot only needs one request per run, so wait a minute and retry."
    );
  }
  if (!res.ok) {
    throw new Error(`LunarCrush request failed: HTTP ${res.status} ${await res.text()}`);
  }

  const body = (await res.json()) as { data?: CoinRow[] };
  if (!Array.isArray(body.data)) {
    throw new Error("Unexpected LunarCrush response shape: missing data array");
  }
  return body.data;
}
