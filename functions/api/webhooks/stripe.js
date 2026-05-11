// POST /api/webhooks/stripe
//
// Receives Stripe webhook events, verifies the signature, and reconciles
// orders / subscriptions / refunds with Supabase. Idempotent: every event ID
// is recorded in a stripe_events table; replayed events short-circuit.

import { json, serverError } from '../../_lib/json.js';
import { stripeClient } from '../../_lib/stripe.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { sendOrderConfirmation } from '../../_lib/email.js';

export const onRequestPost = async ({ request, env }) => {
  const stripe = stripeClient(env);
  if (!stripe) return serverError('Stripe not configured.');
  if (!env.STRIPE_WEBHOOK_SECRET) return serverError('Webhook secret not configured.');

  const sig = request.headers.get('stripe-signature');
  if (!sig) return new Response('Missing signature', { status: 400 });

  const raw = await request.text();
  let event;
  try {
    event = await stripe.webhooks.constructEventAsync(raw, sig, env.STRIPE_WEBHOOK_SECRET);
  } catch (e) {
    return new Response(`Bad signature: ${e.message}`, { status: 400 });
  }

  const sb = supabaseAdmin(env);

  // Idempotency: record-and-skip on replay.
  if (sb) {
    const { error: insertErr } = await sb.from('stripe_events').insert({
      id: event.id,
      type: event.type,
    });
    if (insertErr && insertErr.code === '23505') {
      return json({ received: true, deduped: true });
    }
  }

  try {
    switch (event.type) {
      case 'payment_intent.succeeded':
        await handlePaymentSucceeded(event.data.object, sb, env);
        break;
      case 'payment_intent.payment_failed':
        await handlePaymentFailed(event.data.object, sb);
        break;
      case 'charge.refunded':
        await handleChargeRefunded(event.data.object, sb);
        break;
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
        await handleSubscriptionChange(event.data.object, sb);
        break;
      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(event.data.object, sb);
        break;
      default:
        break;
    }
  } catch (e) {
    return new Response(`Handler failed: ${e.message}`, { status: 500 });
  }

  return json({ received: true });
};

async function handlePaymentSucceeded(intent, sb, env) {
  if (!sb) return;
  const { data: order } = await sb.from('orders')
    .update({ status: 'paid', paid_at: new Date().toISOString() })
    .eq('stripe_payment_intent_id', intent.id)
    .select('*').single();
  if (!order) return;
  try {
    await sendOrderConfirmation(env, order);
  } catch (_) {
    // email failure must not fail the webhook (stripe will retry forever)
  }
}

async function handlePaymentFailed(intent, sb) {
  if (!sb) return;
  await sb.from('orders')
    .update({ status: 'failed' })
    .eq('stripe_payment_intent_id', intent.id);
}

async function handleChargeRefunded(charge, sb) {
  if (!sb || !charge.payment_intent) return;
  await sb.from('orders')
    .update({ status: 'refunded', refunded_at: new Date().toISOString() })
    .eq('stripe_payment_intent_id', charge.payment_intent);
}

async function handleSubscriptionChange(sub, sb) {
  if (!sb) return;
  await sb.from('subscriptions').upsert({
    stripe_subscription_id: sub.id,
    stripe_customer_id: sub.customer,
    status: sub.status,
    current_period_end: new Date(sub.current_period_end * 1000).toISOString(),
    cancel_at_period_end: sub.cancel_at_period_end,
    items: sub.items?.data || [],
  }, { onConflict: 'stripe_subscription_id' });
}

async function handleSubscriptionDeleted(sub, sb) {
  if (!sb) return;
  await sb.from('subscriptions')
    .update({ status: 'canceled', canceled_at: new Date().toISOString() })
    .eq('stripe_subscription_id', sub.id);
}
