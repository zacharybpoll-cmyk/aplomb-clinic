// POST /cron/welcome-series
//
// Auth: X-Cron-Secret header must match env.CRON_SHARED_SECRET.
//
// Runs the day-0 (self-healing), day-3, and day-7 batches of the newsletter
// welcome series. Scheduled daily by the companion Worker (30 9 * * *).

import { json, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { runWelcomeBatch } from '../_lib/newsletter.js';

export const onRequestPost = async ({ request, env }) => {
  const provided = request.headers.get('x-cron-secret') || '';
  if (!env.CRON_SHARED_SECRET || provided !== env.CRON_SHARED_SECRET) {
    return new Response('Forbidden', { status: 401 });
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  try {
    // Day-0 recovery: re-send the welcome to anyone whose synchronous send in
    // subscribe.js failed in the last ~3 days (transient error, or the
    // EMAIL_UNSUB_SECRET-unset window). Idempotent — subscribe.js stamps
    // welcome_sent_at on success, so already-welcomed rows are skipped.
    const day0 = await runWelcomeBatch(sb, env, {
      ageMinDays: 0, ageMaxDays: 3, sentColumn: 'welcome_sent_at', templateName: 'newsletter-welcome',
    });
    const day3 = await runWelcomeBatch(sb, env, {
      ageMinDays: 3, ageMaxDays: 4, sentColumn: 'welcome_day_3_sent_at', templateName: 'welcome-day-3',
    });
    const day7 = await runWelcomeBatch(sb, env, {
      ageMinDays: 7, ageMaxDays: 8, sentColumn: 'welcome_day_7_sent_at', templateName: 'welcome-day-7',
    });
    return json({ day0: day0.processed, day3: day3.processed, day7: day7.processed });
  } catch (e) {
    return serverError(e.message);
  }
};
