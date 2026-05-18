// APLOMB. — global cart module
//
// Loaded on every page that sells anything (home, PDPs, /checkout/).
// Owns the cart state, persists to localStorage, injects the cart drawer
// into the page if it isn't already there, and exposes window.AplombCart
// for ATC buttons + the standalone checkout page.
//
// Cart schema: { items: { <productKey>: { qty: number, mode: 'onetime'|'subscription' } } }
// We enforce one mode per cart (mixed carts are rejected server-side too);
// adding a mismatched mode prompts the user to clear or finish.
//
// To wire a button:  <button data-aplomb-add="serum" data-mode="onetime">Add to bag</button>
// To open the drawer: <button data-open-cart>Bag <span data-cart-count>0</span></button>
//
// The module is intentionally framework-free; it runs as soon as the DOM is parsed.

(function () {
  'use strict';

  // ---- Product catalog (mirrors functions/_lib/products.js) ----
  // Prices in dollars (display only); server is authoritative for charges.
  const PRODUCTS = {
    serum:  { name: 'APLOMB. The Serum.', priceVal: 129, subscribeDiscountPct: 10, img: '/assets/serum-rail.jpg',         freq: '30 mL · 60-day supply',     allowsSubscription: true,  pdp: '/serum/' },
    daily:  { name: 'APLOMB. Daily.',     priceVal: 49,  subscribeDiscountPct: 15, img: '/assets/serum-rail.jpg',         freq: '30-day supply',             allowsSubscription: true,  pdp: '/'      },
    roots:  { name: 'APLOMB. Roots.',     priceVal: 39,  subscribeDiscountPct: 15, img: '/assets/roots-rail.jpg',         freq: '30-day supply · 3 caps/day', allowsSubscription: true,  pdp: '/roots/' },
    calm:   { name: 'APLOMB. Calm.',      priceVal: 35,  subscribeDiscountPct: 15, img: '/assets/calm-rail.jpg',          freq: '30-day starter kit',        allowsSubscription: true,  pdp: '/calm/'  },
    breath: { name: 'APLOMB. Breath.',    priceVal: 35,  subscribeDiscountPct: 15, img: '/assets/pharmaloz-tin-hero.jpg', freq: '30-day tin · 4 loz/day',    allowsSubscription: true,  pdp: '/breath/' },
  };

  const STORAGE_KEY = 'aplomb-cart-v2';
  const LEGACY_KEY = 'aplomb-serum-cart';
  const COUPON_KEY = 'aplomb-coupon';
  const SHIPPING_FLAT_CENTS = 799;
  const FREE_SHIPPING_THRESHOLD_CENTS = 7500;
  // First-order welcome code. This is the code the newsletter welcome series
  // already promises ("10% off your first order with code APLOMB10"). The
  // SERVER (functions/api/checkout.js) is the only authority — it re-validates
  // the code, enforces first-order-only, and discounts the actual charge.
  // These constants only keep the on-page order summary honest/consistent.
  // If WELCOME_COUPON_CODE/PCT are overridden server-side, update these too.
  const WELCOME_CODE = 'APLOMB10';
  const WELCOME_PCT = 10;

  let state = { items: {} };
  const subscribers = [];

  // ---- Persistence ----
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) { state = JSON.parse(raw) || { items: {} }; return; }
      // Migrate legacy schema (object mapping key -> qty) to new schema (mode='onetime')
      const legacy = localStorage.getItem(LEGACY_KEY);
      if (legacy) {
        const old = JSON.parse(legacy);
        const items = {};
        Object.entries(old || {}).forEach(([k, v]) => {
          if (v > 0 && PRODUCTS[k]) items[k] = { qty: v, mode: 'onetime' };
        });
        state = { items };
        save();
      }
    } catch (_) { state = { items: {} }; }
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {}
    subscribers.forEach(fn => { try { fn(snapshot()); } catch (_) {} });
    renderAll();
  }

  function snapshot() { return JSON.parse(JSON.stringify(state)); }

  // ---- Public API ----
  function unitPriceCents(key, mode) {
    const p = PRODUCTS[key];
    if (!p) return 0;
    const baseCents = p.priceVal * 100;
    if (mode === 'subscription' && p.allowsSubscription) {
      return Math.round(baseCents * (100 - p.subscribeDiscountPct) / 100);
    }
    return baseCents;
  }

  function cartMode() {
    const modes = new Set(Object.values(state.items).map(i => i.mode));
    if (modes.size === 0) return null;
    if (modes.size > 1) return 'mixed';
    return modes.values().next().value;
  }

  function add(key, mode, qty) {
    if (!PRODUCTS[key]) return { ok: false, error: 'Unknown product.' };
    mode = (mode === 'subscription' && PRODUCTS[key].allowsSubscription) ? 'subscription' : 'onetime';
    qty = Math.max(1, qty | 0 || 1);

    const existing = cartMode();
    if (existing && existing !== mode) {
      // Mismatched mode — confirm replacing the cart.
      const ok = window.confirm(
        existing === 'subscription'
          ? 'Your bag has subscription items. Switching to a one-time item will clear the bag. Continue?'
          : 'Your bag has one-time items. Switching to a subscription will clear the bag. Continue?'
      );
      if (!ok) return { ok: false, error: 'Cart not modified.' };
      state.items = {};
    }

    if (state.items[key]) {
      state.items[key].qty += qty;
      state.items[key].mode = mode;
    } else {
      state.items[key] = { qty, mode };
    }
    save();
    openDrawer();
    return { ok: true };
  }

  function setQty(key, qty) {
    qty = Math.max(0, qty | 0);
    if (qty === 0) delete state.items[key];
    else if (state.items[key]) state.items[key].qty = qty;
    save();
  }

  function remove(key) { delete state.items[key]; save(); }
  function clear() { state.items = {}; save(); }

  function getLineItems() {
    return Object.entries(state.items).map(([key, v]) => ({
      productKey: key,
      quantity: v.qty,
      mode: v.mode,
      name: PRODUCTS[key]?.name || key,
      unitPriceCents: unitPriceCents(key, v.mode),
    }));
  }

  function getSubtotalCents() {
    return getLineItems().reduce((sum, li) => sum + li.unitPriceCents * li.quantity, 0);
  }

  function getShippingCents() {
    const sub = getSubtotalCents();
    if (!sub) return 0;
    if (sub >= FREE_SHIPPING_THRESHOLD_CENTS) return 0;
    return SHIPPING_FLAT_CENTS;
  }

  function getTotalCents() { return getSubtotalCents() + getShippingCents(); }

  function getTotalQty() {
    return Object.values(state.items).reduce((n, v) => n + v.qty, 0);
  }

  // ---- First-order coupon (display-side only; server is authoritative) ----
  function notify() {
    subscribers.forEach(fn => { try { fn(snapshot()); } catch (_) {} });
    renderAll();
  }
  function getCoupon() {
    try { return (localStorage.getItem(COUPON_KEY) || '').trim().toUpperCase() || null; }
    catch (_) { return null; }
  }
  function setCoupon(code) {
    code = (code || '').trim().toUpperCase();
    try {
      if (code) localStorage.setItem(COUPON_KEY, code);
      else localStorage.removeItem(COUPON_KEY);
    } catch (_) {}
    notify();
    return code || null;
  }
  function clearCoupon() { return setCoupon(''); }
  // Estimated first-order discount for the stored welcome code, one-time carts
  // only (subscription discounts go through Stripe's promotion-code field).
  function welcomeDiscountCents(subtotalCents) {
    if (getCoupon() !== WELCOME_CODE) return 0;
    if (cartMode() === 'subscription') return 0;
    return Math.round((subtotalCents * WELCOME_PCT) / 100);
  }

  // Add a curated routine (#5) in one click: all component SKUs, one-time,
  // single state update + one drawer open. Honest by construction — it adds
  // each product at its real price (no fabricated bundle markup/discount) and
  // pre-applies the first-order code the bundle page promises; the server
  // still re-validates that code and enforces first-order-only.
  function addBundle(keys, opts) {
    keys = (Array.isArray(keys) ? keys : String(keys || '').split(','))
      .map(k => k.trim())
      .filter(k => PRODUCTS[k]);
    if (!keys.length) return { ok: false, error: 'No valid products.' };

    const existing = cartMode();
    if (existing && existing !== 'onetime') {
      const ok = window.confirm(
        'Your bag has subscription items. Adding the full routine (one-time) will clear the bag. Continue?'
      );
      if (!ok) return { ok: false, error: 'Cart not modified.' };
      state.items = {};
    }
    keys.forEach(k => {
      if (state.items[k]) { state.items[k].qty += 1; state.items[k].mode = 'onetime'; }
      else state.items[k] = { qty: 1, mode: 'onetime' };
    });
    if (!opts || opts.coupon !== false) {
      try { localStorage.setItem(COUPON_KEY, WELCOME_CODE); } catch (_) {}
    }
    save();
    openDrawer();
    return { ok: true };
  }

  // ---- Drawer rendering ----
  function ensureDrawer() {
    if (document.querySelector('[data-cart-drawer]')) return;
    const backdrop = document.createElement('div');
    backdrop.className = 'overlay-backdrop';
    backdrop.setAttribute('data-backdrop', '');
    document.body.appendChild(backdrop);

    const aside = document.createElement('aside');
    aside.className = 'cart-drawer';
    aside.setAttribute('data-cart-drawer', '');
    aside.innerHTML = `
      <div class="cart-head">
        <h3>Your bag</h3>
        <button class="cart-close" data-close-cart aria-label="Close cart">×</button>
      </div>
      <div class="cart-items" data-cart-items>
        <div class="cart-empty">Your bag is empty.</div>
      </div>
      <div class="cart-foot">
        <div class="cart-totals">
          <span class="label">Subtotal</span>
          <span data-cart-subtotal>$0</span>
        </div>
        <div class="cart-totals" data-cart-shipping-row hidden>
          <span class="label">Shipping</span>
          <span data-cart-shipping>$0</span>
        </div>
        <div class="cart-freeship" data-cart-freeship hidden>
          <div class="cart-freeship-msg" data-cart-freeship-msg></div>
          <div class="cart-freeship-track" aria-hidden="true"><div class="cart-freeship-fill" data-cart-freeship-fill></div></div>
          <button type="button" class="cart-suggest" data-cart-suggest hidden></button>
        </div>
        <a class="cart-checkout" data-checkout-link href="/checkout/" aria-disabled="true">Checkout</a>
        <p class="micro" data-cart-disclosure></p>
      </div>
    `;
    document.body.appendChild(aside);
  }

  function fmt(cents) {
    const dollars = (cents / 100);
    return '$' + (dollars % 1 === 0 ? dollars.toFixed(0) : dollars.toFixed(2));
  }

  function shortName(key) {
    const p = PRODUCTS[key]; if (!p) return key;
    return p.name.replace(/^APLOMB\.\s*/, '').replace(/\.\s*$/, '');
  }

  // Pick the single best add-on to suggest: the cheapest SKU not already in
  // the bag that, added once, would cross the free-shipping line (near-miss);
  // failing that, the cheapest remaining SKU (routine-completion bump).
  function pickSuggestion() {
    // Cheapest SKU not already in the bag (price-ascending order). The render
    // layer decides whether adding it crosses the free-ship line and labels
    // it accordingly — we never push the $129 SKU just to "unlock" $8 shipping.
    const order = ['breath', 'calm', 'roots', 'serum'];
    const key = order.find(k => PRODUCTS[k] && !state.items[k]);
    if (!key) return null;
    return { key, priceCents: PRODUCTS[key].priceVal * 100, shortName: shortName(key) };
  }

  function renderDrawer() {
    const itemsEl = document.querySelector('[data-cart-items]');
    if (!itemsEl) return;
    const items = getLineItems();
    if (!items.length) {
      itemsEl.innerHTML = '<div class="cart-empty">Your bag is empty.</div>';
    } else {
      itemsEl.innerHTML = items.map(li => {
        const p = PRODUCTS[li.productKey];
        const lineCents = li.unitPriceCents * li.quantity;
        return `
          <div class="cart-item">
            <img class="cart-item-img" src="${p.img}" alt="">
            <div>
              <div class="cart-item-name">${p.name}</div>
              <div class="cart-item-meta">${p.freq}${li.mode === 'subscription' ? ` · subscribe & save ${p.subscribeDiscountPct}%` : ''}</div>
              <div class="cart-item-qty">
                <button data-cart-dec="${li.productKey}" aria-label="Decrease">−</button>
                <span>${li.quantity}</span>
                <button data-cart-inc="${li.productKey}" aria-label="Increase">+</button>
              </div>
            </div>
            <div>
              <div class="cart-item-price">${fmt(lineCents)}</div>
              <button class="cart-item-remove" data-cart-remove="${li.productKey}">Remove</button>
            </div>
          </div>
        `;
      }).join('');
    }
    const subtotal = getSubtotalCents();
    const shipping = getShippingCents();
    const totalQty = getTotalQty();
    const subEl = document.querySelector('[data-cart-subtotal]'); if (subEl) subEl.textContent = fmt(subtotal);
    const shipRow = document.querySelector('[data-cart-shipping-row]');
    const shipEl = document.querySelector('[data-cart-shipping]');
    if (shipRow && shipEl) {
      if (subtotal > 0) {
        shipRow.hidden = false;
        shipEl.textContent = shipping === 0 ? 'Free' : fmt(shipping);
      } else {
        shipRow.hidden = true;
      }
    }
    const fsWrap = document.querySelector('[data-cart-freeship]');
    const fsMsg = document.querySelector('[data-cart-freeship-msg]');
    const fsFill = document.querySelector('[data-cart-freeship-fill]');
    const fsBtn = document.querySelector('[data-cart-suggest]');
    if (fsWrap && fsMsg && fsFill && fsBtn) {
      const fsMode = cartMode();
      if (subtotal <= 0) {
        fsWrap.hidden = true;
      } else if (fsMode !== 'subscription' && subtotal < FREE_SHIPPING_THRESHOLD_CENTS) {
        // Under the threshold on a one-time order: progress + add-to-unlock.
        const remaining = FREE_SHIPPING_THRESHOLD_CENTS - subtotal;
        const pct = Math.min(100, Math.round((subtotal / FREE_SHIPPING_THRESHOLD_CENTS) * 100));
        fsWrap.hidden = false;
        fsMsg.innerHTML = `<strong>${fmt(remaining)}</strong> away from free shipping`;
        fsFill.style.width = pct + '%';
        const s = pickSuggestion();
        if (s) {
          fsBtn.hidden = false;
          fsBtn.textContent = (s.priceCents >= remaining)
            ? `Add ${s.shortName} (${fmt(s.priceCents)}) and ship free`
            : `Add ${s.shortName} (${fmt(s.priceCents)})`;
          fsBtn.setAttribute('data-cart-suggest', s.key);
        } else { fsBtn.hidden = true; }
      } else if (fsMode !== 'subscription' && subtotal >= FREE_SHIPPING_THRESHOLD_CENTS) {
        // One-time order already ships free: positive confirm + gentle bump.
        const s = pickSuggestion();
        fsWrap.hidden = false;
        fsMsg.innerHTML = `Free shipping unlocked.`;
        fsFill.style.width = '100%';
        if (s) {
          fsBtn.hidden = false;
          fsBtn.textContent = `Complete the routine · add ${s.shortName} (${fmt(s.priceCents)})`;
          fsBtn.setAttribute('data-cart-suggest', s.key);
        } else { fsBtn.hidden = true; }
      } else {
        // Subscription cart: no free-shipping claim (shipping is not waived for
        // subscriptions in pricing logic). Keep the panel out of the way.
        fsWrap.hidden = true;
      }
    }

    const checkoutBtn = document.querySelector('[data-checkout-link]');
    if (checkoutBtn) {
      if (totalQty === 0) {
        checkoutBtn.classList.add('is-disabled');
        checkoutBtn.setAttribute('aria-disabled', 'true');
      } else {
        checkoutBtn.classList.remove('is-disabled');
        checkoutBtn.setAttribute('aria-disabled', 'false');
      }
    }
    document.querySelectorAll('[data-cart-count]').forEach(el => el.textContent = totalQty);

    const disclosure = document.querySelector('[data-cart-disclosure]');
    if (disclosure) {
      const mode = cartMode();
      if (mode === 'subscription') {
        const days = 30;
        disclosure.innerHTML = `Auto-renews every ${days} days at the subscribed price. Cancel any time from your account.`;
      } else if (subtotal > 0 && subtotal < FREE_SHIPPING_THRESHOLD_CENTS) {
        const remaining = (FREE_SHIPPING_THRESHOLD_CENTS - subtotal) / 100;
        disclosure.innerHTML = `Ships in 48 hours · ${fmt(FREE_SHIPPING_THRESHOLD_CENTS - subtotal)} away from free shipping · 15-day returns`;
      } else {
        disclosure.innerHTML = `Ships in 48 hours · 15-day returns`;
      }
      if (mode !== 'subscription' && subtotal > 0 && getCoupon() === WELCOME_CODE) {
        disclosure.innerHTML += ` · <strong>${WELCOME_CODE}</strong> · ${WELCOME_PCT}% off first order at checkout`;
      }
    }
  }

  function renderAll() { renderDrawer(); }

  function openDrawer() {
    ensureDrawer();
    const drawer = document.querySelector('[data-cart-drawer]');
    const backdrop = document.querySelector('[data-backdrop]');
    if (drawer) drawer.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-open');
    document.body.classList.add('no-scroll');
  }
  function closeDrawer() {
    const drawer = document.querySelector('[data-cart-drawer]');
    const backdrop = document.querySelector('[data-backdrop]');
    if (drawer) drawer.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-open');
    document.body.classList.remove('no-scroll');
  }

  // ---- Event delegation ----
  function bindEvents() {
    document.addEventListener('click', function (e) {
      const open = e.target.closest('[data-open-cart]');
      if (open) { e.preventDefault(); openDrawer(); return; }

      const closeBtn = e.target.closest('[data-close-cart]');
      if (closeBtn) { closeDrawer(); return; }

      const backdrop = e.target.closest('[data-backdrop]');
      if (backdrop && backdrop === e.target) { closeDrawer(); return; }

      const sug = e.target.closest('button[data-cart-suggest]');
      if (sug && !sug.hidden) {
        e.preventDefault();
        const k = sug.getAttribute('data-cart-suggest');
        if (k && PRODUCTS[k]) {
          const m = cartMode();
          add(k, m === 'subscription' ? 'subscription' : 'onetime', 1);
        }
        return;
      }

      const bundleBtn = e.target.closest('[data-bundle-add]');
      if (bundleBtn) {
        e.preventDefault();
        addBundle(bundleBtn.dataset.bundleAdd);
        return;
      }

      const addBtn = e.target.closest('[data-aplomb-add]');
      if (addBtn) {
        e.preventDefault();
        const key = addBtn.dataset.aplombAdd;
        // Mode from button's data-mode, or from any nearby radio group with data-mode-group
        let mode = addBtn.dataset.mode || 'onetime';
        const group = addBtn.closest('[data-buy-box]');
        if (group) {
          const chosen = group.querySelector('input[name^="aplomb-mode"]:checked');
          if (chosen) mode = chosen.value;
        }
        add(key, mode, 1);
        return;
      }

      const inc = e.target.closest('[data-cart-inc]');
      if (inc) { const k = inc.dataset.cartInc; setQty(k, (state.items[k]?.qty || 0) + 1); return; }

      const dec = e.target.closest('[data-cart-dec]');
      if (dec) { const k = dec.dataset.cartDec; setQty(k, (state.items[k]?.qty || 0) - 1); return; }

      const rm = e.target.closest('[data-cart-remove]');
      if (rm) { remove(rm.dataset.cartRemove); return; }

      const link = e.target.closest('[data-checkout-link]');
      if (link && link.getAttribute('aria-disabled') === 'true') {
        e.preventDefault();
        return;
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeDrawer();
    });
  }

  // ---- Bootstrap ----
  function init() {
    load();
    ensureDrawer();
    bindEvents();
    renderAll();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  // ---- Exposed API ----
  window.AplombCart = {
    PRODUCTS,
    add, addBundle, setQty, remove, clear,
    getLineItems, getSubtotalCents, getShippingCents, getTotalCents, getTotalQty,
    cartMode,
    getCoupon, setCoupon, clearCoupon, welcomeDiscountCents,
    WELCOME_CODE, WELCOME_PCT,
    freeShippingThresholdCents: FREE_SHIPPING_THRESHOLD_CENTS,
    open: openDrawer, close: closeDrawer,
    subscribe: (fn) => { subscribers.push(fn); fn(snapshot()); return () => { const i = subscribers.indexOf(fn); if (i >= 0) subscribers.splice(i, 1); }; },
  };
  // Compat: assets/checkout.js reads window.AplombCheckout.getCartLineItems()
  window.AplombCheckout = window.AplombCheckout || {};
  window.AplombCheckout.getCartLineItems = getLineItems;
})();
