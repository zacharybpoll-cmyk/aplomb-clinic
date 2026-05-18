# APLOMB. — smoke harness

Reusable, re-runnable verification for the launch-critical paths. No secrets are
committed; every credentialed check reads from the environment and SKIPs (never
hard-fails) when its key is absent.

```bash
npm run smoke           # Tier 1/2/4.1 — curl vs prod, read-only (~30s)
npm run smoke:browser   # Tier 3      — Playwright consent matrix
npm run smoke:webhook   # Tier W/4.2  — local wrangler, synthetic Stripe events
```

`npm run smoke` exits non-zero if any gated check fails — it is a real gate, safe
for CI.

## What each tier proves

| Tier | Script | Proves |
|------|--------|--------|
| 1 | `smoke.sh` | analytics.js is the consent-gated build; pixel-id swap on every page; `must-revalidate` on assets; HSTS/CSP/nosniff/Referrer/Permissions headers; robots/llms/sitemap; FAQPage/Person/Product JSON-LD; real page bodies; cookie/privacy copy accurate; Meta CAPI credential live |
| 2 | `smoke.sh` | `/api/checkout` rejects malformed body + bad SKU before any Stripe call; auth callback redirects (no-token, bad-token); `/api/account/me` 401; `/admin` is CF-Access-gated; `/api/webhooks/stripe` rejects unsigned events before any handler |
| 3 | `smoke-browser.spec.mjs` | The consent gate end-to-end: banner shown first visit; Essential-only blocks Pixel+Clarity; Accept-all loads them; **GPC overrides a stored "accepted" consent (privacy promise)**; consent persists; checkout.js consumes `adConsentGranted()` |
| 4.1 | `smoke.sh` | All 12 transactional email templates render |
| 4.2 | `smoke-webhook.sh` | companion-worker routes each cron expression to the correct `/cron/*` endpoint with `X-Cron-Secret`; unknown cron no-ops |
| W | `smoke-webhook.sh` | Webhook signature enforcement + the Stripe signing scheme + event routing; (DB leg) order→paid, inventory decrement, replay idempotency |

## Environment variables

| Var | Used by | If absent |
|-----|---------|-----------|
| `BASE_URL` | smoke.sh, smoke-browser | defaults to `https://getaplomb.com` |
| `META_CAPI_ACCESS_TOKEN` | smoke.sh 1.10 | 1.10 SKIPs |
| `META_TEST_EVENT_CODE` | smoke.sh 1.10 | defaults to `APLOMB_SMOKE` (Test Events tab; never pollutes standard reporting) |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | smoke-webhook DB leg | DB leg SKIPs (signature/routing leg still runs) |
| `WK_PORT` | smoke-webhook | defaults to `8788` |

The service-role key is a full-DB credential. It is **never** hard-coded or
solicited into chat. The DB-reconciliation leg only runs when an authorized
operator has it exported in their own shell.

## False-positive guards (these caused real misdiagnoses — do not remove)

1. **SPA 200-fallback.** getaplomb.com serves HTTP 200 for unknown paths.
   Assertions check the response **body** for a page-unique marker, never the
   status code alone. A 404-that-returns-200 would otherwise pass silently.
2. **CF Browser-Cache-TTL clamp.** The zone rewrites asset `max-age=0` up to
   `14400`. We assert `cache-control` **contains `must-revalidate`** (the
   directive `_headers` actually controls) — never an exact `max-age`.
   A pre-PR#32 `immutable` entry may linger on the *bare* `/assets/analytics.js`
   URL until it ages out; this is reported as WARN, not FAIL, because no live
   HTML references it (HTML is `DYNAMIC`, never edge-cached) and the live pages
   load the healthy `?v=` URL. Optional one-time CF cache purge fully evicts it.
3. **One magic link per test.** Supabase keeps only the latest token per email
   valid. The harness never generates magic links; the live click-through is a
   manual Tier R step (fire exactly one, click within minutes).
4. **No committed secrets.** `git grep` for `sk_live`/`sk_test`/`whsec_`/`SERVICE_ROLE`
   returns nothing in `scripts/`. Pixel IDs are public, not secrets.
5. **LIVE Stripe + single PROD Supabase.** Tiers 1–4 are GET/negative only.
   Tier W is local-only (a hard interlock aborts on a non-localhost target),
   uses synthetic signed events (no real Stripe account), and the DB leg's
   `trap` teardown deletes every sentinel row and restores inventory on ANY
   exit. Verified: post-run sentinel count is zero and inventory is restored.
6. **`set -o pipefail` + `grep -q`.** `grep -q` exits on first match and
   SIGPIPEs `curl`; with pipefail that false-fails large pages. The harness
   captures bodies into variables before matching — never `curl | grep -q`.

## Tier R — residual founder-only (not auto-runnable)

| # | Check | Why manual |
|---|-------|-----------|
| R1 | Real magic-link click-through (fire ONE link, click within minutes) | Single-use token; Gmail-MCP mangles the URL; browser MCP permission-blocked |
| R2 | Live Apple Pay sheet on a real device | Needs a real device + wallet |
| R3 | Eyeball Meta Events Manager → Test Events showing the smoke + Tier W server events | Meta UI |
| R4 | First real end-to-end paid order at launch | No synthetic substitute for LIVE Stripe keys |

Run order: `smoke.sh` first (fast, catches deploy/cache regressions), then
`smoke-browser`, then `smoke-webhook` (boots local wrangler).

---

# APLOMB. — Facebook Page control (`fb-page.mjs`)

Thin Meta Graph API control of the getaplomb.com Page (publish, schedule,
read, moderate, insights), driven by `npm run fb -- <command>`. No browser,
no third party — this script is the only thing that holds the Page token.
Out of scope by design: the live v18.0 CAPI code, the Ads/Marketing API, and
Facebook Groups (Meta killed the Groups API in 2024 — group work stays manual).

```bash
npm run fb -- help
npm run fb -- whoami                       # verify token + identity
npm run fb -- posts                        # read paths need no flag
npm run fb -- post --message "…" --confirm  # writes need --confirm
```

**Secrets** (`scripts/.fb.env`, gitignored — see `.fb.env.example`):
`FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`, optional `FB_API_VERSION` (default
`v23.0`). `process.env` always wins. The token is never echoed and never
solicited into chat; `bootstrap-token` writes it straight to `.fb.env`.

**Conventions kept consistent with the smoke harness:** env-only secrets that
fail loudly when absent (never a hard-coded fallback), the real Graph API
error surfaced verbatim (message/code/`fbtrace_id`), and — because publishing
is outward-facing and hard to reverse — **read-only by default; every write
refuses without `--confirm` (or `FB_CONFIRM=1`).**

**Founder-only (Meta side, needs the founder's login):** generate a System
User token (non-expiring) inside the controllable "Get Aplomb" portfolio
`1183365767175630` with scopes `pages_manage_posts`, `pages_read_engagement`,
`pages_show_list` (+ `pages_manage_engagement` to moderate comments). The Page
must be owned by that portfolio or Meta's "must be an admin of this business
portfolio" gate blocks token generation — the same trap that bit the CAPI
setup. App stays in Development mode, so no full App Review is needed for an
owned Page.
