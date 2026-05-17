// Transactional email dispatcher via Resend. Routes template names to
// individual modules with lazy-load pattern. Each template exports
// { SUBJECT, render(env, data) }.

const RESEND_ENDPOINT = 'https://api.resend.com/emails';

const templates = {
  'order-confirmation': () => import('./email-templates/order-confirmation.js'),
  'shipping-notification': () => import('./email-templates/shipping-notification.js'),
  'refund-confirmation': () => import('./email-templates/refund-confirmation.js'),
  'renewal-heads-up': () => import('./email-templates/renewal-heads-up.js'),
  'renewal-receipt': () => import('./email-templates/renewal-receipt.js'),
  'card-failed': () => import('./email-templates/card-failed.js'),
  'cancellation-confirmation': () => import('./email-templates/cancellation-confirmation.js'),
  'magic-link': () => import('./email-templates/magic-link.js'),
  'newsletter-welcome': () => import('./email-templates/newsletter-welcome.js'),
  'welcome-day-3': () => import('./email-templates/welcome-day-3.js'),
  'welcome-day-7': () => import('./email-templates/welcome-day-7.js'),
  'review-request': () => import('./email-templates/review-request.js'),
};

export async function sendEmail(env, templateName, data) {
  if (!env.RESEND_API_KEY) {
    console.warn('Resend API key not configured; email skipped');
    return { skipped: true };
  }
  if (!templates[templateName]) {
    throw new Error(`Unknown email template: ${templateName}`);
  }

  const template = await templates[templateName]();
  // Some templates are async (those that sign unsubscribe tokens). Always await.
  const { subject, html, text } = await template.render(env, data);

  // `data.email` is how newsletter/welcome-series callers name the recipient;
  // explicit `data.to` still wins, and customer/order remain the fallbacks for
  // transactional templates. Without this, a caller that passes only `email`
  // (e.g. the synchronous welcome in subscribe.js) throws "No recipient found".
  const to = data.to || data.email || data.customer?.email || data.order?.email;
  if (!to) {
    throw new Error(`No recipient found in data for template ${templateName}`);
  }

  const res = await fetch(RESEND_ENDPOINT, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: env.EMAIL_FROM || 'Aplomb. <orders@getaplomb.com>',
      to: [to],
      subject,
      html,
      text,
      reply_to: 'zachary@getaplomb.com',
    }),
  });

  if (!res.ok) {
    throw new Error(`Resend ${res.status}: ${await res.text()}`);
  }

  return { sent: true };
}

// Backward-compatibility shim: existing stripe.js call site continues to work.
export async function sendOrderConfirmation(env, order) {
  if (!env.RESEND_API_KEY || !env.EMAIL_FROM) return;
  try {
    await sendEmail(env, 'order-confirmation', { order });
  } catch (_) {
    // email failure must not fail webhook (stripe will retry forever)
  }
}
