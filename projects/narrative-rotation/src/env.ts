import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ENV_CANDIDATES = [
  join(HERE, "..", ".env"),
  join(HERE, "..", "..", "altrank-movers", ".env"),
];

/** Minimal .env loader; falls back to the altrank-movers .env for the shared key. */
export function loadEnv(): void {
  for (const path of ENV_CANDIDATES) {
    let raw: string;
    try {
      raw = readFileSync(path, "utf8");
    } catch {
      continue;
    }
    for (const line of raw.split("\n")) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      const [, key, value] = m;
      if (process.env[key] === undefined && value !== "") {
        process.env[key] = value.replace(/^["']|["']$/g, "");
      }
    }
  }
}
