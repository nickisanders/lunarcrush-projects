# Narrative Rotation

Weekly report on where crypto's social attention moved: which narratives (DeFi, memecoins, stablecoins, gaming, ...) gained or lost share of attention week over week, plus what's on the global topic board right now.

"Narrative rotation" is usually asserted from vibes. This measures it: for each tracked LunarCrush category, pull 30 days of daily interactions, compare the last 7 complete days against the 7 before, and compute each narrative's share of tracked attention. Share deltas sum to zero by construction, so a narrative can only gain attention share by taking it from the others, which is what rotation means.

## Usage

```bash
npm install

# Without an API key
npm run weekly -- --mock

# Real run (~9 requests; key reused from ../altrank-movers/.env)
npm run weekly
```

Outputs `out/post.txt`, `out/chart.png` (diverging bars), `out/story.png` (9:16), and `out/report.json`.

The tracked set lives in `src/rotation.ts` (`NARRATIVES`). Categories that 404 are skipped with a warning, so the list is safe to tune.

## Notes

- The trailing partial day is always dropped; weeks compare complete days only.
- Share is measured within the tracked set, not against all of social media, so adding or removing a narrative changes every share number. Keep the set stable for comparable weeks.
- Sentiment is interaction-weighted; a narrative can gain attention while its mood sours, which is often the more interesting story.

## Automate it

`.github/workflows/narrative-rotation.yml` runs every Sunday at 14:00 UTC and uploads the outputs as an artifact. Requires the `LUNARCRUSH_API_KEY` secret (already set for this repo).
