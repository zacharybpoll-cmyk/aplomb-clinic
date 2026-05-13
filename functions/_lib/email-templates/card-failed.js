// Sent when a subscription invoice's first charge attempt fails.
// Stripe Smart Retries handles the next 3 attempts automatically; this email
// just nudges the customer to update their card before retries exhaust.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';
import { signUnsubscribeToken } from '../auth.js';

export const SUBJECT = 'Your card on file needs an update';

export async function render(env, data) {
  const { customer = {}, nextAttempt = 'in 3 days' } = data;
  const email = String(customer.email || '').toLowerCase();
  const siteUrl = env.SITE_URL || 'https://getaplomb.com';
  const unsubscribeUrl = email
    ? `${siteUrl}/api/newsletter/unsubscribe?token=${await signUnsubscribeToken(email, env)}`
    : null;

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 18px;">Your card on file was declined.</p>
      <p style="margin:0 0 18px;color:${BRAND.colors.secondary};">
        We'll automatically try again ${escapeHtml(nextAttempt)}. To avoid an interruption to your subscription, you can update your card now in 1 click.
      </p>
      <p style="margin:24px 0;">
        <a href="${siteUrl}/account/subscriptions/" style="display:inline-block;padding:14px 26px;background:${BRAND.colors.accent};color:#fff;font:600 14px/1 ${BRAND.fonts.body};text-decoration:none;letter-spacing:0.04em;text-transform:uppercase;">Update payment</a>
      </p>
      <p style="margin:24px 0 0;font:400 13px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        Banks reject cards for many reasons — expired, daily limit, address mismatch. Updating the card and trying again usually solves it. If you have any trouble, reply to this email and we'll help.
      </p>
    </td></tr>
  `, env, { unsubscribeUrl });

  const text = `Your card on file was declined.

We'll automatically try again ${nextAttempt}. To avoid an interruption to your subscription, update your card now:
${siteUrl}/account/subscriptions/

If you have any trouble, reply to this email and we'll help.
`;

  return { subject: SUBJECT, html, text };
}
