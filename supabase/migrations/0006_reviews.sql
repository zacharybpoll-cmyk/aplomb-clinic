-- 0006: product reviews — verified-buyer, moderated, honestly displayed
--
-- Design notes (consistent with 0001_init.sql conventions):
-- * A review is tied to a real order (order_id FK) and a product_key that must
--   appear in that order's line_items — enforced in the API, not the DB, since
--   line_items is denormalized jsonb. One review per (order, product).
-- * status starts 'pending'. Nothing is shown on a PDP until a human flips it
--   to 'published' via /api/admin/reviews (Cloudflare Access protected). We
--   never fabricate or auto-publish — the trust moat is the whole point.
-- * RLS on, no public policies: all reads/writes flow through Cloudflare
--   Functions using the service-role key, exactly like orders/subscriptions.
--   /api/reviews filters to status='published' server-side before responding.
--
-- Apply via: supabase db push  (or paste into the Supabase SQL editor)

create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  product_key text not null,
  rating int not null check (rating between 1 and 5),
  title text check (title is null or char_length(title) <= 160),
  body text not null check (char_length(body) between 1 and 4000),
  customer_name text check (customer_name is null or char_length(customer_name) <= 80),
  status text not null default 'pending'
    check (status in ('pending', 'published', 'rejected')),
  created_at timestamptz not null default now(),
  published_at timestamptz,
  unique (order_id, product_key)
);

-- PDP read path: published reviews for one product, newest first.
create index if not exists reviews_pdp_idx
  on reviews (product_key, published_at desc)
  where status = 'published';

-- Moderation queue: oldest-pending first.
create index if not exists reviews_moderation_idx
  on reviews (created_at)
  where status = 'pending';

alter table reviews enable row level security;

-- service_role bypasses RLS; no anon/authenticated policies are defined, so
-- the table is unreadable/unwritable except through the server Functions.
