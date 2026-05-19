// Command Center — live Stripe financials: balance, payouts, and 30-day
// gross/fee/net volume. Read-only. Reuses the shared Stripe client factory
// (SDK pinned to 2024-12-18.acacia with the Workers fetch http client).
//
// Single-currency (USD) — the business is US/CA, one settlement currency.
// Each sub-call degrades independently: a failure in volume still returns
// balance, never blanks the whole tile.

import { stripeClient } from '../stripe.js';

const DAY = 86400000;

function usd(list) {
  // Stripe balance.available/pending are arrays per currency.
  const row = (list || []).find((b) => b.currency === 'usd');
  return row ? row.amount : 0;
}

function payoutShape(p) {
  return p ? { amount_cents: p.amount, arrival_date: p.arrival_date, status: p.status } : null;
}

export async function getFinanceMetrics(env) {
  const stripe = stripeClient(env);
  if (!stripe) return { connected: false };

  const out = { connected: true, currency: 'usd' };

  const [balanceR, payoutsR, txnsR] = await Promise.allSettled([
    stripe.balance.retrieve(),
    stripe.payouts.list({ limit: 12 }),
    stripe.balanceTransactions
      .list({ limit: 100, created: { gte: Math.floor((Date.now() - 30 * DAY) / 1000) } })
      .autoPagingToArray({ limit: 2000 }),
  ]);

  if (balanceR.status === 'fulfilled') {
    out.available_cents = usd(balanceR.value.available);
    out.pending_cents = usd(balanceR.value.pending);
  } else {
    out.balance_error = balanceR.reason?.message || 'balance unavailable';
  }

  if (payoutsR.status === 'fulfilled') {
    const ps = payoutsR.value.data || [];
    // "Next" = soonest in-flight payout; "last" = most recent paid one.
    const inFlight = ps
      .filter((p) => p.status === 'pending' || p.status === 'in_transit')
      .sort((a, b) => a.arrival_date - b.arrival_date)[0];
    const paid = ps.filter((p) => p.status === 'paid')
      .sort((a, b) => b.arrival_date - a.arrival_date)[0];
    out.next_payout = payoutShape(inFlight);
    out.last_payout = payoutShape(paid);
  } else {
    out.payouts_error = payoutsR.reason?.message || 'payouts unavailable';
  }

  if (txnsR.status === 'fulfilled') {
    let gross = 0, fee = 0, net = 0, refund = 0, n = 0;
    for (const t of txnsR.value) {
      if (t.currency !== 'usd') continue;
      if (t.type === 'charge' || t.type === 'payment') {
        gross += t.amount; fee += t.fee; net += t.net; n++;
      } else if (t.type === 'refund' || t.type === 'payment_refund') {
        refund += Math.abs(t.amount); fee += t.fee; net += t.net;
      }
    }
    out.volume_30d = { gross_cents: gross, fee_cents: fee, net_cents: net, refund_cents: refund, txn_count: n };
  } else {
    out.volume_error = txnsR.reason?.message || 'volume unavailable';
  }

  return out;
}
