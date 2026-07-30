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
  const maxBarWidth = WIDTH - PAD * 2 - 440;
  const w = Math.max(8, Math.round((Math.abs(m.delta) / maxAbsDelta) * maxBarWidth));
  const color = isClimber ? COLORS.climber : COLORS.faller;
  const deltaLabel = m.delta > 0 ? `+${m.delta}` : `${m.delta}`;
  return `
    <text x="${PAD}" y="${y + 34}" font-size="26" font-weight="600" fill="${COLORS.text}">$${esc(m.symbol)}</text>
    <rect x="${PAD + 160}" y="${y + 12}" width="${maxBarWidth}" height="28" rx="6" fill="${COLORS.track}"/>
    <rect x="${PAD + 160}" y="${y + 12}" width="${w}" height="28" rx="6" fill="${color}"/>
    <text x="${PAD + 170 + maxBarWidth}" y="${y + 34}" font-size="24" font-weight="600" fill="${color}">${deltaLabel}</text>
    <text x="${PAD + 250 + maxBarWidth}" y="${y + 34}" font-size="22" fill="${COLORS.subtext}">#${m.altRankPrevious} → #${m.altRank}</text>`;
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

/** 1080x1920 Instagram Story variant. Content stays inside the safe zones
 * (roughly 250px top and bottom are covered by IG UI). */
export function renderStorySvg(report: MoversReport): string {
  const W = 1080;
  const H = 1920;
  const M = 80;
  const rowH = 96;
  const date = new Date(report.generatedAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
  const barMax = W - M * 2 - 300;
  const rows = [...report.climbers, ...report.fallers];
  const maxAbsDelta = Math.max(1, ...rows.map((m) => Math.abs(m.delta)));

  const section = (title: string, color: string, movers: Mover[], startY: number): string => {
    let out = `<text x="${M}" y="${startY}" font-size="30" font-weight="700" fill="${color}" letter-spacing="2">${title}</text>`;
    let y = startY + 28;
    for (const m of movers) {
      const w = Math.max(10, Math.round((Math.abs(m.delta) / maxAbsDelta) * barMax));
      const deltaLabel = m.delta > 0 ? `+${m.delta}` : `${m.delta}`;
      out += `
      <text x="${M}" y="${y + 44}" font-size="34" font-weight="600" fill="${COLORS.text}">$${esc(m.symbol)}</text>
      <text x="${W - M}" y="${y + 44}" font-size="26" fill="${COLORS.subtext}" text-anchor="end">#${m.altRankPrevious} → #${m.altRank}</text>
      <rect x="${M}" y="${y + 60}" width="${barMax}" height="26" rx="7" fill="${COLORS.track}"/>
      <rect x="${M}" y="${y + 60}" width="${w}" height="26" rx="7" fill="${color}"/>
      <text x="${M + barMax + 16}" y="${y + 82}" font-size="28" font-weight="700" fill="${color}">${deltaLabel}</text>`;
      y += rowH;
    }
    return out;
  };

  const climbersY = 470;
  const fallersY = climbersY + 28 + report.climbers.length * rowH + 56;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${M}" y="330" font-size="64" font-weight="700" fill="${COLORS.text}">AltRank Movers</text>
  <text x="${M}" y="380" font-size="30" fill="${COLORS.subtext}">${date} · 24h change in LunarCrush AltRank</text>
  ${section("CLIMBERS", COLORS.climber, report.climbers, climbersY)}
  ${section("FALLERS", COLORS.faller, report.fallers, fallersY)}
  <text x="${M}" y="${H - 290}" font-size="26" fill="${COLORS.subtext}">Data: LunarCrush · lower rank = stronger</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
