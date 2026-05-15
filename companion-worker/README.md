# aplomb-clinic-cron — companion scheduled Worker

A tiny Cloudflare **Worker** that exists for one reason: Pages Functions does not support `triggers.crons`. This Worker schedules them.

Three triggers, three POSTs:

| Cron | UTC time | Target endpoint | What it does |
|---|---|---|---|
| `0  9 * * *` | 09:00 | `/cron/renewal-reminder` | Email subscribers whose next renewal is in 4–6 days |
| `15 9 * * *` | 09:15 | `/cron/review-requests`  | Email customers whose order shipped 10–30 days ago |
| `30 9 * * *` | 09:30 | `/cron/welcome-series`   | Day-3 + Day-7 newsletter touches |

All three endpoints require the `X-Cron-Secret` header, which this Worker injects automatically.

## Deploy (~5 minutes, founder)

```bash
cd companion-worker

# 1. Log in if you have not already
wrangler login

# 2. Paste the cron secret (same value as Pages env var CRON_SHARED_SECRET)
wrangler secret put CRON_SHARED_SECRET

# 3. (Optional) override the base URL if you need to point at a preview
wrangler secret put PAGES_BASE_URL      # only needed if not https://getaplomb.com

# 4. Ship it
wrangler deploy
```

Cloudflare auto-registers the schedules from `wrangler.toml`. You can verify in the dashboard under **Workers & Pages → aplomb-clinic-cron → Triggers**.

## Verify (~2 minutes)

```bash
# Local dry-run (without deploying):
wrangler dev

# In another shell, manually fire each trigger
curl -i "http://localhost:8787/__scheduled?cron=0+9+*+*+*"
curl -i "http://localhost:8787/__scheduled?cron=15+9+*+*+*"
curl -i "http://localhost:8787/__scheduled?cron=30+9+*+*+*"
```

After deploy, tail the production logs:

```bash
wrangler tail
```

Then, to force-run a trigger against production (still requires the secret):

```bash
curl -X POST "https://aplomb-clinic-cron.<your-subdomain>.workers.dev/run/review-requests" \
  -H "X-Cron-Secret: $CRON_SHARED_SECRET"
```

The Worker's response is the JSON the Pages endpoint returned, e.g. `{"processed": 12, "scanned": 47}`.

## When to update

- **Add a new cron endpoint** in `functions/cron/`? Add the path to the `SCHEDULE` map in `src/index.js`, add a trigger to `wrangler.toml`, redeploy.
- **Change the time?** Edit the cron expression in both `wrangler.toml` and `src/index.js`'s `SCHEDULE` map (they must match exactly so the dispatcher finds the path).
- **Rotate `CRON_SHARED_SECRET`?** Update it in both places: `wrangler secret put CRON_SHARED_SECRET` here AND the Pages project env var (CF Dashboard → Workers & Pages → aplomb-clinic → Settings → Environment variables).

## Why a separate Worker (not just adding crons to Pages)?

Cloudflare Pages Functions (the `functions/` directory in the main repo) executes server-side code on every request, but **does not support scheduled invocation**. Workers do. So we ship a 70-line Worker whose only job is to call our Pages endpoints on a clock. It does no business logic itself; the Pages endpoints do.

If Cloudflare adds cron support to Pages Functions in a future release, this Worker can be retired and the schedules moved into the main `wrangler.toml`.
