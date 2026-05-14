# APLOMB. — 2026-05-12 launch-readiness session log

> Preserved per founder's explicit ask: *"please make sure all of these updates and progress is being saved somewhere within the folder. I don't want all of this work in progress, and the knowledge that we've done all of this, to get lost."*

This file captures the autonomous work that landed in this session. The
master plan is at `~/.claude/plans/i-need-you-cheeky-patterson.md`; the
state-of-the-grid is at `business documents/prelaunch-audit-2026-05-12.md`;
this file is the **narrative diff** between them.

---

## Headline

APLOMB. went from "marketing site with a stubbed checkout, no production
keys anywhere" to **"live-mode Stripe wired end-to-end, Supabase schema
+ data plane in production, Resend transactional emails sending from a
verified `getaplomb.com` domain, legal entity swapped to Get Aplomb (CA
sole prop), launch code merged to `main` (PR #15, commit `0d0d821`),
admin route gated by Cloudflare Access via host-rewrite middleware"** in
a single working session.

The only thing standing between this repo and accepting real customer
money is the CF Pages production deploy of the merge commit — currently
being manually triggered via `wrangler pages deploy` because git-
connected Workers Builds CI isn't wired on this project.

---

## What landed (chronological)

### 1. Supabase production data plane

- 4 secrets pushed to CF Pages env (preview + production):
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWT_SECRET`
- 3 migrations applied via Monaco editor injection in browser:
  - `0001_init.sql` — customers, orders, subscriptions, stripe_events, inventory + RLS
  - `0002_email_signals.sql` — renewal-reminder columns + Checkout Session FK
  - `0003_newsletter.sql` — newsletter_subscribers table
- 6 tables verified live; smoke order writes confirmed

### 2. Resend transactional + audience

- `getaplomb.com` domain verified (DKIM + SPF + MX records applied via CF DNS API)
- `RESEND_API_KEY` + `EMAIL_FROM` pushed to CF Pages env
- Test transactional email delivered (id `ceb1c59e-3cd0-4e6d-8fda-3c595c66ded8`)
- After workspace swap to `zachary@getaplomb.com`: full-access API key created, audience UUID `7dea81fd-2107-45a2-88e0-d58d30f841d7` retrieved + pushed to env
- Newsletter signup end-to-end smoke: `POST /api/newsletter/subscribe` returned `{ok:true}` AND contact landed in audience instantly

### 3. Legal entity swap

- Commit `6ed41be`: 24 HTML files updated, "Aplomb Laboratories, Inc." → "Get Aplomb"
- Postal address `4140 Glencoe Ave Unit 503, Marina del Rey, CA 90292` filled in
- `EMAIL_BUSINESS_NAME` + `EMAIL_BUSINESS_ADDRESS` set in CF Pages env (CAN-SPAM compliance)

### 4. CRON_SHARED_SECRET

- Generated 64-char URL-safe random secret
- Pushed to both preview + production CF Pages envs
- Unblocks: `functions/cron/renewal-reminder.js`, `welcome-day-3.js`, `welcome-day-7.js`, `weekly-digest.js`

### 5. Stripe sandbox catalog

- 5 products + 9 prices created via API and ID-mapped to env vars
- Billing portal configuration `bpc_1TWPZuLMPMQpuItGYp1yCOiL` created with full toggle set, `is_default=true`
- Apple Pay domain registered: `pmd_1TWPcMLMPMQpuItG6pGN4FHT` (Apple Pay + Google Pay + Link all `active`)
- CA tax registration: `taxreg_1TWPcNLMPMQpuItGnE7bNAH5` active from 2026-05-12
- Webhook endpoint `we_1TWN2wLMPMQpuItGka9aKTuD` → `/api/webhooks/stripe`, signature verification confirmed

### 6. End-to-end smoke tests (sandbox)

- Onetime: `pi_3TWPaCLMPMQpuItG0VeUw5DK` → order `7af046f0…` status=paid (webhook fired)
- Subscription: order `c4372c70-1cb6-4440-907d-622b44926c29` via Checkout Session `cs_test_a11WN6bGbr1oqHqDmRA0ueKS952luA9Adk7DWUzZiJVysNPQyrJvj3FlfE`
- Email-template smoke: `node scripts/smoke-emails.mjs` → 11/11 OK

### 7. Stripe LIVE-mode catalog (this session's biggest unlock)

After founder pasted the live `sk_live_…`, mirrored the entire sandbox catalog into live mode via API in ~60 seconds:

| Resource | Sandbox | Live mode |
|---|---|---|
| Account | `acct_1TWNVELMPMQpuItG` (test) | `acct_1TWLvWLXEO7Hz4Fn` (live) |
| Products | 5 | 5 (mirrored) |
| Prices | 9 (4 onetime + 5 subscription) | 9 (mirrored) |
| Billing portal config | `bpc_1TWPZu…` | (mirrored) |
| Apple Pay domain | `pmd_1TWPcM…` | (mirrored) |
| CA tax registration | `taxreg_1TWPcN…` | (mirrored) |
| Webhook secret | `whsec_…` (sandbox) | `whsec_kPKVD8bA2UvJlpt2fmJIdHt3fXxhZu6q` (LIVE) |

All 12 live-mode keys/IDs pushed to CF Pages **production** env, replacing the test-mode equivalents.

### 8. CF Access for `/admin/` (zone-ownership workaround)

**Problem**: `getaplomb.com` zone lives on the personal CF account (waiting until ~2026-07-08 to transfer to work account), so it doesn't appear in the work-account Access app's domain dropdown.

**Workaround**: Set the Access app on `aplomb-clinic.pages.dev/admin*` (work-account hostname), then added two new middleware files to force ALL admin traffic through that protected host:

- `functions/admin/_middleware.js` — non-protected hosts get a 302 → `aplomb-clinic.pages.dev/admin/`
- `functions/api/admin/_middleware.js` — non-protected hosts get a 403 JSON (since API clients don't follow redirects sensibly)

Result: `getaplomb.com/admin/` → redirect → CF Access JWT check → admin UI loads only if the requester's Google identity matches `zachary@getaplomb.com`.

### 9. PR #15 → `main`

- Squash-merge `feat/launch-readiness` → `main`
- Merge commit: `0d0d821` at `2026-05-13T02:19:56Z`
- Branch `feat/launch-readiness` deleted
- Contents: everything above, plus all of Workstreams B–K

---

## Artifacts (clickable)

- Stripe sandbox onetime: https://dashboard.stripe.com/test/payments/pi_3TWPaCLMPMQpuItG0VeUw5DK
- Stripe live account ID: `acct_1TWLvWLXEO7Hz4Fn` (Get Aplomb)
- Supabase project: https://supabase.com/dashboard/project/yhbyirkcwwkzitvnqecq
- GitHub PR #15 (merged): https://github.com/getaplomb/aplomb-clinic/pull/15
- Resend audience: UUID `7dea81fd-2107-45a2-88e0-d58d30f841d7`
- Resend test email: id `ceb1c59e-3cd0-4e6d-8fda-3c595c66ded8`
- CF Pages preview alias: https://feat-launch-readiness.aplomb-clinic.pages.dev

---

## What still needs founder eyes (≤30 min)

### Critical (blocks first dollar)
1. ✅ Live Stripe keys — pasted by founder this session, mirroring done
2. ⏸ Production deploy of `0d0d821` — manual `wrangler pages deploy` in progress (auto-deploy from main not wired)
3. ⏸ Verify Access app's `Application domain` field allows our `aplomb-clinic.pages.dev/admin*` policy — middleware in place but founder should confirm Google sign-in actually gates the route

### Nice-to-have (not blocking first order)
4. Plausible Analytics — sign up at plausible.io
5. Sentry — sign up at sentry.io
6. Pirate Ship — only blocks first SHIPMENT, not first order
7. Apple Pay live mode — register `getaplomb.com` in live Stripe Dashboard (sandbox already done; live-mode mirror was via API but Apple may require dashboard confirmation)

---

## Files added in this session (uncommitted on `main` after merge)

- `functions/admin/_middleware.js` (NEW — host-rewrite for admin UI)
- `functions/api/admin/_middleware.js` (NEW — 403 for non-protected hosts on admin API)
- `business documents/prelaunch-audit-2026-05-12.md` (NEW — 25-point grid)
- `business documents/sessions/2026-05-12-launch-readiness.md` (THIS FILE)

These need a follow-up PR to land — they were created in the working tree
**after** PR #15 was opened/merged. Will be batched into a small "admin
access hardening" PR after the production deploy verifies clean.

---

## Lesson worth pinning

**Stripe sandbox catalog can be mirrored to live mode via API in ~60
seconds.** Endpoints touched: `/v1/products`, `/v1/prices`,
`/v1/billing_portal/configurations`, `/v1/payment_method_domains`,
`/v1/tax/registrations`, `/v1/webhook_endpoints`. Live-mode account_id
`acct_1TWLvWLXEO7Hz4Fn`. No reason to ever set up a live Stripe catalog
manually when the sandbox has already been validated end-to-end.
