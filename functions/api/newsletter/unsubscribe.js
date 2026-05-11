// POST /api/newsletter/unsubscribe
//
// Body: { token } OR GET ?token=
// Returns: { ok: true }
//
// Verifies token signature and expiry, marks subscriber as unsubscribed,
// removes from Resend audience. Idempotent.

import { json, badRequest, serverError } from '../../_lib/json.js';
import { supabaseAdmin } from '../../_lib/supabase.js';
import { verifyUnsubscribeToken } from '../../_lib/auth.js';

async function unsubscribeWithToken(token, env) {
  if (!token) return { status: 400, body: { error: 'Token is required.' } };
  const email = await verifyUnsubscribeToken(token, env);
  if (!email) return { status: 400, body: { error: 'Invalid or expired link.' } };

  const sb = supabaseAdmin(env);
  if (!sb) return { status: 500, body: { error: 'Database not configured.' } };

  try {
    await sb.from('newsletter_subscribers')
      .update({ unsubscribed_at: new Date().toISOString() })
      .eq('email', email);
  } catch (_) {
    return { status: 500, body: { error: 'Could not update subscription.' } };
  }

  if (env.RESEND_AUDIENCE_ID && env.RESEND_API_KEY) {
    try {
      await fetch(`https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts/${email}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${env.RESEND_API_KEY}` },
      });
    } catch (_) {}
  }
  return { status: 200, body: { ok: true } };
}

export const onRequestPost = async ({ request, env }) => {
  let body;
  try { body = await request.json(); } catch (_) { return badRequest('Invalid JSON body.'); }
  const r = await unsubscribeWithToken((body?.token || '').trim(), env);
  return new Response(JSON.stringify(r.body), { status: r.status, headers: { 'content-type': 'application/json' } });
};

// GET /api/newsletter/unsubscribe?token=... — landing page redirect target from email footers
export const onRequestGet = async ({ request, env }) => {
  const url = new URL(request.url);
  const token = (url.searchParams.get('token') || '').trim();
  const r = await unsubscribeWithToken(token, env);
  // Redirect to /email-preferences/ with a status query so the page can render the right state
  const target = new URL('/email-preferences/', url);
  target.searchParams.set('status', r.body.ok ? 'unsubscribed' : 'error');
  if (r.body.error) target.searchParams.set('reason', r.body.error);
  return Response.redirect(target.toString(), 302);
};
