# Aplomb. — Commerce Runbook

How to wire the Cloudflare Pages deploy, Stripe, Supabase, and Resend so that getaplomb.com can take real orders. Every step is the kind of thing only a human with credentials can do; the code is in place.

## 0. Prerequisites
- GitHub repo: `zacharybpoll-cmyk/aplomb-clinic` (already exists; live on GitHub Pages today).
- Cloudflare account with Pages enabled.
- Stripe account.
- Supabase account.
- Resend account.

## 1. Cloudflare Pages — connect the repo
1. In the Cloudflare dashboard, **Workers & Pages → Create application → Pages → Connect to Git**.
2. Select `zacharybpoll-cmyk/aplomb-clinic`.
3. Production branch: `main`. Build command: leave blank. Output directory: `/` (the repo root is the site).
4. Compatibility flags: tick `nodejs_compat` (also lives in `wrangler.toml`).
5. Custom domain: add `getaplomb.com` and `www.getaplomb.com`. Cloudflare will guide DNS; replace the GitHub-Pages A records with the CF ones.

## 2. Stripe — products, prices, webhook
1. Create the Stripe account in **test mode** first. Do everything here in test mode, then duplicate to live mode at the end.
2. Stripe → **Products** → create five products. Use these exact Names and Default prices (cents):
   - `APLOMB. The Serum.` &mdash; one-time **$129.00**, recurring 60-day **$116.10**
   - `APLOMB. Daily.` &mdash; one-time **$49.00**, recurring 30-day **$41.65**
   - `APLOMB. Roots.` &mdash; one-time **$39.00**, recurring 30-day **$33.15**
   - `APLOMB. Calm.` &mdash; one-time **$35.00** only (titration kit, not subscription)
   - `APLOMB. Breath.` &mdash; one-time **$35.00**, recurring 30-day **$29.75**
3. Copy each Price ID. There are nine total (Calm only has one).
4. Stripe → **Tax** → enable. Set the origin address to your business address. Stripe Tax does the registration and filing for the states where you cross threshold.
5. Stripe → **Developers → Webhooks** → add endpoint `https://getaplomb.com/api/webhooks/stripe`. Subscribe to:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Copy the webhook signing secret (`whsec_...`).

## 3. Supabase — project + schema
1. Create a new Supabase project in the same region as your Cloudflare account.
2. SQL editor → paste `supabase/migrations/0001_init.sql` and run.
3. Project Settings → API → copy the **Project URL**, **anon public key**, and **service_role key**.
4. Authentication → Sign In Providers → enable **Email** with magic-link only (we are not using passwords).

## 4. Resend — domain + API key
1. Create a Resend account.
2. Add the domain `getaplomb.com`. Resend gives you DKIM and SPF records — paste them into Cloudflare DNS.
3. Verify the domain (this can take a few minutes to propagate).
4. Create an API key, scope: `Send emails`. Copy it.

## 5. Cloudflare Pages env vars
In **Workers & Pages → aplomb-clinic → Settings → Environment variables**, set the following for both **Production** and **Preview** environments. (Use Stripe live keys for Production, test keys for Preview.)

```
STRIPE_SECRET_KEY                  sk_live_... (or sk_test_... in preview)
STRIPE_PUBLISHABLE_KEY             pk_live_... (or pk_test_...)
STRIPE_WEBHOOK_SECRET              whsec_... (the signing secret from Stripe → Webhooks)

STRIPE_PRICE_SERUM_ONETIME         price_...
STRIPE_PRICE_SERUM_SUBSCRIPTION    price_...
STRIPE_PRICE_DAILY_ONETIME         price_...
STRIPE_PRICE_DAILY_SUBSCRIPTION    price_...
STRIPE_PRICE_ROOTS_ONETIME         price_...
STRIPE_PRICE_ROOTS_SUBSCRIPTION    price_...
STRIPE_PRICE_CALM_ONETIME          price_...
STRIPE_PRICE_BREATH_ONETIME        price_...
STRIPE_PRICE_BREATH_SUBSCRIPTION   price_...

SUPABASE_URL                       https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY          eyJhb... (server-side only — never goes to the browser)
SUPABASE_ANON_KEY                  eyJhb...

RESEND_API_KEY                     re_...
EMAIL_FROM                         Aplomb. <orders@getaplomb.com>

SITE_URL                           https://getaplomb.com
```

The `STRIPE_PUBLISHABLE_KEY` also needs to be in the HTML. The simplest path: add a meta tag to each page that includes `assets/checkout.js`:

```html
<meta name="stripe-publishable-key" content="pk_live_...">
```

Or set it once at the top of `assets/checkout.js` (acceptable — it is a publishable key).

## 6. Local development
1. `npm install`
2. `cp .dev.vars.example .dev.vars` and fill in test values.
3. `npm run dev` — `wrangler` serves the static site + Functions on http://localhost:8788.
4. To test webhooks locally: `stripe listen --forward-to localhost:8788/api/webhooks/stripe`. Stripe CLI prints a `whsec_...` for local; put it in `.dev.vars`.

## 7. End-to-end smoke test (test mode)
1. Visit the preview URL (`*.pages.dev`).
2. Add Serum to bag, open checkout.
3. Email + name → Continue → Stripe Address Element + Payment Element render.
4. Use `4242 4242 4242 4242`, any future date, any CVC, any ZIP. Submit.
5. Stripe redirects you to `/checkout/success/?payment_intent=pi_...`.
6. Verify in this order:
   - Stripe dashboard shows the PaymentIntent succeeded.
   - Supabase `orders` row has status `paid`.
   - The receipt email has landed in the inbox.
   - Tax line is present and reasonable.
7. Trigger the failure path with `4000 0000 0000 0002` → confirm no `paid` row is created.
8. Replay the success webhook from the Stripe dashboard → confirm `stripe_events` dedupes; no duplicate order rows.

## 8. Going live
1. Switch all env vars from test to live keys (Cloudflare Pages → Settings → Env vars → Production).
2. Re-create the webhook in Stripe live mode (the secret changes; update `STRIPE_WEBHOOK_SECRET`).
3. Re-deploy (push to main triggers it).
4. Run the dress rehearsal: real card, real address, real shipment, real cancellation via Customer Portal.

## 9. Day-2 ops
- **Refunds:** Stripe dashboard → find the charge → Refund. The webhook flips the order to `refunded` automatically and emails the customer (TODO: refund email template).
- **Cancellations:** customer self-serves via Stripe Customer Portal (Week 2). Until that ships, do them in the Stripe dashboard.
- **Inventory:** edit the `inventory` table directly until the admin UI ships in Week 3.
