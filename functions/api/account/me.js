// GET /api/account/me
//
// Requires session (JWT cookie: sb-access-token)
// Returns: { email, orders: [...last 25], subscriptions: [...active+canceled], addresses: [...unique from orders] }
//
// Queries Supabase with service-role; filters by JWT email claim from auth.jwt().

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { getSessionFromRequest } from '../../_lib/auth.js';

export const onRequestGet = async ({ request, env }) => {
  const session = await getSessionFromRequest(request, env);
  if (!session || !session.email) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  const email = session.email;
  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  // Fetch orders (last 25)
  let orders = [];
  try {
    const { data, error } = await sb
      .from('orders')
      .select('*')
      .eq('email', email)
      .order('created_at', { ascending: false })
      .limit(25);
    if (error) throw error;
    orders = data || [];
  } catch (_) {
    return serverError('Could not fetch orders.');
  }

  // Fetch subscriptions (all: active + canceled)
  let subscriptions = [];
  try {
    const { data, error } = await sb
      .from('subscriptions')
      .select('*')
      .eq('email', email);
    if (error) throw error;
    subscriptions = data || [];
  } catch (_) {
    return serverError('Could not fetch subscriptions.');
  }

  // Extract unique addresses from orders (shipping_address is jsonb)
  const addressMap = new Map();
  for (const order of orders) {
    if (order.shipping_address) {
      const addr = order.shipping_address;
      const key = `${addr.line1}|${addr.city}|${addr.state}|${addr.postal_code}`;
      if (!addressMap.has(key)) {
        addressMap.set(key, addr);
      }
    }
  }
  const addresses = Array.from(addressMap.values());

  return json({
    email,
    orders,
    subscriptions,
    addresses,
  });
};
