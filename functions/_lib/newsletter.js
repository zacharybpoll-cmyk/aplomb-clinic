// Shared newsletter welcome-series batch logic. Used by:
//   - functions/cron/welcome-series.js   — recurring day-0/3/7 (X-Cron-Secret)
//   - functions/admin/backfill-welcome.js — one-time historical backfill
//                                            (Cloudflare Access gated)
//
// Each batch filters on its own `sentColumn IS NULL` and stamps it on a
// successful send, so every subscriber gets a given email at most once and
// re-runs are idempotent. A per-row send failure is logged and skipped (the
// row stays NULL and is retried next run) — one bad address never blocks the
// rest of the batch.

import { sendEmail } from './email.js';

const DAY_MS = 24 * 60 * 60 * 1000;

// Active subscribers eligible for `sentColumn` (not unsubscribed, not yet
// sent). Unless allAges, also bounded to signups aged [ageMinDays, ageMaxDays].
async function selectPending(sb, { ageMinDays, ageMaxDays, sentColumn, allAges = false }) {
  let q = sb
    .from('newsletter_subscribers')
    .select('*')
    .is('unsubscribed_at', null)
    .is(sentColumn, null);

  if (!allAges) {
    const minDate = new Date(Date.now() - ageMaxDays * DAY_MS).toISOString();
    const maxDate = new Date(Date.now() - ageMinDays * DAY_MS).toISOString();
    q = q.gte('subscribed_at', minDate).lte('subscribed_at', maxDate);
  }

  const { data, error } = await q;
  if (error) throw new Error(error.message);
  return data || [];
}

// Sends `templateName` to every pending subscriber and stamps `sentColumn`.
// opts: { sentColumn, templateName, ageMinDays?, ageMaxDays?, allAges?, dryRun? }
// Returns { count, sample } when dryRun, otherwise { processed }.
export async function runWelcomeBatch(sb, env, opts) {
  const { sentColumn, templateName, dryRun = false } = opts;
  const subs = await selectPending(sb, opts);

  if (dryRun) {
    return { count: subs.length, sample: subs.slice(0, 10).map((s) => s.email) };
  }

  let processed = 0;
  for (const sub of subs) {
    try {
      await sendEmail(env, templateName, {
        to: sub.email,
        email: sub.email,
        discountCode: 'APLOMB10',
      });
      await sb
        .from('newsletter_subscribers')
        .update({ [sentColumn]: new Date().toISOString() })
        .eq('id', sub.id);
      processed++;
    } catch (e) {
      console.warn(`${templateName} send failed for`, sub.id, e?.message || e);
    }
  }
  return { processed };
}
