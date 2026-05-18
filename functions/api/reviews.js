// /api/reviews
//
//   GET  /api/reviews?product=serum
//        Public. Returns only status='published' reviews for one product plus
//        an aggregate { count, avg }. First name only — never email.
//
//   POST /api/reviews
//        Body: { rt, product, rating, title?, body, name? }
//        `rt` is the HMAC review token from the T+10-day review-request email.
//        It proves the submitter bought a real shipped order, so no email
//        enumeration and no CAPTCHA plumbing on the PDP. Inserts status
//        ='pending' — a human publishes it via /api/admin/reviews. One review
//        per (order, product); a second attempt is reported, not duplicated.
//
// RLS keeps the table server-only; all filtering happens here before anything
// leaves the function. We never invent reviews and never show unpublished ones.

import { json, badRequest, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { verifyReviewToken } from '../_lib/auth.js';
import { PRODUCTS } from '../_lib/products.js';

const PRODUCT_KEYS = new Set(Object.keys(PRODUCTS));

function firstName(name) {
  const n = String(name || '').trim();
  if (!n) return '';
  return n.split(/\s+/)[0].slice(0, 40);
}

export const onRequestGet = async ({ request, env }) => {
  const url = new URL(request.url);
  const product = (url.searchParams.get('product') || '').trim().toLowerCase();
  if (!PRODUCT_KEYS.has(product)) return badRequest('Unknown product.');

  const sb = supabaseAdmin(env);
  if (!sb) {
    // Degrade honestly: an empty, valid payload — the PDP shows "no reviews
    // yet", never an error and never fabricated content.
    return json({ product, count: 0, avg: null, items: [] });
  }

  const { data, error } = await sb
    .from('reviews')
    .select('rating, title, body, customer_name, published_at')
    .eq('product_key', product)
    .eq('status', 'published')
    .order('published_at', { ascending: false })
    .limit(50);

  if (error) {
    console.warn('[reviews] read failed', error.message);
    return json({ product, count: 0, avg: null, items: [] });
  }

  const rows = data || [];
  const count = rows.length;
  const avg = count
    ? Math.round((rows.reduce((s, r) => s + r.rating, 0) / count) * 10) / 10
    : null;

  return json({
    product,
    count,
    avg,
    items: rows.map((r) => ({
      rating: r.rating,
      title: r.title || '',
      body: r.body,
      name: firstName(r.customer_name),
      date: r.published_at,
    })),
  });
};

export const onRequestPost = async ({ request, env }) => {
  let body;
  try {
    body = await request.json();
  } catch (_) {
    return badRequest('Invalid JSON body.');
  }

  const token = await verifyReviewToken(body?.rt, env);
  if (!token) {
    return badRequest('This review link is invalid or has expired.', 403);
  }

  const product = (body?.product || '').trim().toLowerCase();
  if (!PRODUCT_KEYS.has(product)) return badRequest('Unknown product.');

  const rating = parseInt(body?.rating, 10);
  if (!(rating >= 1 && rating <= 5)) return badRequest('Rating must be 1 to 5.');

  const text = String(body?.body || '').trim();
  if (text.length < 10) return badRequest('Please write at least a sentence.');
  if (text.length > 4000) return badRequest('Review is too long (4000 char max).');

  const title = String(body?.title || '').trim().slice(0, 160) || null;

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  // The token says which order; confirm it exists, belongs to this buyer, is
  // actually paid/shipped, and that this product was in it.
  const { data: order, error: oErr } = await sb
    .from('orders')
    .select('id, email, customer_name, status, line_items')
    .eq('id', token.orderId)
    .maybeSingle();

  if (oErr) return serverError('Could not verify the order.');
  if (!order || String(order.email).toLowerCase() !== token.email) {
    return badRequest('This review link is invalid or has expired.', 403);
  }
  if (!['paid', 'shipped', 'fulfilled'].includes(order.status)) {
    return badRequest('Reviews open once your order has shipped.', 409);
  }

  const items = Array.isArray(order.line_items) ? order.line_items : [];
  const boughtThis = items.some(
    (li) => String(li?.productKey || li?.k || '').toLowerCase() === product
  );
  if (!boughtThis) {
    return badRequest('That product was not in this order.', 409);
  }

  const name =
    String(body?.name || '').trim().slice(0, 80) ||
    String(order.customer_name || '').trim().slice(0, 80) ||
    null;

  const { error: insErr } = await sb.from('reviews').insert({
    order_id: order.id,
    product_key: product,
    rating,
    title,
    body: text,
    customer_name: name,
    status: 'pending',
  });

  if (insErr) {
    // 23505 = unique_violation on (order_id, product_key): already reviewed.
    if (insErr.code === '23505') {
      return json({ ok: true, status: 'duplicate' });
    }
    console.warn('[reviews] insert failed', insErr.message);
    return serverError('Could not save your review.');
  }

  return json({ ok: true, status: 'pending' });
};
