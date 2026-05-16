// APLOMB. — Tier 3: autonomous browser consent matrix (@playwright/test).
//
//   npm run smoke:browser              # vs https://getaplomb.com
//   BASE_URL=http://localhost:8788 npm run smoke:browser
//
// Proves the consent gate end-to-end — the highest-risk change shipped
// (PR #31). Each case uses a FRESH browser context so localStorage and
// network capture are isolated. The privacy-promise case (GPC overrides a
// stored "accepted" consent) is the security-critical one.
//
// No secrets. Read-only against the target. Pixel/Clarity are detected by
// observing outbound requests to connect.facebook.net / clarity.ms.

import { test, expect } from '@playwright/test';

const BASE = process.env.BASE_URL || 'https://getaplomb.com';

function tracker(context) {
  const reqs = [];
  context.on('request', (r) => reqs.push(r.url()));
  return {
    fb: () => reqs.some((u) => u.includes('connect.facebook.net')),
    clarity: () => reqs.some((u) => u.includes('clarity.ms')),
    plausible: () => reqs.some((u) => u.includes('plausible.io')),
  };
}

const probe = (p) =>
  p.evaluate(() => ({
    banner: !!document.getElementById('aplomb-cookie-banner'),
    accept: (document.querySelector('[data-acb-accept]') || {}).textContent?.trim(),
    reject: (document.querySelector('[data-acb-reject]') || {}).textContent?.trim(),
    consent: (() => {
      try { return localStorage.getItem('aplomb-cookie-consent'); } catch { return 'ERR'; }
    })(),
    adGranted: !!(window.AplombAnalytics &&
      window.AplombAnalytics.adConsentGranted &&
      window.AplombAnalytics.adConsentGranted()),
  }));

test('3.1 first visit — banner shown, no ad-tech, essential analytics OK', async ({ browser }) => {
  const ctx = await browser.newContext();
  const net = tracker(ctx);
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  const s = await probe(p);
  expect(s.banner, 'cookie banner visible on first visit').toBe(true);
  expect(s.accept).toBe('Accept all');
  expect(s.reject).toBe('Essential only');
  expect(net.fb(), 'no Meta Pixel before consent').toBe(false);
  expect(net.clarity(), 'no Clarity before consent').toBe(false);
  expect(net.plausible(), 'Plausible (cookieless, essential) still loads').toBe(true);
  expect(s.adGranted).toBe(false);
  await ctx.close();
});

test('3.2 Essential only — rejected, nothing ad-tech ever loads', async ({ browser }) => {
  const ctx = await browser.newContext();
  const net = tracker(ctx);
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.click('[data-acb-reject]');
  await p.waitForTimeout(2500);
  const s = await probe(p);
  expect(s.consent).toBe('rejected');
  expect(s.banner, 'banner dismissed').toBe(false);
  expect(net.fb()).toBe(false);
  expect(net.clarity()).toBe(false);
  expect(s.adGranted).toBe(false);
  await ctx.close();
});

test('3.3 Accept all — Pixel + Clarity load, consent persists', async ({ browser }) => {
  const ctx = await browser.newContext();
  const net = tracker(ctx);
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.click('[data-acb-accept]');
  await p.waitForTimeout(3500);
  const s = await probe(p);
  expect(s.consent).toBe('accepted');
  expect(s.banner).toBe(false);
  expect(net.fb(), 'Meta Pixel loads after Accept all').toBe(true);
  expect(net.clarity(), 'Clarity loads after Accept all').toBe(true);
  expect(s.adGranted).toBe(true);
  await ctx.close();
});

test('3.4 GPC overrides stored consent — privacy promise honored', async ({ browser }) => {
  const ctx = await browser.newContext();
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, 'globalPrivacyControl', { get: () => true, configurable: true });
  });
  const net = tracker(ctx);
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.evaluate(() => { try { localStorage.setItem('aplomb-cookie-consent', 'accepted'); } catch {} });
  await p.reload({ waitUntil: 'networkidle' });
  await p.waitForTimeout(3000);
  const s = await probe(p);
  expect(s.consent, 'consent is stored as accepted').toBe('accepted');
  expect(s.adGranted, 'but GPC forces adConsentGranted() false').toBe(false);
  expect(net.fb(), 'no Meta Pixel under GPC even with consent').toBe(false);
  expect(net.clarity(), 'no Clarity under GPC even with consent').toBe(false);
  expect(s.banner, 'banner suppressed under GPC').toBe(false);
  await ctx.close();
});

test('3.5 consent persists across navigation', async ({ browser }) => {
  const ctx = await browser.newContext();
  const net = tracker(ctx);
  const p = await ctx.newPage();
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.click('[data-acb-accept]');
  await p.waitForTimeout(3000);
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.waitForTimeout(3000);
  const s = await probe(p);
  expect(s.consent).toBe('accepted');
  expect(s.banner, 'banner does not reappear').toBe(false);
  expect(net.fb(), 'Pixel loads immediately on return visit').toBe(true);
  expect(s.adGranted).toBe(true);
  await ctx.close();
});

test('3.6 checkout.js consumes adConsentGranted() on a PDP', async ({ browser }) => {
  const ctx = await browser.newContext();
  const p = await ctx.newPage();
  await p.goto(BASE + '/serum/', { waitUntil: 'networkidle' });
  await p.evaluate(() => { try { localStorage.setItem('aplomb-cookie-consent', 'accepted'); } catch {} });
  await p.reload({ waitUntil: 'networkidle' });
  await p.waitForTimeout(2000);
  // This is the exact expression checkout.js line ~101 uses to set the
  // `adConsent` field on the cart payload.
  const v = await p.evaluate(() =>
    !!(window.AplombAnalytics &&
       window.AplombAnalytics.adConsentGranted &&
       window.AplombAnalytics.adConsentGranted()));
  expect(v, 'cart payload would carry adConsent:true').toBe(true);
  await ctx.close();
});
