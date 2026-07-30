import type { CoinVerdict, DetectorReport } from "./types.js";

const WIDTH = 1200;
const ROW_HEIGHT = 72;
const HEADER = 170;
const FOOTER = 70;
const PAD = 48;

const COLORS: Record<string, string> = {
  bg: "#0d1117",
  text: "#e6edf3",
  subtext: "#8b949e",
  track: "#21262d",
  manufactured: "#f85149",
  mixed: "#d29922",
  organic: "#3fb950",
};

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function row(v: CoinVerdict, y: number): string {
  const maxBarWidth = WIDTH - PAD * 2 - 420;
  const w = Math.max(8, Math.round((v.score / 100) * maxBarWidth));
  const color = COLORS[v.verdict];
  const spam = Math.round(v.evidence.spamRatio * 100);
  const conc = Math.round(v.evidence.top3CreatorShare * 100);
  return `
    <text x="${PAD}" y="${y + 38}" font-size="26" font-weight="600" fill="${COLORS.text}">$${esc(v.symbol)}</text>
    <rect x="${PAD + 150}" y="${y + 14}" width="${maxBarWidth}" height="30" rx="7" fill="${COLORS.track}"/>
    <rect x="${PAD + 150}" y="${y + 14}" width="${w}" height="30" rx="7" fill="${color}"/>
    <text x="${PAD + 160 + maxBarWidth}" y="${y + 38}" font-size="25" font-weight="700" fill="${color}">${v.score}</text>
    <text x="${PAD + 225 + maxBarWidth}" y="${y + 38}" font-size="21" fill="${COLORS.subtext}">${spam}% spam · top3 ${conc}%</text>`;
}

export function renderChartSvg(report: DetectorReport): string {
  const shown = report.verdicts.slice(0, 10);
  const height = HEADER + shown.length * ROW_HEIGHT + FOOTER;
  const date = new Date(report.generatedAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });

  let body = "";
  let y = HEADER;
  for (const v of shown) {
    body += row(v, y);
    y += ROW_HEIGHT;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${height}" viewBox="0 0 ${WIDTH} ${height}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${WIDTH}" height="${height}" fill="${COLORS.bg}"/>
  <text x="${PAD}" y="56" font-size="36" font-weight="700" fill="${COLORS.text}">Manufactured Hype Score</text>
  <text x="${PAD}" y="94" font-size="24" fill="${COLORS.subtext}">${date} · coins in a social spike, scored 0 (organic) to 100 (manufactured)</text>
  <text x="${PAD}" y="128" font-size="21" fill="${COLORS.subtext}">score = spam share of posts + creator concentration + sentiment uniformity</text>
  <g>${body}</g>
  <text x="${PAD}" y="${height - 28}" font-size="20" fill="${COLORS.subtext}">Data: LunarCrush · methodology in the repo · not financial advice</text>
</svg>`;
}

/** 1080x1920 Instagram Story variant, content inside IG-safe zones. */
export function renderStorySvg(report: DetectorReport): string {
  const W = 1080;
  const H = 1920;
  const M = 80;
  const rowH = 118;
  const shown = report.verdicts.slice(0, 9);
  const date = new Date(report.generatedAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
  const barMax = W - M * 2 - 130;

  let body = "";
  let y = 500;
  for (const v of shown) {
    const w = Math.max(10, Math.round((v.score / 100) * barMax));
    const color = COLORS[v.verdict];
    const spam = Math.round(v.evidence.spamRatio * 100);
    const conc = Math.round(v.evidence.top3CreatorShare * 100);
    body += `
    <text x="${M}" y="${y + 40}" font-size="34" font-weight="600" fill="${COLORS.text}">$${esc(v.symbol)}</text>
    <text x="${W - M}" y="${y + 40}" font-size="25" fill="${COLORS.subtext}" text-anchor="end">${spam}% spam · top3 ${conc}%</text>
    <rect x="${M}" y="${y + 56}" width="${barMax}" height="28" rx="8" fill="${COLORS.track}"/>
    <rect x="${M}" y="${y + 56}" width="${w}" height="28" rx="8" fill="${color}"/>
    <text x="${M + barMax + 18}" y="${y + 80}" font-size="30" font-weight="700" fill="${color}">${v.score}</text>`;
    y += rowH;
  }
  if (shown.length === 0) {
    body = `<text x="${M}" y="560" font-size="34" fill="${COLORS.subtext}">No genuine social spikes today.</text>
    <text x="${M}" y="615" font-size="34" fill="${COLORS.subtext}">Quiet markets are allowed.</text>`;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${M}" y="330" font-size="60" font-weight="700" fill="${COLORS.text}">Hype Check</text>
  <text x="${M}" y="380" font-size="30" fill="${COLORS.subtext}">${date} · 0 organic to 100 manufactured</text>
  <text x="${M}" y="422" font-size="26" fill="${COLORS.subtext}">spam share + creator concentration + sentiment uniformity</text>
  ${body}
  <text x="${M}" y="${H - 290}" font-size="26" fill="${COLORS.subtext}">Data: LunarCrush · methodology in the repo</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
