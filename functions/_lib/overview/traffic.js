// Command Center — website traffic, sources, and the on-site funnel via the
// Plausible Stats API v2 (POST /api/v2/query, Bearer auth). Read-only.
// The API key stays server-side; it is never sent to the browser.
//
// v2 returns results as { metrics: [positional], dimensions: [...] } — values
// are ordered to match the requested `metrics` array, so we zip by index.
// Session metrics (bounce_rate, visit_duration) may NOT be combined with event
// dimensions, so breakdown queries request only visitor/event counts.
//
// Env: PLAUSIBLE_API_KEY (Stats API scope) + PLAUSIBLE_SITE_ID
// (defaults to getaplomb.com). Returns { connected:false } when unconfigured.

const ENDPOINT = 'https://plausible.io/api/v2/query';

// Funnel events already emitted by website/assets/analytics.js → track().
const FUNNEL = ['view_product', 'add_to_cart', 'begin_checkout', 'purchase', 'subscribe', 'newsletter_signup'];
// Source substrings that count as social → site click-through.
const SOCIAL = ['instagram', 'facebook', 'fb.', 'youtube', 'youtu.be', 't.co', 'twitter', 'x.com', 'tiktok', 'lnkd', 'linkedin'];

async function query(env, body) {
  const r = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.PLAUSIBLE_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = json?.error || json?.message || `HTTP ${r.status}`;
    throw new Error(`Plausible: ${msg}`);
  }
  return json;
}

// First result row's metrics zipped to the requested metric names.
function agg(json, metrics) {
  const row = (json.results || [])[0];
  const out = {};
  metrics.forEach((m, i) => { out[m] = row ? row.metrics[i] : 0; });
  return out;
}

export async function getTrafficMetrics(env) {
  if (!env.PLAUSIBLE_API_KEY) return { connected: false };
  const site_id = env.PLAUSIBLE_SITE_ID || 'getaplomb.com';
  const AGG = ['visitors', 'pageviews', 'bounce_rate', 'visit_duration'];

  const [today, d7, d30, ts, sources, pages, events] = await Promise.all([
    query(env, { site_id, metrics: AGG, date_range: 'day' }),
    query(env, { site_id, metrics: AGG, date_range: '7d' }),
    query(env, { site_id, metrics: AGG, date_range: '30d' }),
    query(env, {
      site_id, metrics: ['visitors', 'pageviews'], date_range: '30d',
      dimensions: ['time:day'], include: { time_labels: true }, order_by: [['time:day', 'asc']],
    }),
    query(env, {
      site_id, metrics: ['visitors'], date_range: '30d',
      dimensions: ['visit:source'], order_by: [['visitors', 'desc']], pagination: { limit: 12 },
    }),
    query(env, {
      site_id, metrics: ['visitors', 'pageviews'], date_range: '30d',
      dimensions: ['event:page'], order_by: [['visitors', 'desc']], pagination: { limit: 8 },
    }),
    query(env, {
      site_id, metrics: ['events', 'visitors'], date_range: '30d',
      dimensions: ['event:name'], pagination: { limit: 30 },
    }),
  ]);

  // 30-day daily visitors sparkline (time_labels:true → empty days present).
  const spark30 = (ts.results || []).slice(-30).map((r) => r.metrics[0] || 0);

  const top_sources = (sources.results || []).map((r) => ({
    source: r.dimensions[0] || '(direct)',
    visitors: r.metrics[0] || 0,
  }));
  const social_to_site = top_sources
    .filter((s) => SOCIAL.some((h) => s.source.toLowerCase().includes(h)))
    .reduce((sum, s) => sum + s.visitors, 0);

  const top_pages = (pages.results || []).map((r) => ({
    page: r.dimensions[0] || '/',
    visitors: r.metrics[0] || 0,
    pageviews: r.metrics[1] || 0,
  }));

  // Funnel event counts (events, visitors) keyed by event name.
  const funnel = {};
  for (const r of events.results || []) {
    const name = r.dimensions[0];
    if (FUNNEL.includes(name)) funnel[name] = { events: r.metrics[0] || 0, visitors: r.metrics[1] || 0 };
  }
  for (const f of FUNNEL) if (!funnel[f]) funnel[f] = { events: 0, visitors: 0 };

  const rate = (a, b) => (b > 0 ? Math.round((a / b) * 1000) / 10 : null); // % 1dp
  const onsite_ctr = {
    product_to_cart: rate(funnel.add_to_cart.visitors, funnel.view_product.visitors),
    cart_to_checkout: rate(funnel.begin_checkout.visitors, funnel.add_to_cart.visitors),
    checkout_to_purchase: rate(
      funnel.purchase.visitors + funnel.subscribe.visitors,
      funnel.begin_checkout.visitors
    ),
  };

  return {
    connected: true,
    site_id,
    today: agg(today, AGG),
    d7: agg(d7, AGG),
    d30: agg(d30, AGG),
    spark30,
    top_sources: top_sources.slice(0, 8),
    top_pages,
    social_to_site_d30: social_to_site,
    funnel,
    onsite_ctr,
  };
}
