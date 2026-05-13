-- 0002: signals for email scheduling + subscription Checkout Sessions.
-- Adds the columns needed by the renewal-reminder cron, the
-- checkout.session.completed webhook handler, and the renewal-receipt
-- row insert in invoice.paid.

alter table orders
  add column if not exists stripe_checkout_session_id text unique,
  add column if not exists stripe_invoice_id text,
  add column if not exists stripe_subscription_id text,
  add column if not exists stripe_charge_id text,
  add column if not exists total_cents_override integer;

alter table subscriptions
  add column if not exists renewal_reminder_sent_at timestamptz,
  add column if not exists shipping_address jsonb;

create index if not exists subscriptions_period_status_idx
  on subscriptions (current_period_end, status)
  where status = 'active';

create index if not exists orders_checkout_session_idx
  on orders (stripe_checkout_session_id)
  where stripe_checkout_session_id is not null;

create index if not exists orders_subscription_idx
  on orders (stripe_subscription_id)
  where stripe_subscription_id is not null;
