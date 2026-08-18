import assert from "node:assert/strict";
import { test } from "node:test";
import {
  burstShare24h,
  interactionZScore,
  isInstitutionalAccount,
  isInstitutionalBroadcast,
  isMegaphone,
  manufacturedScore,
  pickCandidates,
  spamBaseline,
  spamLift,
  spamRatio,
  top1CreatorShare,
  top3CreatorShare,
  topCreatorName,
  verdictFor,
} from "../src/classify.js";
import { measureDecay, pickDecayWatch } from "../src/decaywatch.js";
import type { CoinRow, SeriesRow } from "../src/types.js";

function flatSeries(days: number, base: number, todayMult = 1): SeriesRow[] {
  return Array.from({ length: days }, (_, i) => ({
    time: i,
    interactions: i === days - 1 ? base * todayMult : base,
    posts_created: 100,
    spam: 20,
  }));
}

test("z-score is high for a genuine spike and ~0 for flat activity", () => {
  // Slight noise so the trailing window has nonzero variance
  const noisy = flatSeries(35, 1000).map((r, i) => ({
    ...r,
    interactions: r.interactions + (i % 2 === 0 ? 50 : -50),
  }));
  const spiked = [...noisy.slice(0, -1), { ...noisy.at(-1)!, interactions: 40_000 }];
  assert.ok(interactionZScore(spiked) > 3);
  assert.ok(Math.abs(interactionZScore(noisy)) < 1.5);
});

test("z-score returns 0 when history is too short", () => {
  assert.equal(interactionZScore(flatSeries(10, 1000, 50)), 0);
});

test("spam ratio ignores today's partial row and reads the last complete day", () => {
  const s = flatSeries(35, 1000);
  s[s.length - 2] = { time: 98, interactions: 5000, posts_created: 200, spam: 150 };
  // Today mid-accumulation: spam and posts_created fill at different rates and
  // the ratio reads far too high. It must not be used.
  s[s.length - 1] = { time: 99, interactions: 900, posts_created: 10, spam: 95 };
  assert.equal(spamRatio(s), 0.75);
});

test("creator concentration: botnet vs broad crowd", () => {
  const botnet = [
    { interactions_24h: 60_000 },
    { interactions_24h: 20_000 },
    { interactions_24h: 10_000 },
    ...Array.from({ length: 20 }, () => ({ interactions_24h: 500 })),
  ];
  const crowd = Array.from({ length: 40 }, () => ({ interactions_24h: 2500 }));
  assert.ok(top3CreatorShare(botnet) > 0.85);
  assert.ok(top3CreatorShare(crowd) < 0.2);
});

test("manufactured score separates the archetypes", () => {
  const manufactured = manufacturedScore({
    zScore: 5,
    spamRatio: 0.85,
    spamRatioRaw: 2.2,
    spamBaseline: 0.6,
    top3CreatorShare: 0.8,
    sentiment: 95,
  });
  const organic = manufacturedScore({
    zScore: 5,
    spamRatio: 0.1,
    spamRatioRaw: 0.1,
    spamBaseline: 0.12,
    top3CreatorShare: 0.15,
    sentiment: 65,
  });
  assert.ok(manufactured >= 60, `expected manufactured >= 60, got ${manufactured}`);
  assert.ok(organic < 30, `expected organic < 30, got ${organic}`);
  assert.equal(verdictFor(manufactured), "manufactured");
  assert.equal(verdictFor(organic), "organic");
});

test("spam lift rewards fresh spam waves, not chronic baselines", () => {
  // Chronically botted coin at its usual level: no lift
  assert.equal(spamLift(1.0, 1.0), 0);
  // Spam tripled vs baseline: full lift
  assert.equal(spamLift(3.0, 1.0), 1);
  // Clean coin with a sudden 2x wave: half lift
  assert.equal(spamLift(0.4, 0.2), 0.5);
});

test("spam baseline is the trailing median of the raw ratio, excluding today", () => {
  const rows = Array.from({ length: 35 }, (_, i) => ({
    time: i,
    interactions: 1000,
    posts_created: 100,
    spam: i === 34 ? 900 : 50, // today spikes to 9.0 raw, history at 0.5
  }));
  const base = spamBaseline(rows);
  assert.ok(Math.abs(base - 0.5) < 1e-9, `expected 0.5, got ${base}`);
});

test("institutional broadcast: an exchange or alert feed IS the spike", () => {
  // The real $USDT case from Aug 6: MEXC alone was 89% of 11.6M interactions,
  // spam 0.59 — too spammy for the megaphone rule, not a botnet either.
  const usdt = {
    zScore: 2.1, spamRatio: 0.59, spamRatioRaw: 0.59, spamBaseline: 0.46,
    top3CreatorShare: 0.96, top1CreatorShare: 0.89, topCreatorName: "MEXC", sentiment: 70,
  };
  assert.equal(isInstitutionalBroadcast(usdt), true);
  assert.equal(isMegaphone(usdt), false, "megaphone rule should still miss it; that was the gap");

  // Same shape, but the dominant account is an unknown handle: fall back to
  // the generic case rather than claiming an institution we can't identify.
  assert.equal(isInstitutionalBroadcast({ ...usdt, topCreatorName: "some_random_kol" }), false);

  // A known feed that isn't actually dominant is just one voice among many.
  assert.equal(
    isInstitutionalBroadcast({ ...usdt, top1CreatorShare: 0.2, topCreatorName: "whale_alert" }),
    false
  );
});

