// Shipping notification email template.
// Sent when an order ships, includes tracking information.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';

export const SUBJECT = 'Your Order Has Shipped';

export function render(env, data) {
  const { order, trackingUrl, trackingNumber, carrier } = data;
  if (!order) throw new Error('shipping-notification requires order object');

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 24px;">Great news! Your order has shipped.</p>
      ${trackingNumber ? `
      <p style="margin:0 0 24px;">
        Tracking Number: <span style="font:600;color:${BRAND.colors.accent};">${escapeHtml(trackingNumber)}</span>
        ${carrier ? `via ${escapeHtml(carrier)}` : ''}
      </p>
      ` : ''}
      ${trackingUrl ? `
      <p style="margin:0 0 24px;">
        <a href="${escapeHtml(trackingUrl)}" style="color:${BRAND.colors.accent};text-decoration:none;font:600;">View Tracking</a>
      </p>
      ` : ''}
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        You'll receive the package within the timeframe provided by ${carrier ? escapeHtml(carrier) : 'your carrier'}. If you have any questions, feel free to reply to this email.
      </p>
    </td></tr>
  `, env, { footerText: '— Aplomb<span style="font-style:normal;">.</span>' });

  const text = `Your Order Has Shipped

Great news! Your order has shipped.

${trackingNumber ? `Tracking Number: ${trackingNumber}${carrier ? ` via ${carrier}` : ''}\n` : ''}
${trackingUrl ? `View Tracking: ${trackingUrl}\n` : ''}
You'll receive the package within the timeframe provided by ${carrier || 'your carrier'}. If you have any questions, feel free to reply to this email.

Questions? Reply to this email — it reaches us directly.
`;

  return { subject: SUBJECT, html, text };
}
