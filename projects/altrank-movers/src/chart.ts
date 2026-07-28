import type { Mover, MoversReport } from "./types.js";

const WIDTH = 1200;
const ROW_HEIGHT = 64;
const HEADER = 160;
const FOOTER = 60;
const PAD = 48;

const COLORS = {
  bg: "#0d1117",
  text: "#e6edf3",
  subtext: "#8b949e",
  climber: "#3fb950",
  faller: "#f85149",
  track: "#21262d",
};

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function bar(m: Mover, y: number, maxAbsDelta: number, isClimber: boolean): string {
  const maxBarWidth = WIDTH - PAD * 2 - 330;
  const w = Math.max(8, Math.round((Math.abs(m.delta) / maxAbsDelta) * maxBarWidth));
  const color = isClimber ? COLORS.climber : COLORS.faller;
  const deltaLabel = m.delta > 0 ? `+${m.delta}` : `${m.delta}`;
  return `
    <text x="${PAD}" y="${y + 34}" font-size="26" font-weight="600" fill="${COLORS.text}">$${esc(m.symbol)}</text>
    <rect x="${PAD + 160}" y="${y + 12}" width="${maxBarWidth}" height="28" rx="6" fill="${COLORS.track}"/>
    <rect x="${PAD + 160}" y="${y + 12}" width="${w}" height="28" rx="6" fill="${color}"/>
    <text x="${PAD + 170 + maxBarWidth}" y="${y + 34}" font-size="24" font-weight="600" fill="${color}">${deltaLabel}</text>
    <text x="${PAD + 250 + maxBarWidth}" y="${y + 34}" font-size="22" fill="${COLORS.subtext}">#${m.altRank}</text>`;
}

export function renderChartSvg(report: MoversReport): string {
  const rows = [...report.climbers, ...report.fallers];
  const maxAbsDelta = Math.max(1, ...rows.map((m) => Math.abs(m.delta)));
  const sectionGap = 56;
  const height =
    HEADER +
    rows.length * ROW_HEIGHT +
    (report.climbers.length > 0 && report.fallers.length > 0 ? sectionGap : 0) +
    FOOTER;

  const date = new Date(report.generatedAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });

  let body = "";
  let y = HEADER;

  if (report.climbers.length > 0) {
    body += `<text x="${PAD}" y="${y - 12}" font-size="22" font-weight="700" fill="${COLORS.climber}">CLIMBERS</text>`;
    for (const m of report.climbers) {
      body += bar(m, y, maxAbsDelta, true);
      y += ROW_HEIGHT;
    }
  }
  if (report.fallers.length > 0) {
    y += report.climbers.length > 0 ? sectionGap : 0;
    body += `<text x="${PAD}" y="${y - 12}" font-size="22" font-weight="700" fill="${COLORS.faller}">FALLERS</text>`;
    for (const m of report.fallers) {
      body += bar(m, y, maxAbsDelta, false);
      y += ROW_HEIGHT;
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${height}" viewBox="0 0 ${WIDTH} ${height}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${WIDTH}" height="${height}" fill="${COLORS.bg}"/>
  <text x="${PAD}" y="56" font-size="36" font-weight="700" fill="${COLORS.text}">AltRank Movers</text>
  <text x="${PAD}" y="92" font-size="24" fill="${COLORS.subtext}">${date} · 24h change in LunarCrush AltRank</text>
  <g>${body}</g>
  <text x="${PAD}" y="${height - 24}" font-size="20" fill="${COLORS.subtext}">Data: LunarCrush · lower rank = stronger relative performance</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
