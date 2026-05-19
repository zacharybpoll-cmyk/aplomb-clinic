// Command Center — Supabase-derived metrics: orders/revenue, subscriptions/MRR,
// newsletter, reviews. Read-only. Reuses the service-role client and the
// server-side product catalog (the single source of truth for prices).
//
// All time windows are UTC. "today" = since 00:00:00Z; "d7"/"d30" are rolling
// 7/30-day windows (now - N days). MRR is computed locally from the product
// catalog (zero Stripe API calls): an active subscription's monthly value is
// the product's subscribe-and-save price (unit price minus its discount %).

import { supabaseAdmin } from '../supabase.js';
import { PRODUCTS } from '../products.js';

const DAY = 86400000;
const REVENUE_STATUSES = ['paid', 'shipped', 'fulfilled'];

function amountCents(o) {
  // total_cents is a generated column (subtotal+shipping+tax); an override
  // wins when set (discounts / manual adjustments) — matches checkout.js.
  return (o.total_cents_override != null ? o.total_cents_override : o.total_cents) || 0;
}

function utcMidnightISO() {
  return new Date(new Date().toISOString().slice(0, 10) + 'T00:00:00.000Z').toISOString();
}

// Reverse-map a Stripe subscription price id → product key, by convention
// STRIPE_PRICE_<KEY>_SUBSCRIPTION (same lookup checkout.js uses, inverted).
function buildPriceKeyMap(env) {
  const map = {};
  for (const key of Object.keys(PRODUCTS)) {
    const id = env[`STRIPE_PRICE_${key.toUpperCase()}_SUBSCRIPTION`];
    if (id) map[id] = key;
  }
  return map;
}

// Monthly recurring value of one product subscription, in cents.
function monthlyCents(productKey) {
  const p = PRODUCTS[productKey];
  if (!p) return null;
  return Math.round(p.unitPriceCents * (1 - (p.subscribeDiscountPct || 0) / 100));
}

async function ordersBlock(sb) {
  const now = Date.now();
  const since365 = new Date(now - 365 * DAY).toISOString();
  // Numeric (ms) cutoffs — Supabase returns timestamptz with a +00:00 offset
  // while our ISO cutoffs use Z, so string comparison is unsafe. Parse both.
  const cut = { today: Date.parse(utcMidnightISO()), d7: now - 7 * DAY, d30: now - 30 * DAY };

  // Bounded fetch — early-stage volume is small; 365d/5000 is ample and keeps
  // the function fast. all_time_count comes from an exact head count instead.
  const [{ data: rows, error }, allCount, pending] = await Promise.all([
    sb.from('orders')
      .select('status,total_cents,total_cents_override,paid_at,created_at,refunded_at')
      .gte('created_at', since365)
      .order('created_at', { ascending: false })
      .limit(5000),
    sb.from('orders').select('*', { count: 'exact', head: true }).in('status', REVENUE_STATUSES),
    sb.from('orders').select('*', { count: 'exact', head: true }).eq('status', 'paid').is('tracking_number', null),
  ]);
  if (error) throw new Error('orders: ' + error.message);

  const win = (k) => ({ count: 0, gross_cents: 0 });
  const acc = { today: win(), d7: win(), d30: win() };
  let net30 = 0, refunds30 = 0;
  const spark = new Array(30).fill(0); // index 0 = 29 days ago … 29 = today

  for (const o of rows || []) {
    const ts = o.paid_at || o.created_at;
    const t = Date.parse(ts);
    if (Number.isNaN(t)) continue;
    const amt = amountCents(o);
    if (REVENUE_STATUSES.includes(o.status)) {
      if (t >= cut.today) { acc.today.count++; acc.today.gross_cents += amt; }
      if (t >= cut.d7) { acc.d7.count++; acc.d7.gross_cents += amt; }
      if (t >= cut.d30) { acc.d30.count++; acc.d30.gross_cents += amt; net30 += amt; }
      const dayIdx = 29 - Math.floor((now - t) / DAY);
      if (dayIdx >= 0 && dayIdx < 30) spark[dayIdx] += amt;
    }
    if (o.status === 'refunded' && o.refunded_at) {
      const r = Date.parse(o.refunded_at);
      if (!Number.isNaN(r) && r >= cut.d30) { refunds30 += amt; net30 -= amt; }
    }
  }

  return {
    today: acc.today,
    d7: acc.d7,
    d30: { ...acc.d30, net_cents: net30, aov_cents: acc.d30.count ? Math.round(acc.d30.gross_cents / acc.d30.count) : 0 },
    refunds_d30_cents: refunds30,
    all_time_count: allCount.count || 0,
    pending_fulfillment: pending.count || 0,
    spark30: spark,
  };
}

