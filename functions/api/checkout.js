// POST /api/checkout
//
// Body: { email, name, lineItems: [{ productKey, quantity }] }
// Returns: { clientSecret, orderId }
//
// Validates the cart against the server-side product catalog (never trusts
// client-supplied prices), creates a Stripe PaymentIntent with automatic
// payment methods + Stripe Tax enabled, and persists a pending row in
// Supabase orders. The webhook handler (functions/api/webhooks/stripe.js)
// flips that row to paid on payment_intent.succeeded.

import { json, badRequest, serverError } from '../_lib/json.js';
import { stripeClient } from '../_lib/stripe.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { getProduct, computeSubtotalCents } from '../_lib/products.js';

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
  for (const li of lineItems) {
    const p = getProduct(li.productKey);
    if (!p) return badRequest(`Unknown product: ${li.productKey}`);
    const qty = Math.max(1, Math.min(99, (li.quantity | 0) || 1));
    validated.push({ productKey: li.productKey, name: p.name, quantity: qty, unitPriceCents: p.unitPriceCents });
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

  let intent;
  try {
    intent = await stripe.paymentIntents.create({
      amount: subtotalCents,
      currency: 'usd',
      customer: customer.id,
      receipt_email: email,
      automatic_payment_methods: { enabled: true },
      metadata: {
        cart: JSON.stringify(validated.map(v => ({ k: v.productKey, q: v.quantity }))),
        customer_name: name,
      },
      shipping: undefined, // collected by Stripe Address Element on the client
    });
  } catch (e) {
    return serverError('Could not create payment intent.');
  }

  // Persist pending order in Supabase (best-effort — we still return the
  // client_secret if the DB write fails, because the webhook will reconcile).
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
        currency: 'usd',
        status: 'pending',
        line_items: validated,
      }).select('id').single();
      if (!error) orderId = data?.id || null;
    } catch (_) {}
  }

  return json({ clientSecret: intent.client_secret, orderId });
};
