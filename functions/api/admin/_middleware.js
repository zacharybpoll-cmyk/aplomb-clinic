// Mirrors functions/admin/_middleware.js for the JSON endpoints.
// All /api/admin/* must go through aplomb-clinic.pages.dev so Access
// gates them. Non-protected hosts get a 403 (API clients don't follow
// redirects sensibly, and a 302 from an admin POST would silently lose
// the body).

const PROTECTED_HOST = 'aplomb-clinic.pages.dev';

export const onRequest = async ({ request, next }) => {
  const url = new URL(request.url);
  if (url.hostname !== PROTECTED_HOST) {
    return new Response(
      JSON.stringify({ error: 'Admin API only available via aplomb-clinic.pages.dev (Cloudflare Access).' }),
      { status: 403, headers: { 'content-type': 'application/json' } }
    );
  }
  return next();
};
