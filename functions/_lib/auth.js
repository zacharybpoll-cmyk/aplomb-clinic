// Shared auth helpers for Cloudflare Pages Functions:
//  - getSessionFromRequest(): decode + HMAC-verify a Supabase Auth JWT from the
//    sb-access-token cookie. Returns { email, userId, role, exp } or null.
//  - requireSession(): throws a 401 Response when no valid session exists.
//  - signUnsubscribeToken / verifyUnsubscribeToken: HMAC-signed tokens used in
//    email footers to let recipients unsubscribe without logging in.
//
// All crypto uses the Web Crypto API available in the Workers runtime; no
// Node packages required.

function b64urlDecode(s) {
  const pad = s.length % 4 === 2 ? '==' : s.length % 4 === 3 ? '=' : '';
  return atob(s.replace(/-/g, '+').replace(/_/g, '/') + pad);
}

function b64urlEncode(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function readCookie(request, name) {
  const header = request.headers.get('cookie') || '';
  for (const part of header.split(/;\s*/)) {
    const i = part.indexOf('=');
    if (i < 0) continue;
    if (part.slice(0, i) === name) return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

async function importHmacKey(secret) {
  return crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify']
  );
}

// Verify a Supabase Auth JWT (HS256) and return the decoded payload, or null
// on any failure (missing, malformed, bad sig, expired). Never throws.
export async function getSessionFromRequest(request, env) {
  const token = readCookie(request, 'sb-access-token');
  if (!token || !env.SUPABASE_JWT_SECRET) return null;

  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, sigB64] = parts;

  try {
    const header = JSON.parse(b64urlDecode(headerB64));
    if (header.alg !== 'HS256') return null;

    const key = await importHmacKey(env.SUPABASE_JWT_SECRET);
    const sigBytes = Uint8Array.from(b64urlDecode(sigB64), (c) => c.charCodeAt(0));
    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const valid = await crypto.subtle.verify('HMAC', key, sigBytes, data);
    if (!valid) return null;

    const payload = JSON.parse(b64urlDecode(payloadB64));
    if (!payload.exp || payload.exp * 1000 < Date.now()) return null;
    return {
      email: (payload.email || '').toLowerCase(),
      userId: payload.sub,
      role: payload.role || 'authenticated',
      exp: payload.exp,
      raw: token,
    };
  } catch (_) {
    return null;
  }
}

// Throws a 401 Response when no valid session. Use in Functions like:
//   const session = await requireSession(request, env);
export async function requireSession(request, env) {
  const session = await getSessionFromRequest(request, env);
  if (!session) {
    throw new Response(JSON.stringify({ error: 'Sign in to access this resource.' }), {
      status: 401,
      headers: { 'content-type': 'application/json' },
    });
  }
  return session;
}

// Token format: base64url(JSON({email, exp})) + "." + base64url(HMAC).
// 1-year expiry; secret comes from env.EMAIL_UNSUB_SECRET.
export async function signUnsubscribeToken(email, env) {
  const exp = Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 365;
  const payload = b64urlEncode(new TextEncoder().encode(JSON.stringify({ email, exp })));
  const key = await importHmacKey(env.EMAIL_UNSUB_SECRET || '');
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(payload));
  return `${payload}.${b64urlEncode(sig)}`;
}

export async function verifyUnsubscribeToken(token, env) {
  try {
    const [payloadB64, sigB64] = String(token || '').split('.');
    if (!payloadB64 || !sigB64) return null;
    const key = await importHmacKey(env.EMAIL_UNSUB_SECRET || '');
    const sigBytes = Uint8Array.from(b64urlDecode(sigB64), (c) => c.charCodeAt(0));
    const valid = await crypto.subtle.verify(
      'HMAC',
      key,
      sigBytes,
      new TextEncoder().encode(payloadB64)
    );
    if (!valid) return null;
    const { email, exp } = JSON.parse(b64urlDecode(payloadB64));
    if (!email || !exp || exp < Math.floor(Date.now() / 1000)) return null;
    return String(email).toLowerCase();
  } catch (_) {
    return null;
  }
}

// Convenience: set the session cookie on a Response object.
export function setSessionCookie(response, accessToken, { maxAgeSeconds = 60 * 60 * 24 * 7 } = {}) {
  response.headers.append(
    'Set-Cookie',
    [
      `sb-access-token=${encodeURIComponent(accessToken)}`,
      `Max-Age=${maxAgeSeconds}`,
      'Path=/',
      'HttpOnly',
      'Secure',
      'SameSite=Lax',
    ].join('; ')
  );
  return response;
}

export function clearSessionCookie(response) {
  response.headers.append('Set-Cookie', 'sb-access-token=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax');
  return response;
}
