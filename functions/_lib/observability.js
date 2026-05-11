// APLOMB. — Server-side Sentry forwarding for Pages Functions.
//
// withSentry(handler) wraps a Function so any thrown error is forwarded to
// Sentry (if SENTRY_DSN is configured) with request context. The wrapper
// rethrows after capture; the Pages runtime still returns the 500.
//
// Designed to be cheap: a DSN miss makes the wrapper a no-op. No SDK
// dependency — we POST directly to the Sentry Store endpoint.

function parseDsn(dsn) {
  try {
    const u = new URL(dsn);
    return { host: u.host, projectId: u.pathname.replace(/^\//, ''), publicKey: u.username };
  } catch (_) { return null; }
}

async function reportToSentry(env, eventLike) {
  if (!env || !env.SENTRY_DSN) return;
  const parsed = parseDsn(env.SENTRY_DSN);
  if (!parsed) return;
  const endpoint = `https://${parsed.host}/api/${parsed.projectId}/store/?sentry_key=${parsed.publicKey}&sentry_version=7`;
  try {
    const body = JSON.stringify(Object.assign({
      platform: 'javascript',
      timestamp: new Date().toISOString(),
      environment: env.ENVIRONMENT || 'production',
      release: env.RELEASE || 'getaplomb-functions',
      tags: { runtime: 'cloudflare-pages-functions' },
    }, eventLike));
    await fetch(endpoint, { method: 'POST', body, headers: { 'Content-Type': 'application/json' } });
  } catch (_) {
    // Don't let the error reporter throw — that would mask the original error.
  }
}

export function withSentry(handler) {
  return async (context) => {
    try {
      return await handler(context);
    } catch (err) {
      const request = context?.request;
      const url = request ? (() => { try { return new URL(request.url).pathname; } catch (_) { return null; } })() : null;
      await reportToSentry(context?.env, {
        exception: {
          values: [{
            type: err?.name || 'Error',
            value: err?.message || String(err),
            stacktrace: err?.stack ? { frames: parseStack(err.stack) } : undefined,
          }],
        },
        request: url ? { url, method: request.method } : undefined,
      });
      throw err;
    }
  };
}

// Crude Sentry-compatible stack-frame array from a V8 stack string.
function parseStack(stack) {
  return stack.split('\n').slice(1, 16).map(line => {
    const m = line.match(/at (?:(.+?) )?\(?([^()]+):(\d+):(\d+)\)?$/);
    if (!m) return { function: line.trim() };
    return { function: m[1] || '?', filename: m[2], lineno: parseInt(m[3], 10), colno: parseInt(m[4], 10) };
  }).reverse(); // Sentry expects oldest-first
}

export const captureMessage = (env, message, level = 'info') => reportToSentry(env, {
  message: { formatted: message },
  level,
});
