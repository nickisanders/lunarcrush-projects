import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  SPIKE_Z_MIN,
  burstShare24h,
  interactionZScore,
  isInstitutionalBroadcast,
  isMegaphone,
  manufacturedScore,
  pickCandidates,
  spamBaseline,
  spamRatio,
  spamRatioRaw,
  top1CreatorShare,
  top3CreatorShare,
  topCreatorName,
  verdictFor,
} from "./classify.js";
import { measureDecay, pickDecayWatch, readHistoryLines } from "./decaywatch.js";
import { renderDecayChartSvg } from "./chart.js";
import { renderChartSvg, renderStorySvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import {
  fetchCoinsList,
  fetchDailySeries,
  fetchDailySeriesBySymbol,
  fetchHourlySeries,
  fetchTopicCreators,
} from "./lunarcrush.js";
import { renderPost } from "./render.js";
import type { CoinRow, CoinVerdict, Creator, DetectorReport, SeriesRow } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const FIXTURES = join(HERE, "..", "fixtures", "sample.json");

interface CliArgs {
  mock: boolean;
  maxCandidates: number;
  fromReport: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { mock: false, maxCandidates: 40, fromReport: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--mock") args.mock = true;
    else if (a === "--max-candidates") args.maxCandidates = Number(argv[++i]);
    else if (a === "--from-report") args.fromReport = true;
  }
  return args;
}

interface MockData {
  coins: CoinRow[];
  series: Record<string, SeriesRow[]>;
  creators: Record<string, Creator[]>;
}

function writeOutputs(report: DetectorReport): Promise<void> {
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify(report, null, 1));
  const post = renderPost(report, process.env.POST_PROMO_CODE);
  writeFileSync(join(OUT_DIR, "post.txt"), post);
  const svg = renderChartSvg(report);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  const storySvg = renderStorySvg(report);
  writeFileSync(join(OUT_DIR, "story.svg"), storySvg);
  return Promise.all([
    svgToPng(svg).then((png) => writeFileSync(join(OUT_DIR, "chart.png"), png)),
    svgToPng(storySvg).then((png) => writeFileSync(join(OUT_DIR, "story.png"), png)),
  ]).then(() => {
    console.log("\n" + post + "\n");
    console.log("Wrote out/report.json, post.txt, chart.svg, chart.png, story.svg, story.png");
  });
}

async function main(): Promise<void> {
  loadEnv();
  const args = parseArgs(process.argv.slice(2));

  if (args.fromReport) {
    const report = JSON.parse(readFileSync(join(OUT_DIR, "report.json"), "utf8")) as DetectorReport;
    await writeOutputs(report);
    return;
  }

  let coins: CoinRow[];
  let getSeries: (c: CoinRow) => Promise<SeriesRow[]>;
  let getCreators: (c: CoinRow) => Promise<Creator[]>;
  let getHourly: ((c: CoinRow) => Promise<SeriesRow[]>) | null = null;

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
    getHourly = (c) => fetchHourlySeries(apiKey, c.id);
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
      let burst: number | null = null;
      if (getHourly) {
        try {
          burst = burstShare24h(await getHourly(c));
        } catch {
          burst = null;
        }
      }
      const evidence = {
        burstShare24h: burst,
        zScore: z,
        spamRatio: spamRatio(series),
        spamRatioRaw: spamRatioRaw(series),
        spamBaseline: spamBaseline(series),
        top3CreatorShare: top3CreatorShare(creators),
        top1CreatorShare: top1CreatorShare(creators),
        topCreatorName: topCreatorName(creators),
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
        megaphone: isMegaphone(evidence),
        institutionalBroadcast: isInstitutionalBroadcast(evidence),
        topCreators: [...creators]
          .sort((a, b) => (b.interactions_24h ?? 0) - (a.interactions_24h ?? 0))
          .slice(0, 10)
          .map((cr) => ({
            id: cr.creator_id,
            name: cr.creator_name,
            followers: cr.creator_followers,
            interactions: cr.interactions_24h,
          })),
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

  await writeOutputs(report);

  // Append to the local verdict history for future calibration passes.
  // (In CI the data/ dir persists via actions/cache.)
  const histDir = join(HERE, "..", "data");
  mkdirSync(histDir, { recursive: true });
  const histPath = join(histDir, "history.jsonl");
  appendFileSync(histPath, JSON.stringify(report) + "\n");

  // Decay-watch: high-scoring specimens from 3-5 days ago get an automatic
  // "what happened next" chart. Live runs only.
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  if (args.mock || !apiKey) return;
  const targets = pickDecayWatch(readHistoryLines(histPath), new Date(), (t) =>
    existsSync(join(OUT_DIR, `decay-${t.symbol}-${t.spikeDate}.png`))
  );
  for (const t of targets) {
    try {
      const series = await fetchDailySeriesBySymbol(apiKey, t.symbol);
      const result = measureDecay(t, series);
      if (!result) continue;
      const svg = renderDecayChartSvg(result);
      writeFileSync(join(OUT_DIR, `decay-${t.symbol}-${t.spikeDate}.png`), await svgToPng(svg));
      console.log(
        `decay-watch: $${t.symbol} (flagged ${t.score}/100 on ${t.spikeDate}) now retains ` +
          `${result.retainedPct.toFixed(0)}% of spike volume · wrote out/decay-${t.symbol}-${t.spikeDate}.png`
      );
    } catch (e) {
      console.warn(`decay-watch: skipping ${t.symbol}: ${e}`);
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
