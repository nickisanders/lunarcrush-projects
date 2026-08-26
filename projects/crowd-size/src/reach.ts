/** Does follower count predict who actually drives a coin's conversation?
 *
 * Reads out/creators.json, written by the daily run.
 *
 * Read the population carefully. These are the accounts that ALREADY made a
 * coin's top 10, so a small account only appears here if it landed. That makes
 * this a statement about who the loud accounts are, not a claim that small
 * accounts get more reach in general: the selection guarantees the small ones
 * present are the ones that worked. Reporting per-follower engagement across
 * these bands would be pure survivorship and is deliberately not done.
 *
 * A fair objection to any of this is that the raw feed contains junk: stale
 * follower counts, bot amplification, accounts that were later suspended. That
 * objection lands hardest on the smallest accounts, so `--min-followers N`
 * exists to drop them and see whether the result depends on them. It does not.
 * Among only the 137 accounts with 100k+ followers, spanning a 125x follower
 * range, followers still explain 24% of impact: the same as the full sample.
 *
 * Usage: npm run reach [-- --min-followers 100000]
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { renderReachChartSvg, svgToPng } from "./chart.js";
import type { Creator } from "./types.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(HERE, "..", "out");
const DEPTH = 10;

export interface Voice {
  coin: string;
  rank: number;
  name: string;
  followers: number;
  interactions: number;
}

/** The top `depth` voices on each coin, with a usable follower count. */
export function topVoices(
  raw: { symbol: string; creators: Creator[] }[],
  depth = DEPTH
): Voice[] {
  const out: Voice[] = [];
  for (const { symbol, creators } of raw) {
    const sorted = [...creators]
      .filter((c) => (c.interactions_24h ?? 0) > 0)
      .sort((a, b) => (b.interactions_24h ?? 0) - (a.interactions_24h ?? 0))
      .slice(0, depth);
    sorted.forEach((c, i) => {
      const followers = Number(c.creator_followers);
      if (!Number.isFinite(followers) || followers <= 0 || !c.creator_name) return;
      out.push({ coin: symbol, rank: i + 1, name: c.creator_name,
        followers, interactions: c.interactions_24h ?? 0 });
    });
  }
  return out;
}

export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Pearson correlation of log10 followers against log10 interactions.
 *
 * Logs because both quantities span five orders of magnitude, where a raw
 * correlation would be decided entirely by the largest handful of accounts. */
export function logCorrelation(voices: Voice[]): number {
  if (voices.length < 3) return 0;
  const x = voices.map((v) => Math.log10(v.followers));
  const y = voices.map((v) => Math.log10(v.interactions));
  const mx = x.reduce((a, b) => a + b, 0) / x.length;
  const my = y.reduce((a, b) => a + b, 0) / y.length;
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < x.length; i++) {
    num += (x[i] - mx) * (y[i] - my);
    dx += (x[i] - mx) ** 2;
    dy += (y[i] - my) ** 2;
  }
  return dx && dy ? num / Math.sqrt(dx * dy) : 0;
}

export function summarize(voices: Voice[]) {
  const r = logCorrelation(voices);
  const under = (n: number) => voices.filter((v) => v.followers < n).length;
  return {
    voices: voices.length,
    coins: new Set(voices.map((v) => v.coin)).size,
    correlation: r,
    rSquared: r * r,
    medianFollowers: median(voices.map((v) => v.followers)),
    medianFollowersTopVoice: median(voices.filter((v) => v.rank === 1).map((v) => v.followers)),
    underOneThousand: under(1_000),
    underTenThousand: under(10_000),
    overOneMillion: voices.filter((v) => v.followers > 1_000_000).length,
  };
}

function parseFloor(argv: string[]): number {
  const i = argv.indexOf("--min-followers");
  return i >= 0 ? Number(argv[i + 1]) || 0 : 0;
}

function main(): void {
  const floor = parseFloor(process.argv.slice(2));
  const raw = JSON.parse(readFileSync(join(OUT_DIR, "creators.json"), "utf8"));
  const all = topVoices(raw);
  const voices = all.filter((v) => v.followers >= floor);
  const s = summarize(voices);

  if (floor > 0) {
    console.log(`Dropping accounts under ${floor.toLocaleString()} followers: ${all.length} -> ${voices.length}\n`);
  }
  console.log(`${s.voices} top-${DEPTH} voices across ${s.coins} coins\n`);
  console.log(`followers explain ${(s.rSquared * 100).toFixed(0)}% of the variation in impact`);
  console.log(`  (log-log correlation ${s.correlation.toFixed(2)})\n`);
  console.log(`median followers of a top-${DEPTH} voice: ${s.medianFollowers.toLocaleString()}`);
  console.log(`median followers of a #1 voice:        ${s.medianFollowersTopVoice.toLocaleString()}\n`);
  const pct = (n: number) => `${((n / s.voices) * 100).toFixed(0)}%`;
  console.log(`under 1,000 followers:   ${s.underOneThousand} (${pct(s.underOneThousand)})`);
  console.log(`under 10,000 followers:  ${s.underTenThousand} (${pct(s.underTenThousand)})`);
  console.log(`over 1,000,000:          ${s.overOneMillion} (${pct(s.overOneMillion)})`);

  const small = voices
    .filter((v) => v.followers < 5_000 && v.interactions > 20_000)
    .sort((a, b) => b.interactions - a.interactions);
  console.log("\nsmall accounts carrying a major coin:");
  for (const v of small.slice(0, 8)) {
    console.log(`  $${v.coin.padEnd(6)} #${v.rank}  ${v.name.padEnd(18)} ${v.followers.toLocaleString().padStart(7)} followers  ${v.interactions.toLocaleString()} interactions`);
  }

  // Does the result depend on the smallest, least verifiable accounts?
  if (floor === 0) {
    console.log("\nrobustness, dropping small accounts:");
    console.log("  floor        n   corr    R^2");
    for (const f of [0, 1_000, 10_000, 50_000, 100_000]) {
      const sub = all.filter((v) => v.followers >= f);
      const r = logCorrelation(sub);
      console.log(
        `  ${f.toLocaleString().padStart(7)}  ${String(sub.length).padStart(7)}   ${r.toFixed(2)}   ${(r * r).toFixed(2)}`
      );
    }
  }

  writeFileSync(join(OUT_DIR, "reach.json"), JSON.stringify({ summary: s, voices, minFollowers: floor }, null, 1));
  const svg = renderReachChartSvg(voices, s);
  writeFileSync(join(OUT_DIR, "reach-chart.svg"), svg);
  svgToPng(svg).then((png) => {
    writeFileSync(join(OUT_DIR, "reach-chart.png"), png);
    console.log("\nWrote out/reach.json, reach-chart.svg, reach-chart.png");
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
