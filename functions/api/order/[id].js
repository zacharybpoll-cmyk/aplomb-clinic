// GET /api/order/[id]
//
// Fetch order by Stripe PaymentIntent ID (pi_...) OR Checkout Session ID (cs_...)
// Public endpoint (ID is unguessable auth token)
// Returns: order row with all fields (id, email, status, line_items, total_cents, etc.)

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';

export const onRequestGet = async ({ params, env }) => {
  const stripeId = (params?.id || '').trim();

  if (!stripeId) {
    return badRequest('Order ID is required.');
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  let order;
  try {
    // Try payment intent ID first
    if (stripeId.startsWith('pi_')) {
      const { data, error } = await sb
        .from('orders')
        .select('*')
        .eq('stripe_payment_intent_id', stripeId)
        .maybeSingle();
      if (error) throw error;
      order = data;
    }
    // Try checkout session ID
    else if (stripeId.startsWith('cs_')) {
      const { data, error } = await sb
        .from('orders')
        .select('*')
        .eq('stripe_checkout_session_id', stripeId)
        .maybeSingle();
      if (error) throw error;
      order = data;
    }
    // Invalid format
    else {
      return badRequest('Invalid order ID format. Use pi_... or cs_...');
    }
  } catch (_) {
    return serverError('Could not fetch order.');
  }

  if (!order) {
    return json({ error: 'Order not found' }, { status: 404 });
  }

  return json(order);
};
