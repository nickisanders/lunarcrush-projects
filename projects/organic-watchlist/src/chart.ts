import { BASELINE } from "./watchlist.js";
import type { WatchlistReport } from "./types.js";

const COLORS = {
  bg: "#0d1117",
  text: "#e6edf3",
  sub: "#8b949e",
  track: "#21262d",
  green: "#3fb950",
  dim: "#6e7681",
};
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function renderChartSvg(report: WatchlistReport): string {
  const W = 1200;
  const PAD = 55;
  const HEADER = 190;
  const rowH = 76;
  const rows = report.entries.slice(0, 8);
  const H = rows.length === 0
    ? HEADER + 200 + report.nearMisses.length * 44 + 110
    : HEADER + rows.length * rowH + 110;
  const maxMult = Math.max(2, ...rows.map((e) => e.multiple));
  const barMax = W - PAD * 2 - 430;

  let body = "";
  let y = HEADER;
  for (const e of rows) {
    const w = Math.max(8, Math.round((e.multiple / maxMult) * barMax));
    const spam = Math.round(e.spam * 100);
    const move = e.percentChange24h >= 0 ? `+${e.percentChange24h.toFixed(1)}` : e.percentChange24h.toFixed(1);
    body += `
    <text x="${PAD}" y="${y + 34}" font-size="27" font-weight="600" fill="${COLORS.text}">$${esc(e.symbol)}</text>
    <text x="${PAD}" y="${y + 60}" font-size="19" fill="${COLORS.sub}">${spam}% spam · price ${move}%</text>
    <rect x="${PAD + 190}" y="${y + 14}" width="${barMax}" height="32" rx="8" fill="${COLORS.track}"/>
    <rect x="${PAD + 190}" y="${y + 14}" width="${w}" height="32" rx="8" fill="${COLORS.green}"/>
    <text x="${PAD + 205 + barMax}" y="${y + 39}" font-size="27" font-weight="700" fill="${COLORS.green}">${e.multiple.toFixed(0)}x</text>
    <text x="${PAD + 285 + barMax}" y="${y + 39}" font-size="20" fill="${COLORS.sub}">normal chatter</text>`;
    y += rowH;
  }
  if (rows.length === 0) {
    body = `<text x="${PAD}" y="${HEADER + 40}" font-size="32" font-weight="600" fill="${COLORS.text}">Nothing qualifies today.</text>
    <text x="${PAD}" y="${HEADER + 84}" font-size="24" fill="${COLORS.dim}">This setup shows up about one day in six. That is the point of waiting for it.</text>`;
    let ny = HEADER + 150;
    if (report.nearMisses.length > 0) {
      body += `<text x="${PAD}" y="${ny}" font-size="22" fill="${COLORS.sub}">Closest, and why each missed:</text>`;
      ny += 44;
      for (const n of report.nearMisses) {
        body += `
    <text x="${PAD}" y="${ny}" font-size="27" font-weight="600" fill="${COLORS.text}">$${esc(n.symbol)}</text>
    <text x="${PAD + 150}" y="${ny}" font-size="25" fill="${COLORS.dim}">${esc(n.failed)}</text>`;
        ny += 44;
      }
    }
  }

  const hit = (BASELINE.organic * 100).toFixed(0);
  const base = (BASELINE.ordinary * 100).toFixed(0);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
  <rect width="${W}" height="${H}" fill="${COLORS.bg}"/>
  <text x="${PAD}" y="58" font-size="36" font-weight="700" fill="${COLORS.text}">Organic attention, price hasn't moved</text>
  <text x="${PAD}" y="98" font-size="24" fill="${COLORS.sub}">${fmtDate(report.generatedAt)} · real conversation spikes, low spam, flat price</text>
  <text x="${PAD}" y="140" font-size="21" fill="${COLORS.green}">Historically this setup beat BTC over the next 3 days ${hit}% of the time.</text>
  <text x="${PAD}" y="168" font-size="21" fill="${COLORS.sub}">An ordinary coin-day does it ${base}% of the time. An odds shift, not a prediction.</text>
  ${body}
  <text x="${PAD}" y="${H - 58}" font-size="19" fill="${COLORS.sub}">Scanned ${report.scanned} coins · criteria fixed to the published backtest · not financial advice</text>
  <text x="${PAD}" y="${H - 28}" font-size="19" fill="${COLORS.sub}">Data: LunarCrush</text>
</svg>`;
}

export async function svgToPng(svg: string): Promise<Buffer> {
  const { default: sharp } = await import("sharp");
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}

/** Decomposition of a resolved pick: how much of the move was the market, and
 * how much was the thing the signal actually claims.
 *
 * Drawn as one stacked bar against Bitcoin's own bar, because the honest
 * reading of a winning call in a rising market is that most of the number was
 * beta. The spread is the only part the backtest ever claimed.
 */
export function renderTrackChartSvg(r: {
  symbol: string;
  date: string;
  coinReturn: number;
  btcReturn: number;
  spread: number;
}): string {
  const W = 1200;
  const H = 780;
  const TOP = 250;
  const CH = 330;
  const BW = 200;
  const top = Math.max(r.coinReturn, r.btcReturn) * 1.25;
  const y = (v: number) => TOP + CH - (v / top) * CH;
  const xBtc = 260;
  const xCoin = 660;
  const marketH = CH - (y(r.btcReturn) - TOP);
  const spreadH = CH - (y(r.coinReturn) - TOP) - marketH;
  const pct = (v: number) => `${v >= 0 ? "+" : ""}${(v * 100).toFixed(1)}%`;

  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${COLORS.bg}"/>`,
    `<text x="60" y="72" font-size="36" font-weight="700" fill="${COLORS.text}">My pick won. Most of that was not the pick.</text>`,
    `<text x="60" y="112" font-size="23" fill="${COLORS.sub}">$${esc(r.symbol)}, flagged ${esc(r.date)}, measured over the 3 days the signal actually covers</text>`,
    `<line x1="150" y1="${TOP + CH}" x2="${W - 90}" y2="${TOP + CH}" stroke="${COLORS.track}" stroke-width="2"/>`,
    `<rect x="${xBtc}" y="${y(r.btcReturn)}" width="${BW}" height="${marketH}" rx="8" fill="${COLORS.dim}"/>`,
    `<text x="${xBtc + BW / 2}" y="${y(r.btcReturn) - 18}" font-size="32" font-weight="700" fill="${COLORS.dim}" text-anchor="middle">${pct(r.btcReturn)}</text>`,
    `<text x="${xBtc + BW / 2}" y="${TOP + CH + 42}" font-size="24" fill="${COLORS.text}" text-anchor="middle">Bitcoin</text>`,
    `<rect x="${xCoin}" y="${y(r.btcReturn)}" width="${BW}" height="${marketH}" rx="8" fill="${COLORS.dim}"/>`,
    `<rect x="${xCoin}" y="${y(r.coinReturn)}" width="${BW}" height="${spreadH}" rx="8" fill="${COLORS.green}"/>`,
    `<text x="${xCoin + BW / 2}" y="${y(r.coinReturn) - 18}" font-size="32" font-weight="700" fill="${COLORS.green}" text-anchor="middle">${pct(r.coinReturn)}</text>`,
    `<text x="${xCoin + BW / 2}" y="${TOP + CH + 42}" font-size="24" fill="${COLORS.text}" text-anchor="middle">$${esc(r.symbol)}</text>`,
    `<text x="${xCoin + BW + 30}" y="${y(r.coinReturn) + spreadH / 2 + 8}" font-size="26" font-weight="700" fill="${COLORS.green}">${pct(r.spread)} the signal</text>`,
    `<text x="${xCoin + BW + 30}" y="${y(r.btcReturn) + marketH / 2 + 8}" font-size="26" font-weight="700" fill="${COLORS.dim}">the market</text>`,
    `<text x="60" y="${H - 108}" font-size="23" fill="${COLORS.text}">The coin rose 25.8%. Bitcoin rose 19.2% in the same window with no signal required.</text>`,
    `<text x="60" y="${H - 74}" font-size="21" fill="${COLORS.sub}">The green sliver is the entire claim: a coin beating BTC over 3 days. Everything below it was the rally.</text>`,
    `<text x="60" y="${H - 44}" font-size="21" fill="${COLORS.sub}">One pick. The measured edge is 49% vs 42%, so roughly half of these lose. This is a result, not evidence.</text>`,
    `<text x="60" y="${H - 16}" font-size="19" fill="${COLORS.sub}">Data: LunarCrush · method and code in the repo</text>`,
    `</svg>`,
  ].join("\n");
}

