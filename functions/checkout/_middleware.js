// Middleware for /checkout/* — injects public client-side keys into the
// HTML response head as <meta> tags so the same static HTML works for both
// test (preview) and live (production) without committing pk_… strings to git.
//
// Reads:
//   - STRIPE_PUBLISHABLE_KEY  → <meta name="stripe-publishable-key">
//   - TURNSTILE_SITE_KEY      → <meta name="turnstile-site-key">
//   - PLAUSIBLE_SITE_ID       → <meta name="plausible-site-id">
//   - SENTRY_DSN              → <meta name="sentry-dsn">
//
// If a variable is unset, that tag is omitted; the corresponding feature
// gracefully no-ops on the client.

const META_FROM_ENV = [
  { env: 'STRIPE_PUBLISHABLE_KEY', meta: 'stripe-publishable-key' },
  { env: 'TURNSTILE_SITE_KEY',     meta: 'turnstile-site-key' },
  { env: 'PLAUSIBLE_SITE_ID',      meta: 'plausible-site-id' },
  { env: 'SENTRY_DSN',             meta: 'sentry-dsn' },
];

function escapeAttr(s) {
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export const onRequest = async ({ request, env, next }) => {
  const response = await next();
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.toLowerCase().includes('text/html')) return response;

  const tags = META_FROM_ENV
    .filter(({ env: key }) => env[key])
    .map(({ env: key, meta }) => `<meta name="${meta}" content="${escapeAttr(env[key])}">`)
    .join('\n');

  if (!tags) return response;

  const text = await response.text();
  const newText = text.replace(/<\/head>/i, `${tags}\n</head>`);
  return new Response(newText, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
