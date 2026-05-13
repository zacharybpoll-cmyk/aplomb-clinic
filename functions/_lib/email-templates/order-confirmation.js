// Order confirmation email template.
// Sent when payment succeeds on a one-time order.

import { BRAND, layoutEmail, dollars, shortId, renderLineItemsHtml, escapeHtml } from './_layout.js';

export const SUBJECT = 'Order Confirmed';

export function render(env, data) {
  const { order } = data;
  if (!order) throw new Error('order-confirmation requires order object');

  const orderId = shortId(order.id);
  const totalCents = order.total_cents || 0;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 24px;">Thank you for your order!</p>
      <p style="margin:0 0 24px;">Your order #${escapeHtml(orderId)} has been confirmed and will ship within 1-2 business days.</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <thead>
          <tr style="border-bottom:2px solid ${BRAND.colors.accent};">
            <th style="padding:12px 0;text-align:left;font:600 14px/1 ${BRAND.fonts.body};color:${BRAND.colors.accent};">Item</th>
            <th style="padding:12px 0;text-align:right;font:600 14px/1 ${BRAND.fonts.body};color:${BRAND.colors.accent};">Price</th>
          </tr>
        </thead>
        <tbody>
          ${renderLineItemsHtml(order.line_items || [])}
        </tbody>
      </table>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr style="border-top:1px solid ${BRAND.colors.border};">
          <td style="padding:12px 0;font:600 15px/1 ${BRAND.fonts.body};color:${BRAND.colors.text};">Total</td>
          <td style="padding:12px 0;font:600 15px/1 ${BRAND.fonts.body};color:${BRAND.colors.text};text-align:right;">${dollars(totalCents)}</td>
        </tr>
      </table>
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        You'll receive a shipping notification with tracking info as soon as your order ships.
      </p>
    </td></tr>
  `, env, { footerText: '— Aplomb<span style="font-style:normal;">.</span>' });

  const text = `Order Confirmed

Thank you for your order!

Your order #${orderId} has been confirmed and will ship within 1-2 business days.

Items:
${(order.line_items || []).map(li => `${li.name} (Qty ${li.quantity}) — ${dollars(li.unitPriceCents * li.quantity)}`).join('\n')}

Total: ${dollars(totalCents)}

You'll receive a shipping notification with tracking info as soon as your order ships.

Questions? Reply to this email — it reaches us directly.
`;

  return { subject: SUBJECT, html, text };
}
