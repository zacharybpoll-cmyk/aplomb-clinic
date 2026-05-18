// Root host canonicalization. Consolidates every request onto the single
// canonical host so search engines don't split a brand-new domain's scarce
// crawl budget across three live copies of the site:
//
//   getaplomb.com          → canonical (served as-is)
//   www.getaplomb.com      → 301 → getaplomb.com (www has no role here)
//   aplomb-clinic.pages.dev → 301 → getaplomb.com  EXCEPT /admin + /api/admin,
//                             which MUST stay on pages.dev because Cloudflare
//                             Access gates only that hostname while the zone
//                             migration is locked until 2026-07-08
//                             (see functions/admin/_middleware.js).
//
// Cloudflare Pages runs this root middleware first, then the nested
// /admin, /api/admin, /checkout middleware via next() — so passing admin
// requests through untouched preserves the existing Access flow exactly.

const CANONICAL_HOST = 'getaplomb.com';
const PAGES_HOST = 'aplomb-clinic.pages.dev';

function isAdminPath(pathname) {
  return (
    pathname === '/admin' ||
    pathname.startsWith('/admin/') ||
    pathname === '/api/admin' ||
    pathname.startsWith('/api/admin/')
  );
}

export const onRequest = async ({ request, next }) => {
  const url = new URL(request.url);
  const host = url.hostname;

  // www → apex. Admin never uses www, so no exclusion needed.
  if (host === 'www.getaplomb.com') {
    const target = new URL(url.pathname + url.search, `https://${CANONICAL_HOST}`);
    return Response.redirect(target.toString(), 301);
  }

  // Pages preview host: redirect the public duplicate to apex, but leave the
  // Access-gated admin surface on pages.dev untouched.
  if (host === PAGES_HOST && !isAdminPath(url.pathname)) {
    const target = new URL(url.pathname + url.search, `https://${CANONICAL_HOST}`);
    return Response.redirect(target.toString(), 301);
  }

  return next();
};
