import { BASELINE, CRITERIA } from "./watchlist.js";
import type { WatchEntry, WatchlistReport } from "./types.js";

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function line(e: WatchEntry, i: number): string {
  const spam = Math.round(e.spam * 100);
  const move = e.percentChange24h >= 0 ? `+${e.percentChange24h.toFixed(1)}` : e.percentChange24h.toFixed(1);
  return `${i + 1}. $${e.symbol} · ${e.multiple.toFixed(0)}x its normal chatter · ${spam}% spam · price ${move}%`;
}

export function renderPost(report: WatchlistReport, promoCode?: string): string {
  const lines: string[] = [];
  lines.push(`🌱 Organic attention watchlist, ${fmtDate(report.generatedAt)}`);
  lines.push("");
  if (report.entries.length === 0) {
    lines.push("Nothing qualifies today. This setup is rare by design: in 6.5 years of");
    lines.push("history it appeared on roughly one day in six.");
    if (report.nearMisses.length > 0) {
      lines.push("");
      lines.push("Closest, and why each missed:");
      report.nearMisses.forEach((n) => lines.push(`· $${n.symbol} — ${n.failed}`));
    }
  } else {
    lines.push("Genuine attention spikes where price hasn't reacted yet:");
    lines.push("");
    report.entries.forEach((e, i) => lines.push(line(e, i)));
  }
  lines.push("");
  lines.push(
    `Setup: interactions ${CRITERIA.zMin}+ standard deviations above the coin's own ` +
      `30-day norm, under ${Math.round(CRITERIA.spamMax * 100)}% spam, price flat within ` +
      `${CRITERIA.flatPriceMax * 100}%.`
  );
  lines.push(
    `Historically this setup beat BTC over the next ${BASELINE.horizonDays} days ` +
      `${(BASELINE.organic * 100).toFixed(0)}% of the time, versus ` +
      `${(BASELINE.ordinary * 100).toFixed(0)}% for an ordinary coin-day. ` +
      `An odds shift, not a prediction. Not advice.`
  );
  lines.push("");
  lines.push(`Scanned ${report.scanned} coins, checked ${report.checked} in detail.`);
  lines.push("Data: LunarCrush");
  if (promoCode) lines.push(`Affiliate code ${promoCode} gets 15% off at checkout`);
  return lines.join("\n");
}
