// POST /cron/renewal-reminder
//
// Auth: X-Cron-Secret header must match env.CRON_SHARED_SECRET (poor-man's
// shared secret; sufficient because the only caller is a Cloudflare Worker
// scheduled trigger we control).
//
// Scans subscriptions whose current_period_end falls 4-6 days from now, has
// status='active', and hasn't been reminded this cycle. Sends the
// renewal-heads-up email and stamps renewal_reminder_sent_at.

import { json, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { sendEmail } from '../_lib/email.js';
import { PRODUCTS } from '../_lib/products.js';

export const onRequestPost = async ({ request, env }) => {
  const provided = request.headers.get('x-cron-secret') || '';
  if (!env.CRON_SHARED_SECRET || provided !== env.CRON_SHARED_SECRET) {
    return new Response('Forbidden', { status: 401 });
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const from = new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString();
  const to = new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString();

  const { data: subs, error } = await sb.from('subscriptions')
    .select('*')
    .eq('status', 'active')
    .is('renewal_reminder_sent_at', null)
    .gte('current_period_end', from)
    .lte('current_period_end', to);

  if (error) return serverError(error.message);

  let processed = 0;
  for (const sub of subs || []) {
    // Build items list from sub.items (Stripe subscription_items shape, jsonb)
    const items = (sub.items || []).map((si) => {
      const priceProductId = si?.price?.id || si?.price?.product || '';
      // Best-effort map back to our catalog key (matches one of the env-configured price IDs)
      const matchedKey = Object.keys(PRODUCTS).find((k) => {
        const upper = k.toUpperCase();
        return env[`STRIPE_PRICE_${upper}_SUBSCRIPTION`] === priceProductId;
      });
      const product = matchedKey ? PRODUCTS[matchedKey] : null;
      return {
        name: product?.name || si?.price?.nickname || 'Subscription item',
        quantity: si?.quantity || 1,
        unitPriceCents: si?.price?.unit_amount || (product?.unitPriceCents || 0),
        productKey: matchedKey || 'unknown',
      };
    });

    const totalCents = items.reduce((acc, it) => acc + (it.unitPriceCents * it.quantity), 0);

    try {
      await sendEmail(env, 'renewal-heads-up', {
        to: sub.email,
        subscription: sub,
        customer: { email: sub.email },
        items,
        totalCents,
        daysUntilRenewal: 5,
      });
      await sb.from('subscriptions')
        .update({ renewal_reminder_sent_at: new Date().toISOString() })
        .eq('id', sub.id);
      processed++;
    } catch (e) {
      console.warn('renewal-reminder send failed for', sub.id, e?.message || e);
    }
  }

  return json({ processed, scanned: subs?.length || 0 });
};
