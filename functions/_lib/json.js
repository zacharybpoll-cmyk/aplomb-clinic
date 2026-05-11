// Tiny helpers for JSON responses on Cloudflare Pages Functions.

export function json(body, init = {}) {
  return new Response(JSON.stringify(body), {
    status: init.status || 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      ...(init.headers || {}),
    },
  });
}

export function badRequest(error, status = 400) {
  return json({ error }, { status });
}

export function serverError(error = 'Internal error') {
  return json({ error }, { status: 500 });
}
