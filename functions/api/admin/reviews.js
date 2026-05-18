// /api/admin/reviews
//
//   GET  ?status=pending|published|rejected|all   (default: pending)
//        Lists reviews for the moderation tab, newest first.
//
//   POST { id, action: 'publish' | 'reject' | 'unpublish' }
//        Flips a review's status. Publishing stamps published_at so the PDP
//        ordering is stable; unpublish/reject clears it.
//
// Auth: Cloudflare Access protects /api/admin/* at the edge (founder email
// allowlist). No in-code auth check — same trust model as orders.js /
// ship-order.js. Nothing reaches a PDP until it is published here.

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';

const STATUSES = new Set(['pending', 'published', 'rejected']);

export const onRequestGet = async ({ request, env }) => {
  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const url = new URL(request.url);
  const status = (url.searchParams.get('status') || 'pending').toLowerCase();
  const limit = Math.min(200, Math.max(1, parseInt(url.searchParams.get('limit') || '100', 10)));

  let q = sb
    .from('reviews')
    .select('id, order_id, product_key, rating, title, body, customer_name, status, created_at, published_at')
    .order('created_at', { ascending: false })
    .limit(limit);

  if (status !== 'all') {
    if (!STATUSES.has(status)) return badRequest('Invalid status filter.');
    q = q.eq('status', status);
  }

  const { data, error } = await q;
  if (error) return serverError(error.message);
  return json({ reviews: data || [], count: (data || []).length });
};

export const onRequestPost = async ({ request, env }) => {
  let body;
  try {
    body = await request.json();
  } catch (_) {
    return badRequest('Invalid JSON body.');
  }

  const id = String(body?.id || '').trim();
  const action = String(body?.action || '').trim().toLowerCase();
  if (!id) return badRequest('id is required.');

  let patch;
  if (action === 'publish') {
    patch = { status: 'published', published_at: new Date().toISOString() };
  } else if (action === 'reject') {
    patch = { status: 'rejected', published_at: null };
  } else if (action === 'unpublish') {
    patch = { status: 'pending', published_at: null };
  } else {
    return badRequest("action must be 'publish', 'reject', or 'unpublish'.");
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const { data, error } = await sb
    .from('reviews')
    .update(patch)
    .eq('id', id)
    .select('id, status, published_at')
    .single();

  if (error || !data) {
    return new Response(JSON.stringify({ error: 'Review not found or update failed.' }), {
      status: 404,
      headers: { 'content-type': 'application/json' },
    });
  }

  return json({ review: data });
};
