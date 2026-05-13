// Renewal receipt email. Sent after a subscription invoice.paid webhook
// (billing_reason='subscription_cycle'). Mirrors order-confirmation but framed
// as a renewal, with a link to manage/skip the next cycle.

import { BRAND, layoutEmail, dollars, shortId, renderLineItemsHtml, escapeHtml } from './_layout.js';

export const SUBJECT = 'Your APLOMB. subscription renewed';

export function render(env, data) {
  const { order } = data;
  if (!order) throw new Error('renewal-receipt requires order object');

  const orderId = shortId(order.id);
  const totalCents = order.total_cents || order.total_cents_override || 0;
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;">Your APLOMB. subscription renewed today.</p>
      <p style="margin:0 0 24px;color:${BRAND.colors.secondary};">Order #${escapeHtml(orderId)} — your next shipment is on the way.</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <thead><tr style="border-bottom:2px solid ${BRAND.colors.accent};">
          <th style="padding:12px 0;text-align:left;font:600 14px/1 ${BRAND.fonts.body};color:${BRAND.colors.accent};">Item</th>
          <th style="padding:12px 0;text-align:right;font:600 14px/1 ${BRAND.fonts.body};color:${BRAND.colors.accent};">Price</th>
        </tr></thead>
        <tbody>${renderLineItemsHtml(order.line_items || [])}</tbody>
      </table>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
        <tr style="border-top:1px solid ${BRAND.colors.border};">
          <td style="padding:12px 0;font:600 15px/1 ${BRAND.fonts.body};color:${BRAND.colors.text};">Charged today</td>
          <td style="padding:12px 0;font:600 15px/1 ${BRAND.fonts.body};color:${BRAND.colors.text};text-align:right;">${dollars(totalCents)}</td>
        </tr>
      </table>
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        Manage your subscription, skip a shipment, or update your card any time at <a href="${siteUrl}/account/subscriptions/" style="color:${BRAND.colors.accent};">your account</a>.
      </p>
    </td></tr>
  `, env);

  const text = `Your APLOMB. subscription renewed today.

Order #${orderId} — your next shipment is on the way.

Items:
${(order.line_items || []).map(li => `${li.name} (Qty ${li.quantity}) — ${dollars(li.unitPriceCents * li.quantity)}`).join('\n')}

Charged today: ${dollars(totalCents)}

Manage at ${siteUrl}/account/subscriptions/
`;

  return { subject: SUBJECT, html, text };
}
