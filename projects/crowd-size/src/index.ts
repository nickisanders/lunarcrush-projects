import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { measure, median, rankByCrowd, repeatVoices } from "./crowd.js";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchTopicCreators } from "./lunarcrush.js";
import type { CoinCrowd, Creator, CrowdReport } from "./types.js";

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

  const all = await fetchCoinsList(apiKey);
  const universe = all
    .filter((c) => c.market_cap >= MIN_MARKET_CAP && c.market_cap_rank > 0)
    .sort((a, b) => a.market_cap_rank - b.market_cap_rank);
  console.log(`${universe.length} coins over $${(MIN_MARKET_CAP / 1e9).toFixed(0)}B`);

  const coins: CoinCrowd[] = [];
  const raw: { symbol: string; creators: Creator[] }[] = [];
  for (const c of universe) {
    try {
      const creators = await fetchTopicCreators(apiKey, c.topic);
      const m = measure(c, creators);
      if (!m) continue;
      coins.push(m);
      raw.push({ symbol: c.symbol, creators });
      console.log(`  ${c.symbol.padEnd(7)} ${String(m.accountsToHalf ?? ">list").padStart(5)} accounts to half · top 10 hold ${(m.top10Share * 100).toFixed(0)}%`);
    } catch (e) {
      console.error(`  skipping ${c.symbol}: ${e}`);
    }
  }

  const report: CrowdReport = {
    generatedAt: new Date().toISOString(),
    scanned: universe.length,
    coins: rankByCrowd(coins),
  };

  const known = coins.map((c) => c.accountsToHalf).filter((n): n is number => n !== null);
  console.log(`\nMedian accounts to reach half: ${median(known)}`);
  console.log(`Median share held by the top 10: ${(median(coins.map((c) => c.top10Share)) * 100).toFixed(0)}%`);

  const repeats = repeatVoices(raw);
  console.log(`\n${repeats.length} accounts sit in the top 10 of more than one coin. Busiest:`);
  for (const v of repeats.slice(0, 8)) {
    console.log(`  ${String(v.coins.length).padStart(2)}  ${v.name}  (${v.coins.join(", ")})`);
  }

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify({ ...report, repeats }, null, 1));
  const svg = renderChartSvg(report);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  writeFileSync(join(OUT_DIR, "chart.png"), await svgToPng(svg));
  console.log("\nWrote out/report.json, chart.svg, chart.png");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
