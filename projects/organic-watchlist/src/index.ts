import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderChartSvg, renderCollisionChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries, fetchTopic } from "./lunarcrush.js";
import { renderPost } from "./render.js";
import {
  eligibleCandidates,
  failureReason,
  interactionZScore,
  medianInteractions,
  bareTopic,
  isNameCollision,
  priorWeekReturn,
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

/** Traffic on the bare ticker as a topic, or undefined if it will not resolve.
 *
 * A topic that does not exist is not evidence either way, so it returns
 * undefined rather than zero: zero would read as "no collision" and quietly
 * pass a coin the check never actually examined. */
async function bareTopicInteractions(topic: string): Promise<number | undefined> {
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  const bare = bareTopic(topic);
  if (!apiKey || !bare) return undefined;
  try {
    const t = await fetchTopic(apiKey, bare);
    const n = Number(t.interactions_24h);
    return Number.isFinite(n) && n > 0 ? n : undefined;
  } catch {
    return undefined;
  }
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
      // A qualifying spike still has to be about the coin. Only run this for
      // coins that already passed everything else: it costs a request each,
      // and only a handful get this far on any given day.
      const lastComplete = series[series.length - 2];
      const bare = await bareTopicInteractions(row.topic);
      const collision = isNameCollision({
        interactions24h: row.interactions_24h,
        contributors: lastComplete?.contributors_active,
        bareInteractions: bare,
      });
      if (collision.collision) {
        console.log(`  ${row.symbol}: rejected, ${collision.reason}`);
        const contributors = lastComplete?.contributors_active;
        nearMisses.push({
          symbol: row.symbol, z, spam, percentChange24h: row.percent_change_24h,
          failed: `the conversation is not about the coin: ${collision.reason}`,
          collision: {
            multiple: med > 0 ? row.interactions_24h / med : 0,
            interactions24h: row.interactions_24h,
            medianInteractions: med,
            contributors,
            perContributor: contributors ? row.interactions_24h / contributors : undefined,
            bareTopic: bareTopic(row.topic),
            bareInteractions: bare,
          },
        });
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
        priorWeekReturn: priorWeekReturn(series),
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

  // A rejected collision gets its own chart: it is the more interesting result
  // on a day the scanner finds nothing.
  const collided = report.nearMisses.find((m) => m.collision);
  if (collided) {
    const cSvg = renderCollisionChartSvg(collided, report.generatedAt);
    writeFileSync(join(OUT_DIR, "collision.svg"), cSvg);
    writeFileSync(join(OUT_DIR, "collision.png"), await svgToPng(cSvg));
    console.log(`Wrote out/collision.png ($${collided.symbol})`);
  }

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
