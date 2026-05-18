// APLOMB. Newsletter capture module
//
// Auto-injects a signup form into the page footer (the `.foot` element) on
// every page that includes this script. Submits to /api/newsletter/subscribe;
// captures the page path as `source` for attribution.
//
// Also exposes a 30-second soft popup that runs once per browser
// (cookie-suppressed after dismiss/submit), but is suppressed on
// /checkout/, /account/, and /email-preferences/.

(function () {
  'use strict';

  const STORAGE_KEY = 'aplomb-nl-seen';
  let shownPopup = false;

  function isSuppressedPath() {
    const p = window.location.pathname;
    return p.startsWith('/checkout/')
        || p.startsWith('/account/')
        || p.startsWith('/email-preferences/')
        || p.startsWith('/admin/')
        || p.startsWith('/legal/');
  }

  function buildFooterBlock() {
    const block = document.createElement('div');
    block.className = 'foot-newsletter';
    block.setAttribute('data-newsletter-block', '');
    block.innerHTML = `
      <div class="foot-newsletter-inner">
        <div class="foot-newsletter-copy">
          <h3>Quiet, intermittent, useful.</h3>
          <p>The GLP-1 side-effect literature, the cohort data, and the occasional product note.</p>
        </div>
        <form class="foot-newsletter-form" data-newsletter-form novalidate>
          <label for="footer-nl-email" class="visually-hidden">Email</label>
          <input type="email" required name="email" id="footer-nl-email" autocomplete="email" placeholder="you@example.com">
          <button type="submit" data-newsletter-submit>
            <span data-submit-label>Subscribe</span>
            <span data-submit-spinner hidden>&hellip;</span>
          </button>
        </form>
        <p class="foot-newsletter-status" data-newsletter-status hidden></p>
      </div>
    `;
    return block;
  }

  function buildPopup() {
    const overlay = document.createElement('div');
    overlay.className = 'newsletter-popup';
    overlay.setAttribute('data-newsletter-popup', '');
    overlay.innerHTML = `
      <div class="newsletter-popup-inner" role="dialog" aria-labelledby="nl-popup-title" aria-modal="false">
        <button type="button" class="newsletter-popup-close" data-newsletter-popup-close aria-label="Close">&times;</button>
        <h3 id="nl-popup-title">Built for the side effects nobody is selling you a solution to.</h3>
        <p>Drop your email for 10% off your first order, and the occasional note when the literature gets interesting.</p>
        <form data-newsletter-popup-form class="foot-newsletter-form">
          <label for="popup-nl-email" class="visually-hidden">Email</label>
          <input type="email" required name="email" id="popup-nl-email" autocomplete="email" placeholder="you@example.com">
          <button type="submit" data-newsletter-popup-submit>
            <span data-submit-label>Get the code</span>
            <span data-submit-spinner hidden>&hellip;</span>
          </button>
        </form>
        <p class="foot-newsletter-status" data-newsletter-popup-status hidden></p>
        <p class="newsletter-popup-fine">We send no more than 4 emails a month. Unsubscribe with one click any time.</p>
      </div>
    `;
    return overlay;
  }

  async function submit(email, source) {
    const resp = await fetch('/api/newsletter/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, source }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || 'Could not subscribe.');
    }
    return resp.json();
  }

  function setStatus(el, msg, ok) {
    if (!el) return;
    el.hidden = false;
    el.textContent = msg;
    el.classList.toggle('is-ok', !!ok);
    el.classList.toggle('is-err', !ok);
  }
  function setSubmitState(form, working) {
    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;
    btn.disabled = !!working;
    const label = btn.querySelector('[data-submit-label]');
    const spinner = btn.querySelector('[data-submit-spinner]');
    if (label) label.hidden = !!working;
    if (spinner) spinner.hidden = !working;
  }

  function mountFooter() {
    const foot = document.querySelector('.foot');
    if (!foot) return;
    if (foot.querySelector('[data-newsletter-block]')) return;
    foot.insertBefore(buildFooterBlock(), foot.firstChild);
  }

  function showPopup() {
    if (shownPopup) return;
    if (document.querySelector('[data-newsletter-popup]')) return;
    shownPopup = true;
    document.body.appendChild(buildPopup());
    requestAnimationFrame(() => {
      const el = document.querySelector('[data-newsletter-popup]');
      if (el) el.classList.add('is-open');
    });
  }

  // Show on whichever comes first: a 20s dwell, scrolling past ~55% of the
  // page, or desktop exit-intent (pointer leaving through the top). Still
  // once per browser (STORAGE_KEY, set on dismiss) and never on suppressed
  // paths. Slide-in style is unchanged — trigger quality, not size.
  function maybeShowPopup() {
    if (isSuppressedPath()) return;
    try { if (localStorage.getItem(STORAGE_KEY)) return; } catch (_) {}

    let armed = true;
    function cleanup() {
      armed = false;
      window.removeEventListener('scroll', onScroll);
      document.removeEventListener('mouseout', onExit);
      clearTimeout(timer);
    }
    function fire() { if (!armed) return; cleanup(); showPopup(); }
    function onScroll() {
      const sc = window.scrollY || document.documentElement.scrollTop || 0;
      const h = (document.documentElement.scrollHeight - window.innerHeight) || 1;
      if (sc / h >= 0.55) fire();
    }
    function onExit(e) { if (e.clientY <= 0) fire(); }

    const timer = setTimeout(fire, 20000);
    window.addEventListener('scroll', onScroll, { passive: true });
    document.addEventListener('mouseout', onExit);
  }

  function dismissPopup() {
    const el = document.querySelector('[data-newsletter-popup]');
    if (el) el.remove();
    try { localStorage.setItem(STORAGE_KEY, '1'); } catch (_) {}
  }

  function bindEvents() {
    document.addEventListener('submit', async function (e) {
      const form = e.target.closest('[data-newsletter-form], [data-newsletter-popup-form]');
      if (!form) return;
      e.preventDefault();
      const isPopup = form.matches('[data-newsletter-popup-form]');
      const email = (form.email.value || '').trim();
      const statusEl = isPopup
        ? document.querySelector('[data-newsletter-popup-status]')
        : document.querySelector('[data-newsletter-status]');
      if (!email || !email.includes('@')) {
        setStatus(statusEl, 'Please enter a valid email.', false);
        return;
      }
      setSubmitState(form, true);
      try {
        const { alreadySubscribed } = await submit(email, isPopup ? 'popup' : ('footer:' + window.location.pathname));
        setSubmitState(form, false);
        try { localStorage.setItem(STORAGE_KEY, '1'); } catch (_) {}
        if (alreadySubscribed) {
          setStatus(statusEl, "You're already on the list. Thanks.", true);
        } else {
          setStatus(statusEl, isPopup
            ? 'Check your inbox for your 10% code.'
            : "Thanks. We'll be in touch.", true);
          form.reset();
        }
        if (isPopup) setTimeout(dismissPopup, 2500);
      } catch (err) {
        setSubmitState(form, false);
        setStatus(statusEl, err.message || 'Could not subscribe. Please try again.', false);
      }
    });

    document.addEventListener('click', function (e) {
      if (e.target.closest('[data-newsletter-popup-close]')) dismissPopup();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.querySelector('[data-newsletter-popup]')) dismissPopup();
    });
  }

  function init() {
    mountFooter();
    bindEvents();
    maybeShowPopup();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
