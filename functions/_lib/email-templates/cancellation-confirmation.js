// Sent when a subscription is cancelled (via Customer Portal or admin).
// Confirms the cancellation, names the last shipment date, leaves the door open.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken } from '../auth.js';

export const SUBJECT = 'Your APLOMB. subscription is cancelled';

export async function render(env, data) {
  const { subscription = {}, customer = {}, lastShipmentDate = null } = data;
  const email = String(customer.email || subscription.email || '').toLowerCase();
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const formattedDate = lastShipmentDate
    ? new Date(lastShipmentDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : null;
  const unsubscribeUrl = email
    ? `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`
    : null;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;">Your APLOMB. subscription is cancelled.</p>
      ${formattedDate ? `<p style="margin:0 0 18px;color:${BRAND.colors.secondary};">Your last shipment was on ${escapeHtml(formattedDate)}.</p>` : ''}
      <p style="margin:0 0 18px;">We're sorry to see you go. If you change your mind, your address and product preferences are saved — restarting is one click away.</p>
      <p style="margin:24px 0;">
        <a href="${siteUrl}/account/" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Visit your account</a>
      </p>
      <p style="margin:32px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        If you cancelled because something wasn't working, we'd love to hear about it. Reply to this email — every response goes straight to the founder.
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `Your APLOMB. subscription is cancelled.
${formattedDate ? `\nYour last shipment was on ${formattedDate}.\n` : ''}
We're sorry to see you go. If you change your mind, restarting is one click away: ${siteUrl}/account/

If you cancelled because something wasn't working, we'd love to hear about it. Reply to this email — every response goes straight to the founder.
`;

  return { subject: SUBJECT, html, text };
}
