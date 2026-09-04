/** Resolve every pick this watchlist has ever published.
 *
 * The published claim is a 3-day BTC-adjusted odds shift, so that is what gets
 * scored: the coin's close-to-close return from the pick day to three days
 * later, minus Bitcoin's over the same window. Absolute return is reported too
 * but it is not the claim, and on a week when the whole market runs it will
 * flatter every pick regardless of whether the signal did anything.
 *
 * Usage: npm run track
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { renderTrackChartSvg, svgToPng } from "./chart.js";
import { PEGGED } from "./watchlist.js";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries } from "./lunarcrush.js";
import type { WatchlistReport } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const HORIZON_DAYS = 3;
const DAY = 86_400;

export interface Pick {
  date: string;
  symbol: string;
  z: number;
  spam: number;
}

export interface Decay {
  /** Interactions on the spike day that triggered the pick. */
  spike: number;
  /** Interactions on the most recent COMPLETE day. */
  latest: number;
  latestDate: string;
  daysElapsed: number;
  /** latest / spike, i.e. how much of the conversation survived. */
  retained: number;
}

export interface Resolved extends Pick {
  entry: number;
  exit: number;
  coinReturn: number;
  btcReturn: number;
  /** The published measure: coin return minus BTC's over the same window. */
  spread: number;
  beatBtc: boolean;
  decay?: Decay;
}

/** Every pick this bot actually published.
 *
 * Only the LAST run of each date counts. The bot is often run more than once a
 * day, and when a filter is added mid-day the earlier run reflects the state
 * before it. Counting every run credited the record with $HOT and $HNT, both
 * of which were caught by new checks in a later run the same day and publicly
 * rejected rather than published. A track record that includes calls I told
 * people not to take is worse than no track record.
 *
 * Pegged assets are dropped to match the live filter: they sit inside the
 * flat-price band by construction, and $USDE only ever appeared through that
 * bug.
 */
export function collectPicks(lines: string[]): Pick[] {
  const lastRunByDate = new Map<string, WatchlistReport>();
  for (const line of lines) {
    if (!line.trim()) continue;
    const report = JSON.parse(line) as WatchlistReport;
    const date = report.generatedAt.slice(0, 10);
    const prior = lastRunByDate.get(date);
    if (!prior || report.generatedAt > prior.generatedAt) lastRunByDate.set(date, report);
  }

  const seen = new Set<string>();
  const picks: Pick[] = [];
  for (const [date, report] of lastRunByDate) {
    for (const e of report.entries ?? []) {
      const key = `${e.symbol}@${date}`;
      if (seen.has(key) || PEGGED.has(e.symbol)) continue;
      seen.add(key);
      picks.push({ date, symbol: e.symbol, z: e.z, spam: e.spam });
    }
  }
  return picks.sort((a, b) => a.date.localeCompare(b.date));
}

/** Close on a given UTC date, or undefined if that day is not in the series. */
export function closeOn(series: { time: number; close?: number }[], date: string): number | undefined {
  const target = Date.parse(`${date}T00:00:00Z`) / 1000;
  return series.find((r) => r.time === target)?.close;
}

export function addDays(date: string, days: number): string {
  return new Date(Date.parse(`${date}T00:00:00Z`) + days * DAY * 1000).toISOString().slice(0, 10);
}

/** How much of the conversation that triggered a pick is still there.
 *
 * Measured against the most recent COMPLETE day, never the day in progress.
 * A partial day holds only the hours elapsed so far, so comparing it to a full
 * spike day silently overstates the decay: on 2026-08-24 at 15:00 UTC $LINK's
 * partial row read 1.37M against a complete 2.11M the day before, which turns
 * "31% retained after 5 days" into "20% after 6" and both numbers are wrong.
 * This is the same partial-day trap the spam ratios hit. */
export function attentionDecay(
  series: { time: number; interactions?: number }[],
  pickDate: string
): Decay | undefined {
  const spikeTime = Date.parse(`${pickDate}T00:00:00Z`) / 1000;
  const spike = series.find((r) => r.time === spikeTime)?.interactions;
  const lastComplete = series[series.length - 2];
  if (!spike || !lastComplete?.interactions) return undefined;
  return {
    spike,
    latest: lastComplete.interactions,
    latestDate: new Date(lastComplete.time * 1000).toISOString().slice(0, 10),
    daysElapsed: Math.round((lastComplete.time - spikeTime) / DAY),
    retained: lastComplete.interactions / spike,
  };
}

