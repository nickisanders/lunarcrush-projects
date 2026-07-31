import assert from "node:assert/strict";
import { test } from "node:test";
import { computeRotation, lastCompleteDays } from "../src/rotation.js";
import type { SeriesRow } from "../src/types.js";

function series(days: number, perDay: (i: number) => number): SeriesRow[] {
  return Array.from({ length: days }, (_, i) => ({
    time: i,
    interactions: perDay(i),
    sentiment: 70,
  }));
}

test("lastCompleteDays drops the trailing partial day", () => {
  const s = series(20, (i) => 100 + i);
  const window = lastCompleteDays(s, 14);
  assert.equal(window.length, 14);
  // Excludes the final row (partial day)
  assert.equal(window[window.length - 1].interactions, 100 + 18);
});

test("lastCompleteDays returns empty when history is too short", () => {
  assert.deepEqual(lastCompleteDays(series(10, () => 100), 14), []);
});

test("share deltas sum to ~0 across narratives", () => {
  const data = {
    a: series(20, (i) => (i >= 12 ? 2000 : 1000)),
    b: series(20, () => 1000),
    c: series(20, (i) => (i >= 12 ? 500 : 1000)),
  };
  const result = computeRotation(data, { a: "A", b: "B", c: "C" });
  const sum = result.reduce((acc, n) => acc + n.shareDeltaPp, 0);
  assert.ok(Math.abs(sum) < 1e-9, `expected ~0, got ${sum}`);
});

test("a narrative gaining volume gains share and is sorted first", () => {
  const data = {
    gaining: series(20, (i) => (i >= 12 ? 3000 : 1000)),
    flat: series(20, () => 1000),
  };
  const result = computeRotation(data, { gaining: "Gaining", flat: "Flat" });
  assert.equal(result[0].key, "gaining");
  assert.ok(result[0].shareDeltaPp > 0);
  assert.ok(result[0].wowPct > 100);
  assert.ok(result[1].shareDeltaPp < 0); // flat loses share when the other grows
});

test("narratives with short history are excluded, not zero-filled", () => {
  const data = {
    ok: series(20, () => 1000),
    young: series(5, () => 99999),
  };
  const result = computeRotation(data, { ok: "OK", young: "Young" });
  assert.deepEqual(result.map((n) => n.key), ["ok"]);
});
