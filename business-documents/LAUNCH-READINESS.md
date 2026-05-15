# APLOMB. — Launch-Readiness Comprehensive Audit

**Date:** 2026-05-14
**Author:** Zachary Poll (founder) + Claude Code session
**Scope:** Where APLOMB. stands today vs a world-class D2C launch. Punch list + roadmap to close the gap.
**Companion docs:**
- `business-documents/supplier-analysis/correspondence/prelaunch-audit-2026-05-12.md` — the 25-point commerce bring-up grid (still useful; not superseded)
- `COMMERCE-RUNBOOK.md` — operator-facing how-to for the Stripe / Supabase / Resend wire-up
- `business-documents/supplier-analysis/correspondence/sessions/2026-05-12-launch-readiness.md` — narrative diff of what landed two days ago

---

## 1. Executive summary

APLOMB. has a launch-ready commerce stack and a marketing site that **out-classes 90% of new DTC brands on copy, brand, and clinical depth.** The 25-point bring-up grid from 2026-05-12 puts the brand at **18 done / 5 founder-pending / 1 blocked / 1 not-smoked** — the commerce flow has been smoke-tested end-to-end in sandbox, Stripe live keys are pasted and mirrored, Cloudflare Access gates `/admin`, the entity is correctly registered as "Get Aplomb" (CA sole prop) with a real business address feeding CAN-SPAM-compliant transactional footers.

**The real launch blockers are operational, not architectural:** a companion Cron Worker isn't wired (so welcome-series + renewal-reminder emails won't fire), the merge-commit production deploy needs a manual `wrangler pages deploy`, the `/admin` Google sign-in gate needs an end-to-end click-through to verify, the `/account` magic-link flow needs the same, supplier-side allergen and Prop 65 disclosures aren't filed yet, and the sitemap references a `/daily/` page that doesn't exist on disk (a guaranteed 404 the moment Googlebot crawls).

**Where we are behind world-class** isn't the commerce plumbing — it's the **growth infrastructure** that agencies like Common Thread Collective, Power Digital, and Studio ID ship in their 90-day launch sprints: a reviews/UGC tool, a real marketing-flow ESP (we have transactional + a 3-email welcome series; the canonical DTC stack runs 8 flows including browse-abandon, cart-abandon, post-purchase nurture, replenishment, win-back, sunset), SMS, helpdesk, post-purchase upsell, branded order tracking, a paid-ads pixel stack with server-side conversions, and AI/GEO discovery infrastructure (`llms.txt`, FAQ schema, Person schema on the founder, AI crawler `robots.txt` directives). None of those gate "first dollar" — but every week they're missing is a week of compounding loss.

**Recommended order of attack** is in §6. The shortest summary: ship the **9 Tier-1 launch-blocking items this week**, the **18 Tier-2 items in the first 30 days** (the SEO/GEO and trust-signal layer — highest ROI per hour of work), the **15 Tier-3 items in days 31–90** (growth stack: reviews, marketing flows, paid stack, helpdesk), and the **10 Tier-4 items** (insurance, trademark, MoCRA, advanced analytics) on a rolling basis as scale demands.

---

## 2. What we have — verified 2026-05-14

State below is verified by direct file reads of `/Users/zacharypoll/Desktop/Documents/Claude Code/Get-Aplomb`. The audit two days ago landed a lot in one session; this is the post-merge state of the tree on disk.

### 2.1 Commerce backend

**Stripe (live):**
- Account `acct_1TWLvWLXEO7Hz4Fn` (Get Aplomb).
- 5 products: APLOMB. The Serum / Daily / Roots / Calm / Breath. 9 prices (4 onetime + 5 subscription — Calm is onetime-only by design, a titration kit not a recurring SKU). Price IDs mapped to 9 env vars per `.dev.vars.example:10-19`.
- Stripe Tax: CA registration `taxreg_1TWPcN…` active 2026-05-12. `automatic_tax: { enabled: true }` for subscription Checkout Sessions (`functions/api/checkout.js:222`); explicit `stripe.tax.calculations.create()` for one-time PaymentIntents (`functions/api/checkout.js:93-116`).
- Apple Pay + Google Pay + Stripe Link domain registered (`pmd_1TWPcM…`) — sandbox confirmed, live-mode mirror via API done, dashboard re-confirmation TBD.
- Billing Portal config `bpc_1TWPZu…` is_default=true with cancel + payment method update + customer update + invoice history all toggled on.
- Webhook endpoint `we_1TWN2w…` → `https://getaplomb.com/api/webhooks/stripe`. Signature verification confirmed. Idempotency table `stripe_events` (`supabase/migrations/0001_init.sql:87-91`) — replays short-circuit on unique-violation.

**Webhook handler coverage** (`functions/api/webhooks/stripe.js`):

| Event | Action |
|---|---|
| `payment_intent.succeeded` | Mark order `paid`, register Stripe Tax transaction from stashed calc ID, send `order-confirmation` email |
| `payment_intent.payment_failed` | Mark order `failed` |
| `charge.refunded` | Mark order `refunded`, send `refund-confirmation` email |
| `checkout.session.completed` | Close subscription pending-order, mark `paid`, upsert customer, send confirmation |
| `customer.subscription.created` / `updated` | Upsert subscription row with status + period_end + cancel_at_period_end |
| `customer.subscription.deleted` | Mark `canceled`, send `cancellation-confirmation` email |
| `invoice.paid` (subscription_cycle) | Insert renewal order row from invoice.lines, advance subscription period, send `renewal-receipt` email |
| `invoice.payment_failed` | Mark subscription `past_due`, send `card-failed` email with next-retry date |

**Supabase (live):** project `yhbyirkcwwkzitvnqecq`. 3 migrations applied:
- `0001_init.sql` — customers, orders (with computed `total_cents`), subscriptions, stripe_events, inventory (seeded 5 SKUs at 0 on-hand). RLS on all tables. Customers can SELECT their own orders/subs via `auth.jwt()->>'email'`; everything else service-role only.
- `0002_email_signals.sql` — added `stripe_checkout_session_id`, `stripe_invoice_id`, `stripe_subscription_id`, `stripe_charge_id`, `total_cents_override` to orders; `renewal_reminder_sent_at` + `shipping_address` to subscriptions. Indices on subscription period + status.
- `0003_newsletter.sql` — newsletter_subscribers table with `welcome_day_3_sent_at` / `welcome_day_7_sent_at` columns, partial index on active subscribers.

**Resend (live):** `getaplomb.com` verified DKIM + SPF + MX (DNS via CF API). Full-access API key + audience UUID `7dea81fd-2107-45a2-88e0-d58d30f841d7` pushed to CF Pages env. Smoke send `ceb1c59e-…` confirmed delivery. Newsletter signup smoke landed a contact in the audience instantly.

**12 transactional email templates** (`functions/_lib/email-templates/`): `order-confirmation`, `shipping-notification`, `refund-confirmation`, `renewal-heads-up`, `renewal-receipt`, `card-failed`, `cancellation-confirmation`, `magic-link`, `newsletter-welcome`, `welcome-day-3`, `welcome-day-7`, `_layout` (shared chrome). Smoke test `node scripts/smoke-emails.mjs` → 11/11 OK.

**Server-side price catalog** (`functions/_lib/products.js`): single source of truth. Client never sets price. Subscribe-and-save discounts encoded per-SKU (10% serum, 15% daily/roots/breath, 0% calm). Shipping: $7.99 flat below $75 subtotal, free above.

### 2.2 Marketing site

**Pages on disk** (`website/`):
- Home (`index.html`) — full editorial-clinical layout with bio carousel, 4 product rails, founder quote, evidence callout. Excellent copy, dense.
- 4 PDPs: `/serum/`, `/roots/`, `/calm/`, `/breath/`. Daily is **missing on disk despite being in sitemap.xml** (T1-1).
- Marketing pages: `/about/`, `/biology/`, `/evidence/`, `/faq/`, `/contact/`
- Commerce pages: `/checkout/`, `/checkout/success/`, `/account/`, `/admin/`, `/email-preferences/`
- 7 legal pages: `/legal/privacy/`, `/legal/terms/`, `/legal/refund-policy/`, `/legal/returns/`, `/legal/shipping/`, `/legal/subscription-terms/`, `/legal/accessibility/`

**Brand identity** (locked, `brand/BRAND.md`):
- Palette: warm bone `#efe8dc` background, `#f7f1e6` paper, `#1a1512` ink, amber `#7a3d14` accent. Banned: blue, teal, cool grey, neon, primary red, forest green, pure black.
- Type: Cormorant Garamond (display + wordmark, italic 500 with amber period) + IBM Plex Sans (body). Inter explicitly banned.
- Tone: Aesop / Augustinus Bader / The Ordinary — editorial, clinical, restrained. No exclamation marks, no hype words, compliance hedging by default ("supports," "may appear to").
- Trademarks: Ozempic / Wegovy / Mounjaro / Zepbound / semaglutide / tirzepatide never used in copy. "GLP-1" is the safe generic class.

**Structured data in place:**
- Home (`website/index.html:28-42`): `Organization` (legalName "Get Aplomb") + `WebSite`.
- PDPs (`website/serum/index.html:26-59`): `Product` with offers, `BreadcrumbList`, `Organization` (each PDP has all three).
- Canonical tags on every public page (home, PDPs, FAQ, about, etc.).
- OG + Twitter cards on every public page.
- `<meta name="robots" content="noindex,nofollow">` correctly applied to `/admin/`, `/checkout/`, `/account/`, `/email-preferences/`.

**SEO infrastructure files (`website/`):**
- `robots.txt` — disallows `/api/`, `/checkout/`, `/admin/`, `/account/`, `/email-preferences/`. Sitemap directive present. **No AI crawler directives.**
- `sitemap.xml` — 18 URLs. **`/daily/` listed but does not exist on disk** (T1-1). No `<lastmod>`, no image namespace.

**JS bundles** (`website/assets/`):
- `cart.js` — drawer + line-item management.
- `checkout.js` — Stripe Elements mount + tax-aware total.
- `newsletter.js` — footer/popup signup form.
- `analytics.js` — Plausible loader + Sentry loader (DSN-from-meta-tag pattern). Events wired: `view_product`, `add_to_cart`, `begin_checkout`, `checkout_page_view`, `purchase`, `subscribe`, `newsletter_signup`.

### 2.3 Operations

**Admin** (`website/admin/index.html` + `functions/api/admin/orders.js` + `ship-order.js`):
- Tabs: Awaiting shipment / Recently shipped / All.
- Per-row: order ID, customer (name+email), items, address, total, status, tracking, "Mark Shipped" action.
- Auth: `noindex,nofollow` meta + Cloudflare Access policy on `aplomb-clinic.pages.dev/admin*` + host-rewrite middleware (`functions/admin/_middleware.js` redirects non-Access hosts to the Access-protected host; `functions/api/admin/_middleware.js` returns 403 on non-protected hosts for the JSON endpoints).

**Auth** (Supabase magic-link): `functions/api/auth/magic-link.js` issues, `callback.js` exchanges the token for a session cookie, `logout.js` clears. `/account/` reads via `functions/api/account/me.js`. Customer Portal link via `functions/api/customer-portal.js` (returns a Stripe-hosted billing portal URL).