export function summarize(rows: Resolved[]) {
  const wins = rows.filter((r) => r.beatBtc).length;
  const meanSpread = rows.reduce((a, r) => a + r.spread, 0) / (rows.length || 1);
  return { n: rows.length, wins, winRate: rows.length ? wins / rows.length : 0, meanSpread };
}

async function main(): Promise<void> {
  loadEnv();
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  if (!apiKey) {
    console.error("LUNARCRUSH_API_KEY is not set.");
    process.exit(1);
  }

  const histPath = join(HERE, "..", "data", "history.jsonl");
  const picks = collectPicks(readFileSync(histPath, "utf8").split("\n"));
  if (picks.length === 0) {
    console.log("No picks published yet.");
    return;
  }

  const coins = await fetchCoinsList(apiKey);
  const btc = coins.find((c) => c.symbol === "BTC");
  if (!btc) throw new Error("BTC missing from coins list");
  const btcSeries = await fetchDailySeries(apiKey, btc.id);

  const rows: Resolved[] = [];
  for (const p of picks) {
    const coin = coins.find((c) => c.symbol === p.symbol);
    if (!coin) {
      console.log(`  ${p.symbol} (${p.date}): no longer in the top 1000, skipping`);
      continue;
    }
    const series = await fetchDailySeries(apiKey, coin.id);
    const exitDate = addDays(p.date, HORIZON_DAYS);
    const entry = closeOn(series, p.date);
    const exit = closeOn(series, exitDate);
    const btcEntry = closeOn(btcSeries, p.date);
    const btcExit = closeOn(btcSeries, exitDate);
    if (!entry || !exit || !btcEntry || !btcExit) {
      console.log(`  ${p.symbol} (${p.date}): still open, resolves ${exitDate}`);
      continue;
    }
    const coinReturn = exit / entry - 1;
    const btcReturn = btcExit / btcEntry - 1;
    rows.push({ ...p, entry, exit, coinReturn, btcReturn,
      spread: coinReturn - btcReturn, beatBtc: coinReturn > btcReturn,
      decay: attentionDecay(series, p.date) });
  }

  console.log(`\nResolved picks (${HORIZON_DAYS}-day horizon, the published claim)\n`);
  console.log("date        coin     coin %    BTC %   spread   result");
  for (const r of rows) {
    console.log(
      `${r.date}  ${r.symbol.padEnd(7)}${(r.coinReturn * 100).toFixed(1).padStart(7)}%` +
        `${(r.btcReturn * 100).toFixed(1).padStart(8)}%${(r.spread * 100).toFixed(1).padStart(8)}pp   ` +
        (r.beatBtc ? "beat BTC" : "lost to BTC")
    );
  }
  for (const r of rows) {
    if (!r.decay) continue;
    console.log(
      `\n$${r.symbol} conversation: ${(r.decay.spike / 1e6).toFixed(1)}M on the spike day, ` +
        `${(r.decay.latest / 1e6).toFixed(1)}M on ${r.decay.latestDate} ` +
        `(${r.decay.daysElapsed} days later, ${(r.decay.retained * 100).toFixed(0)}% retained)`
    );
  }

  const s = summarize(rows);
  console.log(`\n${s.wins} of ${s.n} beat Bitcoin. Mean spread ${(s.meanSpread * 100).toFixed(1)}pp.`);
  console.log(
    "Far too few to mean anything: the backtest edge is 49% vs 42%, so a run of\n" +
      "either kind is expected early. This exists to be honest, not to be evidence."
  );

  const latest = rows[rows.length - 1];
  if (latest) {
    const svg = renderTrackChartSvg(latest);
    writeFileSync(join(HERE, "..", "out", "track-chart.svg"), svg);
    writeFileSync(join(HERE, "..", "out", "track-chart.png"), await svgToPng(svg));
  }

  writeFileSync(join(HERE, "..", "out", "track.json"),
    JSON.stringify({ generatedAt: new Date().toISOString(), horizonDays: HORIZON_DAYS, rows, summary: s }, null, 1));
  console.log("\nWrote out/track.json and out/track-chart.png");
}

// Only run when invoked directly. The test suite imports the pure helpers
// above, and a bare main() call would fire real API requests on import.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
