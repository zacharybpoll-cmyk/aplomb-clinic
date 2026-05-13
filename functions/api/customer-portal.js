// POST /api/customer-portal
//
// Requires the sb-access-token cookie (set after a magic-link sign-in).
// Mints a Stripe Billing Portal session for the customer and returns its URL.
// The /account/ dashboard's "Manage subscription" button calls this and
// then window.location's to session.url.

import { json, serverError } from '../_lib/json.js';
import { stripeClient } from '../_lib/stripe.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { getSessionFromRequest } from '../_lib/auth.js';

export const onRequestPost = async ({ request, env }) => {
  const session = await getSessionFromRequest(request, env);
  if (!session) {
    return new Response(JSON.stringify({ error: 'Sign in to manage your subscription.' }), {
      status: 401, headers: { 'content-type': 'application/json' },
    });
  }

  const stripe = stripeClient(env);
  if (!stripe) return new Response(JSON.stringify({ error: 'Billing portal not configured.' }), {
    status: 503, headers: { 'content-type': 'application/json' },
  });

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  // Look up the customer row by the JWT's email claim
  let stripeCustomerId = null;
  try {
    const { data } = await sb.from('customers')
      .select('stripe_customer_id')
      .eq('email', session.email)
      .maybeSingle();
    stripeCustomerId = data?.stripe_customer_id || null;
  } catch (_) {
    return serverError('Could not look up customer.');
  }

  if (!stripeCustomerId) {
    return new Response(JSON.stringify({ error: 'No subscription on file.' }), {
      status: 404, headers: { 'content-type': 'application/json' },
    });
  }

  let portalSession;
  try {
    portalSession = await stripe.billingPortal.sessions.create({
      customer: stripeCustomerId,
      return_url: `${env.SITE_URL || 'https://getaplomb.com'}/account/`,
    });
  } catch (e) {
    return serverError('Could not create portal session.');
  }

  return json({ url: portalSession.url });
};
