// Transactional email via Resend. Brand-locked: Cormorant Garamond + IBM Plex
// Sans, warm-bone background, deep amber period accents.
//
// Required env: RESEND_API_KEY, EMAIL_FROM (e.g. "Aplomb. <orders@getaplomb.com>")

const RESEND_ENDPOINT = 'https://api.resend.com/emails';

export async function sendOrderConfirmation(env, order) {
  if (!env.RESEND_API_KEY || !env.EMAIL_FROM) return;

  const html = renderOrderConfirmationHtml(order);
  const text = renderOrderConfirmationText(order);

  const res = await fetch(RESEND_ENDPOINT, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: env.EMAIL_FROM,
      to: [order.email],
      subject: `Your APLOMB. order — #${shortId(order.id)}`,
      html,
      text,
      reply_to: 'zachary@getaplomb.com',
    }),
  });
  if (!res.ok) {
    throw new Error(`Resend ${res.status}: ${await res.text()}`);
  }
}

function shortId(id) {
  if (!id) return '—';
  return String(id).split('-')[0]?.toUpperCase() || String(id);
}

function dollars(cents) {
  return '$' + (Math.round(cents) / 100).toFixed(2);
}

function renderOrderConfirmationText(order) {
  const lines = (order.line_items || []).map(li =>
    `  ${li.name} × ${li.quantity}  ${dollars(li.unitPriceCents * li.quantity)}`
  ).join('\n');
  return [
    `Thank you, ${order.customer_name}.`,
    ``,
    `Your APLOMB. order #${shortId(order.id)} is confirmed.`,
    ``,
    `Items`,
    lines,
    ``,
    `Subtotal  ${dollars(order.subtotal_cents)}`,
    ``,
    `It ships within 48 hours. You will receive a tracking number when it leaves us.`,
    ``,
    `Questions? Reply to this email.`,
    ``,
    `— Aplomb.`,
    `getaplomb.com`,
  ].join('\n');
}

function renderOrderConfirmationHtml(order) {
  const itemsHtml = (order.line_items || []).map(li => `
    <tr>
      <td style="padding:14px 0;border-bottom:1px solid #e8dccc;font:400 15px/1.4 'IBM Plex Sans',sans-serif;color:#1a1512;">
        ${escapeHtml(li.name)}
        <br><span style="color:#8a7d6e;font-size:13px;">Quantity ${li.quantity}</span>
      </td>
      <td style="padding:14px 0;border-bottom:1px solid #e8dccc;font:400 15px/1.4 'IBM Plex Sans',sans-serif;color:#1a1512;text-align:right;white-space:nowrap;">
        ${dollars(li.unitPriceCents * li.quantity)}
      </td>
    </tr>`).join('');

  return `<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Your Aplomb. order</title>
</head>
<body style="margin:0;padding:0;background:#efe8dc;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#efe8dc;">
  <tr><td align="center" style="padding:40px 16px;">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#f7f1e6;">
      <tr><td style="padding:32px 40px 16px;text-align:left;">
        <span style="font:italic 500 26px/1 'Cormorant Garamond',Garamond,serif;letter-spacing:-0.02em;color:#1a1512;">
          Aplomb<span style="color:#7a3d14;font-style:normal;">.</span>
        </span>
      </td></tr>
      <tr><td style="padding:8px 40px 4px;">
        <h1 style="margin:0;font:400 32px/1.2 'Cormorant Garamond',Garamond,serif;color:#1a1512;">
          Thank you, ${escapeHtml(order.customer_name)}<span style="color:#7a3d14;">.</span>
        </h1>
      </td></tr>
      <tr><td style="padding:8px 40px 24px;">
        <p style="margin:0;font:400 15px/1.6 'IBM Plex Sans',sans-serif;color:#1a1512;">
          Your order <strong>#${shortId(order.id)}</strong> is confirmed. It ships within 48 hours;
          you will receive tracking when it leaves us.
        </p>
      </td></tr>
      <tr><td style="padding:0 40px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #1a1512;">
          ${itemsHtml}
          <tr>
            <td style="padding:18px 0 0;font:500 12px/1 'IBM Plex Sans',sans-serif;text-transform:uppercase;letter-spacing:0.16em;color:#8a7d6e;">
              Subtotal
            </td>
            <td style="padding:18px 0 0;font:500 16px/1 'IBM Plex Sans',sans-serif;color:#1a1512;text-align:right;">
              ${dollars(order.subtotal_cents)}
            </td>
          </tr>
        </table>
      </td></tr>
      <tr><td style="padding:36px 40px 32px;border-top:1px solid #e8dccc;margin-top:24px;">
        <p style="margin:24px 0 0;font:400 13px/1.6 'IBM Plex Sans',sans-serif;color:#8a7d6e;">
          Questions? Reply to this email — it reaches the founder directly.
        </p>
        <p style="margin:18px 0 0;font:italic 400 14px/1 'Cormorant Garamond',serif;color:#7a3d14;">
          — Aplomb<span style="font-style:normal;">.</span>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`;
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
