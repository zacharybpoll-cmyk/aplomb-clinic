// POST /api/webhooks/stripe
//
// Receives Stripe webhook events, verifies the signature, and reconciles
// orders / subscriptions / refunds with Supabase. Idempotent: every event ID
// is recorded in a stripe_events table; replayed events short-circuit.

import { json, serverError } from '../../_lib/json.js';
import { stripeClient } from '../../_lib/stripe.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { sendOrderConfirmation, sendEmail } from '../../_lib/email.js';

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
        await handlePaymentSucceeded(event.data.object, sb, env, stripe);
        break;
      case 'payment_intent.payment_failed':
        await handlePaymentFailed(event.data.object, sb);
        break;
      case 'charge.refunded':
        await handleChargeRefunded(event.data.object, sb, env);
        break;
      case 'checkout.session.completed':
        await handleCheckoutSessionCompleted(event.data.object, sb, env);
        break;
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
        await handleSubscriptionChange(event.data.object, sb);
        break;
      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(event.data.object, sb, env);
        break;
      case 'invoice.paid':
        await handleInvoicePaid(event.data.object, sb, env);
        break;
      case 'invoice.payment_failed':
        await handleInvoicePaymentFailed(event.data.object, sb, env);
        break;
      default:
        break;
    }
  } catch (e) {
    return new Response(`Handler failed: ${e.message}`, { status: 500 });
  }

  return json({ received: true });
};

