// Quick smoke test: import each template and call render with stub data.
const env = {
  SITE_URL: 'https://getaplomb.com',
  EMAIL_BUSINESS_NAME: 'APLOMB.',
  EMAIL_BUSINESS_ADDRESS: '123 Test St, Brooklyn, NY 11201',
  EMAIL_UNSUB_SECRET: 'deadbeefcafedeadbeefcafedeadbeef',
  EMAIL_FROM: 'APLOMB. <orders@getaplomb.com>',
  RESEND_API_KEY: 'stub',
};
const STUB_ORDER = {
  id: 'abc-def-1234-5678',
  email: 'test@example.com',
  customer_name: 'Test Buyer',
  line_items: [{ name: 'APLOMB. The Serum.', quantity: 1, unitPriceCents: 12900 }],
  subtotal_cents: 12900,
  shipping_cents: 799,
  tax_cents: 0,
  total_cents: 13699,
  tracking_number: '9400000000000000000000',
  carrier: 'usps',
  shipping_address: { line1: '1 Test', city: 'Brooklyn', state: 'NY', postal_code: '11201' },
};
const STUB_SUB = { id: 'sub-1234', email: 'test@example.com', current_period_end: new Date(Date.now() + 5*86400000).toISOString() };
const cases = [
  ['order-confirmation', { order: STUB_ORDER }],
  ['shipping-notification', { order: STUB_ORDER }],
  ['refund-confirmation', { order: STUB_ORDER, refundCents: 13699 }],
  ['renewal-heads-up', { subscription: STUB_SUB, customer: { email: 'test@example.com' }, items: [{ name: 'Serum', quantity: 1, unitPriceCents: 12900 }], totalCents: 12900, daysUntilRenewal: 5 }],
  ['renewal-receipt', { order: STUB_ORDER }],
  ['card-failed', { customer: { email: 'test@example.com' }, subscription: STUB_SUB, nextAttempt: 'in 3 days' }],
  ['cancellation-confirmation', { subscription: STUB_SUB, customer: { email: 'test@example.com' }, lastShipmentDate: STUB_SUB.current_period_end }],
  ['magic-link', { signInUrl: 'https://example.com/magic?token=xxx', email: 'test@example.com', expiresIn: '15 minutes' }],
  ['newsletter-welcome', { email: 'test@example.com', discountCode: 'APLOMB10' }],
  ['welcome-day-3', { email: 'test@example.com' }],
  ['welcome-day-7', { email: 'test@example.com', discountCode: 'APLOMB10' }],
  ['review-request', { order: STUB_ORDER }],
];

let ok = 0, fail = 0;
for (const [name, data] of cases) {
  try {
    const mod = await import(`../../functions/_lib/email-templates/${name}.js`);
    const r = await mod.render(env, data);
    if (!r.subject || !r.html || !r.text) throw new Error('missing fields');
    console.log(`✓ ${name.padEnd(28)} subject="${r.subject}" html=${r.html.length}b text=${r.text.length}b`);
    ok++;
  } catch (e) {
    console.log(`✘ ${name.padEnd(28)} ERROR: ${e.message}`);
    fail++;
  }
}
console.log(`\n${ok} OK, ${fail} FAIL`);
process.exit(fail ? 1 : 0);
