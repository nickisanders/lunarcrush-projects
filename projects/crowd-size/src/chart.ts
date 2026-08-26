import sharp from "sharp";
import type { CoinCrowd, CrowdReport } from "./types.js";

const C = { bg: "#0d1117", text: "#e6edf3", sub: "#8b949e", track: "#21262d",
  grid: "#30363d", green: "#3fb950", amber: "#d29922", red: "#f85149" };
const FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Wide crowds green, narrow ones red. The thresholds group the eye; the
 * number is the claim. */
function color(n: number | null): string {
  if (n === null || n >= 50) return C.green;
  if (n >= 15) return C.amber;
  return C.red;
}

/** Log scale, because the range runs from 3 accounts to over 200 and a linear
 * axis would flatten every narrow coin into the same invisible stub. */
export function renderChartSvg(report: CrowdReport): string {
  const coins = report.coins.filter((c) => c.accountsToHalf !== null);
  const W = 1200;
  const TOP = 230;
  const ROW = 40;
  const BAR_X = 250;
  const BAR_W = 760;
  const H = TOP + coins.length * ROW + 170;
  const max = Math.max(...coins.map((c) => c.accountsToHalf ?? 1), 10);
  const scale = (n: number) => (Math.log10(n) / Math.log10(max)) * BAR_W;

  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${C.text}">How many people is a crypto crowd?</text>`,
    `<text x="60" y="120" font-size="23" fill="${C.sub}">accounts needed to make up half of everything said about a coin in 24 hours</text>`,
    `<text x="60" y="156" font-size="23" fill="${C.sub}">fewer accounts means fewer people are the conversation. log scale.</text>`,
  ];

  for (const tick of [1, 3, 10, 30, 100, 300].filter((t) => t <= max)) {
    const x = BAR_X + scale(tick);
    parts.push(
      `<line x1="${x.toFixed(0)}" y1="${TOP - 22}" x2="${x.toFixed(0)}" y2="${TOP + coins.length * ROW - 14}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${x.toFixed(0)}" y="${TOP - 32}" font-size="18" fill="${C.sub}" text-anchor="middle">${tick}</text>`
    );
  }

  coins.forEach((c: CoinCrowd, i: number) => {
    const y = TOP + i * ROW;
    const n = c.accountsToHalf ?? 1;
    const w = Math.max(4, scale(n));
    const col = color(c.accountsToHalf);
    parts.push(
      `<text x="${BAR_X - 20}" y="${y + 8}" font-size="23" font-weight="600" fill="${C.text}" text-anchor="end">${esc(c.symbol)}</text>`,
      `<rect x="${BAR_X}" y="${y - 12}" width="${w.toFixed(0)}" height="24" rx="6" fill="${col}"/>`,
      `<text x="${BAR_X + w + 14}" y="${y + 8}" font-size="21" font-weight="700" fill="${col}">${n}</text>`
    );
  });

  const footY = TOP + coins.length * ROW + 52;
  const widest = coins[0];
  const narrowest = coins[coins.length - 1];
  parts.push(
    `<text x="60" y="${footY}" font-size="23" fill="${C.text}">$${esc(widest.symbol)} takes ${widest.accountsToHalf} accounts to reach half. $${esc(narrowest.symbol)} takes ${narrowest.accountsToHalf}.</text>`,
    `<text x="60" y="${footY + 36}" font-size="21" fill="${C.sub}">Counts posts and their engagement, not people: one account can be a team, and automated posting is included.</text>`,
    `<text x="60" y="${footY + 66}" font-size="21" fill="${C.sub}">Coins whose crowd is wider than the API will list are left off rather than guessed at.</text>`,
    `<text x="60" y="${footY + 104}" font-size="19" fill="${C.sub}">Data: LunarCrush · ${esc(report.generatedAt.slice(0, 10))} · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}

export function svgToPng(svg: string): Promise<Buffer> {
  return sharp(Buffer.from(svg), { density: 144 }).png().toBuffer();
}

/** Followers against impact for every top-10 voice, both axes log.
 *
 * A scatter rather than bars because the message is the absence of a
 * relationship: a cloud with no slope says "these are unrelated" faster than
 * any correlation coefficient does.
 */
export function renderReachChartSvg(
  voices: { coin: string; rank: number; name: string; followers: number; interactions: number }[],
  s: { rSquared: number; underTenThousand: number; voices: number; overOneMillion: number }
): string {
  const W = 1200;
  const H = 860;
  const L = 130;
  const R = 60;
  const T = 235;
  const B = 240;
  const PW = W - L - R;
  const PH = H - T - B;
  const decades = [2, 3, 4, 5, 6, 7]; // 100 .. 10M followers
  const yDecades = [2, 3, 4, 5, 6, 7];
  const x = (f: number) => L + ((Math.log10(f) - decades[0]) / (decades.at(-1)! - decades[0])) * PW;
  const y = (i: number) => T + PH - ((Math.log10(i) - yDecades[0]) / (yDecades.at(-1)! - yDecades[0])) * PH;
  const label = (e: number) => (e >= 6 ? `${10 ** (e - 6)}M` : e >= 3 ? `${10 ** (e - 3)}k` : `${10 ** e}`);

  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">`,
    `<rect width="${W}" height="${H}" fill="${C.bg}"/>`,
    `<text x="60" y="76" font-size="38" font-weight="700" fill="${C.text}">Followers barely predict who drives the conversation</text>`,
    `<text x="60" y="120" font-size="23" fill="${C.sub}">every account in the top 10 of a major coin's conversation, ${voices.length} of them across 37 coins</text>`,
    `<text x="60" y="156" font-size="23" fill="${C.sub}">if followers decided impact, this would be a line. both axes are log scale.</text>`,
  ];
  for (const e of decades) {
    parts.push(
      `<line x1="${x(10 ** e).toFixed(0)}" y1="${T}" x2="${x(10 ** e).toFixed(0)}" y2="${T + PH}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${x(10 ** e).toFixed(0)}" y="${T + PH + 38}" font-size="19" fill="${C.sub}" text-anchor="middle">${label(e)}</text>`
    );
  }
  for (const e of yDecades) {
    parts.push(
      `<line x1="${L}" y1="${y(10 ** e).toFixed(0)}" x2="${L + PW}" y2="${y(10 ** e).toFixed(0)}" stroke="${C.grid}" stroke-width="1"/>`,
      `<text x="${L - 16}" y="${(y(10 ** e) + 7).toFixed(0)}" font-size="19" fill="${C.sub}" text-anchor="end">${label(e)}</text>`
    );
  }
  parts.push(
    `<text x="${L + PW / 2}" y="${T + PH + 76}" font-size="22" fill="${C.text}" text-anchor="middle">followers</text>`,
    `<text x="34" y="${T + PH / 2}" font-size="22" fill="${C.text}" text-anchor="middle" transform="rotate(-90 34 ${T + PH / 2})">interactions in 24h</text>`
  );
  for (const v of voices) {
    const small = v.followers < 10_000;
    parts.push(
      `<circle cx="${x(v.followers).toFixed(1)}" cy="${y(v.interactions).toFixed(1)}" r="6" fill="${small ? C.amber : C.sub}" opacity="${small ? 0.9 : 0.5}"/>`
    );
  }
  // The single most extreme case earns a label; the rest speak as a cloud.
  const star = [...voices].sort((a, b) => b.interactions / b.followers - a.interactions / a.followers)[0];
  if (star) {
    parts.push(
      `<circle cx="${x(star.followers).toFixed(1)}" cy="${y(star.interactions).toFixed(1)}" r="10" fill="none" stroke="${C.red}" stroke-width="3"/>`,
      `<text x="${(x(star.followers) + 22).toFixed(0)}" y="${(y(star.interactions) - 6).toFixed(0)}" font-size="21" font-weight="700" fill="${C.red}">${esc(star.name)}</text>`,
      `<text x="${(x(star.followers) + 22).toFixed(0)}" y="${(y(star.interactions) + 20).toFixed(0)}" font-size="19" fill="${C.sub}">${star.followers.toLocaleString()} followers · #${star.rank} voice on $${esc(star.coin)}</text>`
    );
  }
  parts.push(
    `<text x="60" y="${H - 116}" font-size="23" fill="${C.text}">Follower count explains ${(s.rSquared * 100).toFixed(0)}% of the variation. ${((s.underTenThousand / s.voices) * 100).toFixed(0)}% of these accounts have under 10,000 followers.</text>`,
    `<text x="60" y="${H - 82}" font-size="21" fill="${C.sub}">Amber dots are those small accounts. Only ${((s.overOneMillion / s.voices) * 100).toFixed(0)}% of the loudest voices in crypto have over a million followers.</text>`,
    `<text x="60" y="${H - 52}" font-size="21" fill="${C.sub}">These are accounts that already landed, so this says who the loud accounts are, not that small accounts get more reach in general.</text>`,
    `<text x="60" y="${H - 20}" font-size="19" fill="${C.sub}">Data: LunarCrush · method and code in the repo</text>`,
    `</svg>`
  );
  return parts.join("\n");
}