async function handlePaymentSucceeded(intent, sb, env, stripe) {
  if (!sb) return;
  const { data: order } = await sb.from('orders')
    .update({ status: 'paid', paid_at: new Date().toISOString() })
    .eq('stripe_payment_intent_id', intent.id)
    .select('*').single();
  if (!order) return;

  // Register the Stripe Tax transaction so Stripe Tax reports include this
  // order in its filing data. The calculation ID was stashed in PI metadata
  // by /api/checkout. Skip cleanly when there isn't one (e.g., orders placed
  // before this code shipped, or anon test traffic with no address).
  const calcId = intent?.metadata?.tax_calculation_id;
  if (stripe && calcId && !calcId.startsWith('error:')) {
    try {
      await stripe.tax.transactions.createFromCalculation({
        calculation: calcId,
        reference: intent.id,
      });
    } catch (_) {
      // Stripe Tax registration failure is non-fatal — log via order metadata
      // for follow-up reconciliation; do NOT fail the webhook.
    }
  }

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

async function handleChargeRefunded(charge, sb, env) {
  if (!sb || !charge.payment_intent) return;
  const { data: order } = await sb.from('orders')
    .update({ status: 'refunded', refunded_at: new Date().toISOString() })
    .eq('stripe_payment_intent_id', charge.payment_intent)
    .select('*').single();
  if (!order) return;
  // Email the customer so they know the refund landed. The refund-confirmation
  // template reads total_cents off the order row (generated column).
  try {
    await sendEmail(env, 'refund-confirmation', { order, charge });
  } catch (_) {
    // email failure must not fail the webhook
  }
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

async function handleSubscriptionDeleted(sub, sb, env) {
  if (!sb) return;
  const { data: row } = await sb.from('subscriptions')
    .update({ status: 'canceled', canceled_at: new Date().toISOString() })
    .eq('stripe_subscription_id', sub.id)
    .select('*').single();
  if (row && env) {
    try {
      await sendEmail(env, 'cancellation-confirmation', {
        subscription: row,
        customer: { email: row.email },
        lastShipmentDate: row.current_period_end || null,
      });
    } catch (_) {}
  }
}

// Triggered when the Stripe-hosted Checkout completes for a subscription cart.
// Closes the loop on the pending order row created at /api/checkout.
async function handleCheckoutSessionCompleted(session, sb, env) {
  if (!sb) return;
  // Only handle subscription sessions; payment-mode sessions complete via payment_intent.succeeded.
  if (session.mode !== 'subscription') return;

  const shippingDetails = session.shipping_details || session.customer_details?.address || null;
  const customerEmail = (session.customer_details?.email || session.customer_email || '').toLowerCase();
  const customerName = session.customer_details?.name || null;

  const { data: order } = await sb.from('orders')
    .update({
      status: 'paid',
      paid_at: new Date().toISOString(),
      stripe_customer_id: session.customer || null,
      stripe_subscription_id: session.subscription || null,
      subtotal_cents: session.amount_subtotal || 0,
      tax_cents: session.total_details?.amount_tax || 0,
      shipping_cents: session.total_details?.amount_shipping || 0,
      total_cents_override: session.amount_total || null,
      shipping_address: shippingDetails,
      email: customerEmail || undefined,
      customer_name: customerName || undefined,
    })
    .eq('stripe_checkout_session_id', session.id)
    .select('*').single();

  if (order) {
    try { await sendOrderConfirmation(env, order); } catch (_) {}
  }

  // Upsert into customers table
  if (customerEmail && session.customer) {
    try {
      await sb.from('customers').upsert({
        email: customerEmail,
        name: customerName,
        stripe_customer_id: session.customer,
      }, { onConflict: 'email' });
    } catch (_) {}
  }
}

// Invoices fire on every billing cycle. The first one is suppressed (handled by checkout.session.completed).
// Subsequent ones are renewals: insert a new order, advance the subscription period, send renewal receipt.
async function handleInvoicePaid(invoice, sb, env) {
  if (!sb) return;
  const reason = invoice.billing_reason;
  // first invoice on a new sub is already handled by checkout.session.completed
  if (reason === 'subscription_create') return;
  if (reason !== 'subscription_cycle' && reason !== 'subscription_update') return;

  // Build line_items from invoice.lines
  const lineItems = (invoice.lines?.data || []).map(li => ({
    productKey: (li.price?.product || li.price?.id || 'unknown').toString(),
    name: li.description || li.price?.nickname || 'Subscription item',
    quantity: li.quantity || 1,
    unitPriceCents: li.amount || 0,
    mode: 'subscription',
  }));

  // Look up the most-recent prior order for this subscription to get shipping_address
  let shippingAddress = null;
  if (invoice.subscription) {
    try {
      const { data: prior } = await sb.from('orders')
        .select('shipping_address')
        .eq('stripe_subscription_id', invoice.subscription)
        .not('shipping_address', 'is', null)
        .order('paid_at', { ascending: false })
        .limit(1)
        .maybeSingle();
      shippingAddress = prior?.shipping_address || null;
    } catch (_) {}
  }

  // Insert renewal order
  const { data: order } = await sb.from('orders').insert({
    stripe_payment_intent_id: invoice.payment_intent || null,
    stripe_charge_id: invoice.charge || null,
    stripe_subscription_id: invoice.subscription || null,
    stripe_customer_id: invoice.customer || null,
    stripe_invoice_id: invoice.id,
    email: invoice.customer_email?.toLowerCase() || '',
    customer_name: invoice.customer_name || '',
    subtotal_cents: invoice.subtotal || 0,
    tax_cents: invoice.tax || 0,
    shipping_cents: invoice.shipping_cost?.amount_total || 0,
    total_cents_override: invoice.total || null,
    line_items: lineItems,
    shipping_address: shippingAddress,
    status: 'paid',
    paid_at: new Date().toISOString(),
    metadata: { source: 'subscription_cycle', invoice_id: invoice.id },
  }).select('*').single();

  // Advance subscription period
  if (invoice.subscription && invoice.lines?.data?.[0]?.period?.end) {
    try {
      await sb.from('subscriptions').update({
        current_period_end: new Date(invoice.lines.data[0].period.end * 1000).toISOString(),
        renewal_reminder_sent_at: null, // reset so the next cycle sends a heads-up
      }).eq('stripe_subscription_id', invoice.subscription);
    } catch (_) {}
  }

  // Send renewal receipt
  if (order) {
    try { await sendEmail(env, 'renewal-receipt', { order }); } catch (_) {}
  }
}

async function handleInvoicePaymentFailed(invoice, sb, env) {
  if (!sb) return;
  if (invoice.subscription) {
    try {
      await sb.from('subscriptions')
        .update({ status: 'past_due' })
        .eq('stripe_subscription_id', invoice.subscription);
    } catch (_) {}
  }
  // Notify customer; Stripe Smart Retries will handle the actual dunning attempts
  try {
    await sendEmail(env, 'card-failed', {
      customer: { email: (invoice.customer_email || '').toLowerCase() },
      subscription: { id: invoice.subscription },
      nextAttempt: invoice.next_payment_attempt
        ? new Date(invoice.next_payment_attempt * 1000).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
        : 'in 3 days',
    });
  } catch (_) {}
}
