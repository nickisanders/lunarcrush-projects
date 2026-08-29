import sharp from "sharp";
import type { CollisionReport, Suspect } from "./types.js";

const C = { bg: "#0d1117", text: "#e6edf3", sub: "#8b949e", track: "#21262d",
  grid: "#30363d", red: "#f85149", amber: "#d29922", green: "#3fb950" };
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function short(n: number): string {
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}k`;
  return String(Math.round(n));
}

/** Log scale: the range runs from 100x the median to over 10,000x, and a
 * linear axis would collapse everything below the worst offender. */
export function renderChartSvg(report: CollisionReport, top = 14): string {
  // Only confirmed collisions are plotted. A coin that is merely loud has
  // a real conversation and does not belong on a chart about naming.
  const rows = report.suspects.filter((s) => s.verdict === "collision").slice(0, top);
  const W = 1300;
  const TOP = 250;
  const ROW = 46;
  const BAR_X = 430;
  const BAR_W = 620;
  const H = TOP + rows.length * ROW + 300;
  const max = Math.max(...rows.map((r) => r.vsMedian), 100);
  const scale = (v: number) => (Math.log10(v) / Math.log10(max)) * BAR_W;

  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${C.text}">Coins that look popular because of their name</text>`,
    `<text x="60" y="120" font-size="23" fill="${C.sub}">social interactions per dollar of market cap, against the median coin. log scale.</text>`,
    `<text x="60" y="156" font-size="23" fill="${C.sub}">every one of these tickers is an ordinary word or a famous name. ${report.scanned.toLocaleString()} coins scanned.</text>`,
  ];

  for (const tick of [1, 10, 100, 1000, 10000].filter((t) => t <= max)) {
    const x = BAR_X + scale(tick);
    parts.push(
      `<line x1="${x.toFixed(0)}" y1="${TOP - 24}" x2="${x.toFixed(0)}" y2="${TOP + rows.length * ROW - 16}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${x.toFixed(0)}" y="${TOP - 34}" font-size="18" fill="${C.sub}" text-anchor="middle">${tick >= 1000 ? `${tick / 1000}kx` : `${tick}x`}</text>`
    );
  }

  rows.forEach((s: Suspect, i: number) => {
    const y = TOP + i * ROW;
    const w = Math.max(4, scale(s.vsMedian));
    const col = s.vsMedian >= 1000 ? C.red : C.amber;
    parts.push(
      `<text x="${BAR_X - 20}" y="${y + 8}" font-size="23" font-weight="600" fill="${C.text}" text-anchor="end">$${esc(s.symbol)}</text>`,
      `<text x="60" y="${y + 8}" font-size="19" fill="${C.sub}">${esc(s.name.slice(0, 26))}</text>`,
      `<rect x="${BAR_X}" y="${y - 13}" width="${w.toFixed(0)}" height="26" rx="6" fill="${col}"/>`,
      `<text x="${BAR_X + w + 14}" y="${y + 8}" font-size="21" font-weight="700" fill="${col}">${Math.round(s.vsMedian).toLocaleString()}x</text>`
    );
  });

  const footY = TOP + rows.length * ROW + 74;
  // The clearest example is the one whose word carries the most traffic, not
  // the one with the highest ratio. A big ratio on a small word is a weaker
  // illustration than a modest ratio on a word the whole internet uses.
  const star = [...rows].sort((a, b) => (b.bareInteractions ?? 0) - (a.bareInteractions ?? 0))[0];
  const vsBtc = report.btcPerDollar && star
    ? (star.bareInteractions ?? 0) / (report.btcInteractions || 1)
    : 0;
  parts.push(
    `<text x="60" y="${footY}" font-size="24" fill="${C.text}" font-weight="700">$${esc(star.symbol)} carries ${short(star.interactions24h)} interactions on a $${short(star.marketCap)} market cap.</text>`,
    `<text x="60" y="${footY + 38}" font-size="22" fill="${C.sub}">Its ticker as a topic, "${esc(star.bareTopic ?? "")}", draws ${short(star.bareInteractions ?? 0)} interactions a day from ${short(star.bareContributors ?? 0)} people.</text>`,
    vsBtc >= 1
      ? `<text x="60" y="${footY + 72}" font-size="22" fill="${C.sub}">That is about ${vsBtc.toFixed(1)}x Bitcoin's entire daily conversation, for a $${short(star.marketCap)} token.</text>`
      : `<text x="60" y="${footY + 72}" font-size="22" fill="${C.sub}">The coin accounts for ${(((star.shareOfBare ?? 0) * 100)).toFixed(1)}% of it. The rest is people using the word.</text>`,
    `<text x="60" y="${footY + 122}" font-size="21" fill="${C.text}">These tickers are ordinary words and famous names, so their "social volume" is mostly not about them.</text>`,
    `<text x="60" y="${footY + 156}" font-size="20" fill="${C.sub}">Ranking coins by social volume puts them near the top. This is a data-reading problem, not a verdict on any project.</text>`,
    `<text x="60" y="${footY + 190}" font-size="19" fill="${C.sub}">Data: LunarCrush · ${esc(report.generatedAt.slice(0, 10))} · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}

export function svgToPng(svg: string): Promise<Buffer> {
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
