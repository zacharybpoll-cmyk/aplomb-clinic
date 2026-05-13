// Shared HTML email layout and brand utilities.
// All transactional emails inherit this structure.

export const BRAND = {
  name: 'Aplomb',
  displayName: 'Aplomb.',
  email: 'zachary@getaplomb.com',
  url: 'getaplomb.com',
  colors: {
    canvas: '#efe8dc',
    contentBg: '#f7f1e6',
    text: '#1a1512',
    accent: '#7a3d14',
    border: '#e8dccc',
    secondary: '#8a7d6e',
  },
  fonts: {
    display: "'Cormorant Garamond',Garamond,serif",
    body: "'IBM Plex Sans',sans-serif",
  },
};

export function shortId(id) {
  if (!id) return '—';
  return String(id).split('-')[0]?.toUpperCase() || String(id);
}

export function dollars(cents) {
  return '$' + (Math.round(cents) / 100).toFixed(2);
}

export function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Wraps template HTML with standard layout (brand header, footer, background).
// templateContent is the middle section.
// env: optional { EMAIL_FROM, EMAIL_BUSINESS_NAME, EMAIL_BUSINESS_ADDRESS }
// opts: { footerText, unsubscribeUrl }
export function layoutEmail(templateContent, env = {}, opts = {}) {
  const { footerText, unsubscribeUrl } = opts;
  const businessName = env.EMAIL_BUSINESS_NAME || 'APLOMB.';
  const businessAddress = env.EMAIL_BUSINESS_ADDRESS || '[business address pending]';

  let footerHtml = `
        <p style="margin:24px 0 0;font:400 13px/1.6 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
          Questions? Reply to this email — it reaches us directly.
        </p>
        <p style="margin:18px 0 0;font:italic 400 14px/1 ${BRAND.fonts.display};color:${BRAND.colors.accent};">
          ${footerText || '— Aplomb<span style="font-style:normal;">.</span>'}
        </p>
        <p style="margin:12px 0 0;font:400 11px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};font-style:italic;">
          These statements have not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease.
        </p>
        <p style="margin:12px 0 0;font:400 11px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
          ${escapeHtml(businessName)} • ${escapeHtml(businessAddress)}
        </p>`;

  if (unsubscribeUrl) {
    footerHtml += `
        <p style="margin:12px 0 0;font:400 12px/1.5 ${BRAND.fonts.body};color:${BRAND.colors.secondary};">
          <a href="${escapeHtml(unsubscribeUrl)}" style="color:${BRAND.colors.accent};text-decoration:none;">Don't want these emails? Unsubscribe.</a>
        </p>`;
  }

  return `<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Aplomb.</title>
</head>
<body style="margin:0;padding:0;background:${BRAND.colors.canvas};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BRAND.colors.canvas};">
  <tr><td align="center" style="padding:40px 16px;">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:${BRAND.colors.contentBg};">
      <tr><td style="padding:32px 40px 16px;text-align:left;">
        <span style="font:italic 500 26px/1 ${BRAND.fonts.display};letter-spacing:-0.02em;color:${BRAND.colors.text};">
          Aplomb<span style="color:${BRAND.colors.accent};font-style:normal;">.</span>
        </span>
      </td></tr>
      ${templateContent}
      <tr><td style="padding:36px 40px 32px;border-top:1px solid ${BRAND.colors.border};margin-top:24px;">
        ${footerHtml}
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>`;
}

// Utility: render a 2-column item list (name + quantity, price right-aligned)
export function renderLineItemsHtml(lineItems) {
  if (!Array.isArray(lineItems)) return '';
  return lineItems.map(li => `
    <tr>
      <td style="padding:14px 0;border-bottom:1px solid ${BRAND.colors.border};font:400 15px/1.4 ${BRAND.fonts.body};color:${BRAND.colors.text};">
        ${escapeHtml(li.name)}
        <br><span style="color:${BRAND.colors.secondary};font-size:13px;">Quantity ${li.quantity}</span>
      </td>
      <td style="padding:14px 0;border-bottom:1px solid ${BRAND.colors.border};font:400 15px/1.4 ${BRAND.fonts.body};color:${BRAND.colors.text};text-align:right;white-space:nowrap;">
        ${dollars(li.unitPriceCents * li.quantity)}
      </td>
    </tr>`).join('');
}
