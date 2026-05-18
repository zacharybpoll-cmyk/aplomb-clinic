// Server-side product catalog. The client never tells the server how much to
// charge — the client only tells the server which products and how many. Prices
// live here, keyed to Stripe Price IDs supplied via Cloudflare environment.
//
// Each SKU has two Stripe prices: a one-time and a recurring (subscribe & save).
// The discount percentage on each product is the "subscribe and save" copy on
// the marketing site. Source of truth for that copy is index.html PRODUCTS.

export const PRODUCTS = {
  serum: {
    name: 'APLOMB. The Serum.',
    unitPriceCents: 12900,
    subscribeDiscountPct: 10,
    description: '30 mL · 60-day supply · peptide + plant-active facial serum',
    requiresShipping: true,
  },
  daily: {
    name: 'APLOMB. Daily.',
    unitPriceCents: 4900,
    subscribeDiscountPct: 15,
    description: '30-day nutrient daily — methyl-B12, D3+K2, iron, zinc, magnesium',
    requiresShipping: true,
  },
  roots: {
    name: 'APLOMB. Roots.',
    unitPriceCents: 3900,
    subscribeDiscountPct: 15,
    description: '30-day hair-shed daily — iron, D3, zinc, saw palmetto',
    requiresShipping: true,
  },
  calm: {
    name: 'APLOMB. Calm.',
    unitPriceCents: 3500,
    subscribeDiscountPct: 15,
    description: '30-day titration kit — ginger capsules + electrolyte sticks',
    requiresShipping: true,
  },
  breath: {
    name: 'APLOMB. Breath.',
    unitPriceCents: 3500,
    subscribeDiscountPct: 15,
    description: '30-day lozenge tin — zinc acetate, xylitol, green-tea polyphenols',
    requiresShipping: true,
  },
};

export function getProduct(key) {
  return PRODUCTS[key] || null;
}

// Returns Stripe Price IDs for a given product key, looking up env vars by
// convention (e.g. STRIPE_PRICE_SERUM_ONETIME, STRIPE_PRICE_SERUM_SUBSCRIPTION).
export function getStripePriceIds(env, key) {
  const upper = key.toUpperCase();
  return {
    oneTime: env[`STRIPE_PRICE_${upper}_ONETIME`] || null,
    subscription: env[`STRIPE_PRICE_${upper}_SUBSCRIPTION`] || null,
  };
}

// Computes the cart subtotal in cents from validated line items. Caller is
// responsible for confirming each productKey is real (use getProduct first).
export function computeSubtotalCents(lineItems) {
  let total = 0;
  for (const li of lineItems) {
    const p = PRODUCTS[li.productKey];
    if (!p) continue;
    const qty = Math.max(1, Math.min(99, li.quantity | 0));
    total += p.unitPriceCents * qty;
  }
  return total;
}

// Defaults mirror assets/cart.js so the cart drawer and the server agree.
// Override via CF Pages env (SHIPPING_FLAT_CENTS, FREE_SHIPPING_THRESHOLD_CENTS).
export const SHIPPING_FLAT_CENTS_DEFAULT = 799;
export const FREE_SHIPPING_THRESHOLD_CENTS_DEFAULT = 7500;

export function computeShippingCents(lineItems, env) {
  const subtotal = computeSubtotalCents(lineItems);
  if (subtotal === 0) return 0;
  const flat = parseInt(env?.SHIPPING_FLAT_CENTS, 10) || SHIPPING_FLAT_CENTS_DEFAULT;
  const threshold = parseInt(env?.FREE_SHIPPING_THRESHOLD_CENTS, 10) || FREE_SHIPPING_THRESHOLD_CENTS_DEFAULT;
  if (subtotal >= threshold) return 0;
  return flat;
}
