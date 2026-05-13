// Day-0 newsletter welcome.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken } from '../auth.js';

export const SUBJECT = 'Welcome to APLOMB.';

export async function render(env, data) {
  const { email, discountCode = 'APLOMB10' } = data;
  if (!email) throw new Error('newsletter-welcome requires email');
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const unsubscribeUrl = `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;font:italic 400 22px/1.3 ${BRAND.fonts.display};color:${BRAND.colors.text};">
        For women on GLP-1, the side effects nobody talks about.
      </p>
      <p style="margin:0 0 18px;">APLOMB. is a small line of four products for the things GLP-1 medications quietly do to your face, hair, gut, and breath. Nothing is bundled with a pill — these address the actual mechanisms.</p>
      <ul style="padding-left:20px;margin:0 0 24px;color:${BRAND.colors.text};font:400 15px/1.7 ${BRAND.fonts.body};">
        <li><strong style="color:${BRAND.colors.accent};">The Serum.</strong> Peptide + plant-active facial serum, for lost facial volume.</li>
        <li><strong style="color:${BRAND.colors.accent};">Roots.</strong> Iron, D3, zinc, saw palmetto — for telogen-effluvium hair shedding.</li>
        <li><strong style="color:${BRAND.colors.accent};">Calm.</strong> Ginger capsules + electrolyte sticks — for the early-titration nausea.</li>
        <li><strong style="color:${BRAND.colors.accent};">Breath.</strong> Zinc acetate + xylitol lozenges — for keto-style halitosis.</li>
      </ul>
      <p style="margin:18px 0;">Take 10% off your first order with code <strong style="color:${BRAND.colors.accent};">${escapeHtml(discountCode)}</strong> at checkout.</p>
      <p style="margin:24px 0;">
        <a href="${siteUrl}/" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Shop the line</a>
      </p>
      <p style="margin:32px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        Over the next week, we'll share two more emails: a deep-dive on the ingredient science and a reminder before your discount expires. After that, you'll hear from us about once a month.
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `Welcome to APLOMB.

For women on GLP-1, the side effects nobody talks about.

APLOMB. is a small line of four products for the things GLP-1 medications quietly do to your face, hair, gut, and breath.

— The Serum. Peptide + plant-active facial serum.
— Roots. Iron, D3, zinc, saw palmetto.
— Calm. Ginger capsules + electrolyte sticks.
— Breath. Zinc acetate + xylitol lozenges.

Take 10% off your first order with code ${discountCode} at checkout.

Shop: ${siteUrl}/
`;

  return { subject: SUBJECT, html, text };
}
