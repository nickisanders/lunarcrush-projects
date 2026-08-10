import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries } from "./lunarcrush.js";
import { renderPost } from "./render.js";
import {
  eligibleCandidates,
  failureReason,
  interactionZScore,
  medianInteractions,
  qualifies,
  rankEntries,
  spamRatio,
} from "./watchlist.js";
import type { CoinRow, NearMiss, SeriesRow, WatchEntry, WatchlistReport } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const FIXTURES = join(HERE, "..", "fixtures", "sample.json");

interface MockData {
  coins: CoinRow[];
  series: Record<string, SeriesRow[]>;
}

async function main(): Promise<void> {
  loadEnv();
  const mock = process.argv.includes("--mock");
  const maxArg = process.argv.indexOf("--max-candidates");
  const maxCandidates = maxArg > -1 ? Number(process.argv[maxArg + 1]) : 80;

  let coins: CoinRow[];
  let getSeries: (c: CoinRow) => Promise<SeriesRow[]>;

  if (mock) {
    const data = JSON.parse(readFileSync(FIXTURES, "utf8")) as MockData;
    coins = data.coins;
    getSeries = async (c) => data.series[String(c.id)] ?? [];
    console.log(`Loaded ${coins.length} coins (mock data)`);
  } else {
    const apiKey = process.env.LUNARCRUSH_API_KEY;
    if (!apiKey) {
      console.error("LUNARCRUSH_API_KEY is not set. Copy .env.example to .env, or use --mock.");
      process.exit(1);
    }
    coins = await fetchCoinsList(apiKey);
    console.log(`Loaded ${coins.length} coins`);
    getSeries = (c) => fetchDailySeries(apiKey, c.id);
  }

  const candidates = eligibleCandidates(coins, maxCandidates);
  console.log(`${candidates.length} candidates (eligible size, flat price)`);

  const entries: WatchEntry[] = [];
  const nearMisses: NearMiss[] = [];
  for (const { row } of candidates) {
    try {
      const series = await getSeries(row);
      if (series.length === 0) continue;
      // The final series row is today, still accumulating. Substitute the
      // coins-list rolling 24h count so a full day is compared to full days.
      const live = [...series];
      live[live.length - 1] = { ...live[live.length - 1], interactions: row.interactions_24h };

      const z = interactionZScore(live);
      const med = medianInteractions(live);
      const spam = spamRatio(live);
      const legs = { z, spam, medianInteractions: med, percentChange24h: row.percent_change_24h };
      if (!qualifies(legs)) {
        const failed = failureReason(legs);
        // Only worth showing if the conversation actually moved at all.
        if (failed && z >= 2.0) {
          nearMisses.push({ symbol: row.symbol, z, spam, percentChange24h: row.percent_change_24h, failed });
        }
        continue;
      }
      entries.push({
        symbol: row.symbol,
        name: row.name,
        marketCapRank: row.market_cap_rank,
        z,
        spam,
        percentChange24h: row.percent_change_24h,
        interactions24h: row.interactions_24h,
        medianInteractions: med,
        multiple: med > 0 ? row.interactions_24h / med : 0,
      });
      console.log(`  ${row.symbol}: z=${z.toFixed(1)} spam=${(spam * 100).toFixed(0)}%`);
    } catch (e) {
      console.error(`  skipping ${row.symbol}: ${e}`);
    }
  }

  const report: WatchlistReport = {
    generatedAt: new Date().toISOString(),
    scanned: coins.length,
    checked: candidates.length,
    entries: rankEntries(entries),
    nearMisses: nearMisses.sort((a, b) => b.z - a.z).slice(0, 3),
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify(report, null, 1));
  const post = renderPost(report, process.env.POST_PROMO_CODE);
  writeFileSync(join(OUT_DIR, "post.txt"), post);
  const svg = renderChartSvg(report);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  writeFileSync(join(OUT_DIR, "chart.png"), await svgToPng(svg));

  if (!mock) {
    const dataDir = join(HERE, "..", "data");
    mkdirSync(dataDir, { recursive: true });
    // Persist every call so the live hit rate can be measured against the
    // backtest's claim rather than assumed.
    appendFileSync(join(dataDir, "history.jsonl"), JSON.stringify(report) + "\n");
  }

  console.log("\n" + post + "\n");
  console.log("Wrote out/report.json, post.txt, chart.svg, chart.png");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
