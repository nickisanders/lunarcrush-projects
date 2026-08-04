import { existsSync, readFileSync } from "node:fs";
import type { DetectorReport, SeriesRow } from "./types.js";

export interface WatchTarget {
  symbol: string;
  score: number;
  spikeDate: string; // YYYY-MM-DD
}

/** Pick past high-scoring specimens due for a "what happened next" check:
 * score >= minScore, spiked 3-5 days ago, chart not already produced. */
export function pickDecayWatch(
  historyLines: string[],
  now: Date,
  outExists: (t: WatchTarget) => boolean,
  minScore = 80,
  minDays = 3,
  maxDays = 5
): WatchTarget[] {
  const targets = new Map<string, WatchTarget>();
  for (const line of historyLines) {
    let report: DetectorReport;
    try {
      report = JSON.parse(line) as DetectorReport;
    } catch {
      continue;
    }
    const spikeDate = report.generatedAt.slice(0, 10);
    const age = (now.getTime() - new Date(spikeDate + "T00:00:00Z").getTime()) / 86400_000;
    if (age < minDays || age > maxDays) continue;
    for (const v of report.verdicts) {
      if (v.score >= minScore) {
        targets.set(`${v.symbol}:${spikeDate}`, { symbol: v.symbol, score: v.score, spikeDate });
      }
    }
  }
  return [...targets.values()].filter((t) => !outExists(t));
}

export interface DecayResult {
  target: WatchTarget;
  bars: Array<{ label: string; interactions: number; isSpike: boolean }>;
  /** interactions on the latest complete day vs the spike day, percent */
  retainedPct: number;
}

/** Build the decay picture from a daily series: 4 days before the spike
 * through the latest complete day. */
export function measureDecay(target: WatchTarget, series: SeriesRow[]): DecayResult | null {
  const complete = series.slice(0, -1); // trailing day is partial
  const spikeIdx = complete.findIndex(
    (r) => new Date(r.time * 1000).toISOString().slice(0, 10) === target.spikeDate
  );
  if (spikeIdx < 4 || spikeIdx >= complete.length - 1) return null;
  const window = complete.slice(spikeIdx - 4, complete.length);
  const bars = window.map((r, i) => ({
    label: new Date(r.time * 1000).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    }),
    interactions: r.interactions ?? 0,
    isSpike: i === 4,
  }));
  const spike = bars[4].interactions;
  const latest = bars[bars.length - 1].interactions;
  if (spike <= 0) return null;
  return { target, bars, retainedPct: (latest / spike) * 100 };
}

export function readHistoryLines(path: string): string[] {
  if (!existsSync(path)) return [];
  return readFileSync(path, "utf8").split("\n").filter(Boolean);
}
