-- 0004: order delivery signals + review-request gating
--
-- Adds two columns to orders:
--   * delivered_at — set when carrier confirms delivery (future: tracking webhook).
--     For now NULL on every row; the review-request cron uses shipped_at + 10 days
--     as the trigger and will graduate to delivered_at + 5 days once tracking is wired.
--   * review_request_sent_at — set when /cron/review-requests fires the email.
--     Idempotency: NULL means "not yet sent."

alter table orders
  add column if not exists delivered_at timestamptz,
  add column if not exists review_request_sent_at timestamptz;

-- Index for the cron query: find orders ready for a review request.
create index if not exists orders_review_request_idx
  on orders (shipped_at)
  where review_request_sent_at is null and shipped_at is not null;
