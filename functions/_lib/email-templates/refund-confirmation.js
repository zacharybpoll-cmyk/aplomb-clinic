// Refund confirmation email template.
// Sent when an order is refunded.

import { BRAND, layoutEmail, dollars, shortId, escapeHtml } from './_layout.js';

export const SUBJECT = 'Refund Processed';

export function render(env, data) {
  const { order } = data;
  if (!order) throw new Error('refund-confirmation requires order object');

  const orderId = shortId(order.id);
  const refundAmount = order.total_cents || 0;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 24px;">We've processed your refund.</p>
      <p style="margin:0 0 24px;">Order #${escapeHtml(orderId)} has been refunded for ${dollars(refundAmount)}.</p>
      <p style="margin:0 0 24px;">The funds should appear in your original payment method within 3-5 business days, depending on your financial institution.</p>
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        If you have any questions about your refund, feel free to reply to this email.
      </p>
    </td></tr>
  `, env, { footerText: '— Aplomb<span style="font-style:normal;">.</span>' });

  const text = `Refund Processed

We've processed your refund.

Order #${orderId} has been refunded for ${dollars(refundAmount)}.

The funds should appear in your original payment method within 3-5 business days, depending on your financial institution.

If you have any questions about your refund, feel free to reply to this email.

Questions? Reply to this email — it reaches us directly.
`;

  return { subject: SUBJECT, html, text };
}
