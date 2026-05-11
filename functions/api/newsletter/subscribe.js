// POST /api/newsletter/subscribe
//
// Body: { email, source?: string }
// Returns: { ok: true, alreadySubscribed: boolean }
//
// Validates email, upserts into newsletter_subscribers table. If new:
// - Adds to Resend audience (if configured)
// - Sends newsletter-welcome email with discount code

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { sendEmail } from '../../_lib/email.js';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const onRequestPost = async ({ request, env }) => {
  let body;
  try {
    body = await request.json();
  } catch (_) {
    return badRequest('Invalid JSON body.');
  }

  const email = (body?.email || '').trim().toLowerCase();
  const source = (body?.source || '').trim();

  if (!email || !EMAIL_REGEX.test(email)) {
    return badRequest('A valid email is required.');
  }

  const sb = supabaseAdmin(env);
  if (!sb) return serverError('Database not configured.');

  // Upsert into newsletter_subscribers
  let isNew = false;
  try {
    const existing = await sb
      .from('newsletter_subscribers')
      .select('id')
      .eq('email', email)
      .maybeSingle();

    if (existing.data) {
      // Already subscribed; update source only
      await sb
        .from('newsletter_subscribers')
        .update({ source })
        .eq('email', email);
    } else {
      // New subscriber
      await sb.from('newsletter_subscribers').insert({
        email,
        source: source || null,
      });
      isNew = true;
    }
  } catch (e) {
    return serverError('Could not update subscription.');
  }

  // If new: add to Resend audience
  if (isNew && env.RESEND_AUDIENCE_ID && env.RESEND_API_KEY) {
    try {
      await fetch(`https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, unsubscribed: false }),
      });
    } catch (_) {
      // Silently tolerate Resend API failures
    }
  }

  // If new: send welcome email
  if (isNew) {
    try {
      await sendEmail(env, 'newsletter-welcome', { email, discountCode: 'APLOMB10' });
    } catch (_) {
      // Tolerate email failures
    }
  }

  return json({ ok: true, alreadySubscribed: !isNew });
};
