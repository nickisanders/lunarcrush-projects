import { BASELINE } from "./watchlist.js";
import type { WatchlistReport } from "./types.js";

const COLORS = {
  bg: "#0d1117",
  text: "#e6edf3",
  sub: "#8b949e",
  track: "#21262d",
  green: "#3fb950",
  dim: "#6e7681",
};
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function renderChartSvg(report: WatchlistReport): string {
  const W = 1200;
  const PAD = 55;
  const HEADER = 190;
  const rowH = 76;
  const rows = report.entries.slice(0, 8);
  const H = rows.length === 0
    ? HEADER + 200 + report.nearMisses.length * 44 + 110
    : HEADER + rows.length * rowH + 110;
  const maxMult = Math.max(2, ...rows.map((e) => e.multiple));
  const barMax = W - PAD * 2 - 430;

  let body = "";
  let y = HEADER;
  for (const e of rows) {
    const w = Math.max(8, Math.round((e.multiple / maxMult) * barMax));
    const spam = Math.round(e.spam * 100);
    const move = e.percentChange24h >= 0 ? `+${e.percentChange24h.toFixed(1)}` : e.percentChange24h.toFixed(1);
    body += `
    <text x="${PAD}" y="${y + 34}" font-size="27" font-weight="600" fill="${COLORS.text}">$${esc(e.symbol)}</text>
    <text x="${PAD}" y="${y + 60}" font-size="19" fill="${COLORS.sub}">${spam}% spam · price ${move}%</text>
    <rect x="${PAD + 190}" y="${y + 14}" width="${barMax}" height="32" rx="8" fill="${COLORS.track}"/>
    <rect x="${PAD + 190}" y="${y + 14}" width="${w}" height="32" rx="8" fill="${COLORS.green}"/>
    <text x="${PAD + 205 + barMax}" y="${y + 39}" font-size="27" font-weight="700" fill="${COLORS.green}">${e.multiple.toFixed(0)}x</text>
    <text x="${PAD + 285 + barMax}" y="${y + 39}" font-size="20" fill="${COLORS.sub}">normal chatter</text>`;
    y += rowH;
  }
  if (rows.length === 0) {
    body = `<text x="${PAD}" y="${HEADER + 40}" font-size="32" font-weight="600" fill="${COLORS.text}">Nothing qualifies today.</text>
    <text x="${PAD}" y="${HEADER + 84}" font-size="24" fill="${COLORS.dim}">This setup shows up about one day in six. That is the point of waiting for it.</text>`;
    let ny = HEADER + 150;
    if (report.nearMisses.length > 0) {
      body += `<text x="${PAD}" y="${ny}" font-size="22" fill="${COLORS.sub}">Closest, and why each missed:</text>`;
      ny += 44;
      for (const n of report.nearMisses) {
        body += `
    <text x="${PAD}" y="${ny}" font-size="27" font-weight="600" fill="${COLORS.text}">$${esc(n.symbol)}</text>
    <text x="${PAD + 150}" y="${ny}" font-size="25" fill="${COLORS.dim}">${esc(n.failed)}</text>`;
        ny += 44;
      }
    }
  }

  const hit = (BASELINE.organic * 100).toFixed(0);
  const base = (BASELINE.ordinary * 100).toFixed(0);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${PAD}" y="58" font-size="36" font-weight="700" fill="${COLORS.text}">Organic attention, price hasn't moved</text>
  <text x="${PAD}" y="98" font-size="24" fill="${COLORS.sub}">${fmtDate(report.generatedAt)} · real conversation spikes, low spam, flat price</text>
  <text x="${PAD}" y="140" font-size="21" fill="${COLORS.green}">Historically this setup beat BTC over the next 3 days ${hit}% of the time.</text>
  <text x="${PAD}" y="168" font-size="21" fill="${COLORS.sub}">An ordinary coin-day does it ${base}% of the time. An odds shift, not a prediction.</text>
  ${body}
  <text x="${PAD}" y="${H - 58}" font-size="19" fill="${COLORS.sub}">Scanned ${report.scanned} coins · criteria fixed to the published backtest · not financial advice</text>
  <text x="${PAD}" y="${H - 28}" font-size="19" fill="${COLORS.sub}">Data: LunarCrush</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
