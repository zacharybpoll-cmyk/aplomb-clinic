// APLOMB. — Stripe-powered checkout
//
// Loaded by index.html and every product detail page that includes a checkout
// modal. Coordinates with the inline cart code via window.AplombCheckout
// (defined in index.html) and exposes a single externally-visible side effect:
// when the customer presses "Continue to secure payment" on the checkout form,
// we POST to /api/checkout and mount the Stripe Payment Element with the
// returned client_secret. On confirmPayment success Stripe redirects to
// /checkout/success/, where a separate page reads payment_intent and renders
// the order summary.
//
// The publishable key is injected by the host at build time as
// window.STRIPE_PUBLISHABLE_KEY (a meta tag set by Cloudflare Pages, or a
// hardcoded test key during local development). If it is missing we surface
// a clear error rather than rendering a checkout that silently does nothing.

(function () {
  'use strict';

  const RETURN_URL = window.location.origin + '/checkout/success/';
  const API_CHECKOUT = '/api/checkout';

  let stripe = null;
  let elements = null;
  let mounted = false;
  let pendingClientSecret = null;

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

  // Returns the cart payload for /api/checkout.
  function buildCartPayload(form) {
    const data = new FormData(form);
    const checkoutApi = window.AplombCheckout;
    const lineItems = (checkoutApi && checkoutApi.getCartLineItems) ? checkoutApi.getCartLineItems() : [];
    return {
      email: (data.get('email') || '').trim(),
      name: (data.get('name') || '').trim(),
      lineItems: lineItems.map(li => ({
        productKey: li.productKey,
        quantity: li.quantity,
      })),
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

    const { clientSecret } = await resp.json();
    if (!clientSecret) {
      setSubmitState(false);
      showError('Checkout did not return a payment intent. Please try again.');
      return;
    }

    pendingClientSecret = clientSecret;

    // First click: mount Stripe elements with the client_secret. The form's
    // submit handler swaps to "confirmPayment" mode on subsequent presses.
    if (!mounted) {
      mountElements(clientSecret);
      setSubmitState(false);
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
    if (addressContainer) {
      const address = elements.create('address', {
        mode: 'shipping',
        allowedCountries: ['US'],
        fields: { phone: 'always' },
        validation: { phone: { required: 'always' } },
      });
      address.mount(addressContainer);
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
