// POST /api/checkout
//
// Body: { email, name, lineItems: [{ productKey, quantity, mode }], mode? }
// Returns: { clientSecret, orderId } (PaymentIntent) or { checkoutUrl, orderId } (Checkout Session)
//
// Validates the cart against the server-side product catalog (never trusts
// client-supplied prices). Branches on mode: 'onetime' creates a Stripe
// PaymentIntent with automatic payment methods + Stripe Tax; 'subscription'
// creates a Checkout Session with recurring billing. Enforces uniform mode
// across all items. Persists a pending row in Supabase orders.
// The webhook handler (functions/api/webhooks/stripe.js) updates orders
// on payment_intent.succeeded (PaymentIntent) or checkout.session.completed (Session).

import { json, badRequest, serverError } from '../_lib/json.js';
import { stripeClient } from '../_lib/stripe.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { getProduct, computeSubtotalCents, computeShippingCents, getStripePriceIds } from '../_lib/products.js';

export const onRequestPost = async ({ request, env }) => {
  let body;
  try {
    body = await request.json();
  } catch (_) {
    return badRequest('Invalid JSON body.');
  }

  const email = (body?.email || '').trim().toLowerCase();
  const name = (body?.name || '').trim();
  const couponCode = (body?.couponCode || '').trim();
  const lineItems = Array.isArray(body?.lineItems) ? body.lineItems : [];
  const shippingAddress = body?.shippingAddress || null;
  // Cross-context ad-sharing opt-in (browser Pixel + server CAPI). Stored on the
  // Stripe object so the webhook can suppress the Meta Conversions API send.
  // Defaults to false (no sharing) when absent — the privacy-protective default.
  const adConsent = body?.adConsent === true;

  if (!email || !email.includes('@')) return badRequest('A valid email is required.');
  if (!name) return badRequest('Your full name is required.');
  if (!lineItems.length) return badRequest('Your cart is empty.');

  // Validate every line item against the server catalog.
  const validated = [];
  let cartMode = null; // 'onetime' or 'subscription'
  for (const li of lineItems) {
    const p = getProduct(li.productKey);
    if (!p) return badRequest(`Unknown product: ${li.productKey}`);
    const qty = Math.max(1, Math.min(99, (li.quantity | 0) || 1));
    const itemMode = (li.mode || body?.mode || 'onetime').toLowerCase();
    if (itemMode !== 'onetime' && itemMode !== 'subscription') {
      return badRequest(`Invalid mode: ${itemMode}. Use 'onetime' or 'subscription'.`);
    }
    // Enforce uniform mode across cart
    if (cartMode === null) {
      cartMode = itemMode;
    } else if (cartMode !== itemMode) {
      return badRequest('All items must be either one-time or subscription. Mixed carts are not allowed.');
    }
    validated.push({ productKey: li.productKey, name: p.name, quantity: qty, unitPriceCents: p.unitPriceCents, mode: itemMode });
  }

  const subtotalCents = computeSubtotalCents(validated);
  if (subtotalCents < 100) return badRequest('Cart subtotal too small.');

  const stripe = stripeClient(env);
  if (!stripe) return serverError('Payments are not configured for this deploy.');

  let customer;
  try {
    const existing = await stripe.customers.search({ query: `email:'${email.replace(/'/g, "\\'")}'`, limit: 1 });
    customer = existing.data[0]
      || await stripe.customers.create({ email, name, metadata: { source: 'getaplomb.com' } });
  } catch (e) {
    return serverError('Could not create customer.');
  }

  // Branch on cart mode
  if (cartMode === 'subscription') {
    return handleSubscriptionCheckout(validated, email, name, customer, env, stripe, adConsent);
  } else {
    return handleOnetimeCheckout(validated, email, name, customer, env, stripe, shippingAddress, adConsent, couponCode);
  }
};

