// POST /api/auth/logout
// Clears the sb-access-token cookie. Frontend handles the redirect.

import { clearSessionCookie } from '../../_lib/auth.js';

export const onRequestPost = async () => {
  const response = new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
  clearSessionCookie(response);
  return response;
};
