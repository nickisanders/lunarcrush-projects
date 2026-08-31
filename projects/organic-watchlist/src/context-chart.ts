/** Chart the trap the 24-hour flatness test cannot see.
 *
 * A coin's price over the last few weeks, with the signal day marked. The
 * setup asks whether the last bar is flat; this shows what the bars before it
 * were doing.
 *
 * Usage: npx tsx src/context-chart.ts HNT
 */
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { loadEnv } from "./env.js";
import { fetchCoinsList, fetchDailySeries } from "./lunarcrush.js";
import { svgToPng } from "./chart.js";

const OUT_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "out");
const DAYS = 21;
const C = { bg: "#0d1117", text: "#e6edf3", sub: "#8b949e", grid: "#30363d",
  green: "#3fb950", red: "#f85149", amber: "#f7931a" };
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

async function main(): Promise<void> {
  loadEnv();
  const apiKey = process.env.LUNARCRUSH_API_KEY;
  const symbol = process.argv[2];
  if (!apiKey || !symbol) {
    console.error("usage: LUNARCRUSH_API_KEY set, npx tsx src/context-chart.ts SYMBOL");
    process.exit(1);
  }
  const coin = (await fetchCoinsList(apiKey)).find((c) => c.symbol === symbol);
  if (!coin) throw new Error(`${symbol} not in the top 1000`);
  // Complete days only: today is still forming and would draw a false last bar.
  const series = (await fetchDailySeries(apiKey, coin.id)).slice(0, -1).slice(-DAYS);
  const closes = series.map((r) => r.close ?? 0).filter((v) => v > 0);
  const last = closes[closes.length - 1];
  const weekAgo = closes[closes.length - 8];
  const dayBefore = closes[closes.length - 2];

  const W = 1300, H = 720, L = 110, R = 70, T = 250, B = 190;
  const PW = W - L - R, PH = H - T - B;
  const lo = Math.min(...closes) * 0.92, hi = Math.max(...closes) * 1.06;
  const x = (i: number) => L + (i / (closes.length - 1)) * PW;
  const y = (v: number) => T + PH - ((v - lo) / (hi - lo)) * PH;
  const pts = closes.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const weekIdx = closes.length - 8;

  const p = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${C.text}">The price nearly doubled. My scanner called it flat.</text>`,
    `<text x="60" y="120" font-size="23" fill="${C.sub}">$${symbol} daily closes. The last candle rose 91%, and the scanner still called the price flat.</text>`,
    `<text x="60" y="156" font-size="23" fill="${C.sub}">It reads a rolling 24 hours, which by scan time had moved past the move entirely.</text>`,
    // shade the prior week
    `<rect x="${x(weekIdx).toFixed(0)}" y="${T}" width="${(x(closes.length - 1) - x(weekIdx)).toFixed(0)}" height="${PH}" fill="${C.red}" opacity="0.10"/>`,
    // Inside the shaded band at its top-left, where the price line is still low.
    `<text x="${(x(weekIdx) + 16).toFixed(0)}" y="${(T + 30).toFixed(0)}" font-size="22" font-weight="700" fill="${C.red}">the prior 7 days: +${(((last / weekAgo) - 1) * 100).toFixed(0)}%</text>`,
    `<polyline points="${pts}" fill="none" stroke="${C.amber}" stroke-width="3.5"/>`,
    `<circle cx="${x(closes.length - 1).toFixed(1)}" cy="${y(last).toFixed(1)}" r="9" fill="${C.green}"/>`,
    `<text x="${(x(closes.length - 1) - 24).toFixed(0)}" y="${(y(last) + 6).toFixed(0)}" font-size="22" font-weight="700" fill="${C.green}" text-anchor="end">last complete day: +${(((last / dayBefore) - 1) * 100).toFixed(0)}%</text>`,
    `<text x="${(x(closes.length - 1) - 24).toFixed(0)}" y="${(y(last) + 34).toFixed(0)}" font-size="19" fill="${C.sub}" text-anchor="end">the scanner read a ROLLING 24h and saw +0.1%</text>`,
  ];
  for (const v of [lo, (lo + hi) / 2, hi]) {
    p.push(`<line x1="${L}" y1="${y(v).toFixed(0)}" x2="${L + PW}" y2="${y(v).toFixed(0)}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${L - 14}" y="${(y(v) + 7).toFixed(0)}" font-size="18" fill="${C.sub}" text-anchor="end">$${v.toFixed(2)}</text>`);
  }
  p.push(
    `<text x="60" y="${H - 104}" font-size="23" fill="${C.text}">Only 2 of 402 historical signals followed a week this big, so my backtest has almost nothing to say about it.</text>`,
    `<text x="60" y="${H - 70}" font-size="21" fill="${C.sub}">I tested whether a prior run ruins the setup and it does not, detectably: 48.6% after a quiet week vs 51.0% after a run, p = 0.76.</text>`,
    `<text x="60" y="${H - 40}" font-size="21" fill="${C.sub}">So there is no filter to add. The prior week is now printed next to any pick, and the reader decides.</text>`,
    `<text x="60" y="${H - 14}" font-size="19" fill="${C.sub}">Data: LunarCrush · method and code in the repo</text>`,
    `</svg>`);

  const svg = p.join("\n");
  writeFileSync(join(OUT_DIR, "context.svg"), svg);
  writeFileSync(join(OUT_DIR, "context.png"), await svgToPng(svg));
  console.log(`$${symbol}: ${((last / weekAgo - 1) * 100).toFixed(0)}% over 7 days, ${((last / dayBefore - 1) * 100).toFixed(1)}% on the signal day`);
  console.log("Wrote out/context.svg and out/context.png");
}

main().catch((e) => { console.error(e); process.exit(1); });
