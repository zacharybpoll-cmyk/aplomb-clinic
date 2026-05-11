// APLOMB. — Stripe-powered checkout
//
// Owns submission of the standalone /checkout/ form (also works in any legacy
// modal that has the same [data-checkout-form] hooks). Coordinates with
// window.AplombCart (assets/cart.js) for the line-item payload.
//
// Flow:
//  1. User fills email + name + Stripe Address Element (mounted on load).
//  2. First "Continue to secure payment" click POSTs to /api/checkout.
//     - Onetime cart → response is { clientSecret, orderId }; mount Stripe
//       Payment Element with that secret; second click confirms payment.
//     - Subscription cart → response is { checkoutUrl, orderId }; redirect
//       the browser to Stripe Checkout (hosted page with full SCA/3DS).
//  3. confirmPayment redirects on success to /checkout/success/.
//
// Publishable key comes from window.STRIPE_PUBLISHABLE_KEY (set on the page)
// or <meta name="stripe-publishable-key">. Missing key surfaces a clear error.

(function () {
  'use strict';

  const RETURN_URL = window.location.origin + '/checkout/success/';
  const API_CHECKOUT = '/api/checkout';

  let stripe = null;
  let elements = null;
  let mounted = false;
  let addressMounted = false;

  function $(sel, root) { return (root || document).querySelector(sel); }

  function showError(msg) {
    const el = $('[data-checkout-error]');
    if (!el) return;
    el.hidden = false;
    el.textContent = msg;
  }
  function clearError() {
    const el = $('[data-checkout-error]');
    if (!el) return;
    el.hidden = true;
    el.textContent = '';
  }

  function setSubmitState(isWorking) {
    const btn = $('[data-checkout-submit]');
    if (!btn) return;
    btn.disabled = !!isWorking;
    const label = $('[data-submit-label]', btn);
    const spinner = $('[data-submit-spinner]', btn);
    if (label) label.hidden = !!isWorking;
    if (spinner) spinner.hidden = !isWorking;
  }

  function getPublishableKey() {
    if (window.STRIPE_PUBLISHABLE_KEY) return window.STRIPE_PUBLISHABLE_KEY;
    const meta = document.querySelector('meta[name="stripe-publishable-key"]');
    if (meta && meta.content) return meta.content;
    return null;
  }

  function ensureStripe() {
    if (stripe) return stripe;
    if (typeof window.Stripe !== 'function') return null;
    const pk = getPublishableKey();
    if (!pk) return null;
    stripe = window.Stripe(pk);
    return stripe;
  }

  function getTurnstileToken() {
    if (typeof window.turnstile !== 'object' || !window.turnstile) return null;
    const widget = document.querySelector('.cf-turnstile');
    if (!widget) return null;
    try {
      const id = widget.getAttribute('data-widget-id');
      return id ? window.turnstile.getResponse(id) : window.turnstile.getResponse();
    } catch (_) { return null; }
  }

  // Returns the cart payload for /api/checkout. Prefers AplombCart (the global
  // cart module on every page); falls back to legacy AplombCheckout.
  function buildCartPayload(form) {
    const data = new FormData(form);
    const lineItems = (window.AplombCart && window.AplombCart.getLineItems)
      ? window.AplombCart.getLineItems()
      : (window.AplombCheckout && window.AplombCheckout.getCartLineItems
          ? window.AplombCheckout.getCartLineItems()
          : []);
    return {
      email: (data.get('email') || '').trim(),
      name: (data.get('name') || '').trim(),
      lineItems: lineItems.map(li => ({
        productKey: li.productKey,
        quantity: li.quantity,
        mode: li.mode || 'onetime',
      })),
      turnstileToken: getTurnstileToken(),
    };
  }

  async function startCheckout(form) {
    clearError();

    const s = ensureStripe();
    if (!s) {
      showError('Payments are not configured for this preview. Please email zachary@getaplomb.com to place an order.');
      return;
    }

    const payload = buildCartPayload(form);
    if (!payload.email || !payload.name) {
      showError('Please enter your email and full name.');
      return;
    }
    if (!payload.lineItems.length) {
      showError('Your bag is empty.');
      return;
    }

    setSubmitState(true);

    let resp;
    try {
      resp = await fetch(API_CHECKOUT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      setSubmitState(false);
      showError('Network error. Please try again.');
      return;
    }

    if (!resp.ok) {
      setSubmitState(false);
      let msg = 'Could not start checkout. Please try again.';
      try {
        const err = await resp.json();
        if (err && err.error) msg = err.error;
      } catch (_) {}
      showError(msg);
      return;
    }

    const body = await resp.json();

    // Subscription cart — backend returns Stripe Checkout Session URL; redirect.
    if (body.checkoutUrl) {
      window.location.href = body.checkoutUrl;
      return;
    }

    if (!body.clientSecret) {
      setSubmitState(false);
      showError('Checkout did not return a payment intent. Please try again.');
      return;
    }

    // First click: mount Stripe Payment Element with the client_secret. The
    // form's submit handler swaps to "confirmPayment" mode on subsequent presses.
    if (!mounted) {
      mountElements(body.clientSecret);
      setSubmitState(false);
      const fieldset = document.querySelector('[data-payment-fieldset]');
      if (fieldset) fieldset.hidden = false;
      const label = $('[data-submit-label]');
      if (label) label.textContent = 'Place order';
      return;
    }

    await confirmPayment();
  }

  function mountElements(clientSecret) {
    elements = stripe.elements({
      clientSecret,
      appearance: {
        theme: 'stripe',
        variables: {
          colorPrimary: '#7a3d14',           // amber — brand period
          colorBackground: '#f7f1e6',        // warm bone
          colorText: '#1a1512',              // ink
          colorDanger: '#b8341e',
          fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
          fontSizeBase: '16px',
          spacingUnit: '4px',
          borderRadius: '4px',
        },
      },
    });

    const addressContainer = $('[data-stripe-address-element]');
    const paymentContainer = $('[data-stripe-payment-element]');
    if (addressContainer && !addressMounted) {
      const address = elements.create('address', {
        mode: 'shipping',
        allowedCountries: ['US'],
        fields: { phone: 'always' },
        validation: { phone: { required: 'always' } },
      });
      address.mount(addressContainer);
      addressMounted = true;
    }
    if (paymentContainer) {
      const payment = elements.create('payment', { layout: 'tabs' });
      payment.mount(paymentContainer);
    }
    mounted = true;
  }

  async function confirmPayment() {
    setSubmitState(true);
    clearError();
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: RETURN_URL },
    });
    // confirmPayment only returns here on validation/network error;
    // success path redirects to RETURN_URL.
    setSubmitState(false);
    if (error) {
      showError(error.message || 'Payment was not completed. Please try again.');
    }
  }

  document.addEventListener('submit', function (e) {
    const form = e.target.closest('[data-checkout-form]');
    if (!form) return;
    e.preventDefault();
    if (mounted) {
      confirmPayment();
    } else {
      startCheckout(form);
    }
  });
})();
