-- 0003: newsletter subscribers, driven by the footer signup form and a 3-email
-- welcome series cron. Service-role only writes; no public policies.

create extension if not exists citext;

create table if not exists newsletter_subscribers (
  id uuid primary key default gen_random_uuid(),
  email citext unique not null,
  source text,
  subscribed_at timestamptz not null default now(),
  unsubscribed_at timestamptz,
  welcome_day_3_sent_at timestamptz,
  welcome_day_7_sent_at timestamptz,
  preferences jsonb default '{}'::jsonb,
  metadata jsonb default '{}'::jsonb
);

create index if not exists newsletter_email_idx
  on newsletter_subscribers (email);

create index if not exists newsletter_active_subscribed_idx
  on newsletter_subscribers (subscribed_at)
  where unsubscribed_at is null;

alter table newsletter_subscribers enable row level security;
-- Intentionally no public policies. All writes go through service-role.