// First-order welcome discount. The newsletter welcome series has long
// promised "10% off your first order with code APLOMB10" but no redemption
// path existed anywhere — this closes that gap. Single fixed code, server is
// the only authority, capped, first-order-only, every decision logged in
// order metadata. Env can override the code/percent (CF Pages):
//   WELCOME_COUPON_CODE  (default 'APLOMB10')
//   WELCOME_COUPON_PCT   (default '10', clamped 1..50)
// Shipping/free-ship are intentionally computed on the ORIGINAL subtotal so
// the free-shipping promise the cart already made to the customer still holds.
async function resolveWelcomeDiscount({ email, couponCode, subtotalCents, env }) {
  const none = { pct: 0, discountCents: 0, code: null, reason: 'none' };
  const configured = (env.WELCOME_COUPON_CODE || 'APLOMB10').trim().toUpperCase();
  if (!couponCode || couponCode.trim().toUpperCase() !== configured) return none;

  let pct = parseInt(env.WELCOME_COUPON_PCT, 10);
  if (!Number.isFinite(pct)) pct = 10;
  pct = Math.max(1, Math.min(50, pct));

  // First-order-only. If we can't reach the DB, honor the code rather than
  // block a sale over a 10% check — it's a small, single, fixed code.
  let reason = 'applied';
  const sb = supabaseAdmin(env);
  if (sb && email) {
    try {
      const { data, error } = await sb
        .from('orders')
        .select('id')
        .eq('email', email)
        .in('status', ['paid', 'shipped', 'fulfilled'])
        .limit(1);
      if (error) {
        reason = 'applied:db-error';
      } else if (data && data.length) {
        return { ...none, reason: 'denied:not-first-order' };
      }
    } catch (_) {
      reason = 'applied:db-exception';
    }
  } else {
    reason = 'applied:no-db';
  }

  const discountCents = Math.round((subtotalCents * pct) / 100);
  return { pct, discountCents, code: configured, reason };
}

async function handleOnetimeCheckout(validated, email, name, customer, env, stripe, shippingAddress, adConsent, couponCode) {
  const subtotalCents = computeSubtotalCents(validated);
  const shippingCents = computeShippingCents(validated, env);

  const discount = await resolveWelcomeDiscount({ email, couponCode, subtotalCents, env });
  const discountCents = discount.discountCents;
  const discountedSubtotal = subtotalCents - discountCents;
  const discountRatio = subtotalCents > 0 ? discountedSubtotal / subtotalCents : 1;

  // Compute sales tax via Stripe Tax when we have a shipping address.
  // The address is collected by the client's Stripe Address Element before
  // this request. Missing address (e.g., subscription-only Stripe Checkout
  // path, or test traffic without the UI) falls back to no-tax — the
  // subscription path uses automatic_tax inside Stripe Checkout instead.
  let taxCents = 0;
  let taxCalculationId = null;
  let stripeShipping = null;

  if (shippingAddress?.address?.postal_code && shippingAddress?.address?.country) {
    try {
      const calc = await stripe.tax.calculations.create({
        currency: 'usd',
        customer_details: {
          address: {
            line1: shippingAddress.address.line1 || '',
            line2: shippingAddress.address.line2 || '',
            city: shippingAddress.address.city || '',
            state: shippingAddress.address.state || '',
            postal_code: shippingAddress.address.postal_code,
            country: shippingAddress.address.country,
          },
          address_source: 'shipping',
        },
        line_items: validated.map(v => ({
          amount: Math.round(v.unitPriceCents * v.quantity * discountRatio),
          quantity: v.quantity,
          reference: v.productKey,
          tax_behavior: 'exclusive',
        })),
        shipping_cost: shippingCents > 0
          ? { amount: shippingCents, tax_behavior: 'exclusive' }
          : undefined,
      });
      taxCents = calc.tax_amount_exclusive || 0;
      taxCalculationId = calc.id;
    } catch (e) {
      // If Stripe Tax fails (invalid address, no nexus, transient API error),
      // proceed without tax rather than blocking the order. We log via the
      // PI metadata so we can find these later.
      taxCalculationId = `error:${(e?.message || 'unknown').slice(0, 80)}`;
    }

    stripeShipping = {
      name: shippingAddress.name || name,
      phone: shippingAddress.phone || undefined,
      address: shippingAddress.address,
    };
  }

  const chargeAmount = discountedSubtotal + shippingCents + taxCents;

  let intent;
  try {
    intent = await stripe.paymentIntents.create({
      amount: chargeAmount,
      currency: 'usd',
      customer: customer.id,
      receipt_email: email,
      automatic_payment_methods: { enabled: true },
      metadata: {
        cart: JSON.stringify(validated.map(v => ({ k: v.productKey, q: v.quantity }))),
        customer_name: name,
        subtotal_cents: String(discountedSubtotal),
        subtotal_before_discount_cents: String(subtotalCents),
        shipping_cents: String(shippingCents),
        tax_cents: String(taxCents),
        tax_calculation_id: taxCalculationId || '',
        coupon_code: discount.code || '',
        coupon_pct: discount.pct ? String(discount.pct) : '',
        discount_cents: String(discountCents),
        coupon_reason: discount.reason,
        ad_consent: adConsent ? '1' : '0',
      },
      ...(stripeShipping ? { shipping: stripeShipping } : {}),
    });
  } catch (e) {
    return serverError('Could not create payment intent.');
  }

  // Persist pending order in Supabase (best-effort). total_cents is a generated
  // column (subtotal + shipping + tax) so we don't write it directly.
  const sb = supabaseAdmin(env);
  let orderId = null;
  if (sb) {
    try {
      const { data, error } = await sb.from('orders').insert({
        stripe_payment_intent_id: intent.id,
        stripe_customer_id: customer.id,
        email,
        customer_name: name,
        subtotal_cents: discountedSubtotal,
        shipping_cents: shippingCents,
        tax_cents: taxCents,
        currency: 'usd',
        status: 'pending',
        line_items: validated,
        shipping_address: stripeShipping || null,
        metadata: discountCents > 0
          ? {
              coupon_code: discount.code,
              coupon_pct: discount.pct,
              discount_cents: discountCents,
              subtotal_before_discount_cents: subtotalCents,
              coupon_reason: discount.reason,
            }
          : {},
      }).select('id').single();
      if (!error) orderId = data?.id || null;
    } catch (_) {}
  }

  return json({ clientSecret: intent.client_secret, orderId });
}

