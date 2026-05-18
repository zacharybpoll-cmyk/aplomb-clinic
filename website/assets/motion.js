/* APLOMB. — scroll-reveal micro-interaction (added 2026-05-17)
 *
 * Gently rises + fades major content blocks into view as you scroll,
 * the way For Hims / Midi Health do. Pure vanilla, no dependencies.
 *
 * Safety contract:
 *  - Never hides content when reduced motion is requested, when
 *    IntersectionObserver is unavailable, or when JS is off — the
 *    hidden state (.reveal-init) is added by THIS script only.
 *  - Transforms / opacity only: GPU-composited, no layout reflow.
 *  - Idempotent; runs once even if included twice.
 *
 * Loaded with `defer`, so it executes after the DOM is parsed and
 * before first paint of below-the-fold content (no FOUC).
 */
(function () {
  if (window.__aplombMotion) return;
  window.__aplombMotion = true;

  // Honour the user's OS-level reduced-motion preference.
  var mq = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  if (mq && mq.matches) return;
  if (!('IntersectionObserver' in window)) return;

  // Curated, non-chrome content blocks. The hero is intentionally
  // excluded so the above-the-fold/LCP area is never delayed.
  // .pdp itself is intentionally absent — it is the above-the-fold
  // product buy area (LCP) and must never be hidden. .pdp-rest is the
  // long-form block below the fold and is safe to reveal.
  var SELECTOR = [
    '.ticker', '.gap', '.rail', '.mh-card', '.voice-card', '.bio-card',
    '.voices-head', '.voices-stat', '.cta', '.standards', '.cross-sell',
    '.pp-section', '.pp-page-head', '.citations', '.acc-item',
    '.contact-form', '.pdp-rest', '.foot-grid'
  ].join(',');

  // Don't animate anything living inside an overlay/drawer/modal/popup.
  var SKIP_INSIDE = '.cart-drawer,.product-modal,.checkout-modal,.newsletter-popup,.overlay-backdrop';

  var all = Array.prototype.slice.call(document.querySelectorAll(SELECTOR));

  // Keep only the outermost match (drop any candidate nested inside
  // another candidate) so a section and its cards don't double-reveal.
  var targets = all.filter(function (el) {
    if (el.closest(SKIP_INSIDE)) return false;
    for (var i = 0; i < all.length; i++) {
      if (all[i] !== el && all[i].contains(el)) return false;
    }
    return true;
  });
  if (!targets.length) return;

  // Stagger siblings within the same parent for a gentle cascade;
  // standalone blocks just rise on their own. Capped so long grids
  // never feel slow.
  var seen = new Map();
  targets.forEach(function (el) {
    el.classList.add('reveal-init');
    var p = el.parentNode;
    var idx = seen.get(p) || 0;
    seen.set(p, idx + 1);
    el.style.transitionDelay = Math.min(idx, 7) * 70 + 'ms';
  });

  // Once the entrance finishes, strip the reveal classes so the
  // element returns to its natural resting state. This is visually
  // seamless (it just animated to exactly that state) and frees any
  // hover transform on the same element (e.g. card lift) from being
  // pinned by the reveal end-state.
  function settle(el) {
    el.classList.remove('reveal-init', 'is-visible');
    el.style.transitionDelay = '';
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      io.unobserve(el);
      el.classList.add('is-visible');
      var done = false;
      var finish = function () { if (done) return; done = true; settle(el); };
      el.addEventListener('transitionend', finish, { once: true });
      // Fallback if transitionend never fires (delay + 600ms anim + buffer).
      var delay = parseFloat(el.style.transitionDelay) || 0;
      setTimeout(finish, delay + 900);
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -8% 0px' });

  targets.forEach(function (el) { io.observe(el); });
})();
