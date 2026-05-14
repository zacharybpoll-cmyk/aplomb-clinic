// POST /api/auth/magic-link
//
// Body: { email }
// Returns: { ok: true } always (don't leak account existence).
//
// Mints a hashed magiclink token via Supabase Auth Admin (no Supabase email
// sent), then emails our own branded link pointing at OUR /api/auth/callback.
// That bypasses Supabase's verify-and-redirect dance — which returns the
// session in the URL fragment (unreadable by a Cloudflare Function) and
// silently falls back to the Site URL if redirect_to isn't allowlisted.
//
// First-time sign-in: if the user doesn't exist in Supabase Auth yet, we
// create them (email_confirm: true) and retry generate_link. Sign in == sign up.

import { json, badRequest, serverError } from '../../_lib/json.js';
import { sendEmail } from '../../_lib/email.js';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

async function callGenerateLink(env, email) {
  return fetch(`${env.SUPABASE_URL}/auth/v1/admin/generate_link`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      'apikey': env.SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type: 'magiclink', email, options: {} }),
  });
}

async function createAuthUser(env, email) {
  return fetch(`${env.SUPABASE_URL}/auth/v1/admin/users`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      'apikey': env.SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, email_confirm: true }),
  });
}

export const onRequestPost = async ({ request, env }) => {
  if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) {
    return serverError('Auth not configured.');
  }

  let body;
  try { body = await request.json(); } catch { return badRequest('Invalid JSON body.'); }

  const email = (body?.email || '').trim().toLowerCase();
  if (!email || !EMAIL_REGEX.test(email)) return badRequest('A valid email is required.');

  const siteUrl = env.SITE_URL || 'https://getaplomb.com';

  let data;
  try {
    let res = await callGenerateLink(env, email);

    if (res.status === 422 || res.status === 404) {
      const errText = await res.clone().text().catch(() => '');
      const isUserMissing = /user[_ ]?not[_ ]?found|User not found/i.test(errText);
      if (isUserMissing) {
        const create = await createAuthUser(env, email);
        if (!create.ok && create.status !== 422) {
          const t = await create.text().catch(() => '');
          console.warn('supabase admin/users create failed', create.status, t);
        }
        res = await callGenerateLink(env, email);
      }
    }

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      console.warn('supabase generate_link failed', res.status, text);
      return json({ ok: true });
    }
    data = await res.json();
  } catch (e) {
    console.warn('supabase generate_link threw', e);
    return json({ ok: true });
  }

  // admin/generate_link returns hashed_token at the top level (older versions
  // nested it under `properties`); accept both.
  const hashedToken = data?.properties?.hashed_token || data?.hashed_token || null;
  if (!hashedToken) return json({ ok: true });

  // Build OUR callback URL — user clicks straight into our Function, which
  // calls /auth/v1/verify server-side and sets the sb-access-token cookie.
  const callbackUrl = new URL(`${siteUrl}/api/auth/callback`);
  callbackUrl.searchParams.set('token_hash', hashedToken);
  callbackUrl.searchParams.set('type', 'magiclink');

  try {
    await sendEmail(env, 'magic-link', {
      to: email,
      signInUrl: callbackUrl.toString(),
      email,
      expiresIn: '15 minutes',
    });
  } catch (e) {
    console.warn('magic-link send failed', e);
  }

  return json({ ok: true });
};
