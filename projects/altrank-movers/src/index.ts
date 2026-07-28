import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { renderChartSvg, svgToPng } from "./chart.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList } from "./lunarcrush.js";
import { DEFAULT_OPTIONS, computeMovers } from "./movers.js";
import { renderPost } from "./render.js";
import { loadPreviousRanks, saveSnapshot } from "./snapshot.js";
import { sendToTelegram } from "./telegram.js";
import type { CoinRow } from "./types.js";

interface CliArgs {
  mock: boolean;
  send: boolean;
  top: number;
  minInteractions: number;
  count: number;
  outDir: string;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {
    mock: false,
    send: false,
    top: DEFAULT_OPTIONS.topN,
    minInteractions: DEFAULT_OPTIONS.minInteractions,
    count: DEFAULT_OPTIONS.count,
    outDir: "out",
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--mock") args.mock = true;
    else if (a === "--send") args.send = true;
    else if (a === "--top") args.top = Number(argv[++i]);
    else if (a === "--min-interactions") args.minInteractions = Number(argv[++i]);
    else if (a === "--count") args.count = Number(argv[++i]);
    else if (a === "--out") args.outDir = argv[++i];
    else {
      console.error(`Unknown argument: ${a}`);
      process.exit(1);
    }
  }
  return args;
}

async function loadRows(mock: boolean): Promise<CoinRow[]> {
  if (mock) {
    const raw = await readFile(new URL("../fixtures/coins-sample.json", import.meta.url), "utf8");
    return JSON.parse(raw) as CoinRow[];
  }
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  if (!apiKey) {
    throw new Error(
      "LUNARCRUSH_API_KEY is not set. Copy .env.example to .env and add your key, or run with --mock."
    );
  }
  return fetchCoinsList(apiKey);
}

async function main(): Promise<void> {
  loadEnv();
  const args = parseArgs(process.argv.slice(2));

  const rows = await loadRows(args.mock);
  console.log(`Loaded ${rows.length} coins${args.mock ? " (mock data)" : ""}`);

  const previousRanks = args.mock ? undefined : await loadPreviousRanks("data");
  const report = computeMovers(rows, {
    topN: args.top,
    minInteractions: args.minInteractions,
    count: args.count,
    previousRanks,
  });

  if (!args.mock) {
    const snapPath = await saveSnapshot("data", rows);
    console.log(`Snapshot saved: ${snapPath}`);
  }

  if (report.climbers.length === 0 && report.fallers.length === 0) {
    console.log("No movers found (missing alt_rank_previous and no prior snapshot). Nothing to post.");
    return;
  }

  const post = renderPost(report, process.env.POST_LINK_URL);
  const svg = renderChartSvg(report);

  await mkdir(args.outDir, { recursive: true });
  await writeFile(join(args.outDir, "post.txt"), post);
  await writeFile(join(args.outDir, "chart.svg"), svg);

  let png: Buffer | undefined;
  try {
    png = await svgToPng(svg);
    await writeFile(join(args.outDir, "chart.png"), png);
  } catch (err) {
    console.warn(`PNG render failed (${(err as Error).message}); SVG still written.`);
  }

  console.log(`\n${post}\n`);
  console.log(`Wrote ${args.outDir}/post.txt, chart.svg${png ? ", chart.png" : ""}`);

  if (args.send) {
    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;
    if (!botToken || !chatId) {
      throw new Error("--send requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment.");
    }
    await sendToTelegram({ botToken, chatId }, post, png);
    console.log("Posted to Telegram.");
  }
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
