/** Re-render the chart from the last saved report, without re-pulling data. */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderChartSvg, svgToPng } from "./chart.js";
import type { BotShareReport } from "./types.js";

const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "out");
const report = JSON.parse(readFileSync(join(OUT, "report.json"), "utf8")) as BotShareReport;
const svg = renderChartSvg(report);
writeFileSync(join(OUT, "chart.svg"), svg);
writeFileSync(join(OUT, "chart.png"), await svgToPng(svg));
console.log("re-rendered out/chart.svg and out/chart.png");
