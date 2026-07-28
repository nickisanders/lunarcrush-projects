import type { Mover, MoversReport } from "./types.js";

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function fmtDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : `${delta}`;
}

function fmtLine(m: Mover, i: number): string {
  return `${i + 1}. $${m.symbol} ${fmtDelta(m.delta)} (#${m.altRankPrevious} to #${m.altRank})`;
}

export function renderPost(report: MoversReport, linkUrl?: string): string {
  const lines: string[] = [];
  lines.push(`🌙 AltRank movers, ${fmtDate(report.generatedAt)}`);
  lines.push("");
  if (report.climbers.length > 0) {
    lines.push("📈 Climbers");
    report.climbers.forEach((m, i) => lines.push(fmtLine(m, i)));
    lines.push("");
  }
  if (report.fallers.length > 0) {
    lines.push("📉 Fallers");
    report.fallers.forEach((m, i) => lines.push(fmtLine(m, i)));
    lines.push("");
  }
  lines.push(`Tracked across the top ${report.universeSize} coins by social activity.`);
  if (linkUrl) {
    lines.push(`Data: LunarCrush ${linkUrl}`);
  }
  return lines.join("\n");
}
