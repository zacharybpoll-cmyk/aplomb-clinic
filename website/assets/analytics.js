// APLOMB. — Analytics, observability, cookie consent, and conditional pixel/heatmap loaders.
//
// Always loaded (essential / privacy-friendly):
//   - Plausible (cookieless, GDPR/CCPA-exempt)
//   - Sentry (error monitoring; no tracking cookies in our config)
//
// Loaded only with consent (or never if GPC / DNT signal is on):
//   - Meta Pixel — reads <meta name="meta-pixel-id" content="...">
//   - Microsoft Clarity — reads <meta name="clarity-project-id" content="...">
//
// Public API:
//   window.AplombAnalytics.track(eventName, props)
//   window.AplombAnalytics.consent.set('accepted' | 'rejected')
//   window.AplombAnalytics.consent.get()  -> 'accepted' | 'rejected' | null

(function () {
  'use strict';

  // ─────────────────────────────────────────────────────────────────────────
  // Consent state
  // ─────────────────────────────────────────────────────────────────────────
  const CONSENT_KEY = 'aplomb-cookie-consent';

  function consentGet() {
    try { return localStorage.getItem(CONSENT_KEY); } catch (_) { return null; }
  }
  function consentSet(value) {
    try { localStorage.setItem(CONSENT_KEY, value); } catch (_) {}
    if (value === 'accepted') loadOptionalAnalytics();
  }
  function isPrivacySignaled() {
    // Global Privacy Control (CCPA-honored) or Do Not Track → never load optional analytics
    try {
      if (navigator.globalPrivacyControl === true) return true;
      if (navigator.doNotTrack === '1' || window.doNotTrack === '1') return true;
    } catch (_) {}
    return false;
  }
  // Single source of truth for cross-context advertising opt-in. Governs BOTH
  // the browser Meta Pixel and the server-side Meta Conversions API: /api/checkout
  // forwards this so the Stripe webhook suppresses CAPI when it is false.
  function adConsentGranted() {
    return consentGet() === 'accepted' && !isPrivacySignaled();
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Plausible — always on (cookieless)
  // ─────────────────────────────────────────────────────────────────────────
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
    window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Sentry — always on (error monitoring is essential)
  // ─────────────────────────────────────────────────────────────────────────
  function loadSentry() {
    const meta = document.querySelector('meta[name="sentry-dsn"]');
    const dsn = meta && meta.content;
    if (!dsn) return;
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

  // ─────────────────────────────────────────────────────────────────────────
  // Meta Pixel + Microsoft Clarity — gated on consent
  // ─────────────────────────────────────────────────────────────────────────
  function loadMetaPixel() {
    const meta = document.querySelector('meta[name="meta-pixel-id"]');
    const pixelId = meta && meta.content;
    if (!pixelId) return;
    if (window.fbq) return;
    /* eslint-disable */
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    /* eslint-enable */
    window.fbq('init', pixelId);
    window.fbq('track', 'PageView');
  }

  function loadClarity() {
    const meta = document.querySelector('meta[name="clarity-project-id"]');
    const projectId = meta && meta.content;
    if (!projectId) return;
    if (window.clarity) return;
    /* eslint-disable */
    (function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src='https://www.clarity.ms/tag/'+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y)})(window,document,'clarity','script',projectId);
    /* eslint-enable */
  }

  function loadOptionalAnalytics() {
    if (isPrivacySignaled()) return;
    loadMetaPixel();
    loadClarity();
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Cookie consent banner — DOM injected, no per-page HTML edit needed
  // ─────────────────────────────────────────────────────────────────────────
  const BANNER_CSS = [
    '#aplomb-cookie-banner{',
    '  position:fixed;left:0;right:0;bottom:0;z-index:9999;',
    '  background:#f7f1e6;color:#1a1512;',
    '  border-top:1px solid #e8dccc;',
    '  box-shadow:0 -4px 24px rgba(26,21,18,0.06);',
    '  font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,sans-serif;',
    '  padding:18px 20px;',
    '}',
    '#aplomb-cookie-banner .acb-inner{',
    '  max-width:1180px;margin:0 auto;',
    '  display:flex;align-items:center;gap:24px;flex-wrap:wrap;',
    '}',
    '#aplomb-cookie-banner .acb-text{',
    '  flex:1 1 320px;font-size:13px;line-height:1.55;color:#3a3128;',
    '}',
    '#aplomb-cookie-banner .acb-text a{color:#7a3d14;text-decoration:underline;}',
    '#aplomb-cookie-banner .acb-buttons{',
    '  display:flex;gap:10px;flex-shrink:0;',
    '}',
    '#aplomb-cookie-banner button{',
    '  font-family:"IBM Plex Sans",sans-serif;',
    '  font-size:12px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;',
    '  padding:11px 18px;border:1px solid #1a1512;cursor:pointer;line-height:1;',
    '  white-space:nowrap;',
    '}',
    '#aplomb-cookie-banner button.acb-accept{background:#1a1512;color:#f7f1e6;}',
    '#aplomb-cookie-banner button.acb-accept:hover{background:#7a3d14;border-color:#7a3d14;}',
    '#aplomb-cookie-banner button.acb-reject{background:transparent;color:#1a1512;}',
    '#aplomb-cookie-banner button.acb-reject:hover{background:#1a1512;color:#f7f1e6;}',
    '@media (max-width:640px){',
    '  #aplomb-cookie-banner .acb-buttons{width:100%;flex-direction:column-reverse;}',
    '  #aplomb-cookie-banner button{width:100%;}',
    '}',
  ].join('');

  function injectBanner() {
    if (document.getElementById('aplomb-cookie-banner')) return;

    const style = document.createElement('style');
    style.id = 'aplomb-cookie-banner-css';
    style.textContent = BANNER_CSS;
    document.head.appendChild(style);

    const wrap = document.createElement('div');
    wrap.id = 'aplomb-cookie-banner';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-label', 'Cookie consent');
    wrap.innerHTML = ''
      + '<div class="acb-inner">'
      + '  <div class="acb-text">'
      + '    We use cookies to run checkout, log errors, and measure anonymous traffic. With your consent, we may also use analytics that show us how visitors use the site (Meta Pixel, Microsoft Clarity). '
      + '    Read our <a href="/legal/cookie-policy/">cookie policy</a> or '
      + '    <a href="/legal/cookie-policy/#ccpa">Do Not Sell or Share My Personal Information</a>.'
      + '  </div>'
      + '  <div class="acb-buttons">'
      + '    <button type="button" class="acb-reject" data-acb-reject>Essential only</button>'
      + '    <button type="button" class="acb-accept" data-acb-accept>Accept all</button>'
      + '  </div>'
      + '</div>';
    document.body.appendChild(wrap);

    wrap.querySelector('[data-acb-accept]').addEventListener('click', () => {
      consentSet('accepted');
      dismissBanner();
    });
    wrap.querySelector('[data-acb-reject]').addEventListener('click', () => {
      consentSet('rejected');
      dismissBanner();
    });
  }

  function dismissBanner() {
    const el = document.getElementById('aplomb-cookie-banner');
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  function bootConsent() {
    if (isPrivacySignaled()) return;

    const state = consentGet();
    if (state === 'accepted') {
      loadOptionalAnalytics();
      return;
    }
    if (state === 'rejected') {
      return;
    }
    if (document.body) injectBanner();
    else document.addEventListener('DOMContentLoaded', injectBanner);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Event tracking
  // ─────────────────────────────────────────────────────────────────────────
  function track(eventName, props) {
    try {
      if (typeof window.plausible === 'function') {
        window.plausible(eventName, { props: props || {} });
      }
    } catch (_) {}
    try {
      if (typeof window.fbq === 'function') {
        const fbMap = {
          view_product: 'ViewContent',
          add_to_cart: 'AddToCart',
          begin_checkout: 'InitiateCheckout',
          purchase: 'Purchase',
          subscribe: 'Subscribe',
          newsletter_signup: 'Lead',
        };
        const fbName = fbMap[eventName];
        if (fbName) window.fbq('track', fbName, props || {});
      }
    } catch (_) {}
  }

  function bindCommerceEvents() {
    const path = location.pathname;
    const match = path.match(/^\/(serum|roots|calm|breath|daily)\//);
    if (match) track('view_product', { product: match[1] });

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

    if (path.startsWith('/checkout/') && !path.startsWith('/checkout/success/')) {
      track('checkout_page_view');
    }
    if (path.startsWith('/checkout/success/')) {
      const isSub = new URLSearchParams(location.search).get('session_id');
      track(isSub ? 'subscribe' : 'purchase');
    }

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
  bootConsent();
  bindCommerceEvents();

  window.AplombAnalytics = {
    track,
    adConsentGranted,
    consent: {
      get: consentGet,
      set: consentSet,
    },
  };
})();
