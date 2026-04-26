#!/usr/bin/env node
/**
 * Snapshot the current visitor count from abacus.jasoncameron.dev into
 * src/data/views.json so the footer always has a real number to render
 * even when the live API is unreachable.
 *
 * Runs as `npm run prebuild` before `astro build`.
 *
 * Failure policy: if the fetch fails, KEEP the existing snapshot.
 * This way a transient API outage never resets the counter to zero.
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");
const OUT_PATH = resolve(REPO_ROOT, "src/data/views.json");

const NAMESPACE = "sukhdeepsingh-eu";
const KEY = "total";
const URL = `https://abacus.jasoncameron.dev/get/${NAMESPACE}/${KEY}`;

const ts = new Date().toISOString();

let previous = null;
if (existsSync(OUT_PATH)) {
  try {
    previous = JSON.parse(readFileSync(OUT_PATH, "utf8"));
  } catch {
    /* ignore corrupt file, will overwrite below */
  }
}

async function fetchWithTimeout(url, ms = 8000) {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), ms);
  try {
    return await fetch(url, { signal: ac.signal });
  } finally {
    clearTimeout(timer);
  }
}

try {
  const r = await fetchWithTimeout(URL);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const data = await r.json();
  const value = typeof data?.value === "number" ? data.value : null;

  if (value === null) {
    throw new Error(`unexpected payload: ${JSON.stringify(data).slice(0, 120)}`);
  }

  // Don't accept a smaller value than the snapshot we already have.
  // Counter APIs occasionally reset; we don't want one bad fetch to wipe progress.
  let final = value;
  if (previous?.value && previous.value > value) {
    console.warn(
      `[snapshot-views] API returned ${value}, previous snapshot was ${previous.value}. Keeping the larger value.`,
    );
    final = previous.value;
  }

  writeFileSync(
    OUT_PATH,
    JSON.stringify(
      {
        value: final,
        source: "abacus.jasoncameron.dev",
        fetched_at: ts,
        previous_value: previous?.value ?? null,
      },
      null,
      2,
    ) + "\n",
  );
  console.log(`[snapshot-views] ✓ ${final} (was ${previous?.value ?? "—"})`);
} catch (err) {
  console.warn(`[snapshot-views] ⚠ fetch failed: ${err?.message ?? err}`);
  if (previous) {
    console.warn(`[snapshot-views] keeping previous snapshot: ${previous.value}`);
  } else {
    // First-ever run with no API access — write a placeholder so build doesn't fail
    writeFileSync(
      OUT_PATH,
      JSON.stringify(
        { value: 0, source: "placeholder", fetched_at: ts, previous_value: null },
        null,
        2,
      ) + "\n",
    );
    console.warn(`[snapshot-views] wrote placeholder views.json (value=0)`);
  }
}
