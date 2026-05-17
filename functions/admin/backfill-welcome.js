// GET /admin/backfill-welcome
//
// One-time recovery for subscribers who never received the day-0 welcome —
// the window where EMAIL_UNSUB_SECRET was unconfigured and every synchronous
// send in subscribe.js threw and was swallowed silently.
//
// Gated by Cloudflare Access (Google SSO, zachary@getaplomb.com) via
// functions/admin/_middleware.js, which forces all /admin/* traffic through
// the Access-protected aplomb-clinic.pages.dev host. Open it in a browser:
//
//   /admin/backfill-welcome          → dry-run: pending count + sample
//   /admin/backfill-welcome?send=1   → send the welcome to every pending sub
//
// Idempotent: only rows with welcome_sent_at IS NULL (and not unsubscribed)
// are touched, and welcome_sent_at is stamped on success — safe to re-run.

import { json, serverError } from '../_lib/json.js';
import { supabaseAdmin } from '../_lib/supabase.js';
import { runWelcomeBatch } from '../_lib/newsletter.js';

export const onRequestGet = async ({ request, env }) => {
  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  const send = new URL(request.url).searchParams.get('send') === '1';

  try {
    const result = await runWelcomeBatch(sb, env, {
      sentColumn: 'welcome_sent_at',
      templateName: 'newsletter-welcome',
      allAges: true,
      dryRun: !send,
    });

    if (!send) {
      return json({
        mode: 'dry-run',
        pending: result.count,
        sample: result.sample,
        note: 'Append ?send=1 to this URL to send the welcome email to all pending subscribers.',
      });
    }
    return json({ mode: 'sent', sent: result.processed });
  } catch (e) {
    return serverError(e.message);
  }
};
