import sharp from "sharp";
import type { CoinCrowd, CrowdReport } from "./types.js";

const C = { bg: "#0d1117", text: "#e6edf3", sub: "#8b949e", track: "#21262d",
  grid: "#30363d", green: "#3fb950", amber: "#d29922", red: "#f85149" };
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Wide crowds green, narrow ones red. The thresholds group the eye; the
 * number is the claim. */
function color(n: number | null): string {
  if (n === null || n >= 50) return C.green;
  if (n >= 15) return C.amber;
  return C.red;
}

/** Log scale, because the range runs from 3 accounts to over 200 and a linear
 * axis would flatten every narrow coin into the same invisible stub. */
export function renderChartSvg(report: CrowdReport): string {
  const coins = report.coins.filter((c) => c.accountsToHalf !== null);
  const W = 1200;
  const TOP = 230;
  const ROW = 40;
  const BAR_X = 250;
  const BAR_W = 760;
  const H = TOP + coins.length * ROW + 170;
  const max = Math.max(...coins.map((c) => c.accountsToHalf ?? 1), 10);
  const scale = (n: number) => (Math.log10(n) / Math.log10(max)) * BAR_W;

  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${C.text}">How many people is a crypto crowd?</text>`,
    `<text x="60" y="120" font-size="23" fill="${C.sub}">accounts needed to make up half of everything said about a coin in 24 hours</text>`,
    `<text x="60" y="156" font-size="23" fill="${C.sub}">fewer accounts means fewer people are the conversation. log scale.</text>`,
  ];

  for (const tick of [1, 3, 10, 30, 100, 300].filter((t) => t <= max)) {
    const x = BAR_X + scale(tick);
    parts.push(
      `<line x1="${x.toFixed(0)}" y1="${TOP - 22}" x2="${x.toFixed(0)}" y2="${TOP + coins.length * ROW - 14}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${x.toFixed(0)}" y="${TOP - 32}" font-size="18" fill="${C.sub}" text-anchor="middle">${tick}</text>`
    );
  }

  coins.forEach((c: CoinCrowd, i: number) => {
    const y = TOP + i * ROW;
    const n = c.accountsToHalf ?? 1;
    const w = Math.max(4, scale(n));
    const col = color(c.accountsToHalf);
    parts.push(
      `<text x="${BAR_X - 20}" y="${y + 8}" font-size="23" font-weight="600" fill="${C.text}" text-anchor="end">${esc(c.symbol)}</text>`,
      `<rect x="${BAR_X}" y="${y - 12}" width="${w.toFixed(0)}" height="24" rx="6" fill="${col}"/>`,
      `<text x="${BAR_X + w + 14}" y="${y + 8}" font-size="21" font-weight="700" fill="${col}">${n}</text>`
    );
  });

  const footY = TOP + coins.length * ROW + 52;
  const widest = coins[0];
  const narrowest = coins[coins.length - 1];
  parts.push(
    `<text x="60" y="${footY}" font-size="23" fill="${C.text}">$${esc(widest.symbol)} takes ${widest.accountsToHalf} accounts to reach half. $${esc(narrowest.symbol)} takes ${narrowest.accountsToHalf}.</text>`,
    `<text x="60" y="${footY + 36}" font-size="21" fill="${C.sub}">Counts posts and their engagement, not people: one account can be a team, and automated posting is included.</text>`,
    `<text x="60" y="${footY + 66}" font-size="21" fill="${C.sub}">Coins whose crowd is wider than the API will list are left off rather than guessed at.</text>`,
    `<text x="60" y="${footY + 104}" font-size="19" fill="${C.sub}">Data: LunarCrush · ${esc(report.generatedAt.slice(0, 10))} · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}

export function svgToPng(svg: string): Promise<Buffer> {
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
