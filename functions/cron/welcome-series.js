// POST /cron/welcome-series
//
// Auth: X-Cron-Secret header must match env.CRON_SHARED_SECRET.
//
// Runs the day-3 and day-7 batches of the newsletter welcome series.

import { json, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { sendEmail } from '../_lib/email.js';

async function runBatch(sb, env, { ageMinDays, ageMaxDays, sentColumn, templateName }) {
  const minDate = new Date(Date.now() - ageMaxDays * 24 * 60 * 60 * 1000).toISOString();
  const maxDate = new Date(Date.now() - ageMinDays * 24 * 60 * 60 * 1000).toISOString();
  const { data: subs, error } = await sb.from('newsletter_subscribers')
    .select('*')
    .is('unsubscribed_at', null)
    .is(sentColumn, null)
    .gte('subscribed_at', minDate)
    .lte('subscribed_at', maxDate);
  if (error) throw new Error(error.message);

  let processed = 0;
  for (const sub of subs || []) {
    try {
      await sendEmail(env, templateName, {
        to: sub.email,
        email: sub.email,
        discountCode: 'APLOMB10',
      });
      await sb.from('newsletter_subscribers')
        .update({ [sentColumn]: new Date().toISOString() })
        .eq('id', sub.id);
      processed++;
    } catch (e) {
      console.warn(`${templateName} send failed for`, sub.id, e?.message || e);
    }
  }
  return processed;
}

export const onRequestPost = async ({ request, env }) => {
  const provided = request.headers.get('x-cron-secret') || '';
  if (!env.CRON_SHARED_SECRET || provided !== env.CRON_SHARED_SECRET) {
    return new Response('Forbidden', { status: 401 });
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  try {
    const day3 = await runBatch(sb, env, {
      ageMinDays: 3, ageMaxDays: 4, sentColumn: 'welcome_day_3_sent_at', templateName: 'welcome-day-3',
    });
    const day7 = await runBatch(sb, env, {
      ageMinDays: 7, ageMaxDays: 8, sentColumn: 'welcome_day_7_sent_at', templateName: 'welcome-day-7',
    });
    return json({ day3, day7 });
  } catch (e) {
    return serverError(e.message);
  }
};
