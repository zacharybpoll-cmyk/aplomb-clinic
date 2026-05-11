// Day-3 newsletter follow-up: ingredient science.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken } from '../auth.js';

export const SUBJECT = 'How APLOMB. actually works — the ingredient science';

export async function render(env, data) {
  const { email } = data;
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const unsubscribeUrl = email
    ? `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`
    : null;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;font:italic 400 22px/1.3 ${BRAND.fonts.display};color:${BRAND.colors.text};">
        The mechanisms, not the marketing.
      </p>
      <p style="margin:0 0 18px;">Most "GLP-1 support" products bundle a vague multivitamin with a wellness-influencer claim. We took the long route: pick the ingredient with peer-reviewed evidence for each specific side effect, then formulate it at the dose used in those studies.</p>
      <p style="margin:0 0 18px;">A few examples:</p>
      <ul style="padding-left:20px;margin:0 0 24px;color:${BRAND.colors.text};font:400 15px/1.7 ${BRAND.fonts.body};">
        <li><strong>Hair-shed:</strong> Iron is the #1 modifiable predictor of telogen effluvium recovery. Roots delivers <span style="color:${BRAND.colors.accent};">25mg ferrous bisglycinate</span> — the dose used in the 2017 hair-recovery trial.</li>
        <li><strong>Nausea:</strong> Ginger root at <span style="color:${BRAND.colors.accent};">1000mg</span> outperformed ondansetron in chemo-induced nausea trials. Calm capsules hit that dose; electrolyte sticks replace what you lose if you're undereating during titration.</li>
        <li><strong>Halitosis:</strong> Zinc acetate, not the chlorhexidine rinses, is the active ingredient with clinical data for ketosis breath. Plus xylitol to nudge the oral microbiome.</li>
      </ul>
      <p style="margin:24px 0;">
        <a href="${siteUrl}/biology/" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Read the biology</a>
        &nbsp;
        <a href="${siteUrl}/evidence/" style="display:inline-block;padding:14px 26px;background:transparent;color:${BRAND.colors.accent};font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;border:1px solid ${BRAND.colors.accent};">See the citations</a>
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `The mechanisms, not the marketing.

Most "GLP-1 support" products bundle a vague multivitamin with a wellness claim. We picked the ingredient with peer-reviewed evidence for each side effect, then formulated it at the trial dose.

Examples:
— Hair-shed: 25mg ferrous bisglycinate (Roots).
— Nausea: 1000mg ginger root + electrolytes (Calm).
— Halitosis: zinc acetate + xylitol (Breath).

Biology: ${siteUrl}/biology/
Citations: ${siteUrl}/evidence/
`;

  return { subject: SUBJECT, html, text };
}
