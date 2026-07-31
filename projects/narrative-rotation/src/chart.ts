import type { RotationReport } from "./types.js";

const COLORS = {
  bg: "#0d1117",
  text: "#e6edf3",
  subtext: "#8b949e",
  track: "#21262d",
  gain: "#3fb950",
  lose: "#f85149",
};

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Landscape diverging bar chart: share change in percentage points. */
export function renderChartSvg(report: RotationReport): string {
  const W = 1200;
  const PAD = 48;
  const HEADER = 150;
  const rowH = 66;
  const rows = report.narratives;
  const H = HEADER + rows.length * rowH + 70;
  const maxAbs = Math.max(0.5, ...rows.map((n) => Math.abs(n.shareDeltaPp)));
  const mid = W / 2 + 60;
  // Negative bars must stop short of the left-hand label column
  const halfW = mid - 420;

  let body = "";
  let y = HEADER;
  for (const n of rows) {
    const w = Math.round((Math.abs(n.shareDeltaPp) / maxAbs) * halfW);
    const gain = n.shareDeltaPp >= 0;
    const color = gain ? COLORS.gain : COLORS.lose;
    const x = gain ? mid : mid - w;
    body += `
    <text x="${PAD}" y="${y + 34}" font-size="26" font-weight="600" fill="${COLORS.text}">${esc(n.title)}</text>
    <text x="${PAD}" y="${y + 58}" font-size="19" fill="${COLORS.subtext}">${n.shareNow.toFixed(1)}% of tracked attention</text>
    <rect x="${x}" y="${y + 16}" width="${Math.max(4, w)}" height="30" rx="7" fill="${color}"/>
    <text x="${gain ? mid + w + 14 : mid - w - 14}" y="${y + 38}" font-size="24" font-weight="700" fill="${color}" text-anchor="${gain ? "start" : "end"}">${n.shareDeltaPp >= 0 ? "+" : ""}${n.shareDeltaPp.toFixed(1)}pp</text>`;
    y += rowH;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${PAD}" y="56" font-size="36" font-weight="700" fill="${COLORS.text}">Narrative Rotation</text>
  <text x="${PAD}" y="94" font-size="24" fill="${COLORS.subtext}">week ending ${esc(report.weekEnding)} · change in share of crypto social attention</text>
  <line x1="${mid}" y1="${HEADER - 14}" x2="${mid}" y2="${y + 6}" stroke="#30363d" stroke-width="2" stroke-dasharray="6 6"/>
  <g>${body}</g>
  <text x="${PAD}" y="${H - 26}" font-size="20" fill="${COLORS.subtext}">Data: LunarCrush · share of interactions across tracked narrative categories</text>
</svg>`;
}

/** 1080x1920 Story variant. */
export function renderStorySvg(report: RotationReport): string {
  const W = 1080;
  const H = 1920;
  const M = 80;
  const rowH = 130;
  // The list is sorted by share delta, so take both ends: biggest gainers
  // AND biggest losers. Taking the front alone silently drops the losers.
  const all = report.narratives;
  const rows =
    all.length <= 8 ? all : [...all.slice(0, 4), ...all.slice(-4)];
  const maxAbs = Math.max(0.5, ...rows.map((n) => Math.abs(n.shareDeltaPp)));
  const mid = W / 2;
  const halfW = (W - M * 2) / 2 - 90;

  let body = "";
  let y = 500;
  for (const n of rows) {
    const w = Math.round((Math.abs(n.shareDeltaPp) / maxAbs) * halfW);
    const gain = n.shareDeltaPp >= 0;
    const color = gain ? COLORS.gain : COLORS.lose;
    const x = gain ? mid : mid - w;
    body += `
    <text x="${M}" y="${y + 40}" font-size="34" font-weight="600" fill="${COLORS.text}">${esc(n.title)}</text>
    <text x="${W - M}" y="${y + 40}" font-size="30" font-weight="700" fill="${color}" text-anchor="end">${n.shareDeltaPp >= 0 ? "+" : ""}${n.shareDeltaPp.toFixed(1)}pp</text>
    <rect x="${x}" y="${y + 58}" width="${Math.max(6, w)}" height="28" rx="8" fill="${color}"/>`;
    y += rowH;
  }

  const date = report.weekEnding;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${M}" y="330" font-size="60" font-weight="700" fill="${COLORS.text}">Narrative Rotation</text>
  <text x="${M}" y="380" font-size="30" fill="${COLORS.subtext}">week ending ${esc(date)}</text>
  <text x="${M}" y="422" font-size="26" fill="${COLORS.subtext}">who gained and lost crypto's attention this week</text>
  <line x1="${mid}" y1="470" x2="${mid}" y2="${y + 10}" stroke="#30363d" stroke-width="2" stroke-dasharray="6 6"/>
  <g>${body}</g>
  <text x="${M}" y="${H - 290}" font-size="26" fill="${COLORS.subtext}">Data: LunarCrush · share of tracked narrative attention</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}
