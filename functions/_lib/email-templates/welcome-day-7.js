// Day-7 newsletter follow-up: discount expiry nudge.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken } from '../auth.js';

export const SUBJECT = 'Your 10% off expires in 24 hours';

export async function render(env, data) {
  const { email, discountCode = 'APLOMB10' } = data;
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const unsubscribeUrl = email
    ? `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`
    : null;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;font:italic 400 22px/1.3 ${BRAND.fonts.display};color:${BRAND.colors.text};">
        A reminder, since it expires tomorrow.
      </p>
      <p style="margin:0 0 18px;">Your 10% welcome discount code <strong style="color:${BRAND.colors.accent};">${escapeHtml(discountCode)}</strong> expires in 24 hours.</p>
      <p style="margin:0 0 18px;">If you've been weighing whether to try the line, this is the cheapest moment. It works on one-time orders and on the first subscription cycle.</p>
      <p style="margin:24px 0;">
        <a href="${siteUrl}/" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Use it now</a>
      </p>
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        No FOMO theater after this — if you don't redeem, we won't keep nagging. You'll just hear from us about once a month with new science and the occasional product update.
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `Your 10% off expires in 24 hours.

Code: ${discountCode}
Shop: ${siteUrl}/

No FOMO theater after this — if you don't redeem, we won't keep nagging.
`;

  return { subject: SUBJECT, html, text };
}