async function handleSubscriptionCheckout(validated, email, name, customer, env, stripe, adConsent) {
  // Map validated items to Stripe line_items with subscription prices
  const lineItems = [];
  for (const item of validated) {
    const priceIds = getStripePriceIds(env, item.productKey);
    if (!priceIds.subscription) {
      return serverError(`No subscription price configured for ${item.productKey}.`);
    }
    lineItems.push({
      price: priceIds.subscription,
      quantity: item.quantity,
    });
  }

  // Shipping for subscription Checkout Sessions: Stripe requires a pre-created
  // `shipping_rate` ID (inline rates aren't supported in Sessions). We expose
  // a free-shipping rate AND a flat rate so customers over the threshold see
  // free shipping. Both IDs are env vars (STRIPE_SHIPPING_RATE_FLAT,
  // STRIPE_SHIPPING_RATE_FREE) — provisioned via scripts/sync-stripe-shipping.mjs.
  const shippingOptions = [];
  if (env.STRIPE_SHIPPING_RATE_FLAT) {
    shippingOptions.push({ shipping_rate: env.STRIPE_SHIPPING_RATE_FLAT });
  }
  if (env.STRIPE_SHIPPING_RATE_FREE) {
    shippingOptions.push({ shipping_rate: env.STRIPE_SHIPPING_RATE_FREE });
  }

  let session;
  try {
    session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      customer: customer.id,
      // When attaching an existing customer + automatic_tax, Stripe needs
      // permission to write the address collected at checkout back onto
      // the customer (for tax computation on future renewals).
      customer_update: { shipping: 'auto', address: 'auto', name: 'auto' },
      line_items: lineItems,
      success_url: `${env.SITE_URL || 'https://getaplomb.com'}/checkout/success/?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${env.SITE_URL || 'https://getaplomb.com'}/checkout/`,
      automatic_tax: { enabled: true },
      allow_promotion_codes: true,
      shipping_address_collection: { allowed_countries: ['US'] },
      metadata: { ad_consent: adConsent ? '1' : '0' },
      ...(shippingOptions.length ? { shipping_options: shippingOptions } : {}),
      subscription_data: {
        metadata: {
          cart: JSON.stringify(validated.map(v => ({ k: v.productKey, q: v.quantity }))),
          customer_name: name,
          ad_consent: adConsent ? '1' : '0',
        },
      },
      // consent_collection.terms_of_service requires a ToS URL on the Stripe
      // account (Dashboard → Settings → Public details). Our /checkout/ page
      // already carries the legal agreement in-line, so we skip Stripe's
      // redundant checkbox. Re-enable here after configuring the dashboard
      // URL if you want the extra friction.
    });
  } catch (e) {
    return serverError('Could not create checkout session.');
  }

  // Persist pending order in Supabase with stripe_checkout_session_id
  const sb = supabaseAdmin(env);
  let orderId = null;
  if (sb) {
    try {
      const { data, error } = await sb.from('orders').insert({
        stripe_checkout_session_id: session.id,
        stripe_customer_id: customer.id,
        email,
        customer_name: name,
        subtotal_cents: computeSubtotalCents(validated),
        currency: 'usd',
        status: 'pending',
        line_items: validated,
      }).select('id').single();
      if (!error) orderId = data?.id || null;
    } catch (_) {}
  }

  return json({ checkoutUrl: session.url, orderId });
}
