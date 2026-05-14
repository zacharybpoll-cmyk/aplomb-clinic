// APLOMB. — Analytics + observability
//
// Loads Plausible (privacy-first, cookieless) if a site ID is present in
// <meta name="plausible-site-id" content="getaplomb.com">. No-op otherwise.
// Exposes window.AplombAnalytics.track(eventName, props) — works whether or
// not Plausible has loaded.
//
// Also wires window.onerror + unhandledrejection to forward to Sentry if a
// DSN is exposed via <meta name="sentry-dsn">. No-op without.

(function () {
  'use strict';

  // ---- Plausible loader ----
  function loadPlausible() {
    const meta = document.querySelector('meta[name="plausible-site-id"]');
    const siteId = meta && meta.content;
    if (!siteId) return;
    if (document.querySelector('script[data-plausible]')) return;
    const s = document.createElement('script');
    s.defer = true;
    s.setAttribute('data-plausible', '');
    s.setAttribute('data-domain', siteId);
    s.src = 'https://plausible.io/js/script.outbound-links.tagged-events.js';
    document.head.appendChild(s);
    // Pre-stub plausible() so callers can queue events before the script loads.
    window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };
  }

  // ---- Sentry browser SDK (very thin) ----
  function loadSentry() {
    const meta = document.querySelector('meta[name="sentry-dsn"]');
    const dsn = meta && meta.content;
    if (!dsn) return;
    // We don't pull the official SDK to keep weight down. Use the public
    // Sentry HTTP API directly. Errors land in the project the DSN points at.
    function parseDsn(dsn) {
      try {
        const u = new URL(dsn);
        return {
          host: u.host,
          projectId: u.pathname.replace(/^\//, ''),
          publicKey: u.username,
        };
      } catch (_) { return null; }
    }
    const parsed = parseDsn(dsn);
    if (!parsed) return;
    const endpoint = `https://${parsed.host}/api/${parsed.projectId}/store/?sentry_key=${parsed.publicKey}&sentry_version=7`;

    function report(eventLike) {
      try {
        const body = JSON.stringify(Object.assign({
          platform: 'javascript',
          timestamp: new Date().toISOString(),
          release: 'getaplomb-web@2026-05',
          environment: location.host,
          request: { url: location.href, headers: { 'User-Agent': navigator.userAgent } },
        }, eventLike));
        // Use sendBeacon if available, fall back to fetch
        if (navigator.sendBeacon) navigator.sendBeacon(endpoint, body);
        else fetch(endpoint, { method: 'POST', body, headers: { 'Content-Type': 'application/json' }, keepalive: true });
      } catch (_) {}
    }

    window.addEventListener('error', (e) => {
      report({
        exception: { values: [{ type: e.error?.name || 'Error', value: e.message || 'window.onerror' }] },
        culprit: e.filename + ':' + e.lineno,
      });
    });
    window.addEventListener('unhandledrejection', (e) => {
      const reason = e.reason;
      report({
        exception: { values: [{ type: 'UnhandledPromiseRejection', value: (reason && reason.message) || String(reason) }] },
      });
    });

    window.AplombSentry = { capture: report };
  }

  // ---- Event tracking API ----
  function track(eventName, props) {
    try {
      if (typeof window.plausible === 'function') {
        window.plausible(eventName, { props: props || {} });
      }
    } catch (_) {}
  }

  // ---- Commerce funnel auto-events ----
  function bindCommerceEvents() {
    // PDP-view: any page under /serum/, /roots/, /calm/, /breath/, /daily/
    const path = location.pathname;
    const match = path.match(/^\/(serum|roots|calm|breath|daily)\//);
    if (match) track('view_product', { product: match[1] });

    // Click on a buy-box ATC
    document.addEventListener('click', function (e) {
      const atc = e.target.closest('[data-aplomb-add]');
      if (atc) {
        const key = atc.dataset.aplombAdd;
        const group = atc.closest('[data-buy-box]');
        let mode = atc.dataset.mode || 'onetime';
        if (group) {
          const chosen = group.querySelector('input[name^="aplomb-mode"]:checked');
          if (chosen) mode = chosen.value;
        }
        track('add_to_cart', { product: key, mode });
      }
      const checkoutLink = e.target.closest('[data-checkout-link]');
      if (checkoutLink && checkoutLink.getAttribute('aria-disabled') !== 'true') {
        track('begin_checkout');
      }
      const newsletterPopup = e.target.closest('[data-newsletter-popup-form] [type="submit"]');
      if (newsletterPopup) track('newsletter_popup_submit');
    });

    // Checkout-page mount counts as begin_checkout entry
    if (path.startsWith('/checkout/') && !path.startsWith('/checkout/success/')) {
      track('checkout_page_view');
    }
    // Success page = purchase
    if (path.startsWith('/checkout/success/')) {
      const isSub = new URLSearchParams(location.search).get('session_id');
      track(isSub ? 'subscribe' : 'purchase');
    }

    // Newsletter footer signup success piggy-backs on the form's behavior.
    // The newsletter module dispatches no custom event today; we listen for
    // the status element gaining .is-ok.
    const obs = new MutationObserver(muts => {
      for (const m of muts) {
        if (m.target.matches && m.target.matches('[data-newsletter-status]') && m.target.classList.contains('is-ok')) {
          track('newsletter_signup', { source: 'footer' });
        }
      }
    });
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('[data-newsletter-status]').forEach(el => obs.observe(el, { attributes: true, attributeFilter: ['class'] }));
    });
  }

  loadPlausible();
  loadSentry();
  bindCommerceEvents();
  window.AplombAnalytics = { track };
})();
