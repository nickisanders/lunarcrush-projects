import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { SUSPECT_MULTIPLE, bareTopic, classify, findSuspects, perDollar } from "./collision.js";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchAllCoins, fetchTopic } from "./lunarcrush.js";
import type { CollisionReport } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const CHECK_TOP = 14;

async function main(): Promise<void> {
  loadEnv();
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  if (!apiKey) {
    console.error("LUNARCRUSH_API_KEY is not set. Copy .env.example to .env and add your key.");
    process.exit(1);
  }

  const coins = await fetchAllCoins(apiKey);
  console.log(`${coins.length.toLocaleString()} coins scanned`);
  const { suspects, medianPerDollar } = findSuspects(coins);
  const btc = coins.find((c) => c.symbol === "BTC");
  console.log(`median coin: ${medianPerDollar.toFixed(6)} interactions per $1 of market cap`);
  if (btc) console.log(`Bitcoin:     ${perDollar(btc).toFixed(6)}`);
  console.log(`\n${suspects.length} coins sit at ${SUSPECT_MULTIPLE}x the median or above\n`);

  // Check the worst offenders against the bare word they collide with.
  for (const s of suspects.slice(0, CHECK_TOP)) {
    const bare = bareTopic(s.topic);
    if (!bare) continue;
    try {
      const t = await fetchTopic(apiKey, bare);
      s.bareTopic = bare;
      s.bareInteractions = Number(t.interactions_24h) || 0;
      s.bareContributors = Number(t.num_contributors) || 0;
      s.shareOfBare = s.bareInteractions ? s.interactions24h / s.bareInteractions : undefined;
      s.verdict = classify(s.interactions24h, s.bareInteractions);
    } catch {
      /* a topic that will not resolve is not evidence either way */
    }
  }

  const checked = suspects.slice(0, CHECK_TOP);
  const line = (s: (typeof checked)[number]) =>
    `$${s.symbol.padEnd(10)}${("$" + Math.round(s.marketCap).toLocaleString()).padStart(12)}` +
    `${s.interactions24h.toLocaleString().padStart(12)}${(Math.round(s.vsMedian).toLocaleString() + "x").padStart(11)}   ` +
    (s.bareInteractions
      ? `"${s.bareTopic}" = ${s.bareInteractions.toLocaleString()} interactions / ${(s.bareContributors ?? 0).toLocaleString()} people`
      : "topic did not resolve");

  const header = `${"coin".padEnd(11)}${"mcap".padStart(12)}${"inter24h".padStart(12)}${"vs median".padStart(11)}   the bare ticker as a topic`;
  console.log("NAME COLLISIONS: the ticker is a word with its own conversation\n");
  console.log(header);
  for (const s of checked.filter((s) => s.verdict === "collision")) console.log(line(s));

  console.log("\nLOUD, NOT COLLIDING: the topic's traffic is the coin's own\n");
  console.log(header);
  for (const s of checked.filter((s) => s.verdict === "loud")) console.log(line(s));

  const unchecked = checked.filter((s) => s.verdict !== "collision" && s.verdict !== "loud");
  if (unchecked.length) {
    console.log(`\nUNCHECKED (topic would not resolve): ${unchecked.map((s) => "$" + s.symbol).join(", ")}`);
  }

  const report: CollisionReport = {
    generatedAt: new Date().toISOString(),
    scanned: coins.length,
    medianPerDollar,
    btcPerDollar: btc ? perDollar(btc) : 0,
    btcInteractions: btc ? btc.interactions_24h : 0,
    suspects,
  };
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, "report.json"), JSON.stringify(report, null, 1));
  const svg = renderChartSvg(report, CHECK_TOP);
  writeFileSync(join(OUT_DIR, "chart.svg"), svg);
  writeFileSync(join(OUT_DIR, "chart.png"), await svgToPng(svg));
  console.log("\nWrote out/report.json, chart.svg, chart.png");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
