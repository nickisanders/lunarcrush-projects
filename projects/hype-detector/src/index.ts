import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  SPIKE_Z_MIN,
  interactionZScore,
  manufacturedScore,
  pickCandidates,
  spamRatio,
  top3CreatorShare,
  verdictFor,
} from "./classify.js";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries, fetchTopicCreators } from "./lunarcrush.js";
import { renderPost } from "./render.js";
import type { CoinRow, CoinVerdict, Creator, DetectorReport, SeriesRow } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const FIXTURES = join(HERE, "..", "fixtures", "sample.json");

interface CliArgs {
  mock: boolean;
  maxCandidates: number;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { mock: false, maxCandidates: 40 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--mock") args.mock = true;
    else if (a === "--max-candidates") args.maxCandidates = Number(argv[++i]);
  }
  return args;
}

interface MockData {
  coins: CoinRow[];
  series: Record<string, SeriesRow[]>;
  creators: Record<string, Creator[]>;
}

async function main(): Promise<void> {
  loadEnv();
  const args = parseArgs(process.argv.slice(2));

  let coins: CoinRow[];
  let getSeries: (c: CoinRow) => Promise<SeriesRow[]>;
  let getCreators: (c: CoinRow) => Promise<Creator[]>;

  if (args.mock) {
    const mock = JSON.parse(readFileSync(FIXTURES, "utf8")) as MockData;
    coins = mock.coins;
    getSeries = async (c) => mock.series[String(c.id)] ?? [];
    getCreators = async (c) => mock.creators[String(c.id)] ?? [];
    console.log(`Loaded ${coins.length} coins (mock data)`);
  } else {
    const apiKey = process.env.LUNARCRUSH_API_KEY;
    if (!apiKey) {
      console.error(
        "LUNARCRUSH_API_KEY is not set. Copy .env.example to .env and add your key, or run with --mock."
      );
      process.exit(1);
    }
    coins = await fetchCoinsList(apiKey);
    console.log(`Loaded ${coins.length} coins`);
    getSeries = (c) => fetchDailySeries(apiKey, c.id);
    getCreators = (c) => fetchTopicCreators(apiKey, c.topic);
  }

  const candidates = pickCandidates(coins, args.maxCandidates);
  console.log(`Stage 1: ${candidates.length} spike candidates`);

  const verdicts: CoinVerdict[] = [];
  for (const c of candidates) {
    try {
      const series = await getSeries(c);
      if (series.length === 0) continue;
      // The last series row is today and usually partial. Substitute the
      // coins-list rolling 24h interactions (a complete window) so the
      // z-score compares a full day against full days.
      const live = [...series];
      live[live.length - 1] = { ...live[live.length - 1], interactions: c.interactions_24h };
      const z = interactionZScore(live);
      if (z < SPIKE_Z_MIN) continue;
      console.log(`  ${c.symbol}: z=${z.toFixed(1)}`);
      const creators = await getCreators(c);
      const evidence = {
        zScore: z,
        spamRatio: spamRatio(series),
        top3CreatorShare: top3CreatorShare(creators),
        sentiment: c.sentiment ?? 50,
      };
      const score = manufacturedScore(evidence);
      verdicts.push({
        symbol: c.symbol,
        name: c.name,
        topic: c.topic,
        marketCapRank: c.market_cap_rank,
        interactions24h: c.interactions_24h,
        evidence,
        score,
        verdict: verdictFor(score),
      });
    } catch (e) {
      console.error(`  skipping ${c.symbol}: ${e}`);
    }
  }
  verdicts.sort((a, b) => b.score - a.score);

  const report: DetectorReport = {
    generatedAt: new Date().toISOString(),
    scanned: coins.length,
    spiking: verdicts.length,
    verdicts,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify(report, null, 1));
  const post = renderPost(report, process.env.POST_PROMO_CODE);
  writeFileSync(join(OUT_DIR, "post.txt"), post);
  const svg = renderChartSvg(report);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  writeFileSync(join(OUT_DIR, "chart.png"), await svgToPng(svg));

  console.log("\n" + post + "\n");
  console.log("Wrote out/report.json, post.txt, chart.svg, chart.png");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
