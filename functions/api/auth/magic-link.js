// POST /api/auth/magic-link
//
// Body: { email }
// Returns: { ok: true } always (don't leak account existence).
//
// Uses Supabase Auth's admin API to mint a magic link without sending the
// default email, then sends our branded one via Resend.

import { json, badRequest, serverError } from '../../_lib/json.js';
import { sendEmail } from '../../_lib/email.js';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const onRequestPost = async ({ request, env }) => {
  if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) {
    return serverError('Auth not configured.');
  }

  let body;
  try { body = await request.json(); } catch { return badRequest('Invalid JSON body.'); }

  const email = (body?.email || '').trim().toLowerCase();
  if (!email || !EMAIL_REGEX.test(email)) return badRequest('A valid email is required.');

  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const redirectTo = `${siteUrl}/api/auth/callback`;

  // Mint a magiclink via Auth Admin (doesn't send a default email)
  let actionLink;
  try {
    const res = await fetch(`${env.SUPABASE_URL}/auth/v1/admin/generate_link`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': env.SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'magiclink',
        email,
        options: { redirect_to: redirectTo },
      }),
    });
    if (!res.ok) {
      // Don't leak: any error other than 500-class is treated as "we attempted; move on"
      const text = await res.text();
      console.warn('supabase generate_link failed', res.status, text);
      // Still return ok to avoid account-existence leak
      return json({ ok: true });
    }
    const data = await res.json();
    actionLink = data?.properties?.action_link || data?.action_link || null;
  } catch (e) {
    console.warn('supabase generate_link threw', e);
    return json({ ok: true });
  }

  if (!actionLink) return json({ ok: true });

  // Send our branded magic-link email instead of Supabase's default
  try {
    await sendEmail(env, 'magic-link', {
      to: email,
      signInUrl: actionLink,
      email,
      expiresIn: '15 minutes',
    });
  } catch (e) {
    console.warn('magic-link send failed', e);
  }

  return json({ ok: true });
};