test("institutional handles match exactly, not by substring", () => {
  assert.equal(isInstitutionalAccount("whale_alert"), true, "separators normalize away");
  assert.equal(isInstitutionalAccount("MEXC_ID"), true);
  assert.equal(isInstitutionalAccount("Gate"), true);
  assert.equal(isInstitutionalAccount("stargate_finance"), false, "no substring false positives");
  assert.equal(isInstitutionalAccount("binance_killer"), false);
  assert.equal(isInstitutionalAccount(undefined), false);
});

test("top1 creator share separates one dominant account from three splitting it", () => {
  const dominant = [{ interactions_24h: 900 }, { interactions_24h: 60 }, { interactions_24h: 40 }];
  const split = [{ interactions_24h: 340 }, { interactions_24h: 330 }, { interactions_24h: 330 }];
  assert.ok(top1CreatorShare(dominant) > 0.85);
  assert.ok(top1CreatorShare(split) < 0.4);
  // Both look identical to the top-3 metric, which is why top1 exists
  assert.equal(top3CreatorShare(dominant), 1);
  assert.equal(top3CreatorShare(split), 1);
  assert.equal(topCreatorName([{ interactions_24h: 5, creator_name: "small" }, { interactions_24h: 50, creator_name: "big" }]), "big");
});

test("megaphone: near-total concentration with low spam", () => {
  const megaphone = {
    zScore: 3, spamRatio: 0.2, spamRatioRaw: 0.2, spamBaseline: 0.2,
    top3CreatorShare: 0.97, sentiment: 90,
  };
  const botnet = { ...megaphone, spamRatio: 0.8, spamRatioRaw: 2.0 };
  assert.equal(isMegaphone(megaphone), true);
  assert.equal(isMegaphone(botnet), false);
});

test("burst share: bursty crowd vs scheduled campaign, over complete hours", () => {
  const hour = (interactions: number, i: number) => ({ time: i, interactions });
  // 25 rows: last is the partial hour and must be ignored
  const bursty = [
    ...Array.from({ length: 21 }, (_, i) => hour(100, i)),
    hour(5000, 21),
    hour(4000, 22),
    hour(3000, 23),
    hour(99999, 24), // partial hour, ignored
  ];
  const flat = Array.from({ length: 25 }, (_, i) => hour(1000, i));
  assert.ok(burstShare24h(bursty)! > 0.8);
  assert.ok(burstShare24h(flat)! < 0.15);
  assert.equal(burstShare24h(flat.slice(0, 10)), null); // too little history
});

test("decay-watch picks 3-5 day old high scorers, once", () => {
  const mk = (date: string, symbol: string, score: number) =>
    JSON.stringify({
      generatedAt: `${date}T13:30:00.000Z`,
      scanned: 1000,
      spiking: 1,
      verdicts: [{ symbol, score, verdict: "manufactured", evidence: {}, megaphone: false }],
    });
  const history = [
    mk("2026-08-01", "OLDIE", 95), // 6 days old at "now": outside window
    mk("2026-08-03", "TARGET", 88), // 4 days old: in window
    mk("2026-08-03", "LOWSCORE", 60), // in window but below threshold
    mk("2026-08-06", "FRESH", 99), // 1 day old: too soon
  ];
  const now = new Date("2026-08-07T14:00:00Z");
  const picked = pickDecayWatch(history, now, () => false);
  assert.deepEqual(picked.map((t) => t.symbol), ["TARGET"]);
  const skipped = pickDecayWatch(history, now, () => true); // chart already exists
  assert.deepEqual(skipped, []);
});

test("measureDecay anchors on the spike day and drops the partial tail", () => {
  const day = 86400;
  const t0 = Date.UTC(2026, 7, 3) / 1000; // Aug 3
  const series = Array.from({ length: 10 }, (_, i) => ({
    time: t0 + (i - 6) * day,
    interactions: i === 6 ? 2_000_000 : 100_000,
  }));
  const result = measureDecay({ symbol: "X", score: 90, spikeDate: "2026-08-03" }, series);
  assert.ok(result);
  assert.equal(result!.bars[4].isSpike, true);
  assert.equal(result!.bars[4].interactions, 2_000_000);
  // 4 pre-spike + spike + 2 post (the partial trailing row is dropped)
  assert.equal(result!.bars.length, 7);
  assert.equal(result!.retainedPct, 5);
});

test("candidate picker enforces eligibility floors", () => {
  const coin = (over: Partial<CoinRow>): CoinRow => ({
    id: 1,
    symbol: "T",
    name: "T",
    topic: "t",
    market_cap: 1e9,
    market_cap_rank: 50,
    volume_24h: 1e8,
    interactions_24h: 100_000,
    alt_rank: 100,
    alt_rank_previous: 500,
    sentiment: 60,
    ...over,
  });
  const rows = [
    coin({ id: 1, symbol: "OK" }),
    coin({ id: 2, symbol: "TINY", market_cap: 1e6 }),
    coin({ id: 3, symbol: "ILLIQUID", volume_24h: 1000 }),
    coin({ id: 4, symbol: "QUIET", interactions_24h: 10 }),
  ];
  const picked = pickCandidates(rows, 10).map((r) => r.symbol);
  assert.deepEqual(picked, ["OK"]);
});
