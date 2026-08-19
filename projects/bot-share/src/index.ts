import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { WINDOW_DAYS, rankScores, scoreCoin } from "./botshare.js";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries } from "./lunarcrush.js";
import { renderPost } from "./render.js";
import type { BotShareReport, CoinScore } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const MIN_MARKET_CAP = 1e9;

async function main(): Promise<void> {
  loadEnv();
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  if (!apiKey) {
    console.error("LUNARCRUSH_API_KEY is not set. Copy .env.example to .env and add your key.");
    process.exit(1);
  }

  const coins = await fetchCoinsList(apiKey);
  const universe = coins
    .filter((c) => c.market_cap >= MIN_MARKET_CAP && c.market_cap_rank > 0)
    .sort((a, b) => a.market_cap_rank - b.market_cap_rank);
  console.log(`${universe.length} coins over $${(MIN_MARKET_CAP / 1e9).toFixed(0)}B`);

  const scored: CoinScore[] = [];
  for (const c of universe) {
    try {
      const score = scoreCoin(c, await fetchDailySeries(apiKey, c.id));
      if (score) {
        scored.push(score);
        const flag = score.quotable ? "" : `  (not quotable: ${score.daysOverOne}/30 days over 100%)`;
        console.log(`  ${c.symbol.padEnd(7)} ${(score.spamShare * 100).toFixed(0)}%${flag}`);
      }
    } catch (e) {
      console.error(`  skipping ${c.symbol}: ${e}`);
    }
  }

  const report: BotShareReport = {
    generatedAt: new Date().toISOString(),
    windowDays: WINDOW_DAYS,
    scanned: universe.length,
    scored: rankScores(scored),
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
