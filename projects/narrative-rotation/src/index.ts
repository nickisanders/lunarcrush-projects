import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderChartSvg, renderStorySvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchTopCoins, fetchTopicSeries } from "./lunarcrush.js";
import { renderPost } from "./render.js";
import { NARRATIVES, computeRotation } from "./rotation.js";
import type { HotCoin, RotationReport, SeriesRow } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const FIXTURES = join(HERE, "..", "fixtures", "sample.json");

interface MockData {
  series: Record<string, SeriesRow[]>;
  coins: HotCoin[];
}

async function main(): Promise<void> {
  loadEnv();
  const mock = process.argv.includes("--mock");

  const seriesByKey: Record<string, SeriesRow[]> = {};
  let hotCoins: HotCoin[] = [];

  if (mock) {
    const data = JSON.parse(readFileSync(FIXTURES, "utf8")) as MockData;
    Object.assign(seriesByKey, data.series);
    hotCoins = data.coins;
    console.log(`Loaded ${Object.keys(seriesByKey).length} narratives (mock data)`);
  } else {
    const apiKey = process.env.LUNARCRUSH_API_KEY;
    if (!apiKey) {
      console.error(
        "LUNARCRUSH_API_KEY is not set. Copy .env.example to .env and add your key, or run with --mock."
      );
      process.exit(1);
    }
    for (const n of NARRATIVES) {
      try {
        const series = await fetchTopicSeries(apiKey, n.key);
        if (series.length < 15) {
          console.warn(`  skipping topic "${n.key}": only ${series.length} days of data`);
          continue;
        }
        seriesByKey[n.key] = series;
        console.log(`  ${n.key}: ${series.length} days`);
      } catch (e) {
        console.warn(`  skipping topic "${n.key}": ${e}`);
      }
    }
    hotCoins = await fetchTopCoins(apiKey);
  }

  const titles = Object.fromEntries(NARRATIVES.map((n) => [n.key, n.title]));
  const narratives = computeRotation(seriesByKey, titles);
  if (narratives.length === 0) {
    throw new Error("No narratives had 14 complete days of data; nothing to report.");
  }

  const report: RotationReport = {
    generatedAt: new Date().toISOString(),
    weekEnding: new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    }),
    narratives,
    hotCoins: hotCoins.slice(0, 5),
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify(report, null, 1));
  const post = renderPost(report, process.env.POST_PROMO_CODE);
  writeFileSync(join(OUT_DIR, "post.txt"), post);
  const svg = renderChartSvg(report);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  const storySvg = renderStorySvg(report);
  writeFileSync(join(OUT_DIR, "story.svg"), storySvg);
  writeFileSync(join(OUT_DIR, "chart.png"), await svgToPng(svg));
  writeFileSync(join(OUT_DIR, "story.png"), await svgToPng(storySvg));

  console.log("\n" + post + "\n");
  console.log("Wrote out/report.json, post.txt, chart.svg, chart.png, story.svg, story.png");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
