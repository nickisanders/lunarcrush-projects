import type { BotShareReport } from "./types.js";

function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

export function renderPost(report: BotShareReport, promoCode?: string): string {
  const quotable = report.scored.filter((s) => s.quotable);
  const dirty = quotable.slice(0, 5);
  const clean = [...quotable].reverse().slice(0, 5);
  const excluded = report.scored.filter((s) => !s.quotable);
  const mid = quotable[Math.floor(quotable.length / 2)];

  const lines = [
    `🤖 Bot share of crypto conversation, ${new Date(report.generatedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" })}`,
    "",
    "Most junk:",
    ...dirty.map((s) => `· $${s.symbol} ${pct(s.spamShare)}`),
    "",
    "Least junk:",
    ...clean.map((s) => `· $${s.symbol} ${pct(s.spamShare)}`),
    "",
    `Median across ${quotable.length} major coins: ${pct(mid.spamShare)} of created posts flagged as spam.`,
  ];

  if (excluded.length) {
    lines.push(
      "",
      `Off the scale: ${excluded.map((s) => `$${s.symbol}`).join(", ")}. Flagged posts outnumber created posts on some days, so no honest percentage exists.`
    );
  }

  lines.push(
    "",
    `Scanned ${report.scanned} coins over $1B. Spam labels are LunarCrush's classifier, not ground truth.`,
    "Data: LunarCrush"
  );
  if (promoCode) lines.push(`Affiliate code ${promoCode} gets 15% off at checkout`);
  return lines.join("\n");
}