/** Break a caption on word boundaries. Slicing at a character count split
 * "~1,600" into "~1,60" and "0." on the first render. */
function wrap(text: string, width: number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of text.split(" ")) {
    if (line && (line + " " + word).length > width) {
      lines.push(line);
      line = word;
    } else {
      line = line ? `${line} ${word}` : word;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/** Anatomy of a rejected spike: what the setup saw, and what killed it.
 *
 * Two panels because the story is the contrast. On the left the coin passes
 * every published leg, which is exactly why it is dangerous. On the right the
 * two checks that show the conversation was never about the coin.
 */
export function renderCollisionChartSvg(
  miss: { symbol: string; z: number; spam: number; percentChange24h: number;
          collision?: { multiple: number; interactions24h: number; contributors?: number;
                        perContributor?: number; bareTopic?: string; bareInteractions?: number } },
  generatedAt: string
): string {
  const c = miss.collision;
  if (!c) return "";
  const W = 1300, H = 760;
  const RED = "#f85149";
  const short = (n: number) =>
    n >= 1e9 ? `${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `${(n / 1e6).toFixed(1)}M`
    : n >= 1e3 ? `${(n / 1e3).toFixed(0)}k` : String(Math.round(n));

  const pass = [
    [`${c.multiple.toFixed(0)}x its normal chatter`, `z-score ${miss.z.toFixed(1)}, threshold is 3.0`],
    [`${(miss.spam * 100).toFixed(0)}% spam`, "under the 50% ceiling"],
    [`price ${miss.percentChange24h >= 0 ? "+" : ""}${miss.percentChange24h.toFixed(1)}%`, "flat, within the 2% band"],
    [`${short(c.interactions24h)} interactions`, "a real social baseline"],
  ];
  const fail: [string, string][] = [];
  if (c.perContributor !== undefined) {
    fail.push([`${Math.round(c.perContributor).toLocaleString()} interactions per person`,
               `${(c.contributors ?? 0).toLocaleString()} contributors made all of it. A genuine spike day runs ~1,600.`]);
  }
  if (c.bareInteractions) {
    fail.push([`the word "${esc(c.bareTopic ?? "")}" drew ${short(c.bareInteractions)}`,
               `${Math.round(c.bareInteractions / c.interactions24h)}x the coin's own traffic, on the same day`]);
  }

  const parts = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${COLORS.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${COLORS.text}">My scanner's best signal in a month was a word</text>`,
    `<text x="60" y="120" font-size="23" fill="${COLORS.sub}">$${esc(miss.symbol)} cleared every published condition, then failed two checks that ask whether the conversation is about the coin</text>`,
    `<text x="70" y="200" font-size="25" font-weight="700" fill="${COLORS.green}">What the setup saw</text>`,
    `<text x="700" y="200" font-size="25" font-weight="700" fill="${RED}">What it actually was</text>`,
  ];
  pass.forEach(([head, sub], i) => {
    const y = 260 + i * 96;
    parts.push(
      `<rect x="70" y="${y - 34}" width="8" height="66" rx="4" fill="${COLORS.green}"/>`,
      `<text x="100" y="${y}" font-size="27" font-weight="700" fill="${COLORS.text}">${esc(head)}</text>`,
      `<text x="100" y="${y + 30}" font-size="20" fill="${COLORS.sub}">${esc(sub)}</text>`
    );
  });
  fail.forEach(([head, sub], i) => {
    const y = 260 + i * 130;
    parts.push(
      `<rect x="700" y="${y - 34}" width="8" height="94" rx="4" fill="${RED}"/>`,
      `<text x="730" y="${y}" font-size="27" font-weight="700" fill="${RED}">${head}</text>`,
      ...wrap(sub, 58).map((line, k) =>
        `<text x="730" y="${y + 32 + k * 26}" font-size="20" fill="${COLORS.sub}">${esc(line)}</text>`)
    );
  });
  parts.push(
    `<text x="60" y="${H - 112}" font-size="23" fill="${COLORS.text}">Rejected. Both checks now run on every coin that clears the rest of the setup.</text>`,
    `<text x="60" y="${H - 76}" font-size="21" fill="${COLORS.sub}">Either one is disqualifying, and the per-contributor test needs no extra request.</text>`,
    `<text x="60" y="${H - 46}" font-size="21" fill="${COLORS.sub}">Nothing here is a verdict on the project. A team that picked a three-letter ticker did not choose to collide with a word.</text>`,
    `<text x="60" y="${H - 16}" font-size="19" fill="${COLORS.sub}">Data: LunarCrush · ${esc(generatedAt.slice(0, 10))} · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}
