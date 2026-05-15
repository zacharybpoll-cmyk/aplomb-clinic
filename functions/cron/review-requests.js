// POST /cron/review-requests
//
// Auth: X-Cron-Secret header must match env.CRON_SHARED_SECRET.
//
// Scans orders shipped 10+ days ago that have not yet received a review
// request, and sends the review-request email. Idempotent via
// orders.review_request_sent_at.
//
// When carrier-tracking delivered_at is wired (Tier 3), this query should
// switch to `coalesce(delivered_at + interval '5 days', shipped_at + interval '10 days')`.

import { json, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { sendEmail } from '../_lib/email.js';

export const onRequestPost = async ({ request, env }) => {
  const provided = request.headers.get('x-cron-secret') || '';
  if (!env.CRON_SHARED_SECRET || provided !== env.CRON_SHARED_SECRET) {
    return new Response('Forbidden', { status: 401 });
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  // Orders shipped between 10 and 30 days ago, with no review request yet.
  // Cap on the upper bound so a long-dormant queue doesn't fire a stale batch.
  const minDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  const maxDate = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString();

  const { data: orders, error } = await sb.from('orders')
    .select('*')
    .is('review_request_sent_at', null)
    .gte('shipped_at', minDate)
    .lte('shipped_at', maxDate)
    .in('status', ['shipped', 'fulfilled', 'paid'])
    .limit(500);

  if (error) return serverError(error.message);

  let processed = 0;
  for (const order of orders || []) {
    try {
      await sendEmail(env, 'review-request', { order });
      await sb.from('orders')
        .update({ review_request_sent_at: new Date().toISOString() })
        .eq('id', order.id);
      processed++;
    } catch (e) {
      console.warn('review-request send failed for', order.id, e?.message || e);
    }
  }

  return json({ processed, scanned: orders?.length || 0 });
};
