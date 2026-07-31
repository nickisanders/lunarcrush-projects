import type { NarrativeWeek, RotationReport } from "./types.js";

function pp(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}pp`;
}

function fmtLine(n: NarrativeWeek): string {
  return `${n.title} ${pp(n.shareDeltaPp)} (now ${n.shareNow.toFixed(1)}% of tracked attention, volume ${n.wowPct >= 0 ? "+" : ""}${n.wowPct.toFixed(0)}% WoW)`;
}

export function renderPost(report: RotationReport, promoCode?: string): string {
  const lines: string[] = [];
  lines.push(`🔄 Narrative rotation, week ending ${report.weekEnding}`);
  lines.push("");
  const gaining = report.narratives.filter((n) => n.shareDeltaPp > 0.2);
  const losing = report.narratives.filter((n) => n.shareDeltaPp < -0.2);
  if (gaining.length > 0) {
    lines.push("📈 Attention rotated in:");
    gaining.forEach((n) => lines.push(fmtLine(n)));
    lines.push("");
  }
  if (losing.length > 0) {
    lines.push("📉 Attention rotated out:");
    losing.forEach((n) => lines.push(fmtLine(n)));
    lines.push("");
  }
  if (report.hotCoins.length > 0) {
    const tops = report.hotCoins
      .slice(0, 5)
      .map((c) => `$${c.symbol}`)
      .join(" ");
    lines.push(`Most talked about right now: ${tops}`);
    lines.push("");
  }
  lines.push("Data: LunarCrush");
  if (promoCode) {
    lines.push(`Affiliate code ${promoCode} gets 15% off at checkout`);
  }
  return lines.join("\n");
}
