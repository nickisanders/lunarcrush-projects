import sharp from "sharp";
import type { BotShareReport, CoinScore } from "./types.js";

const C = {
  bg: "#0d1117",
  text: "#e6edf3",
  sub: "#8b949e",
  track: "#21262d",
  grid: "#30363d",
  red: "#f85149",
  amber: "#d29922",
  green: "#3fb950",
};
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Red above half, green below a quarter, amber between. The thresholds are
 * descriptive, not a verdict: they exist so the eye can group the bars. */
function barColor(share: number): string {
  if (share >= 0.5) return C.red;
  if (share >= 0.25) return C.amber;
  return C.green;
}

export function renderChartSvg(report: BotShareReport): string {
  const quotable = report.scored.filter((s) => s.quotable);
  const W = 1200;
  const TOP = 210;
  const ROW = 44;
  const LABEL_X = 250;
  const BAR_X = 270;
  const BAR_W = 700;
  const H = TOP + quotable.length * ROW + 185;
  const date = new Date(report.generatedAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });

  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="72" font-size="38" font-weight="700" fill="${C.text}">How much of the conversation is junk</text>`,
    `<text x="60" y="116" font-size="23" fill="${C.sub}">share of created posts flagged as spam, median over the last ${report.windowDays} complete days</text>`,
    `<text x="60" y="152" font-size="23" fill="${C.sub}">major coins, ranked. ${date}</text>`,
  ];

  // Gridlines every 25%, drawn behind the bars.
  for (let g = 0; g <= 4; g++) {
    const x = BAR_X + (g / 4) * BAR_W;
    parts.push(
      `<line x1="${x}" y1="${TOP - 26}" x2="${x}" y2="${TOP + quotable.length * ROW - 12}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${x}" y="${TOP - 36}" font-size="18" fill="${C.sub}" text-anchor="middle">${g * 25}%</text>`
    );
  }

  quotable.forEach((s: CoinScore, i: number) => {
    const y = TOP + i * ROW;
    const w = Math.max(3, s.spamShare * BAR_W);
    const color = barColor(s.spamShare);
    parts.push(
      `<text x="${LABEL_X}" y="${y + 8}" font-size="24" font-weight="600" fill="${C.text}" text-anchor="end">${esc(s.symbol)}</text>`,
      `<rect x="${BAR_X}" y="${y - 13}" width="${BAR_W}" height="26" rx="6" fill="${C.track}"/>`,
      `<rect x="${BAR_X}" y="${y - 13}" width="${w.toFixed(0)}" height="26" rx="6" fill="${color}"/>`,
      `<text x="${BAR_X + w + 14}" y="${y + 8}" font-size="22" font-weight="700" fill="${color}">${Math.round(s.spamShare * 100)}%</text>`
    );
  });

  const footY = TOP + quotable.length * ROW + 46;
  const excluded = report.scored.filter((s) => !s.quotable).map((s) => s.symbol);
  parts.push(
    `<text x="60" y="${footY}" font-size="21" fill="${C.text}">This counts posts, not reach. One bot post and one viral thread weigh the same here.</text>`,
    `<text x="60" y="${footY + 34}" font-size="20" fill="${C.sub}">Off the scale entirely: ${esc(excluded.join(", "))}. Their flagged-post counts exceed their created-post counts</text>`,
    `<text x="60" y="${footY + 62}" font-size="20" fill="${C.sub}">on some days, so no honest percentage exists for them.</text>`,
    `<text x="60" y="${footY + 96}" font-size="20" fill="${C.sub}">Spam labels are LunarCrush's classifier, not ground truth.</text>`,
    `<text x="60" y="${footY + 132}" font-size="19" fill="${C.sub}">Data: LunarCrush · stablecoins and wrapped assets excluded · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}

export function svgToPng(svg: string): Promise<Buffer> {
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