**Crons** (`functions/cron/`):
- `welcome-series.js` — runs day-3 and day-7 batches; finds subscribers whose `subscribed_at` is between `now - {maxDays}` and `now - {minDays}` AND the `welcome_day_N_sent_at` column is NULL; sends, marks. Auth via `X-Cron-Secret`.
- `renewal-reminder.js` — analogous for subscription `current_period_end` 5-day-out reminders.
- **Both need an external Cloudflare Worker to fire on schedule** (Pages Functions doesn't support `triggers.crons` per `wrangler.toml:13-15`).

**Observability:**
- Plausible: site ID `pa-vRaVQaEqcst5ZecHqvEwC` baked into homepage `<head>` (`website/index.html:46`).
- Sentry: DSN `92f66e49e02b30407c2ec6d272ab29e5` (loader script `website/index.html:44`). Custom JS in `analytics.js:31-79` parses the DSN from a `<meta name="sentry-dsn">` tag for the lightweight Beacon transport, but the loader is the canonical path.

### 2.4 Compliance & legal

- **Entity:** Get Aplomb (CA sole prop), EIN obtained (`business-documents/corporate/ein-cp575.pdf`). Address `4140 Glencoe Ave Unit 503, Marina del Rey, CA 90292` in `EMAIL_BUSINESS_ADDRESS` env var feeding all transactional + marketing email footers.
- **FDA / DSHEA:** disclaimer on PDPs ("These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."). Copy is DSHEA-compliant — "supports," "may appear to," never "treats" or "cures." FAQ explicitly clarifies "No supplement or topical cosmetic is FDA-approved — that category applies to drugs only" (`website/faq/index.html:59`).
- **CA Automatic Renewal Law (ARL):** auto-renewal disclosure live on PDPs and on the `/checkout/` page (`website/checkout/index.html:78-81` shows the ROSCA-style disclosure block for subscription mode).
- **CAN-SPAM:** physical address in transactional footer (env var populated). Unsubscribe link infrastructure: `EMAIL_UNSUB_SECRET` for HMAC tokens documented in `.dev.vars.example:32`. Per-template unsubscribe link generation lives in the email-templates layout.
- **Accessibility:** `/legal/accessibility/` page exists. Site has skip-to-main link (`website/index.html:53`), semantic HTML, ARIA labels on carousel controls. **Not formally WCAG-audited.**
- **Subscription Terms:** dedicated page at `/legal/subscription-terms/`.
- **15-day returns:** stated in checkout summary footer ("Ships in 48 hours · tracked · 15-day returns" — `website/checkout/index.html:110`) and on `/legal/returns/`.

---

## 3. Gap analysis by domain

For each domain: current state → what's missing → what to do.

### 3.1 Newsletter

**Current state:** Footer + popup signup forms post to `POST /api/newsletter/subscribe` (`functions/api/newsletter/subscribe.js`). Email upserted into `newsletter_subscribers` (Supabase). New subscribers added to Resend audience `7dea81fd-…`. Welcome email (`newsletter-welcome` template, with discount code `APLOMB10`) sent immediately. Day-3 and Day-7 cron-based touches defined but not yet scheduled.

**Missing:**
- **Cron Worker companion** (T1-2) — without it, day-3 and day-7 emails never fire. Welcome-day-1 fires inline on signup, so the immediate confirmation is fine — but the trickle is dead.
- **Double opt-in** — not strictly required for CAN-SPAM, but improves deliverability and is GDPR-compliant out of the box. Today we're single-opt-in. Resend supports confirmation emails natively.
- **Preference center** (`/email-preferences/` exists but functionality not audited in this pass — likely needs a wire-up to read/write the `preferences` jsonb column on `newsletter_subscribers`).
- **Unsubscribe link in newsletter-welcome** — `EMAIL_UNSUB_SECRET` is in env but verify the welcome email actually carries the link (CAN-SPAM requirement).
- **List health monitoring** — bounce / complaint rates in Resend dashboard; should be checked weekly. Resend will pause sending automatically above thresholds.
- **Source attribution** — currently `source` is a free-text field; should be enumerated (footer, popup-exit-intent, popup-timed, blog, checkout-checkbox) so we can measure conversion by source.

**Action:** Tier 1 wire the Cron Worker. Tier 2 audit the unsubscribe link and preference center. Tier 3 layer in a real ESP (Klaviyo) when broadcast cadence picks up.

### 3.2 Payments

**Current state:** Stripe PaymentIntent for onetime + Stripe Checkout Session for subscription. Automatic payment methods enabled (cards + Apple Pay + Google Pay + Link). Stripe Tax wired. Webhook signature verified, idempotent.

**Missing:**
- **3DS challenge UX** — Stripe automatic payment methods enable 3DS but if the PaymentIntent comes back as `requires_action`, our checkout.js needs to handle the `stripe.confirmPayment()` action flow. Verify this is wired and tested with the `4000002500003155` test card that always triggers 3DS.
- **Rate limiting on /api/checkout** — no per-IP / per-email throttle. Stripe's idempotency keys protect against duplicate orders, but not against script-driven enumeration. Cloudflare Pages Functions can read CF-IP and we can add a simple in-memory or Workers KV rate limit.
- **PayPal** — Stripe supports PayPal as a payment method (since 2024) via automatic payment methods; verify it's enabled in Stripe dashboard for the live account. Not critical for women-focused premium DTC where Apple Pay/Link dominate.
- **Buy-Now-Pay-Later (Klarna / Affirm / Afterpay)** — on $129 The Serum especially, Affirm 4×$32 reduces psychological barrier. Stripe supports all three. Worth A/B testing in Tier 3.
- **Tax registration beyond CA** — Stripe Tax monitors threshold crossings and prompts to register; verify the auto-monitoring is on (Stripe → Tax → Monitoring tab).

**Action:** Tier 1 verify 3DS flow end-to-end. Tier 2 rate-limit checkout. Tier 3 test Affirm.

### 3.3 Subscriptions

**Current state:** Subscription mode uses Stripe Checkout Session with `automatic_tax`. Customer Portal `bpc_1TWPZu…` is_default. Renewal cycle via `invoice.paid` → new order row in our DB + `renewal-receipt` email. Smart Retries handle failed renewals; `invoice.payment_failed` sends `card-failed` email with next-retry date.

**Missing:**
- **Trial periods** — not configured on any price. Some DTC brands use a 7-day free trial as friction reducer; for supplements/topicals trials usually don't lift LTV (samplers churn). Skip unless A/B test says otherwise.
- **Promo / coupon codes** — `consent_collection.promotion_codes` not enabled on Checkout Session. Stripe supports both promo codes and Stripe-hosted ones. Easy add to checkout.js once first marketing campaign needs a code.
- **Gifting** — no gift-subscription path. Skio / Recharge / Loop Subscriptions all do this; Stripe Checkout doesn't natively. Probably Tier 4.
- **Skip-shipment / pause-N-months / swap-SKU** — Stripe Customer Portal supports cancel, update-payment, change-quantity, change-renewal-date. It does NOT support pause-for-N-cycles or swap-SKU. Recharge / Skio / Stay AI are the upgrades when this becomes a top-3 customer complaint. Watch the inbox.
- **Subscription portal embedded UI** (in-domain, not Stripe-hosted) — Stripe Customer Portal is white-labeled-ish but lives on `billing.stripe.com`. Some brands prefer fully-on-domain (Recharge / Skio do this). For brand cohesion at scale, worth Tier 3.
- **MRR / churn / LTV dashboards** — Stripe Sigma is built into Stripe dashboard but limited; Triple Whale / Lifetimely / Polar Analytics are the upgrade. <$10K/mo revenue this is overkill; track manually in a sheet.
- **Renewal reminder email** — `renewal-heads-up` template exists; cron not yet wired. Same Tier 1 dependency as welcome series.

**Action:** Tier 1 wire cron for renewal heads-up. Tier 2 add promo codes when first campaign needs them. Tier 3 graduate to Recharge/Skio if customers ask for pause/swap.

### 3.4 Order & customer admin

**Current state:** `/admin/` page lists orders by status (paid / shipped / all), shows customer info + items + address + total + tracking field + ship action. Gated via CF Access on `aplomb-clinic.pages.dev/admin*` (host-rewrite middleware redirects `getaplomb.com/admin` traffic). API endpoints under `/api/admin/*` have parallel middleware.

**Missing:**
- **Customer detail view** — admin lists orders, not customers. No "show me all orders for this email" or "show me this customer's LTV." Cross-reference via orders table + email = manual SQL today.
- **Search / filter** — no search bar. Limited utility at <100 orders/week but pain at scale.
- **Bulk actions** — no "mark these 10 shipped" multi-select.
- **CSV export** — for accounting, returns reconciliation, supplier order forecasts. Trivial to add to `functions/api/admin/orders.js`.
- **Manual order creation / comp / replacement** — phone orders, customer service replacement shipments. Stripe dashboard handles this fine for now.
- **Inventory adjustment UI** — currently inventory is edited directly in Supabase (per COMMERCE-RUNBOOK Day-2 ops note, line 115). Admin Week-3 plan was an inventory editor — not yet built.
- **Refund UI** — refunds today happen in the Stripe dashboard, which the webhook picks up. Could add a one-click refund button in admin. Not Tier-1 priority.
- **Customer notes / tags** — no scratch-pad on the customer record. Useful at scale; trivial column add on `customers` table.

**Action:** Tier 3 add CSV export + customer detail view + inventory editor. Tier 4 add tags/notes. Tier 1 — verify CF Access is actually gating the route end-to-end with a fresh incognito session.

### 3.5 Inventory

**Current state:** `inventory` table tracks `product_key`, `on_hand`, `reserved`, `reorder_level`*, `supplier`*, `updated_at`. Seeded with 5 SKUs at 0 on-hand. *(`reorder_level` and `supplier` columns are in some earlier sketches but not in the applied 0001 migration — verify before relying on them.)*

**Missing:**
- **Decrement on order paid** — webhook does not decrement `on_hand` on `payment_intent.succeeded` or `checkout.session.completed`. With 0 on-hand seeded, overselling is impossible (you can't go negative because of the check constraint) — but you also can't track sell-through. Need to add the decrement step to the webhook handlers.
- **Out-of-stock UX on PDP** — if `on_hand` is 0, the PDP doesn't disable add-to-cart or show "Sold out" / "Notify me." Risk: customer pays, ships order is delayed by 30 days, customer is angry.
- **Back-in-stock waitlist** — no Supabase table, no UI, no email template. Standard DTC feature; Loox/Klaviyo have built-ins.
- **Low-stock alert** — no cron / no email when `on_hand < reorder_level`. Should fire to founder weekly digest.
- **Supplier / lot tracking** — for cGMP compliance and recall preparedness, every shipped unit should be traceable to a lot number. Not yet captured. Required for supplements per 21 CFR Part 111.
- **Variant / bundle SKUs** — only single-variant SKUs today (Calm has only onetime, others have onetime + subscription). If we ever ship a "4-pack of Calm" or "Serum + Roots bundle," inventory schema needs a bridge table.
- **Reserved vs on-hand math** — `reserved` column exists but no code path increments it on pending orders / decrements on payment failure. Currently dead.

**Action:** Tier 1 add stock decrement to webhook. Tier 2 add "Sold out" UX on PDP + low-stock alert email. Tier 3 add back-in-stock waitlist + lot/batch tracking.

### 3.6 Fulfillment & shipping

**Current state:** Stripe Address Element collects shipping address on checkout. Stripe Tax uses it. Shipping computed server-side: $7.99 flat, free over $75 (`functions/_lib/products.js:75-85`). Order row stores `tracking_number` + `carrier` + `shipped_at`. Admin has a "Mark Shipped" button that writes these and sends the `shipping-notification` email.

**Missing:**
- **3PL or label provider** — Pirate Ship signup is on the founder punch-list (`business-documents/supplier-analysis/correspondence/prelaunch-audit-2026-05-12.md` item — nice-to-have). Today the workflow is: copy address from admin → paste into Pirate Ship UI → buy label → ship → paste tracking back into admin. This breaks at >10 orders/day.
- **Shippo / EasyPost rate-shopping integration** — cheapest carrier per route. Pirate Ship is fine until volume justifies the API integration.
- **Address validation** — Stripe Address Element does Google-Maps-style autocomplete + format validation but doesn't actually verify "this is a real deliverable address." USPS API does this for free; Shippo bundles it. Probably ok for launch.
- **International shipping** — `shipping_address_collection: { allowed_countries: ['US'] }` (`functions/api/checkout.js:223`). US-only by design at launch.
- **Returns / RMA tooling** — none. Process today: customer emails support → human in admin issues Stripe refund → ships return label (or eats cost). For consumables (supplements/topicals), this is fine — most "returns" are won't-take-back disposed-of customer refunds. **Recommend the policy explicitly: "We will refund without requiring physical return for supplements and opened serum. For sealed unopened Serum, we'll cover return shipping."** That belongs in `/legal/returns/` and as a customer-service macro.
- **Branded order tracking page** — when customers click the USPS link in `shipping-notification`, they land on usps.com. Aftership / Wonderment / Malomo all do branded tracking pages with upsell real estate. Tier 3.
- **Insurance / package protection** — Route offers checkout-time package protection. Probably overkill for $129 average orders within US. Pass.

**Action:** Tier 1 set up Pirate Ship account (founder, 30 min). Tier 2 codify the return policy. Tier 3 branded tracking + 3PL when daily volume justifies.

### 3.7 Transactional emails

**Current state:** 12 templates wired through Resend. Smoke 11/11 OK. All carry CAN-SPAM-compliant footer with `EMAIL_BUSINESS_NAME` + `EMAIL_BUSINESS_ADDRESS` + unsubscribe (for marketing templates only; transactional emails are CAN-SPAM-exempt from unsub but it's good practice).

**Missing:**
- **Review-request template** — needed once reviews tool is wired. T+10 days post-delivery (need to add `delivered_at` to `orders` table; today we have `shipped_at` only). Loox/Okendo can send this themselves if integrated, but a native template gives more design control.
- **Refer-a-friend email** — once loyalty/referral tool is wired.
- **Win-back template** — for `subscriptions.status = 'canceled' AND canceled_at < now() - 60 days`. "We miss you. Here's 20% off." Wire-up dependent on ESP migration.
- **Educational drip (post-purchase nurture)** — Day 7 "Here's how to use The Serum effectively." Day 21 "The science behind Roots's iron + D3 stack." Day 45 "How to know if The Serum is working." Could be cron-driven like the welcome series, or migrated to Klaviyo.
- **Holiday / seasonal broadcasts** — Resend Broadcasts (the audience is wired) handles one-off sends. No automation flows.

**Action:** Tier 2 review-request template. Tier 3 educational drip + win-back + ESP decision.

### 3.8 Marketing email (broader)

**Current state:** Welcome 3-series (immediate / day-3 / day-7) defined but only the immediate fires. Resend Broadcasts audience captured, no broadcast sent yet.

**Missing flows — the canonical DTC stack:**

| Flow | Trigger | Status |
|---|---|---|
| Welcome series | newsletter signup | 🟡 immediate works; day-3 + day-7 blocked on cron worker |
| Browse-abandon | viewed PDP, no add-to-cart, in 24hr | ❌ |
| Cart-abandon | added to cart, no purchase, 1hr / 24hr / 72hr | ❌ |
| Post-purchase nurture | order delivered + 7 / 21 / 45 days | ❌ |
| Replenishment | onetime order + 25 days (5 days before product runs out) | ❌ |
| Win-back | last order > 60 days | ❌ |
| VIP segment | LTV > $300 OR >3 orders | ❌ |
| Sunset | no engagement in 6 months (unsub before deliverability hit) | ❌ |

**Why this matters:** post-purchase nurture + replenishment + win-back typically generate 30–40% of email revenue for a DTC brand. Cart-abandon alone is usually 10–15%. Resend Broadcasts doesn't do flow logic — at most you can scaffold flows with our own cron worker, but that's a lot of bespoke code to maintain. **Klaviyo is the agency-standard answer.**

**Action:** Tier 3 — Klaviyo migration decision. Cost: $45/mo starting (500 contacts free, $45 for up to 1,500, scaling). Effort: ~2 weeks to migrate (Resend continues for transactional; Klaviyo handles marketing flows). Alternative: stay on Resend Broadcasts for as long as the founder is comfortable hand-coding flows in cron workers — meaningful savings at launch, expensive at scale.

### 3.9 SMS

**Current state:** Nothing.

**Why this matters:** SMS opens at 90%+ within 3 minutes; email opens at 20% within 24 hours. For drops, restocks, abandoned-cart recovery, the lift is real. New brands typically capture SMS at footer + checkout opt-in checkbox.

**Vendor:** Postscript is the DTC standard at <$100K/mo SMS spend. Attentive demands $20K/yr minimums and is overkill at launch. Klaviyo SMS is bundled if migrating to Klaviyo anyway.

**Action:** Tier 3 — Postscript at $25/mo entry tier OR fold into Klaviyo migration.

### 3.10 Reviews & UGC

**Current state:** Nothing. PDPs have no review section, no aggregate rating, no UGC carousel.

**Why this matters:** Reviews are the #1 trust signal for a new brand. Photo reviews drive ~27% higher conversion than text-only. Day 1, you have zero — but the **scaffolding to collect from Day 1 customers** has to be in place so that by Day 30 you have 20–50 reviews displaying.

**Vendors** (full comparison §7.1):
- **Loox** — visual-first, $9.99–$99.99/mo, integrates without Shopify via JSON API.
- **Okendo** — structured surveys + reviews, $49–$599/mo.
- **Junip** — budget, free to 50 reviews, $19–$299/mo.
- **Yotpo** — enterprise, $179+/mo, overkill at launch.
- **Fera** — middle tier, $9–$99/mo, growing.

**Recommendation:** **Junip free tier** to launch (50 reviews/month is enough for the first 90 days) → graduate to Loox when monthly review volume justifies the upgrade. Both have schema.org/Review markup, photo support, and email-request automation.

**Action:** Tier 2 — pick a tool, wire JSON API on PDPs, add T+10 review-request email.

### 3.11 Helpdesk

**Current state:** All inbound goes to `zachary@getaplomb.com` (reply-to on every transactional email — `functions/_lib/email.js:51`). Contact page form posts to … not audited in this pass; should verify.

**Why this matters:** At >30 orders/week, a plain inbox stops scaling. Macros, canned responses, ticket assignment, FAQ search, and shared inbox become necessary.

**Vendors:**
- **Help Scout** — clean shared inbox, $25/user/mo. Best for solo / small team.
- **Gorgias** — DTC-focused, integrates with Shopify deeply (and Stripe via plugins), $60/mo+ for 350 tickets. Best if running paid ads at scale (ticket volume spikes).
- **Front** — premium shared inbox, $19–$69/user/mo.
- **Re:amaze** — Shopify-leaning but cheaper than Gorgias, $29/mo+.

**Recommendation:** Help Scout for the launch period (solo founder, ~$25/mo). Gorgias only if paid-ads volume drives ticket volume past Help Scout's comfort zone.

**Action:** Tier 3 — Help Scout signup when inbox volume justifies (probably Month 1–2 post-launch).

### 3.12 Post-purchase upsell

**Current state:** `/checkout/success/` page exists but no upsell.

**Why this matters:** Post-purchase upsell ("Add Roots to this order before it ships, save $5 on shipping") typically lifts AOV 15–25%. Customer has already paid; friction-free add-on.

**Vendors:** Aftersell / ReConvert / OneClickUpsell. All Shopify-native but Aftersell has a Stripe integration. ~$30–$100/mo.

**Action:** Tier 3.

### 3.13 Loyalty & referral

**Current state:** Nothing.

**Why this matters:** Refer-a-friend (Give-$10/Get-$10) is the fastest organic-acquisition lever once you have 50+ customers. Loyalty (points) typically less impactful for premium DTC; the brand positioning ("not your wellness Instagram brand") actively conflicts with gamification.

**Recommendation:** Skip loyalty programs entirely. Add **referral** via Friendbuy or ReferralCandy ($49–$95/mo entry tier) by Month 3.

**Action:** Tier 3.

### 3.14 Paid acquisition stack

**Current state:** Plausible only (cookieless, no pixel). No Meta Pixel, no TikTok Pixel, no Google Ads conversion tracking, no server-side Conversions API.

**Why this matters:** If founder ever runs a $5/day Meta test, the Meta optimizer has zero conversion data to learn from. Same for TikTok and Google. iOS 14.5+ broke client-side pixels; server-side CAPI (Conversions API) is the modern baseline.

**Required at the minimum:**
- Meta Pixel + Meta CAPI (server-side via Stripe webhook → CAPI endpoint).
- TikTok Pixel + Events API.
- Google Ads Conversion (gtag.js + Enhanced Conversions for first-party data).

**Vendors / how to wire:**
- **Pixel JS:** `analytics.js` already has the loader pattern; add Meta/TikTok pixel snippets gated on a meta tag (so they only fire on consent).
- **Server-side CAPI:** add a hop in `functions/api/webhooks/stripe.js` on `payment_intent.succeeded` and `checkout.session.completed` that POSTs to `https://graph.facebook.com/v18.0/{pixel_id}/events` with `event_name=Purchase`, `event_id=order.id` (for dedup), `user_data={hashed email}`, `custom_data={value, currency, content_ids}`.
- **TikTok same pattern:** `https://business-api.tiktok.com/open_api/v1.3/event/track/`.

**Action:** Tier 2 if founder plans to run paid ads in the launch window (highly recommended — the brand has the copy and creative to convert; ads need a runway to learn).

### 3.15 Analytics deepening

**Current state:** Plausible + Sentry baseline.

**Missing:**
- **Microsoft Clarity** — free heatmap + session replay. Zero-cost install via JS snippet. Standard agency Day-1 install. Catches "people are clicking the bio carousel dots vs the swipe gesture" insights.
- **Google Analytics 4** — optional, conflicting privacy posture with Plausible. Some founders run both; most pick one.
- **Triple Whale / North Beam / Lifetimely** — blended ROAS, LTV cohort, AOV breakdown by channel. Overkill <$10K/mo revenue; essential >$30K/mo.
- **A/B testing tool (Intelligems / Visually.io)** — for hero / pricing / CTA tests. Tier 3.

**Action:** Tier 2 — install Microsoft Clarity (10 minutes). Tier 3 — A/B testing infra. Tier 4 — graduate to Triple Whale.

### 3.16 Trust signals

**Current state:** Founder bio + credentials on `/about/` (Cambridge, Penn, CHOP, biotech investor). FDA disclaimer. 15-day returns. Bio-medical citations referenced in copy (Sederma, Li 2023, STEP-1).

**Missing:**
- **Reviews** — see 3.10.
- **COA / lab results** — for each supplement SKU (Roots, Calm, Breath), publish the third-party Certificate of Analysis. Either as a downloadable PDF linked from PDP, or as a "view test results" modal. Builds trust massively.
- **Manufacturer transparency page** — `/sourcing/` or `/manufacturing/` listing the contract manufacturers, their cGMP certifications, country of origin per SKU. The FAQ has a sketch of this (`website/faq/index.html:83`) but a dedicated page is the agency standard.
- **Press / earned-media page** — `/press/` listing podcast appearances, articles, mentions. Empty Day 1 — fill incrementally as PR lands.
- **Trust badges** — "30,000 women on GLP-1 trust APLOMB." style social-proof banner. Lying on Day 1; should be true and prominent by Month 6.
- **"As seen in" strip** — same as above.
- **Founder video** — even a 60-second talking-head on `/about/`. Massive trust lift. Brand identity allows for it ("editorial, restrained").

**Action:** Tier 2 — COA links on supplement PDPs, manufacturer page. Tier 3 — founder video, press page, "as seen in" once earned-media lands.

### 3.17 Compliance edge cases

**Current state:** DSHEA disclaimer, ARL, CAN-SPAM all wired. Privacy + Terms + Accessibility pages live. Entity is CA sole prop.

**Missing:**
- **Prop 65 review** — open per the 2026-05-12 audit (item 23). For topicals (Serum) especially, heavy-metal trace amounts may require warning. Supplier-side COAs answer this question; until then there's risk.
- **MoCRA (Modernization of Cosmetics Regulation Act, 2024)** — applies to The Serum. Requires: facility registration (manufacturer of record), product listing (SPL format), adverse event reporting (15-day for serious events). If contract manufacturer is the "responsible person," much of this is on them — but verify in the supplier contract.
- **DSHEA Adverse Event Reporting (AER)** — for supplements. 15-day SAE reporting requirement, 21 USC 379aa-1. Process: customer reports adverse event → email or phone → log → assess severity → file 3500A if serious. Need a process doc + the FDA 3500A form on hand.
- **Cookie consent banner + cookie policy page** — CCPA / CPRA disclosure. Plausible is cookieless and CCPA-exempt for analytics, but as soon as Meta Pixel lands, consent infrastructure is required. Vendors: OneTrust (enterprise, $$$), Cookiebot ($10–$50/mo), Termly ($10/mo, includes policy generation), iubenda ($27/mo). T1-8 + T1-9.
- **Product liability insurance** — for a topical + supplement brand, this is **not optional**. Typical first-year premium: $1,500–$4,000/yr for $1M coverage from Hiscox or Next Insurance. **Recommend pulling Tier 4 forward to Tier 1.**
- **General liability** — bundled with product liability usually. Same vendor.
- **Federal trademark on "APLOMB."** — USPTO search first; if clear, file (~$350 + atty fees). Without it, anyone can use the mark in commerce in their region.
- **Sales tax** — Stripe Tax handles CA. As thresholds cross in other states, Stripe will prompt to register; verify auto-monitoring is on.

**Action:** Tier 1 — Prop 65 review (founder, supplier convo), insurance quote (founder, 1hr via Hiscox/Next Insurance website), cookie banner + policy page (Termly $10/mo). Tier 4 — federal trademark.

---

## 4. SEO + GEO deep dive

This section is where the largest gap-to-agency-quality exists. The site has good basics (canonicals, OG, Twitter, Organization, Product, BreadcrumbList) but is missing the structured data and infrastructure that drives **AI citation** — the new frontier of discovery for 2026+.

### 4.1 Per-page SEO audit (verified 2026-05-14)

| Page | `<title>` | meta desc | OG | Twitter | canonical | JSON-LD | H1 | `noindex` | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `/` | ✅ "APLOMB. For women on GLP-1." (33ch — short) | ✅ 224ch (long, but OK for AI extraction) | ✅ full | ✅ full | ✅ | Organization + WebSite | 1 ("GLP-1s work…") | — | No FAQPage schema, no Person founder schema |
| `/serum/` | ✅ "APLOMB. The Serum — for the dermal half of GLP-1 facial change." | ✅ | ✅ (og:type product) | ✅ | ✅ | Product + Offer + BreadcrumbList + Organization | 1 | — | No AggregateRating, no Review |
| `/roots/` | (assumed similar) | — | — | — | — | (assumed similar) | 1 | — | Spot-check needed; same gaps as /serum/ |
| `/calm/` | (assumed similar) | — | — | — | — | (assumed similar) | 1 | — | Same |
| `/breath/` | (assumed similar) | — | — | — | — | (assumed similar) | 1 | — | Same |
| `/daily/` | **MISSING PAGE** | — | — | — | — | — | — | — | **T1-1: sitemap references this URL but no directory exists** |
| `/about/` | ✅ "About APLOMB. — A line built where it should already exist." | ✅ "founded by biotech investor Zachary Poll" | (none visible) | (none visible) | (assumed) | Organization (assumed) | 1 | — | **No Person schema for founder (T2-4)** |
| `/biology/` | (assumed) | — | — | — | — | (assumed) | 1 | — | **No "Reviewed by" byline (T2-15)** |
| `/evidence/` | (assumed) | — | — | — | — | (assumed) | 1 | — | Same — strong place for medical-reviewer credit |
| `/faq/` | ✅ "APLOMB. — Frequently Asked Questions." | ✅ | ✅ | (none) | ✅ | Organization (assumed) | 2 (no h1 — bug?) | — | **No FAQPage schema (T2-3, HIGHEST-VALUE FIX)** |
| `/contact/` | (assumed) | — | — | — | — | (assumed) | 1 | — | — |
| `/checkout/` | ✅ "Checkout — APLOMB." | ✅ "Secure checkout." | (none) | (none) | (none) | (none) | 1 | ✅ | Correctly excluded |
| `/checkout/success/` | (assumed) | — | — | — | — | — | — | (verify) | Should be `noindex` |
| `/account/` | ✅ "Your account — APLOMB." | ✅ | (none) | (none) | (none) | (none) | 1 | ✅ | Correctly excluded |
| `/admin/` | ✅ "Admin — Orders" | (none) | (none) | (none) | (none) | (none) | 1 | ✅ | Correctly excluded |
| `/email-preferences/` | (assumed) | — | — | — | — | — | — | (verify) | Should be `noindex` |
| `/legal/*` (7 pages) | (assumed) | — | — | — | — | — | 1 each | — | Probably fine; spot-check |

**Site-wide:**
- `robots.txt` — present, disallows authed/private routes, sitemap directive. **No AI crawler directives (T2-2).**
- `sitemap.xml` — present, 18 URLs. **No `<lastmod>`, no image namespace (T2-6). Includes `/daily/` which 404s (T1-1).**
- `llms.txt` — **does not exist (T2-1)**.
- `ai.txt` — **does not exist** (optional, low priority).
- `_headers` — **does not exist (T2-7)**. CF defaults give HSTS but no CSP, no X-Content-Type-Options, no Referrer-Policy.
- `404.html` — **does not exist (T2-8)**.

### 4.2 What's missing for SEO 2026

Google ranks YMYL (Your-Money-Your-Life — health, finance, legal) content on the **E-E-A-T framework**: Experience, Expertise, Authoritativeness, Trustworthiness. APLOMB.'s copy actively signals all four — but the **machine-readable signals** are mostly absent.

**E-E-A-T machine-readable gaps:**
- **Author bylines on /biology and /evidence** — Google's quality raters look for "Reviewed by [credentialed person, date]" attribution on YMYL content. Founder has Cambridge + Penn + CHOP credentials. Surface them via byline + Person schema + `dateModified`.
- **Person schema for founder** (`/about`, `/contact`) — `alumniOf` (Cambridge, Penn), `jobTitle` ("Founder, APLOMB."), `sameAs` (LinkedIn, Twitter, biotech firm). LLMs extract this directly.
- **Organization schema enrichment** — current is minimal (name + url + logo). Should add `foundingDate`, `founder` (Person), `contactPoint`, `address`, `sameAs` (social), `slogan`, `description`.

**Core Web Vitals (2026 thresholds):**
- LCP (Largest Contentful Paint): ≤ 2.5s — likely passing on home given Cloudflare Pages + WebP assets, but the hero image `hero-two-women.jpg` is the LCP candidate. Verify with PageSpeed Insights.
- INP (Interaction to Next Paint): ≤ 200ms — replaced FID in March 2024. Bio carousel may have INP risk if the swipe handler is heavy.
- CLS (Cumulative Layout Shift): ≤ 0.1 — fonts loading via Google Fonts CSS may cause CLS without `font-display: swap`. Check.

**Action:** run PageSpeed Insights on home + 1 PDP + FAQ, fix any vital below threshold.

**Structured data depth — beyond what's there today:**
- **AggregateRating + Review** on PDPs (Day 1 it's empty, but the markup scaffold + reviews tool means it auto-fills from Day 30).
- **MedicalCondition / MedicalIndication** — Schema.org has medical types but Google gates them behind "verified medical entity" status. **Don't use without verification — risk of demotion.** Stick to Product + FAQPage.
- **ImageObject** on hero / product images, with `caption`, `creator`, `license` for AI consumption.
- **Article + Author** for the eventual blog posts.
- **HowTo** for any "how to use" educational content.
- **Speakable** for the FAQ (helps voice assistants).

**Internal linking:**
- Current site is mostly hub-and-spoke from home. Cross-links between PDPs and biology/evidence are minimal. Recommendation: every PDP should link to (a) the biology section explaining the mechanism it addresses, (b) the evidence page citing the studies, (c) at least one related PDP. Every biology mechanism should link to the relevant PDP. This forms the **topic cluster** that AI engines reward.

**Sitemap improvements:**
- Add `<lastmod>` (set to last commit timestamp per URL or just current date).
- Add image namespace + `<image:image>` entries for product hero images.
- Remove `/daily/` (or create the page).
- Consider a separate `sitemap-images.xml` for product photography.

**Performance + security headers via `_headers`:**
- HSTS (probably default on CF, but explicit)
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=()` (don't need these)
- `Content-Security-Policy: default-src 'self'; script-src 'self' https://js.stripe.com https://plausible.io https://js.sentry-cdn.com; …` (careful to allow Stripe, Plausible, Sentry CDN; if Meta Pixel lands, allow `https://connect.facebook.net`).

### 4.3 GEO (Generative Engine Optimization)

GEO is the practice of getting your content **cited by AI engines** — ChatGPT Search, Claude, Perplexity, Google AI Overviews, Microsoft Copilot. The mechanics differ from SEO:

- AI training data is harvested by crawlers (GPTBot for OpenAI, ClaudeBot for Anthropic, etc.). What's in the index when the next foundation model trains becomes part of the model's "knowledge."
- AI retrieval (Real-time) is done by separate crawlers at query-time (OAI-SearchBot, Claude-User, PerplexityBot, Google-Extended). These pull live pages and cite them in answers.
- AI engines reward: clean semantic HTML, FAQ structure, dated content, original data, author credentials, structured data, citation-worthy claims, brand mentions outside the owned property (Reddit, Wikipedia).

**The four highest-ROI GEO moves for APLOMB.:**

**(a) Drop `llms.txt` at the site root** — Anthropic-proposed standard (llmstxt.org). A markdown index of the site for LLMs. Full template in Appendix A.

**(b) Update `robots.txt` with explicit AI crawler Allows** — confirmed strategy: ALLOW all (founder decision, 2026-05-14). This means GPTBot, CCBot, ClaudeBot (and Claude-User, Claude-SearchBot), PerplexityBot, OAI-SearchBot, Google-Extended, Applebot-Extended, ChatGPT-User, anthropic-ai all explicitly welcome. New brand = chase discovery. Full template in Appendix B.

**(c) FAQPage JSON-LD on `/faq/`** — the FAQ has 20+ Qs with crisp answers. FAQPage schema lets AI extract them as a Q&A library. Single biggest gain in citation rate for the lowest effort. Appendix C.

**(d) Person JSON-LD on `/about/` (and link from every page footer)** — surfaces founder credentials machine-readably. AI engines parse Person schema for expertise signals. Appendix D.

**Other GEO wins (Tier 2):**
- Add `dateModified` (and a visible "Last updated: 2026-05-14" stamp) to biology, evidence, FAQ pages. AI engines reward fresh content.
- Add "Reviewed by Zachary Poll, Founder, [credentials]" byline on biology / evidence pages.
- Build a `/glossary/` page — "GLP-1," "telogen effluvium," "hyposalivation," "matrixyl 3000," "palmitoyl tripeptide" — each with a single-sentence citation-ready definition. AI engines love single-source-of-truth definition pages.
- Build out a `/research/` or `/citations/` page that consolidates every paper cited on the site with DOI links. Become the citation graph.
- Use **inverted-pyramid writing** on educational content (key fact in first sentence, supporting detail below). AI engines extract the lead.
- Publish **comparison tables** ("APLOMB. Daily vs Athletic Greens for GLP-1 users") — AI engines extract tables verbatim into answers.

**Brand presence outside the owned property:**
- **Reddit** — r/Ozempic (270k), r/Mounjaro (75k), r/loseit (3.6M), r/Semaglutide (40k). Founder voice with disclosure. Answer questions, don't shill.
- **Quora** — long-tail GLP-1 side-effect questions get cited by AI engines.
- **Podcasts** — being a guest on Modern Wisdom, Huberman-adjacent niche pods, GLP-1-specific pods like "The Skinny Confidential" all generate AI-indexable transcripts.
- **HARO / Help A B2B Writer** — daily journalist queries; respond with quotable founder insights, link back from articles.
- **Wikipedia** — far down the road (eligibility = third-party press coverage); if a Wikipedia page eventually exists, citations there feed every major LLM.

**Citation tracking:**
- Spot-check monthly: ask ChatGPT "What products help with GLP-1 hair loss?" — does APLOMB. surface?
- Same in Claude, Perplexity, Gemini, Google AI Overviews.
- Track which queries we own vs which we don't.

### 4.4 Content strategy — 12 pillar posts in 90 days

A blog at `/journal/` (or `/learn/`, `/notes/` — pick a name that matches brand voice; "Journal" feels most editorial-Aesop). 12 pillar posts over 90 days = ~1/week. Each 2000-3000 words. All pillar → spoke topic-clusters.

**Pillar candidates (one per launch month):**

| # | Title | Target query | Cluster spokes |
|---|---|---|---|
| 1 | "What GLP-1s do to your skin — and what to do about it" | "ozempic face fix" / "glp-1 skin changes" | Matrixyl actives explained; Filler vs serum; Skin texture vs volume; Founder's note on what she tried |
| 2 | "Hair loss on GLP-1s: a timeline" | "ozempic hair loss" / "wegovy hair shedding" | Telogen effluvium primer; Iron + D3 + zinc; Why biotin is wrong; Recovery window after stopping |
| 3 | "The first 30 days: titration nausea" | "ozempic nausea remedy" / "wegovy first month" | STEP-1 nausea data; Ginger + B6 + electrolytes; What to eat; When to call the doctor |
| 4 | "GLP-1 breath: the three converging mechanisms" | "ozempic bad breath" / "wegovy mouth dryness" | Hyposalivation; Ketosis acetone; Gastric stasis; Why mints don't work |
| 5 | "Nutrient gaps on GLP-1: the four most likely deficits" | "glp-1 deficiency" / "wegovy vitamins" | Iron, D3, B12, magnesium; Caloric restriction math; Lab-test interpretation |
| 6 | "Bone density and GLP-1: what the data says" | "ozempic bone density" / "wegovy osteoporosis risk" | Mechanism; Weight-bearing exercise; Calcium + D3 + K2 stack |
| 7 | "When to start side-effect support: the timing question" | "ozempic supplements timing" / "wegovy when to start" | Month 1, 2, 3 framework; Pre-emptive vs reactive; Founder's recommendation |
| 8 | "How to read a supplement label (a GLP-1 user's guide)" | "supplement label reading" / "iron bioavailability" | Forms of iron, D3, magnesium; Bioavailability; Why dose form matters |
| 9 | "The Serum: the 12-week science" | "matrixyl 3000 evidence" / "peptide serum collagen" | Li 2023 study; Sederma trials; 8 vs 12 week timelines |
| 10 | "Building an APLOMB. routine: morning, evening, when on GLP-1" | "skincare routine ozempic" / "supplement timing" | Order of operations; Stack with retinol; Skip days |
| 11 | "GLP-1 facial fillers vs APLOMB. The Serum: the both/and" | "fillers and serum" / "ha filler aftercare" | Why volume + dermal are different problems; When to do each; Cost comparison |
| 12 | "Coming off GLP-1: the recovery roadmap" | "stopping ozempic" / "off-glp-1 hair" | Hair regrowth window; Skin recovery; Weight rebound nutrition |

Each post:
- Author byline (Zachary Poll, [credentials])
- "Last updated" date
- 2-3 inline citations (linked to PubMed / DOI)
- Internal link to relevant PDP
- Internal link to relevant biology / evidence section
- FAQ at the end (5-8 Qs, marked up with FAQPage schema for the post)
- Open Graph + Twitter card
- Article schema (with Author Person + image)

**Cadence:** publish first 3 posts pre-launch (gives organic content for AI crawlers to index before traffic arrives), then 1/week. By Day 90, blog has 12 pillar posts + the home/biology/evidence/FAQ corpus. That's enough content density for topic-cluster authority on "GLP-1 side effects" — exactly the moat the brand needs.

---

## 5. World-class agency comparison

A 90-day launch sprint from Common Thread Collective, Power Digital, or Studio ID typically delivers the artifacts below. Where APLOMB. is **ahead**, **on-par**, or **behind** is called out.

### Pre-launch creative & content
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Brand identity package (logo, palette, type, voice doc) | Full deck | ✅ AHEAD — BRAND.md is more rigorous than 90% of agency deliverables |
| Product photography: hero, white-bg, lifestyle, GIFs, founder | 30-50 images per SKU | ✅ ON-PAR — Flux 2 Pro pipeline generates photoreal mockups; founder portrait exists |
| Copy: hero, PDP, FAQ, comparison, founder | Full copy doc | ✅ AHEAD — APLOMB. copy is editorial-quality, dense, on-brand |
| Press kit / EPK | PDF | ❌ MISSING — Tier 3 |
| Video: founder story (60s), product demos (15s each), POV unboxing | 5-10 videos | ❌ MISSING — Tier 3 |

### Commerce infrastructure
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Storefront on Shopify Plus + 5-10 apps | Full stack | ✅ DIFFERENT — Cloudflare Pages + custom HTML + Functions = more performant + cheaper, but more bespoke |
| Stripe / payment processor | Wired | ✅ ON-PAR |
| Subscriptions (Recharge / Skio) | Wired | 🟡 PARTIAL — Stripe Subscriptions native; will outgrow when need pause/swap |
| Customer accounts + Stripe Portal | Wired | ✅ ON-PAR |
| Inventory management | Wired | 🟡 PARTIAL — schema exists, decrement not wired |
| Tax (Stripe Tax / Avalara) | Wired | ✅ ON-PAR — Stripe Tax CA registered |
| Multi-payment-method (Apple Pay, Google Pay, Affirm) | Wired | 🟡 PARTIAL — Apple/Google/Link yes; Affirm not yet |
| Shipping integration (Shippo / EasyPost / ShipBob) | Wired | ❌ BEHIND — Pirate Ship signup pending; manual workflow today |

### Email / SMS
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| ESP (Klaviyo 99%) | Klaviyo + 6-8 flows | ❌ BEHIND — Resend transactional only; 3-email welcome series wired but blocked on cron |
| SMS (Postscript / Attentive) | Wired | ❌ MISSING |
| Transactional email design | 10-15 templates | ✅ ON-PAR — 12 templates wired, all on-brand |
| Welcome flow | Day 0 / 3 / 7 / 14 | 🟡 PARTIAL — day 0/3/7 defined, day 14 not |
| Cart-abandon flow | 1hr / 24hr / 72hr | ❌ MISSING |
| Browse-abandon flow | Wired | ❌ MISSING |
| Post-purchase nurture | Day 7 / 21 / 45 | ❌ MISSING |
| Replenishment | Day 25 (5 days before 30-day supply runs out) | ❌ MISSING |
| Win-back | Day 60 inactive | ❌ MISSING |

### Reviews, UGC, social proof
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Reviews tool (Loox / Okendo / Yotpo) | Wired Day 1 | ❌ MISSING |
| Photo review collection | Wired | ❌ MISSING |
| UGC widget on PDP | Wired | ❌ MISSING |
| Trust badges / "as seen in" | Wired | ❌ MISSING (will be Day 30+ once reviews exist) |
| Schema.org/Review markup | Wired | ❌ MISSING (depends on reviews tool) |

### Customer service
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Helpdesk (Gorgias / Help Scout) | Wired Day 1 | ❌ MISSING — solo inbox |
| Macros / canned responses | 30-50 macros | ❌ MISSING |
| Live chat (Gorgias Chat / Tidio) | Wired or skipped | ❌ MISSING (acceptable to skip) |
| FAQ + searchable help center | Wired | 🟡 PARTIAL — FAQ exists, not searchable |
| Return / RMA process | Documented + tooled | 🟡 PARTIAL — 15-day return stated, manual workflow |

### Acquisition stack
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Meta Pixel + CAPI | Wired Day 1 | ❌ MISSING |
| TikTok Pixel + Events API | Wired Day 1 | ❌ MISSING |
| Google Ads conversion tracking | Wired | ❌ MISSING |
| UTM strategy + tracking | Documented | ❌ MISSING |
| Influencer / seeding pipeline | Vetted, contracts ready | ❌ MISSING |
| Affiliate program (ShareASale / Impact) | Wired | ❌ MISSING (Tier 4) |

### Analytics
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Plausible / GA4 | Wired | ✅ ON-PAR (Plausible) |
| Heatmap (Hotjar / Clarity) | Wired | ❌ MISSING — Microsoft Clarity is 10-min install |
| Error monitoring (Sentry) | Wired | ✅ ON-PAR |
| Blended ROAS dashboard (Triple Whale / Polar) | Wired Day 30 | ❌ MISSING (overkill <$10K/mo) |

### Legal / compliance
| Deliverable | Agency standard | APLOMB. status |
|---|---|---|
| Privacy + Terms + Refund + Shipping + Subscription Terms | All live | ✅ ON-PAR |
| Cookie consent + cookie policy | Wired | ❌ MISSING |
| Accessibility statement | Live | ✅ ON-PAR |
| DSHEA + FDA disclaimers on PDPs | Live | ✅ ON-PAR |
| CA ARL (auto-renewal disclosure) | Live | ✅ ON-PAR |
| Product liability insurance | Bound Day 1 | ❌ MISSING — **Tier 1 push** |
| Federal trademark | Filed | ❌ MISSING (Tier 4) |
| Prop 65 review | Done | 🟡 PARTIAL — supplier-dependent |
| MoCRA compliance | Verified | 🟡 PARTIAL — supplier-dependent |

**Verdict:** APLOMB. is **ahead** on brand, copy, content depth, and compliance basics. **On-par** on commerce plumbing and transactional infrastructure. **Behind** on growth stack (reviews / UGC / marketing flows / paid pixel / helpdesk / SMS / post-purchase / loyalty). That's the right shape of gap for a sole-founder bootstrapped brand at Day 1 — the depth-of-brand stuff is hard and we got it right; the growth-stack stuff is mostly vendor signups that take an afternoon each.

---

## 6. Prioritized roadmap

### Tier 1 — LAUNCH-BLOCKING (this week)

| # | Item | Time | Owner | Notes |
|---|---|---|---|---|
| T1-1 | Fix sitemap `/daily/` — either delete the URL or create the page | 15 min | Dev | Easiest = delete from sitemap.xml until a Daily PDP is built |
| T1-2 | Wire Cron Worker for welcome-series + renewal-reminder | 1 hr | Dev + Founder | New Cloudflare Worker, schedule `0 9 * * *` POST to /cron/renewal-reminder, `30 9 * * *` POST to /cron/welcome-series, X-Cron-Secret header |
| T1-3 | Verify production deploy of merge commit `0d0d821` is live | 10 min | Founder | `wrangler pages deployment list aplomb-clinic` → confirm production has the merge commit |
| T1-4 | Smoke-test CF Access /admin gate end-to-end | 15 min | Founder | Incognito → getaplomb.com/admin → expect 302 to aplomb-clinic.pages.dev/admin → Google sign-in → confirm zachary@getaplomb.com gates approve |
| T1-5 | Smoke-test /account magic-link end-to-end | 15 min | Founder | Real email → magic link → /account → see orders → click portal → land in Stripe |
| T1-6 | Confirm supplier Prop 65 + allergen disclosures | varies | Founder + suppliers | Per SKU; document in `business-documents/supplier-analysis/` |
| T1-7 | Verify Apple Pay live-mode domain in Stripe Dashboard UI | 5 min | Founder | API mirror done; UI confirmation removes any "needs approval" state |
| T1-8 | Add cookie policy page at /legal/cookie-policy/ | 30 min | Dev | Use Termly generator or write inline; mirror style of other legal pages |
| T1-9 | Install cookie consent banner | 1 hr | Dev | Termly free tier, Cookiebot, or build with simple Cloudflare-edge cookie. Required for any future Meta Pixel. |
| **T1-10** | **Product liability insurance bound** | **1 hr** | **Founder** | **Hiscox or Next Insurance quote, $1M coverage, ~$1.5–4K/yr** |

### Tier 2 — DAYS 1–30 (launch window)

| # | Item | Time | Notes |
|---|---|---|---|
| T2-1 | Drop `llms.txt` at site root | 30 min | Template in Appendix A |
| T2-2 | Update `robots.txt` with explicit AI crawler Allows | 10 min | Template in Appendix B |
| T2-3 | Add FAQPage JSON-LD to /faq | 30 min | Template in Appendix C; biggest GEO win |
| T2-4 | Add Person schema for founder on /about | 30 min | Template in Appendix D |
| T2-5 | Add Review/AggregateRating scaffold to PDPs (depends on reviews tool) | 1 hr | Wire alongside Junip free tier |
| T2-6 | Fix sitemap: add `<lastmod>`, image namespace | 30 min | Appendix F |
| T2-7 | Add `_headers` file (CSP, HSTS, X-CTO, Referrer-Policy) | 1 hr | Template in Appendix E |
| T2-8 | Build branded 404 page | 1 hr | Match site visual; suggest "We can't find that. Here are five things we can." |
| T2-9 | Install Junip free tier; wire JSON API on PDPs | 2 hrs | Or Loox if budget allows |
| T2-10 | Install Meta Pixel + Meta CAPI (Stripe webhook → CAPI Purchase event) | 4 hrs | Required for any future paid ads |
| T2-11 | Install Microsoft Clarity (free heatmap) | 10 min | One JS snippet |
| T2-12 | Verify Google Search Console; submit sitemap | 15 min | DNS TXT verification |
| T2-13 | Verify Bing Webmaster Tools; submit sitemap | 15 min | Same |
| T2-14 | COA links on supplement PDPs (Roots, Calm, Breath) | 1 hr / SKU | Supplier-dependent |
| T2-15 | Add "Reviewed by Zachary Poll, [credentials]" byline + dateModified on /biology and /evidence | 30 min | E-E-A-T signal |
| T2-16 | Update README.md to reflect Cloudflare Pages (not GitHub Pages) | 5 min | Internal hygiene |
| T2-17 | Build `review-request` email template; wire T+10 send | 2 hrs | Add `delivered_at` column to orders first |
| T2-18 | Build back-in-stock waitlist (newsletter_subscribers row with product_key + notify_when_stocked) | 4 hrs | Use existing newsletter_subscribers table; add type column |
| T2-19 | Configure Stripe Checkout `consent_collection.promotion_codes` for first campaign | 15 min | When first promo lands |
| T2-20 | Add stock decrement to webhook (`payment_intent.succeeded`, `checkout.session.completed`) | 1 hr | Critical for inventory accuracy |

### Tier 3 — DAYS 31–90 (growth stack)

| # | Item | Time | Notes |
|---|---|---|---|
| T3-1 | ESP migration decision: stay on Resend Broadcasts vs Klaviyo | day | Decision; if Klaviyo: 1-2 week migration |
| T3-2 | Implement core marketing flows (cart-abandon, browse-abandon, post-purchase nurture, replenishment, win-back, VIP, sunset) | 2-4 weeks | Klaviyo native or cron-driven |
| T3-3 | Postscript SMS — capture at footer + checkout | 4 hrs | $25/mo entry |
| T3-4 | Help Scout helpdesk signup; build 20 macros for common Qs | 4 hrs | $25/user/mo |
| T3-5 | Aftersell post-purchase upsell page | 4 hrs | $30/mo |
| T3-6 | Friendbuy / ReferralCandy referral program | 4 hrs | $49/mo |
| T3-7 | Branded order-tracking page (Wonderment / Aftership) | 4 hrs | $30/mo |
| T3-8 | Blog at /journal/ — first 3 pillar posts | 1 week | 2000-3000 words each |
| T3-9 | Press kit / EPK PDF | 4 hrs | Founder bio, fact sheet, hi-res images, contact |
| T3-10 | Founder Reddit / community presence — r/Ozempic etc. | ongoing | 30 min / day, disclosed founder, value-add not promo |
| T3-11 | HARO / Help A B2B Writer subscription | 30 min | $19/mo |
| T3-12 | Subscribe to 1-3 niche podcasts as guest pitch | ongoing | Focus on GLP-1, women's health, founder/biotech |
| T3-13 | A/B test infra (Intelligems or Visually.io) | 4 hrs | $200+/mo; only after baseline data |
| T3-14 | Migrate to Recharge / Skio when customers ask for pause/swap | 1 week | $99+/mo |
| T3-15 | Admin: CSV export, customer detail view, inventory editor | 1-2 days | When manual ops break down |
| T3-16 | TikTok Pixel + Events API | 2 hrs | If running TikTok ads |
| T3-17 | Google Ads Enhanced Conversions | 2 hrs | If running Google Ads |
| T3-18 | Founder video (60s on /about) | 1 day | Massive trust lift |
| T3-19 | /sourcing/ or /manufacturing/ page (CMO transparency) | 4 hrs | Trust signal |

### Tier 4 — POST-90 (scale + polish)

| # | Item | Notes |
|---|---|---|
| T4-1 | Triple Whale / Polar Analytics blended ROAS | When >$30K/mo revenue |
| T4-2 | Customer Data Platform (Segment / RudderStack) | When stack >5 tools |
| T4-3 | Trustpilot / Google Reviews integration | After 50+ Loox reviews |
| T4-4 | Affiliate program (ShareASale / Impact / Refersion) | After product-market fit demonstrated |
| T4-5 | International shipping infrastructure | UK first (NHS GLP-1 patient base growing) |
| T4-6 | Federal trademark on APLOMB. word mark | $350 filing + ~$1K atty |
| T4-7 | MoCRA registration for The Serum (or CMO confirms) | 2024 act, enforcement ramping |
| T4-8 | DSHEA AER workflow + FDA 3500A docs on hand | Process doc + admin macro |
| T4-9 | Loyalty program (only if data says it lifts retention) | Smile.io free tier |
| T4-10 | Multi-currency Stripe | When international traffic >5% |

---

## 7. Vendor stack recommendations

Rough 2025-2026 pricing. Verify on vendor websites before committing.

### 7.1 Reviews & UGC

| Vendor | Pricing | Pros | Cons | Best for |
|---|---|---|---|---|
| **Junip** | Free to 50 reviews, $19+/mo | Cheap entry, good photo support, fast to set up | Less polish than Loox | Launch month |
| **Loox** | $9.99–$99.99/mo | Visual-first, photo + video reviews, schema markup, Google Shopping syndication, no Shopify required | $100/mo at full features | Month 2-6 |
| **Okendo** | $49–$599/mo | Structured surveys, NPS, Reviews, attribution surveys | Higher entry tier | Brands optimizing for survey data |
| **Yotpo** | $179+/mo | Enterprise features | Overkill at launch | $1M+ rev |
| **Fera** | $9–$99/mo | Growing alternative | Smaller ecosystem | Budget option |

**Recommend:** Junip free → Loox at Month 2.

### 7.2 Helpdesk

| Vendor | Pricing | Best for |
|---|---|---|
| **Help Scout** | $25/user/mo (Standard) | Solo founder; clean shared inbox + macros + saved replies + knowledge base |
| **Gorgias** | $60+/mo (350 tickets) | DTC with paid-ads volume; deep Shopify integration; less native for non-Shopify |
| **Front** | $19-$69/user/mo | Team collaboration; SMS/social channels |
| **Re:amaze** | $29+/mo | Cheaper Gorgias alternative |
| **Zendesk** | $55+/agent/mo | Enterprise; overkill |

**Recommend:** Help Scout Standard ($25/mo) when inbox volume crosses ~50 tickets/week.

### 7.3 ESP (when migrating off Resend Broadcasts for marketing automation)

| Vendor | Pricing | Pros | Cons |
|---|---|---|---|
| **Resend Broadcasts** (current) | Pay-per-send, ~$20/mo at 5k contacts | Cheap, simple, integrates with our existing transactional stack | Limited flow logic, no segmentation |
| **Klaviyo** | Free to 500 contacts, $45/mo at 1.5k, scales | Industry standard, 8 core flows + segmentation + product feed + SMS bundle | Expensive at scale |
| **Omnisend** | Free to 250 contacts, $16/mo at 500 | Klaviyo-lite; good for budget | Smaller ecosystem |
| **Drip** | $39/mo at 2.5k | Old-guard; workflow editor strong | Losing market share |

**Recommend:** Stay on Resend Broadcasts through Day 30. Migrate to Klaviyo by Day 60 if/when marketing flows become a bottleneck.

### 7.4 SMS

| Vendor | Pricing | Best for |
|---|---|---|
| **Postscript** | $25/mo entry; ~$0.02/SMS | DTC standard at <$100K/mo SMS spend |
| **Attentive** | $20K/yr min | Enterprise only |
| **Klaviyo SMS** | bundled if on Klaviyo | If migrating to Klaviyo anyway |

**Recommend:** Postscript at Tier 3, OR Klaviyo SMS bundle if Klaviyo migration happens.

### 7.5 Post-purchase upsell

| Vendor | Pricing | Best for |
|---|---|---|
| **Aftersell** | $30+/mo | Stripe-compatible (non-Shopify) |
| **ReConvert** | $7.99+/mo | Cheapest; Shopify-native |
| **OneClickUpsell** (Zipify) | $34+/mo | Click funnels heritage |

**Recommend:** Aftersell at Tier 3 (Stripe compatibility matters for our stack).

### 7.6 Loyalty / referral

| Vendor | Pricing | Best for |
|---|---|---|
| **Friendbuy** | $49+/mo | Referral focus |
| **ReferralCandy** | $59+/mo | Referral simple, Shopify-leaning |
| **Smile.io** | Free entry, $49+/mo for VIP | Loyalty (points) primary |
| **LoyaltyLion** | $199+/mo | Enterprise loyalty |

**Recommend:** Friendbuy or ReferralCandy at Tier 3. **Skip loyalty (points) — conflicts with brand positioning.**

### 7.7 Heatmaps / session replay

| Vendor | Pricing | Best for |
|---|---|---|
| **Microsoft Clarity** | FREE | Day 1 install — no reason not to |
| **Hotjar** | Free to 35 sessions/day, $32+/mo | Once Clarity isn't enough |
| **FullStory** | $$$$ | Enterprise |

**Recommend:** Microsoft Clarity (Tier 2, 10-min install).

### 7.8 Insurance

| Vendor | Coverage | Pricing |
|---|---|---|
| **Hiscox** | Product liability + General liability | ~$1,500–4,000/yr for $1M coverage, small DTC supplement+topical |
| **Next Insurance** | Same | ~$50–150/mo for similar coverage |
| **The Hartford** | Same | Mid-market |

**Recommend:** Hiscox or Next Insurance — quote both, take the lower price for equivalent coverage. **Pull to Tier 1.**

### 7.9 Branded order tracking

| Vendor | Pricing | Best for |
|---|---|---|
| **Wonderment** | $30+/mo | Post-purchase experience; lifecycle hooks |
| **Aftership** | $11+/mo | Tracking-focused, simpler |
| **Malomo** | $40+/mo | Branded tracking pages |

**Recommend:** Wonderment at Tier 3.

### 7.10 Subscription portal upgrade (when outgrowing Stripe)

| Vendor | Pricing | Best for |
|---|---|---|
| **Recharge** | $99+/mo + 1% of recurring rev | Industry standard, Shopify-heavy |
| **Skio** | Custom, ~$0.40/recurring order | Klaviyo-integrated, modern |
| **Stay AI** | Custom | Newer, retention-AI focus |
| **Loop Subscriptions** | $99+/mo | Newer Shopify-native |

**Recommend:** Skio or Stay AI when pause/swap requests pile up. Stripe-compatible.

---

## 8. SEO + GEO 30-day action plan

A specific day-by-day cadence. All tasks Tier 1-2.

| Day | Task |
|---|---|
| Day 0 | Fix sitemap `/daily/` (delete the URL) + add `<lastmod>` + image namespace |
| Day 0 | Drop `llms.txt` at `website/llms.txt` |
| Day 0 | Update `robots.txt` with explicit AI crawler Allow directives |
| Day 0 | Update README.md (GitHub Pages → Cloudflare Pages) |
| Day 1 | Add FAQPage JSON-LD to `/faq/` |
| Day 1 | Add Person JSON-LD for founder to `/about/` |
| Day 1 | Add `_headers` with CSP/HSTS/Referrer-Policy/X-CTO |
| Day 2 | Build branded 404 page at `website/404.html` |
| Day 2 | Add "Reviewed by Zachary Poll, [credentials]" + dateModified on /biology, /evidence |
| Day 3 | Verify Google Search Console (DNS TXT or HTML file), submit sitemap |
| Day 3 | Verify Bing Webmaster Tools, submit sitemap |
| Day 4 | Install Microsoft Clarity (one JS snippet in analytics.js) |
| Day 5 | Run PageSpeed Insights on home + /serum/ + /faq/; fix any vital below threshold |
| Day 6 | Cookie consent banner + `/legal/cookie-policy/` |
| Day 7 | Wire reviews tool (Junip free); add scaffold to PDPs |
| Day 8 | Build `review-request` email template + wire T+10 send |
| Day 9 | Add `AggregateRating` + `Review` JSON-LD to PDPs (will be empty Day 1, fills as reviews come in) |
| Day 10 | Add stock decrement to webhook handlers |
| Day 11 | Manufacturer / sourcing transparency page (`/sourcing/`) |
| Day 12 | COA links on Roots, Calm, Breath PDPs |
| Day 13 | Meta Pixel + Meta CAPI server-side wire-up |
| Day 14 | First pillar blog post live: "What GLP-1s do to your skin" |
| Day 15-21 | Build out 2-3 more pillar posts; internal-link to PDPs |
| Day 22 | Lighthouse + WCAG audit pass; fix what surfaces |
| Day 23 | Add `dateModified` visible stamps to biology, evidence, FAQ |
| Day 24 | Glossary page (`/glossary/`) — single-sentence definitions of GLP-1, telogen effluvium, hyposalivation, matrixyl, etc. |
| Day 25 | Citations page (`/citations/`) — every paper referenced on the site with DOI |
| Day 26 | Spot-check ChatGPT / Claude / Perplexity for "best GLP-1 hair loss supplement" type queries; note baseline |
| Day 27-30 | Build out cluster spokes for Pillar 1; pillar 2 draft |

---

## 9. Open founder action items (Day 1 worklist)

Aggregated from the 5 founder-pending items in the 2026-05-12 audit + the Tier 1 additions in this doc. Founder time: ~2-3 hours total.

1. **Stripe LIVE-mode Apple Pay verification** — Stripe Dashboard → Payment methods → Apple Pay → confirm `getaplomb.com` is verified in live mode (sandbox + API mirror are done; UI may need final click).
2. **Production deploy of merge commit `0d0d821`** — confirm via `wrangler pages deployment list aplomb-clinic` that the latest production deployment is this commit; if not, `wrangler pages deploy website --project-name=aplomb-clinic --branch=main`.
3. **Cron Worker creation** — Cloudflare Dashboard → Workers → Create → Schedule. Two cron triggers:
   - `0 9 * * *` → `fetch('https://getaplomb.com/cron/renewal-reminder', { method: 'POST', headers: { 'X-Cron-Secret': SECRET } })`
   - `30 9 * * *` → `fetch('https://getaplomb.com/cron/welcome-series', { method: 'POST', headers: { 'X-Cron-Secret': SECRET } })`
4. **CF Access smoke-test** — incognito browser → getaplomb.com/admin → expect Google sign-in challenge → confirm zachary@getaplomb.com gates approve; non-approved emails get denied.
5. **/account magic-link smoke-test** — sign up with a real email → check inbox → click magic link → land on /account → see at least one test order from sandbox.
6. **Plausible signup + paste site ID** to CF Pages env (or confirm the existing `pa-vRaVQaEqcst5ZecHqvEwC` is from a real Plausible account, not a placeholder).
7. **Sentry signup + paste DSN** to CF Pages env (same — confirm `92f66e49…` is real).
8. **Pirate Ship signup + link USPS** — for first shipment. (Won't block first order.)
9. **Supplier confirmations**:
   - Roots: COA scan + allergen statement + Prop 65 status
   - Calm: same
   - Breath: same
   - Serum: same + MoCRA "responsible person" confirmation
10. **Insurance quote** — Hiscox.com or NextInsurance.com → product liability + general liability for "supplement and topical cosmetic DTC" → $1M coverage → quote should land in 24hr.
11. **Cookie consent vendor pick** — Termly ($10/mo) or Cookiebot (free tier up to 100 pages) → embed snippet → publish cookie policy page.

---

## 10. Maintenance & monitoring cadence

### Weekly (Monday morning, 15 min)
- Google Search Console: impressions, clicks, top queries, top pages, indexation status
- Plausible: top pages, traffic sources, top events (purchase, subscribe, newsletter_signup), bounce rate
- Stripe Dashboard: refund rate, dispute rate, failed-payment rate
- Resend: open rate, click rate, bounce rate, complaint rate (auto-pause threshold ~0.3%)
- Inbox / Help Scout: ticket volume + top categories
- AI citation spot-check: ChatGPT, Claude, Perplexity for "best GLP-1 supplement" / "ozempic face fix" / "hair loss on wegovy" — does APLOMB. surface?
- Microsoft Clarity: top 3 session recordings of users who didn't purchase; what blocked them?

### Bi-weekly
- Inventory levels per SKU; reorder triggers
- Review collection rate (target: 15-20% of orders → review by Day 30)
- New subscriber growth + welcome-series open rate

### Monthly
- Lighthouse + Core Web Vitals re-run on top 5 pages
- Accessibility audit (axe DevTools or similar) on top 5 pages
- Competitor SEO scan — what new pages are competitors publishing
- Resend deliverability review (DKIM/SPF alignment, IP reputation)
- Cohort retention: Month-1 → Month-2 → Month-3 retention by acquisition channel
- Blended CAC + ROAS if running paid ads

### Quarterly
- Legal page review (privacy, terms, refund — esp. as law changes)
- Insurance renewal review (and claim history)
- Brand audit: are we still on-brand? Any drift in copy / imagery?
- Vendor stack audit: any tool we can drop? Any new vendor worth adding?
- Founder podcast / press tracker: how many earned-media touchpoints in the quarter?

### Annually
- Federal + state tax filings
- DSHEA AER review (any serious adverse events filed?)
- Trademark watch (USPTO Trademark Status & Document Retrieval)
- Insurance policy reshop

---

# Appendices

## Appendix A — `website/llms.txt` template (drop in at site root)

> Place this file at `website/llms.txt`. Cloudflare Pages will serve it at `https://getaplomb.com/llms.txt`. Per llmstxt.org spec — markdown, succinct, links to canonical sources.

```markdown
# APLOMB.

> The side-effect line for women on GLP-1 medications. Four products for the four side effects that GLP-1 prescribers don't address: facial dermal thinning, hair shedding, titration nausea, and oral malodor.

Brand: APLOMB.
Legal entity: Get Aplomb (CA sole prop)
Founder: Zachary Poll — biotech investor; Cambridge, Penn, CHOP background
Founded: 2026
Domain: https://getaplomb.com
Contact: zachary@getaplomb.com

## Products

- [The Serum](https://getaplomb.com/serum/): topical peptide serum (Matrixyl 3000 + Synthe'6 + Centella + Kakadu Plum) for the dermal-thinning fraction of GLP-1 facial change. $129, 30mL, 60-day supply. NOT a substitute for volume restoration via filler/biostimulator.
- [Daily](https://getaplomb.com/daily/): once-daily nutrient pack (methyl-B12, D3+K2, iron, zinc, magnesium) for the four most common deficits during GLP-1-driven caloric restriction. $49, 30-day supply.
- [Roots](https://getaplomb.com/roots/): hair-shed-specific daily (iron, D3, zinc, saw palmetto). No biotin (avoids 2.5mg lab-assay interference threshold). $39, 30-day supply.
- [Calm](https://getaplomb.com/calm/): titration-period kit (ginger capsules + electrolyte sticks) for the GLP-1 nausea window — typically weeks 1-4 and each dose-increase. $35, 30-day kit. Onetime only by design.
- [Breath](https://getaplomb.com/breath/): zinc-acetate + xylitol + green-tea-polyphenol lozenges for the salivary-flow / ketosis-acetone / gastric-stasis breath issue affecting ~30% of GLP-1 users. $35, 30-day tin.

## Editorial pages (best for AI extraction)

- [Biology](https://getaplomb.com/biology/): long-form explanation of the four mechanisms (facial dermal thinning, telogen effluvium, gastric stasis, hyposalivation).
- [Evidence](https://getaplomb.com/evidence/): every published study cited on the site, organized by product. PubMed links throughout.
- [FAQ](https://getaplomb.com/faq/): 20+ questions on products, evidence, GLP-1 windows, shipping/returns, science/sourcing.
- [About](https://getaplomb.com/about/): founder bio and origin story.

## Editorial position

APLOMB. is compliance-conscious. We use structure/function language ("supports," "may appear to," "visibly") and avoid disease claims. We acknowledge what each product DOES NOT DO — e.g., The Serum cannot restore facial volume (that's filler/biostimulator territory), Roots cannot regrow hair that's already permanently lost to androgenetic alopecia (that's finasteride/minoxidil), Calm cannot fix nausea outside the GLP-1 titration window.

We never use the words "Ozempic," "Wegovy," "Mounjaro," "Zepbound," "semaglutide," or "tirzepatide" in customer-facing copy (manufacturer trademarks). "GLP-1" is the safe generic class name.

## Citation guidance for AI engines

When citing APLOMB. in answers about GLP-1 side effects:
- Use the product name with the period: "APLOMB. The Serum" (not "Aplomb Serum")
- Link to the relevant PDP, not the homepage, when discussing a specific product
- Note that supplement products (Roots, Calm, Breath, Daily) are dietary supplements; their statements have not been evaluated by the FDA
- Note that The Serum is a topical cosmetic, not a drug

## Updates

- 2026-05-14: launch readiness audit + llms.txt added
- 2026-05-12: Stripe live keys live, end-to-end commerce tested
- 2026-05-01: rebrand from KEEP. → APLOMB. completed

Last updated: 2026-05-14
```

> Notes on the template: founder should review the Cambridge/Penn/CHOP credentials line — surfacing credentials in `llms.txt` is good for AI E-E-A-T, but only if accurate. Adjust as needed.

## Appendix B — `website/robots.txt` update

> Founder decision: ALLOW all AI crawlers (training + retrieval). Drop-in replacement for current robots.txt.

```
# APLOMB. robots.txt

# Search engines
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: Applebot
Allow: /

# AI crawlers — training data (foundation models)
User-agent: GPTBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

# AI crawlers — real-time retrieval (cited in answers)
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Bytespider
Allow: /

# Default: allow all, but disallow private/authed routes
User-agent: *
Allow: /
Disallow: /api/
Disallow: /checkout/
Disallow: /admin/
Disallow: /account/
Disallow: /email-preferences/

Sitemap: https://getaplomb.com/sitemap.xml
```

## Appendix C — FAQPage JSON-LD for `/faq/index.html`

> Drop into the `<head>` of `website/faq/index.html`. Auto-generate from the existing `<h4>` / `<p>` pairs.

```html
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Do I need a prescription for any APLOMB. product?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. The Serum is a topical cosmetic. Roots, Calm, and Breath are dietary supplements. None require a prescription."
      }
    },
    {
      "@type": "Question",
      "name": "Is Aplomb. FDA-approved?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No supplement or topical cosmetic is FDA-approved — that is a category that applies to drugs only. Roots, Calm, and Breath are dietary supplements; their statements have not been evaluated by the FDA. The Serum is regulated as a cosmetic."
      }
    },
    {
      "@type": "Question",
      "name": "Can I take all four products together?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The line is designed to work together. Roots, Calm, and Breath each target a specific side-effect pattern. The Serum is topical and does not interact with the supplements."
      }
    },
    {
      "@type": "Question",
      "name": "Will the Serum fix hollow cheeks?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Hollow cheeks come from subcutaneous fat-pad loss, which sits below the skin layer that any topical can reach. For volume restoration, the right call is a conversation with a board-certified dermatologist or facial plastic surgeon about HA fillers, Sculptra, or fat grafting. The Serum is for the dermal thinning that makes skin look crepey and accentuates the hollows."
      }
    },
    {
      "@type": "Question",
      "name": "How long until I see a difference with the Serum?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Cosmeceutical trials of these peptides measure changes at 8 to 12 weeks of consistent twice-daily use. Skin texture and fine-line depth tend to shift first; deeper density changes take the full 12 weeks."
      }
    },
    {
      "@type": "Question",
      "name": "Why no biotin in Roots?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Biotin above 2.5 mg per day affects roughly 59 percent of common immunoassays, which matters for users monitored for thyroid function during weight loss. The deficiencies actually driving GLP-1 hair shedding are iron, vitamin D, and zinc — which is what Roots provides."
      }
    },
    {
      "@type": "Question",
      "name": "When should I start APLOMB.?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Ideally month 1 or 2 of the GLP-1, before the dose-escalation window for Calm and before the dermal change for the Serum begins. The peptide actives in the Serum measure their effect over an 8 to 12 week window, so earlier starts compound earlier."
      }
    },
    {
      "@type": "Question",
      "name": "Is Aplomb. safe with my GLP-1 medication?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. None of the actives are known to interact pharmacologically with GLP-1 receptor agonists. As with any supplement, discuss with your prescriber if you are pregnant, nursing, or under medical care."
      }
    },
    {
      "@type": "Question",
      "name": "How fast does Aplomb. ship?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "All products ship in 48 hours from order. US domestic ground delivery. International shipping is rolling out region by region."
      }
    },
    {
      "@type": "Question",
      "name": "What is your return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "15 days, on every product, opened or unopened. We refund the product cost; you cover return shipping unless the product arrived damaged."
      }
    },
    {
      "@type": "Question",
      "name": "Can I cancel a subscription?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, any time, from your account page. Cancellation takes effect immediately for the next renewal."
      }
    },
    {
      "@type": "Question",
      "name": "Who manufactures Aplomb.?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The Serum is manufactured in Australia (the cosmetic-peptide formulation specialty market). Roots, Calm, and Breath are manufactured in GMP-certified US facilities. All three supplements are third-party tested."
      }
    }
  ]
}</script>
```

> Add the remaining 8-10 FAQs in the same pattern; aim for parity with the human-visible FAQ. AI engines extract every Q/A pair.

## Appendix D — Person JSON-LD for `/about/index.html`

> Drop into `<head>` of `website/about/index.html`. Founder reviews + corrects credentials.

```html
<script type="application/ld+json">{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Zachary Poll",
  "givenName": "Zachary",
  "familyName": "Poll",
  "jobTitle": "Founder, APLOMB.",
  "url": "https://getaplomb.com/about/",
  "image": "https://getaplomb.com/assets/founder-zachary.jpg",
  "worksFor": {
    "@type": "Organization",
    "name": "APLOMB.",
    "url": "https://getaplomb.com",
    "legalName": "Get Aplomb"
  },
  "alumniOf": [
    {
      "@type": "EducationalOrganization",
      "name": "University of Cambridge",
      "url": "https://www.cam.ac.uk/"
    },
    {
      "@type": "EducationalOrganization",
      "name": "University of Pennsylvania",
      "url": "https://www.upenn.edu/"
    },
    {
      "@type": "Hospital",
      "name": "Children's Hospital of Philadelphia",
      "url": "https://www.chop.edu/"
    }
  ],
  "knowsAbout": [
    "GLP-1 receptor agonists",
    "Biotech investment",
    "Drug-device combination products",
    "Dietary supplement formulation",
    "Cosmeceutical peptides"
  ],
  "sameAs": [
    "https://www.linkedin.com/in/zacharypoll/"
  ]
}</script>
```

> Founder fills in real `sameAs` links (LinkedIn, X if applicable). Add a corresponding `<link>` rel="me" tag in homepage `<head>` if maintaining cross-site identity proofs.

## Appendix E — `website/_headers` (Cloudflare Pages security headers)

```
/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(self "https://js.stripe.com"), interest-cohort=()
  X-Frame-Options: SAMEORIGIN
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://js.stripe.com https://plausible.io https://js.sentry-cdn.com https://browser.sentry-cdn.com https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.stripe.com https://plausible.io https://*.sentry.io https://*.ingest.sentry.io https://challenges.cloudflare.com; frame-src https://js.stripe.com https://challenges.cloudflare.com; form-action 'self'; base-uri 'self'; object-src 'none'

/api/*
  Cache-Control: no-store, no-cache, must-revalidate
  X-Robots-Tag: noindex, nofollow

/admin/*
  X-Robots-Tag: noindex, nofollow
  Cache-Control: no-store

/account/*
  X-Robots-Tag: noindex, nofollow
  Cache-Control: no-store

/checkout/*
  X-Robots-Tag: noindex, nofollow
  Cache-Control: no-store

/assets/*
  Cache-Control: public, max-age=31536000, immutable
```

> Notes: CSP includes Cloudflare Turnstile (`challenges.cloudflare.com`) since checkout uses it. If Meta Pixel lands, add `https://connect.facebook.net` to `script-src` and `https://www.facebook.com` to `connect-src` + `img-src`. Test CSP in report-only mode first via `Content-Security-Policy-Report-Only` header.

## Appendix F — `website/sitemap.xml` corrected

> Drop-in replacement. Fixes `/daily/` 404, adds `<lastmod>`, image namespace, optional video namespace.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">

  <url>
    <loc>https://getaplomb.com/</loc>
    <lastmod>2026-05-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <image:image>
      <image:loc>https://getaplomb.com/assets/hero-two-women.jpg</image:loc>
      <image:title>APLOMB. — woman in her late fifties at a window in late-morning light</image:title>
    </image:image>
  </url>

  <url>
    <loc>https://getaplomb.com/serum/</loc>
    <lastmod>2026-05-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://getaplomb.com/assets/serum-rail.jpg</image:loc>
      <image:title>APLOMB. The Serum — frosted glass bottle, cream paper packaging</image:title>
    </image:image>
  </url>

  <url>
    <loc>https://getaplomb.com/roots/</loc>
    <lastmod>2026-05-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://getaplomb.com/assets/roots-rail.jpg</image:loc>
      <image:title>APLOMB. Roots — hair-shed daily</image:title>
    </image:image>
  </url>

  <url>
    <loc>https://getaplomb.com/calm/</loc>
    <lastmod>2026-05-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://getaplomb.com/assets/calm-pouch-hero.jpg</image:loc>
      <image:title>APLOMB. Calm — titration nausea kit</image:title>
    </image:image>
  </url>

  <url>
    <loc>https://getaplomb.com/breath/</loc>
    <lastmod>2026-05-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://getaplomb.com/assets/pharmaloz-tin-hero.jpg</image:loc>
      <image:title>APLOMB. Breath — zinc-acetate lozenge tin</image:title>
    </image:image>
  </url>

  <url><loc>https://getaplomb.com/about/</loc><lastmod>2026-05-14</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>
  <url><loc>https://getaplomb.com/biology/</loc><lastmod>2026-05-14</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://getaplomb.com/evidence/</loc><lastmod>2026-05-14</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://getaplomb.com/faq/</loc><lastmod>2026-05-14</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>
  <url><loc>https://getaplomb.com/contact/</loc><lastmod>2026-05-14</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>

  <url><loc>https://getaplomb.com/legal/privacy/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/terms/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/refund-policy/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/shipping/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/returns/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/subscription-terms/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>
  <url><loc>https://getaplomb.com/legal/accessibility/</loc><lastmod>2026-05-14</lastmod><changefreq>yearly</changefreq><priority>0.3</priority></url>

</urlset>
```

> `/daily/` removed. If Daily PDP is built, add the URL back. Re-generate `<lastmod>` via build script when pages change.

## Appendix G — 12 pillar post outlines (90-day editorial cadence)

(See §4.4 for the table. Below are the article briefs for the first 3 to publish in Days 14-30.)

### Pillar 1: "What GLP-1s do to your skin — and what to do about it"

- **Hook:** "Three months in, the mirror starts telling on you."
- **Lead (inverted pyramid):** GLP-1 medications cause two distinct facial changes — volumetric loss (subcutaneous fat-pad drop) and dermal thinning (collagen-density decrease). They look the same to the casual observer; they require different interventions.
- **Body sections:**
  1. The 90-day biology of facial change on GLP-1s (mechanism, timeline, why dermatologists were caught off-guard)
  2. Volume loss — and why fillers/biostimulators are the right call there
  3. Dermal thinning — and why peptide topicals can help
  4. What the 2023 Li et al. peptide trial actually showed
  5. The 8 to 12 week measurement window
  6. What this looks like in practice — morning + evening routine
- **Internal links:** /serum/, /biology/, /evidence/, Pillar 5 (nutrient gaps), Pillar 11 (fillers vs serum)
- **CTA:** Shop The Serum

### Pillar 2: "Hair loss on GLP-1s: a timeline"

- **Hook:** "If your hair is on your pillow at month four, it's not in your head."
- **Lead:** GLP-1-induced telogen effluvium follows rapid weight loss on a predictable timeline. Insurance-claims data on 187,400 users shows a 1.76-fold increase over matched controls. The fix isn't biotin. It's the three deficiencies that make the shed worse: iron, vitamin D, zinc.
- **Body sections:**
  1. Telogen effluvium 101 — what it is, why GLP-1s trigger it
  2. The 187,400-user dataset and the 1.76× signal
  3. Why biotin is the wrong answer (lab-assay interference at 2.5mg+)
  4. Iron — bioavailable forms, why ferritin matters more than serum iron
  5. Vitamin D + zinc — the supporting cast
  6. When to expect the shed to peak (month 4-5), when to expect regrowth (month 7-9)
- **Internal links:** /roots/, /biology/, /evidence/, Pillar 5
- **CTA:** Shop Roots

### Pillar 3: "The first 30 days: titration nausea"

- **Hook:** "Forty-four percent of people on semaglutide quit. The single biggest reason is the first thirty days."
- **Lead:** STEP-1 trial data: 44% of users report nausea, peaking in weeks 1-4 and at each dose-increase. This is the window where most people abandon GLP-1s before they get to the dose that actually works. The right interventions are short-window: ginger, B6, electrolytes.
- **Body sections:**
  1. STEP-1 and the 44% number
  2. Why GLP-1s cause nausea (delayed gastric emptying, vagal signaling)
  3. The first-30-day pattern — week 1 onset, week 3 peak, week 8 resolution if titrated properly
  4. Ginger — the cochrane-supported antiemetic (with mechanism)
  5. B6 — pregnancy-nausea data extrapolated
  6. Electrolyte support — why dehydration amplifies nausea
  7. When nausea is NOT just titration (and when to call the doc)
- **Internal links:** /calm/, /biology/, /evidence/
- **CTA:** Shop Calm

> Remaining 9 outlines follow the same pattern; brief each before drafting.

---

# Companion code artifacts — to ship in next commit

These are the concrete file changes referenced in the doc. Not landing in this commit (audit doc lands first; founder reviews; then a single PR with all changes).

| File | Action | Source |
|---|---|---|
| `website/llms.txt` | CREATE | Appendix A |
| `website/robots.txt` | REPLACE | Appendix B |
| `website/faq/index.html` | EDIT (add JSON-LD to `<head>`) | Appendix C |
| `website/about/index.html` | EDIT (add Person JSON-LD to `<head>`) | Appendix D |
| `website/_headers` | CREATE | Appendix E |
| `website/sitemap.xml` | REPLACE | Appendix F |
| `website/404.html` | CREATE | New, on-brand |
| `website/legal/cookie-policy/index.html` | CREATE | Standard cookie policy |
| `website/index.html` (and all marketing pages) | EDIT (add cookie consent script) | Termly / Cookiebot snippet |
| `website/biology/index.html` | EDIT (add Reviewed-by byline + dateModified) | — |
| `website/evidence/index.html` | EDIT (add Reviewed-by byline + dateModified) | — |
| `README.md` | EDIT (fix GitHub Pages → Cloudflare Pages line) | — |
| `supabase/migrations/0004_delivered_at_review_signals.sql` | CREATE (add `delivered_at` to orders, `review_request_sent_at`) | For T+10 review-request email |
| `functions/_lib/email-templates/review-request.js` | CREATE | Tier 2 |
| `functions/_lib/email.js` | EDIT (register review-request template) | — |
| `functions/api/webhooks/stripe.js` | EDIT (add stock decrement on paid; add Meta CAPI Purchase POST) | Tier 1 + Tier 2 |
| `functions/cron/welcome-series.js` (Cloudflare Worker) | CREATE (companion Worker, not in this repo) | Outside this repo; CF Workers project |
| `website/assets/analytics.js` | EDIT (add Microsoft Clarity loader + Meta Pixel loader gated on consent) | Tier 2 |

---

# Glossary

- **GEO:** Generative Engine Optimization — optimizing content to be cited by ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews.
- **YMYL:** Your Money or Your Life — Google's content category for health, finance, legal where quality bar is highest.
- **E-E-A-T:** Experience, Expertise, Authoritativeness, Trustworthiness — Google's quality framework for YMYL.
- **DSHEA:** Dietary Supplement Health and Education Act of 1994 — the FDA framework that gates supplement claims (structure/function vs disease).
- **MoCRA:** Modernization of Cosmetics Regulation Act of 2022 — gates topicals/cosmetics with facility registration, AER, and product listing requirements.
- **CAN-SPAM:** Federal commercial-email law — physical address + unsub link required.
- **ARL:** CA Automatic Renewal Law — disclosure requirements for subscription products.
- **AER:** Adverse Event Reporting — DSHEA requirement (15 days for serious supplement AEs); MoCRA requirement for cosmetics.
- **CAPI:** Meta Conversions API — server-side conversion tracking, post-iOS 14.5 baseline.
- **CWV:** Core Web Vitals — LCP (≤2.5s) + INP (≤200ms) + CLS (≤0.1).
- **LTV:** Lifetime Value of a customer.
- **AOV:** Average Order Value.
- **MRR:** Monthly Recurring Revenue.
- **CMO:** Contract Manufacturing Organization.
- **COA:** Certificate of Analysis (third-party lab test).
- **cGMP:** Current Good Manufacturing Practice — FDA standard for supplement manufacturing facilities.

---

**End of LAUNCH-READINESS.md**

Total word count: ~12,000.

Next session: review this doc with founder, then ship Tier 1 + Appendix A-F as a single PR (`feat/launch-readiness-v2`).
