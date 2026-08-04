import type { CoinVerdict, DetectorReport, Verdict } from "./types.js";

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

const BADGE: Record<string, string> = {
  manufactured: "🚨",
  mixed: "⚠️",
  organic: "✅",
};

function fmtLine(v: CoinVerdict): string {
  const spam = Math.round(v.evidence.spamRatio * 100);
  const conc = Math.round(v.evidence.top3CreatorShare * 100);
  const tag = v.megaphone ? " · single megaphone, not a botnet" : "";
  return `${BADGE[v.verdict]} $${v.symbol} ${v.score}/100 (${spam}% spam, top 3 accounts drive ${conc}%${tag})`;
}

export function renderPost(report: DetectorReport, promoCode?: string): string {
  const lines: string[] = [];
  lines.push(`🔬 Hype check, ${fmtDate(report.generatedAt)}`);
  lines.push("");
  const groups: Array<[string, Verdict]> = [
    ["Manufactured hype:", "manufactured"],
    ["Mixed signals:", "mixed"],
    ["Looks organic:", "organic"],
  ];
  for (const [title, verdict] of groups) {
    const matched = report.verdicts.filter((v) => v.verdict === verdict);
    if (matched.length === 0) continue;
    lines.push(title);
    matched.slice(0, 5).forEach((v) => lines.push(fmtLine(v)));
    lines.push("");
  }
  lines.push(
    `${report.spiking} of ${report.scanned} scanned coins are in a social spike today.`
  );
  lines.push("Data: LunarCrush");
  if (promoCode) {
    lines.push(`Affiliate code ${promoCode} gets 15% off at checkout`);
  }
  return lines.join("\n");
}
