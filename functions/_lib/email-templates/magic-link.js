// Sign-in magic-link email. Replaces Supabase Auth's default template
// (we mint the link via the Auth Admin API and send our own branded version).

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';

export const SUBJECT = 'Your APLOMB. sign-in link';

export function render(env, data) {
  const { signInUrl, email = '', expiresIn = '15 minutes' } = data;
  if (!signInUrl) throw new Error('magic-link requires signInUrl');

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;">Click the button below to sign in to your APLOMB. account.</p>
      <p style="margin:24px 0;">
        <a href="${escapeHtml(signInUrl)}" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Sign in</a>
      </p>
      <p style="margin:24px 0 0;font:400 13px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        This link expires in ${escapeHtml(expiresIn)} and can only be used once. If the button doesn't work, paste this URL into your browser:<br>
        <span style="word-break:break-all;color:${BRAND.colors.accent};">${escapeHtml(signInUrl)}</span>
      </p>
      <p style="margin:24px 0 0;font:400 12px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        Didn't ask for this? You can safely ignore this email — no one can sign in without clicking the link.
      </p>
    </td></tr>
  `, env);

  const text = `Your APLOMB. sign-in link

Click to sign in: ${signInUrl}

This link expires in ${expiresIn} and can only be used once.

Didn't ask for this? You can safely ignore this email — no one can sign in without clicking the link.
`;

  return { subject: SUBJECT, html, text };
}
