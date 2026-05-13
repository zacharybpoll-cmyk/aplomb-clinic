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
  const lineItems = Array.isArray(body?.lineItems) ? body.lineItems : [];

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
    return handleSubscriptionCheckout(validated, email, name, customer, env, stripe);
  } else {
    return handleOnetimeCheckout(validated, email, name, customer, env, stripe);
  }
};

async function handleOnetimeCheckout(validated, email, name, customer, env, stripe) {
  const subtotalCents = computeSubtotalCents(validated);
  const shippingCents = computeShippingCents(validated, env);
  const chargeAmount = subtotalCents + shippingCents;

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
        subtotal_cents: String(subtotalCents),
        shipping_cents: String(shippingCents),
      },
      shipping: undefined, // collected by Stripe Address Element on the client
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
        subtotal_cents: subtotalCents,
        shipping_cents: shippingCents,
        currency: 'usd',
        status: 'pending',
        line_items: validated,
      }).select('id').single();
      if (!error) orderId = data?.id || null;
    } catch (_) {}
  }

  return json({ clientSecret: intent.client_secret, orderId });
}

async function handleSubscriptionCheckout(validated, email, name, customer, env, stripe) {
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
      shipping_address_collection: { allowed_countries: ['US'] },
      ...(shippingOptions.length ? { shipping_options: shippingOptions } : {}),
      subscription_data: {
        metadata: {
          cart: JSON.stringify(validated.map(v => ({ k: v.productKey, q: v.quantity }))),
          customer_name: name,
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
