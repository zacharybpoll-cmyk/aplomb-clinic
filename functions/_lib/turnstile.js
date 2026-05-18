// Cloudflare Turnstile server-side verification.
//
// The checkout page renders a Turnstile widget (when TURNSTILE_SITE_KEY is
// set) and sends the resulting token to /api/checkout — but until now nothing
// ever validated that token, so the challenge was decorative. This closes
// that gap.
//
// Failure philosophy matches the rest of this codebase (never block a real
// sale over an ancillary system — cf. Stripe Tax and Resend both fail open):
//
//   * No TURNSTILE_SECRET_KEY configured  → { ok: true, skipped: true }
//     (current production state — zero behavior change until the owner sets
//     the secret; the feature is dormant, not breaking checkout).
//   * Configured + Cloudflare says success → { ok: true }
//   * Configured + Cloudflare says FAILURE → { ok: false }  (the only block)
//   * Configured but token missing         → { ok: false }
//   * Network / parse error reaching Cloudflare → { ok: true, degraded: true }
//     (a Cloudflare outage must not take down our checkout)
//
// Never throws.

const SITEVERIFY = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

export async function verifyTurnstile(token, env, remoteIp) {
  const secret = env && env.TURNSTILE_SECRET_KEY;
  if (!secret) return { ok: true, skipped: true };

  if (!token || typeof token !== 'string') {
    return { ok: false, reason: 'missing-token' };
  }

  try {
    const form = new URLSearchParams();
    form.set('secret', secret);
    form.set('response', token);
    if (remoteIp) form.set('remoteip', remoteIp);

    const res = await fetch(SITEVERIFY, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });

    if (!res.ok) {
      // Cloudflare itself is unreachable/erroring — degrade open.
      return { ok: true, degraded: true, reason: `http-${res.status}` };
    }

    const data = await res.json();
    if (data && data.success === true) return { ok: true };
    return {
      ok: false,
      reason: 'verification-failed',
      codes: (data && data['error-codes']) || [],
    };
  } catch (e) {
    return { ok: true, degraded: true, reason: 'exception' };
  }
}
