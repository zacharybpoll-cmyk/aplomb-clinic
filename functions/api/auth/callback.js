// GET /api/auth/callback?token_hash=...&type=magiclink
//
// Lands here after the magic-link click. Exchanges the token_hash for a
// Supabase Auth session, sets the sb-access-token httpOnly cookie, and
// redirects to /account/.

import { setSessionCookie } from '../../_lib/auth.js';

export const onRequestGet = async ({ request, env }) => {
  const url = new URL(request.url);
  const tokenHash = url.searchParams.get('token_hash');
  const type = url.searchParams.get('type') || 'magiclink';
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';

  if (!tokenHash || !env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) {
    return Response.redirect(`${siteUrl}/account/login/?error=invalid_link`, 302);
  }

  let session;
  try {
    const res = await fetch(`${env.SUPABASE_URL}/auth/v1/verify`, {
      method: 'POST',
      headers: {
        'apikey': env.SUPABASE_ANON_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ type, token_hash: tokenHash }),
    });
    if (!res.ok) {
      return Response.redirect(`${siteUrl}/account/login/?error=link_expired`, 302);
    }
    session = await res.json();
  } catch (_) {
    return Response.redirect(`${siteUrl}/account/login/?error=verify_failed`, 302);
  }

  const accessToken = session?.access_token;
  if (!accessToken) {
    return Response.redirect(`${siteUrl}/account/login/?error=no_token`, 302);
  }

  // Build redirect response and attach cookie
  const response = new Response(null, {
    status: 302,
    headers: { Location: `${siteUrl}/account/` },
  });
  setSessionCookie(response, accessToken);
  return response;
};
