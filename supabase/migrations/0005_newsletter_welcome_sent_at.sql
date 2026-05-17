-- 0005: day-0 newsletter welcome delivery tracking
--
-- subscribe.js sends the welcome email synchronously on signup and now stamps
-- welcome_sent_at on success. The welcome-series cron gained a day-0 recovery
-- batch (and /admin/backfill-welcome a one-time historical sweep) that
-- re-sends to any active subscriber whose welcome_sent_at is still NULL —
-- recovering the window where EMAIL_UNSUB_SECRET was unconfigured and every
-- welcome silently threw. NULL = "welcome not yet delivered."

alter table newsletter_subscribers
  add column if not exists welcome_sent_at timestamptz;

-- Index for the day-0 / backfill query: active subscribers awaiting welcome.
create index if not exists newsletter_welcome_pending_idx
  on newsletter_subscribers (subscribed_at)
  where welcome_sent_at is null and unsubscribed_at is null;
