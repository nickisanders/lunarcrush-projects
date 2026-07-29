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

export interface PostFooterOptions {
  linkUrl?: string;
  promoCode?: string;
}

export function renderPost(report: MoversReport, footer: PostFooterOptions = {}): string {
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
  lines.push(`Data: LunarCrush${footer.linkUrl ? ` ${footer.linkUrl}` : ""}`);
  if (footer.promoCode) {
    lines.push(`Affiliate code ${footer.promoCode} gets 15% off at checkout`);
  }
  return lines.join("\n");
}
