// GET /api/admin/overview — the Command Center aggregator.
//
// Cloudflare Access gates this route via functions/api/admin/_middleware.js
// (same host-pin as orders/reviews) — there is intentionally no in-code auth.
//
// Fans out to four independent sources with Promise.allSettled so one slow or
// failing source never blanks the page; every section reports its own
// {status: ok | not_connected | error}. Each source is edge-cached
// (caches.default) under its own synthetic key + TTL so repeatedly opening the
// dashboard doesn't hammer Stripe/Plausible/YouTube. `?fresh=1` bypasses cache.

import { json } from '../../_lib/json.js';
import { getStoreMetrics } from '../../_lib/overview/store.js';
import { getFinanceMetrics } from '../../_lib/overview/finance.js';
import { getTrafficMetrics } from '../../_lib/overview/traffic.js';
import { getYouTubeMetrics } from '../../_lib/overview/youtube.js';

async function cached(name, ttl, producer, fresh) {
  const key = new Request(`https://cc-cache.aplomb.internal/${name}`);
  const cache = caches.default;
  if (!fresh) {
    const hit = await cache.match(key);
    if (hit) { try { return await hit.json(); } catch (_) { /* fall through */ } }
  }
  const value = await producer(); // throws → not cached, surfaces as error
  try {
    await cache.put(key, new Response(JSON.stringify(value), {
      headers: { 'Content-Type': 'application/json', 'Cache-Control': `max-age=${ttl}` },
    }));
  } catch (_) { /* cache best-effort */ }
  return value;
}

// Normalize a settled source into a uniform envelope. A source that returns
// { connected:false } is "not_connected" (expected — unconfigured), not an error.
function section(settled) {
  if (settled.status === 'rejected') {
    return { status: 'error', error: settled.reason?.message || String(settled.reason) };
  }
  const data = settled.value;
  if (data && data.connected === false) {
    return { status: 'not_connected', data: null };
  }
  return { status: 'ok', data };
}

export const onRequestGet = async ({ request, env }) => {
  const fresh = new URL(request.url).searchParams.get('fresh') === '1';

  const [store, finance, traffic, youtube] = await Promise.allSettled([
    cached('store', 60, () => getStoreMetrics(env), fresh),
    cached('finance', 900, () => getFinanceMetrics(env), fresh),
    cached('traffic', 300, () => getTrafficMetrics(env), fresh),
    cached('youtube', 3600, () => getYouTubeMetrics(env), fresh),
  ]);

  const storeS = section(store);
  const trafficS = section(traffic);

  // Conversion is derived: authoritative Supabase orders ÷ Plausible visitors
  // (the funnel does not emit Plausible goal events, so this is more accurate
  // than a Plausible goal rate). Only computed when both sources are ok.
  let conversion = { status: 'unavailable' };
  if (storeS.status === 'ok' && trafficS.status === 'ok') {
    const orders30 = storeS.data.orders.d30.count;
    const visitors30 = trafficS.data.d30.visitors || 0;
    const subs30 = storeS.data.newsletter.new_d30;
    const pct = (a, b) => (b > 0 ? Math.round((a / b) * 1000) / 10 : null);
    conversion = {
      status: 'ok',
      data: {
        window: '30d',
        visitors: visitors30,
        orders: orders30,
        order_conversion_pct: pct(orders30, visitors30),
        newsletter_signups: subs30,
        newsletter_conversion_pct: pct(subs30, visitors30),
      },
    };
  }

  // Instagram / Facebook: auto-activating placeholders. No Meta dev account
  // (known dead end) → not_connected until a META_GRAPH_TOKEN ever exists.
  const metaPlaceholder = (platform) => ({
    status: 'not_connected',
    data: null,
    note: env.META_GRAPH_TOKEN
      ? `${platform} token present but integration not built (Phase 2)`
      : `${platform} metrics require the Meta Graph API (developer account unavailable)`,
  });

  return json({
    generated_at: new Date().toISOString(),
    cache: fresh ? 'bypassed' : 'per-source (store 60s · finance 15m · traffic 5m · youtube 60m)',
    sections: {
      store: storeS,
      finance: section(finance),
      traffic: trafficS,
      conversion,
      social: {
        youtube: section(youtube),
        instagram: metaPlaceholder('Instagram'),
        facebook: metaPlaceholder('Facebook'),
      },
    },
  });
};
