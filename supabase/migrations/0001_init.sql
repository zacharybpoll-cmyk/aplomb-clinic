-- APLOMB. — initial schema for orders, customers, subscriptions
-- Apply via: supabase db push  (or paste into Supabase SQL editor)
--
-- Design notes:
-- * orders is the system of record for a single transaction. line_items are
--   denormalized as a jsonb column to keep checkout writes atomic; the source
--   of truth for product pricing lives in functions/_lib/products.js.
-- * subscriptions mirrors Stripe state, written by the webhook handler.
-- * stripe_events is the idempotency table — every webhook event id is
--   inserted; a unique-violation tells the handler the event is a replay.
-- * Row-Level Security: orders & subscriptions are visible to the customer
--   themselves (matched on email = auth.jwt()->>'email') and the
--   service_role; everything else is service_role-only.

create extension if not exists "pgcrypto";
create extension if not exists "citext";

-- ----------------------------------------------------------------------------
-- customers
-- ----------------------------------------------------------------------------
create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  email citext not null unique,
  name text,
  stripe_customer_id text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists customers_stripe_customer_id_idx on customers(stripe_customer_id);

-- ----------------------------------------------------------------------------
-- orders
-- ----------------------------------------------------------------------------
create type order_status as enum ('pending', 'paid', 'failed', 'refunded', 'fulfilled', 'shipped', 'canceled');

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  email citext not null,
  customer_name text,
  stripe_payment_intent_id text unique,
  stripe_customer_id text,
  subtotal_cents integer not null check (subtotal_cents >= 0),
  shipping_cents integer not null default 0 check (shipping_cents >= 0),
  tax_cents integer not null default 0 check (tax_cents >= 0),
  total_cents integer generated always as (subtotal_cents + shipping_cents + tax_cents) stored,
  currency text not null default 'usd',
  status order_status not null default 'pending',
  line_items jsonb not null default '[]'::jsonb,
  shipping_address jsonb,
  tracking_number text,
  carrier text,
  created_at timestamptz not null default now(),
  paid_at timestamptz,
  shipped_at timestamptz,
  refunded_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists orders_email_idx on orders(email);
create index if not exists orders_status_idx on orders(status);
create index if not exists orders_stripe_pi_idx on orders(stripe_payment_intent_id);

-- ----------------------------------------------------------------------------
-- subscriptions (mirror of Stripe)
-- ----------------------------------------------------------------------------
create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  stripe_subscription_id text not null unique,
  stripe_customer_id text not null,
  email citext,
  status text not null,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  items jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  canceled_at timestamptz
);

create index if not exists subscriptions_email_idx on subscriptions(email);
create index if not exists subscriptions_customer_idx on subscriptions(stripe_customer_id);

-- ----------------------------------------------------------------------------
-- stripe_events (webhook idempotency)
-- ----------------------------------------------------------------------------
create table if not exists stripe_events (
  id text primary key,
  type text not null,
  received_at timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- inventory (single-row counter per SKU; week 3 will read this)
-- ----------------------------------------------------------------------------
create table if not exists inventory (
  product_key text primary key,
  on_hand integer not null check (on_hand >= 0),
  reserved integer not null default 0 check (reserved >= 0),
  updated_at timestamptz not null default now()
);

-- Seed inventory rows so the admin UI can see all SKUs from day one.
insert into inventory (product_key, on_hand) values
  ('serum', 0), ('daily', 0), ('roots', 0), ('calm', 0), ('breath', 0)
on conflict (product_key) do nothing;

-- ----------------------------------------------------------------------------
-- updated_at trigger
-- ----------------------------------------------------------------------------
create or replace function set_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists customers_updated_at on customers;
create trigger customers_updated_at before update on customers
  for each row execute function set_updated_at();

drop trigger if exists subscriptions_updated_at on subscriptions;
create trigger subscriptions_updated_at before update on subscriptions
  for each row execute function set_updated_at();

drop trigger if exists inventory_updated_at on inventory;
create trigger inventory_updated_at before update on inventory
  for each row execute function set_updated_at();

-- ----------------------------------------------------------------------------
-- Row-Level Security
-- ----------------------------------------------------------------------------
alter table customers enable row level security;
alter table orders enable row level security;
alter table subscriptions enable row level security;
alter table stripe_events enable row level security;
alter table inventory enable row level security;

-- Customers can read their own row; nothing else.
create policy customers_self_select on customers
  for select using (email = auth.jwt() ->> 'email');

-- Customers can read their own orders.
create policy orders_self_select on orders
  for select using (email = auth.jwt() ->> 'email');

-- Customers can read their own subscriptions.
create policy subscriptions_self_select on subscriptions
  for select using (email = auth.jwt() ->> 'email');

-- service_role bypasses RLS automatically; no other write policies are
-- defined, which means anon/authenticated users cannot write to any of these
-- tables. All writes flow through the Cloudflare Functions using the service
-- role key.
