// T+10-day post-shipment review request. Sent by /cron/review-requests once
// per order; idempotency via orders.review_request_sent_at.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken, signReviewToken } from '../auth.js';

export const SUBJECT = 'How is APLOMB. working for you?';

export async function render(env, data) {
  const { order } = data;
  const email = order?.email || data.email || '';
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';

  const unsubscribeUrl = email
    ? `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`
    : null;

  // Pull the first line-item as the focal product for the review prompt.
  const firstItem = Array.isArray(order?.line_items) && order.line_items[0] ? order.line_items[0] : null;
  const productName = firstItem?.name || 'your APLOMB. order';
  const productKey = (firstItem?.productKey || firstItem?.k || '').toString();
  // Review form lives on the PDP, unlocked by a signed per-order token (?rt=)
  // so the buyer can submit without re-entering anything and we can trust it.
  const reviewToken = order?.id && email
    ? await signReviewToken({ orderId: order.id, email }, env)
    : null;
  const reviewUrl = productKey && reviewToken && ['serum','roots','calm','breath'].includes(productKey)
    ? `${siteUrl}/${productKey}/?rt=${encodeURIComponent(reviewToken)}#reviews`
    : `${siteUrl}/faq/`;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;font:italic 400 22px/1.3 ${BRAND.fonts.display};color:${BRAND.colors.text};">
        Ten days in. How is it going?
      </p>
      <p style="margin:0 0 18px;">${escapeHtml(productName)} should be settled into your routine by now. We are still a small team, and your honest feedback &mdash; what is working, what is not &mdash; shapes everything we build next.</p>
      <p style="margin:0 0 24px;">If you have a minute, leave a short review. Even one line helps the next person on a GLP-1 decide whether APLOMB. is for them.</p>
      <p style="margin:24px 0;">
        <a href="${reviewUrl}" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Leave a review</a>
      </p>
      <p style="margin:24px 0 0;font-size:14px;color:${BRAND.colors.secondary};">
        Something not working? Reply to this email &mdash; it reaches us directly, and we want to know.
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `Ten days in. How is it going?

${productName} should be settled into your routine by now. Your honest feedback shapes everything we build next.

If you have a minute, leave a short review: ${reviewUrl}

Something not working? Reply to this email — we want to know.

— Aplomb.
`;

  return { subject: SUBJECT, html, text };
}
