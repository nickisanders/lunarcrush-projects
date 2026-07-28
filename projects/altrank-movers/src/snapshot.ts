import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import type { CoinRow } from "./types.js";

/**
 * Daily snapshots of alt_rank per symbol. Used as a fallback source of
 * "yesterday's rank" if the API ever omits alt_rank_previous, and as raw
 * material for longer-horizon charts later.
 */
export async function saveSnapshot(dir: string, rows: CoinRow[]): Promise<string> {
  await mkdir(dir, { recursive: true });
  const date = new Date().toISOString().slice(0, 10);
  const path = join(dir, `${date}.json`);
  const slim = rows.map((r) => ({
    symbol: r.symbol,
    alt_rank: r.alt_rank,
    market_cap_rank: r.market_cap_rank,
    interactions_24h: r.interactions_24h,
  }));
  await writeFile(path, JSON.stringify(slim));
  return path;
}

export async function loadPreviousRanks(dir: string): Promise<Map<string, number> | undefined> {
  let files: string[];
  try {
    files = (await readdir(dir)).filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort();
  } catch {
    return undefined;
  }
  const today = new Date().toISOString().slice(0, 10);
  const prior = files.filter((f) => f.slice(0, 10) < today);
  if (prior.length === 0) return undefined;

  const latest = prior[prior.length - 1];
  const rows = JSON.parse(await readFile(join(dir, latest), "utf8")) as {
    symbol: string;
    alt_rank: number;
  }[];
  return new Map(rows.map((r) => [r.symbol, r.alt_rank]));
}