async function subsBlock(sb, env) {
  const churnCut = Date.now() - 30 * DAY;
  const { data: subs, error } = await sb
    .from('subscriptions')
    .select('status,items,canceled_at')
    .limit(5000);
  if (error) throw new Error('subscriptions: ' + error.message);

  const priceMap = buildPriceKeyMap(env);
  let mrr = 0, active = 0, pastDue = 0, churn30 = 0, unknownPrices = 0;

  for (const s of subs || []) {
    if (s.status === 'active') {
      active++;
      for (const it of Array.isArray(s.items) ? s.items : []) {
        const key = priceMap[it.price_id];
        const m = key ? monthlyCents(key) : null;
        if (m == null) { unknownPrices++; continue; }
        mrr += m * (it.quantity || 1);
      }
    } else if (s.status === 'past_due') {
      pastDue++;
    }
    if (s.status === 'canceled' && s.canceled_at && Date.parse(s.canceled_at) >= churnCut) churn30++;
  }

  return {
    active,
    past_due: pastDue,
    mrr_cents: mrr,
    churn_30d: churn30,
    unknown_price_items: unknownPrices, // > 0 means a sub price id has no catalog match
  };
}

async function newsletterBlock(sb) {
  const now = Date.now();
  const c7 = new Date(now - 7 * DAY).toISOString();
  const c30 = new Date(now - 30 * DAY).toISOString();
  const head = (q) => q.select('*', { count: 'exact', head: true });

  const [total, n7, n30, unsub30, welcomePending, sourceRows] = await Promise.all([
    head(sb.from('newsletter_subscribers')).is('unsubscribed_at', null),
    head(sb.from('newsletter_subscribers')).gte('subscribed_at', c7),
    head(sb.from('newsletter_subscribers')).gte('subscribed_at', c30),
    head(sb.from('newsletter_subscribers')).gte('unsubscribed_at', c30),
    head(sb.from('newsletter_subscribers')).is('welcome_sent_at', null).is('unsubscribed_at', null),
    sb.from('newsletter_subscribers').select('source').is('unsubscribed_at', null).limit(10000),
  ]);

  const tally = {};
  for (const r of sourceRows.data || []) {
    const s = (r.source || 'unknown').split(':')[0]; // 'footer:/serum' -> 'footer'
    tally[s] = (tally[s] || 0) + 1;
  }
  const by_source = Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 6)
    .map(([source, count]) => ({ source, count }));

  return {
    total_active: total.count || 0,
    new_d7: n7.count || 0,
    new_d30: n30.count || 0,
    unsub_d30: unsub30.count || 0,
    welcome_pending: welcomePending.count || 0,
    by_source,
  };
}

async function reviewsBlock(sb) {
  const head = (q) => q.select('*', { count: 'exact', head: true });
  const [pending, published, ratingRows] = await Promise.all([
    head(sb.from('reviews')).eq('status', 'pending'),
    head(sb.from('reviews')).eq('status', 'published'),
    sb.from('reviews').select('rating').eq('status', 'published').limit(5000),
  ]);
  const ratings = (ratingRows.data || []).map((r) => r.rating).filter((n) => n > 0);
  const avg = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null;
  return {
    pending: pending.count || 0,
    published: published.count || 0,
    avg_published_rating: avg == null ? null : Math.round(avg * 100) / 100,
  };
}

export async function getStoreMetrics(env) {
  const sb = supabaseAdmin(env);
  if (!sb) throw new Error('Supabase not configured');
  const [orders, subscriptions, newsletter, reviews] = await Promise.all([
    ordersBlock(sb),
    subsBlock(sb, env),
    newsletterBlock(sb),
    reviewsBlock(sb),
  ]);
  return { orders, subscriptions, newsletter, reviews };
}
