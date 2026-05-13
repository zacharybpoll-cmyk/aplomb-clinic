// GET /api/admin/orders
//
// Auth: Cloudflare Access protects this route at the edge via founder's email
// allowlist (configured in CF dashboard → Access → Applications). No in-code
// auth check — we trust the upstream.
//
// Returns paid orders that haven't shipped yet, newest first.

import { json, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';

export const onRequestGet = async ({ request, env }) => {
  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const url = new URL(request.url);
  const limit = Math.min(200, Math.max(1, parseInt(url.searchParams.get('limit') || '50', 10)));
  const status = url.searchParams.get('status'); // optional: paid|shipped|all

  let query = sb.from('orders').select(`
    id, email, customer_name, status, line_items, shipping_address,
    subtotal_cents, tax_cents, shipping_cents, total_cents, total_cents_override,
    tracking_number, carrier, paid_at, shipped_at, created_at,
    stripe_payment_intent_id, stripe_checkout_session_id, stripe_subscription_id, stripe_customer_id
  `).order('paid_at', { ascending: false }).limit(limit);

  if (!status || status === 'paid') {
    query = query.eq('status', 'paid').is('tracking_number', null);
  } else if (status === 'shipped') {
    query = query.eq('status', 'shipped');
  } else if (status === 'all') {
    // no extra filter
  }

  const { data, error } = await query;
  if (error) return serverError(error.message);
  return json({ orders: data || [], count: (data || []).length });
};
