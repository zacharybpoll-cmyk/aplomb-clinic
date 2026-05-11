// POST /api/admin/ship-order
//
// Body: { orderId, trackingNumber, carrier }
// Auth: Cloudflare Access (edge), no in-code check.
//
// Marks an order shipped, stamps tracking + carrier, sends the shipping
// notification email.

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { sendEmail } from '../../_lib/email.js';

const VALID_CARRIERS = new Set(['usps', 'ups', 'fedex', 'dhl', 'other']);

export const onRequestPost = async ({ request, env }) => {
  let body;
  try { body = await request.json(); } catch { return badRequest('Invalid JSON body.'); }

  const orderId = (body?.orderId || '').trim();
  const trackingNumber = (body?.trackingNumber || '').trim();
  const carrier = (body?.carrier || 'usps').trim().toLowerCase();

  if (!orderId) return badRequest('orderId is required.');
  if (!trackingNumber) return badRequest('trackingNumber is required.');
  if (!VALID_CARRIERS.has(carrier)) return badRequest(`Invalid carrier. Must be one of: ${[...VALID_CARRIERS].join(', ')}`);

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const { data: order, error } = await sb.from('orders').update({
    status: 'shipped',
    tracking_number: trackingNumber,
    carrier,
    shipped_at: new Date().toISOString(),
  }).eq('id', orderId).select('*').single();

  if (error || !order) {
    return new Response(JSON.stringify({ error: 'Order not found or update failed.' }), {
      status: 404, headers: { 'content-type': 'application/json' },
    });
  }

  try {
    await sendEmail(env, 'shipping-notification', { order });
  } catch (e) {
    console.warn('shipping email send failed', e?.message || e);
  }

  return json({ order });
};
