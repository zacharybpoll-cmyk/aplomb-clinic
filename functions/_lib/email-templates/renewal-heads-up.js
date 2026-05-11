// Renewal heads-up email template.
// Sent 7 days before subscription renewal.

import { BRAND, layoutEmail, escapeHtml } from './_layout.js';

export const SUBJECT = 'Your Subscription Renews Soon';

export function render(env, data) {
  const { subscription, renewalDate } = data;
  if (!subscription) throw new Error('renewal-heads-up requires subscription object');

  const html = layoutEmail(`
    <tr><td style="padding:24px 40px;font:400 16px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.text};">
      <p style="margin:0 0 24px;">Just a heads up — your subscription renews in 7 days.</p>
      <p style="margin:0 0 24px;">
        Your subscription will renew on <span style="font:600;">${escapeHtml(renewalDate || 'the scheduled date')}</span>.
      </p>
      <p style="margin:0 0 24px;">If you'd like to make any changes to your subscription before renewal, you can manage it anytime from your account.</p>
      <p style="margin:24px 0 0;font:400 14px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
        Questions? Reply to this email or visit your account settings.
      </p>
    </td></tr>
  `, env, { footerText: '— Aplomb<span style="font-style:normal;">.</span>' });

  const text = `Your Subscription Renews Soon

Just a heads up — your subscription renews in 7 days.

Your subscription will renew on ${renewalDate || 'the scheduled date'}.

If you'd like to make any changes to your subscription before renewal, you can manage it anytime from your account.

Questions? Reply to this email or visit your account settings.

Questions? Reply to this email — it reaches us directly.
`;

  return { subject: SUBJECT, html, text };
}
