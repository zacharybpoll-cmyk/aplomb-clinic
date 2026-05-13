// Force all /admin/* traffic to go through aplomb-clinic.pages.dev so
// Cloudflare Access (configured only on that hostname while the zone
// migration is locked until 2026-07-08) gates 100% of admin access.
//
// Any other host (getaplomb.com, www.getaplomb.com, custom previews)
// gets a 302 to the Access-protected URL with the original path.

const PROTECTED_HOST = 'aplomb-clinic.pages.dev';

export const onRequest = async ({ request, next }) => {
  const url = new URL(request.url);
  if (url.hostname !== PROTECTED_HOST) {
    const target = new URL(url.pathname + url.search, `https://${PROTECTED_HOST}`);
    return Response.redirect(target.toString(), 302);
  }
  return next();
};
