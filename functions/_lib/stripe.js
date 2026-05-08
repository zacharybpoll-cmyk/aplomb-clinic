// Stripe client factory for Cloudflare Pages Functions. Returns null if the
// secret key is unset so callers can degrade gracefully in preview deploys.

import Stripe from 'stripe';

export function stripeClient(env) {
  if (!env.STRIPE_SECRET_KEY) return null;
  return new Stripe(env.STRIPE_SECRET_KEY, {
    apiVersion: '2024-12-18.acacia',
    httpClient: Stripe.createFetchHttpClient(),
  });
}
