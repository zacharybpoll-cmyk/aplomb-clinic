# Aplomb Project — Tasks

## Session 2026-05-03 — Supplier Shortlist Deck

### Completed
- [x] Consolidate supplier data for all 5 side-effect categories (ozempic_face, halitosis, hair_loss, nausea, nutrient_depletion)
- [x] Build 13-slide PowerPoint deck with brand compliance (Bone #F5F4F0, near-black #1A1D21)
- [x] Implement supplier matrix tables (8 columns × 3 suppliers per category)
- [x] Verify all 15 suppliers pass MOQ gate (≤100 units OR <$250 total cost)
- [x] Add hyperlinks to supplier websites in tables
- [x] Apply post-save scrub to remove python-pptx artifacts (prevents repair prompt)
- [x] Commit to git: e8db8d1

### Output
**File:** `/Users/zacharypoll/Desktop/Documents/Claude Code/aplomb.clinic/business documents/Aplomb_Supplier_Shortlist_v1.pptx`
- 13 slides, 16:9 aspect ratio
- All 15 suppliers verified, MOQ-compliant
- Hyperlinked supplier matrix tables
- Brand-compliant design (Playfair Display + Inter)

### Remaining Tasks
- [ ] User review of deck content
- [ ] Refinement requests (if any)
- [ ] Presentation to stakeholders

---

## Session 2026-05-06 — Hair Loss Product Sourcing Research (In Progress)

### Completed
- [x] Lane B Research (Multi-Deficiency Collagen Capsules): 5 candidates identified
  - Lief Labs + Rousselot Peptan (72–76/100, gold-standard)
  - Makers Nutrition (66–70/100, marginal MOQ pass via stock trial)
  - Custom Nutra Trial (62–74/100, ONLY hard MOQ gate compliant at 48 units/$84)
  - Robinson Pharma Liquid (68–72/100, high collagen dose)
  - Vox Nutrition Upgrade (60–64/100, existing supplier)
- [x] Lane C Research (Topical Serums & Format-Shifters): 4 candidates identified
  - FormuNova Hair Growth Serum (64/100, marginal MOQ pass at 140 units)
  - Xiran Capixyl Serum (62/100, comprehensive peptide stack)
  - ING Pharmaceutical Saw Palmetto (54/100, DHT blocker, narrow indication)
  - SMP Nutra Gummies (48/100 AS-IS, 68/100 with reformulation; highest-impact opportunity)
- [x] Clinical Foundation (both lanes): Milani 2023 RCT, Panahi 2015 RCT, peptide growth factor mechanisms documented
- [x] MOQ Gate Analysis: Identified 2 hard-pass candidates, 2 marginal-pass candidates, 6 scale-up-tier candidates
- [x] Consolidated Report Creation: Merged Lanes B + C into unified markdown with ranked summary table, strategic recommendations, and references

### In Progress
- [ ] Lane A Research (Supliful + Low-MOQ Alternatives): PENDING agent completion
  - Expected: 4–5 Supliful products with verified URLs, ingredient panels, pricing, MOQ, lead times
  - Expected: 3+ verified low-MOQ SKUs from Custom Nutra, Vitalabs, Nutracap, NutraScience, Lief Labs
  - Status: Re-launched with explicit tool-use instructions; awaiting output file

### Output (Current)
**File:** `/Users/zacharypoll/Desktop/Documents/Claude Code/aplomb.clinic/Aplomb_hair_loss_consolidated_research_final.md`
- Executive Summary (MOQ gate tension, highest-impact opportunities, Lane A pending)
- Clinical Foundation (Milani 2023, Panahi 2015, mechanisms)
- Lane B (5 candidates, full specs, MOQ/cost/biotin analysis)
- Lane C (4 candidates, full specs, MOQ/cost/biotin analysis)
- Critical MOQ Gate Analysis (compliance breakdown)
- Unified Summary Table (9 candidates + baseline, ranked by rubric score)
- Strategic Recommendations (Phase 1 immediate actions)
- Verification Gates & References (complete citations)

### Remaining Tasks
- [ ] Await Lane A completion and output file
- [ ] Perform final consolidation merge (update unified summary table with Lane A candidates)
- [ ] Execute Phase 1 procurement actions:
  - [ ] Contact SMP Nutra with custom reformulation request (biotin ≤2.5mg, +18mg iron, +vitamin D to 1,000 IU)
  - [ ] Confirm Custom Nutra 48-unit trial order ($84)
  - [ ] Request samples/quotes from top topical candidates (FormuNova, Xiran)
  - [ ] Initiate Lief Labs negotiation call for pilot batch pricing
- [ ] Commit consolidated report to git (branch → PR → merge per project workflow)

---

## Session 2026-05-14 — Launch-Readiness Comprehensive Audit

Reference: `business-documents/LAUNCH-READINESS.md` (full doc, ~12K words).
Companion: `business-documents/prelaunch-audit-2026-05-12.md` (25-point commerce bring-up grid; still valid).

### Tier 1 — LAUNCH-BLOCKING (this week)
- [ ] **T1-1** Fix sitemap `/daily/` (delete URL from `website/sitemap.xml` until a Daily PDP exists) — 15 min, dev
- [ ] **T1-2** Wire Cron Worker (companion CF Worker) for `/cron/welcome-series` (`30 9 * * *`) and `/cron/renewal-reminder` (`0 9 * * *`) with `X-Cron-Secret` header — 1 hr, dev+founder
- [ ] **T1-3** Verify production deploy of merge commit `0d0d821` is live (`wrangler pages deployment list aplomb-clinic`) — 10 min, founder
- [ ] **T1-4** Smoke-test CF Access `/admin` gate end-to-end (incognito → Google sign-in → confirm gating) — 15 min, founder
- [ ] **T1-5** Smoke-test `/account` magic-link end-to-end (real email → link → orders + Stripe Portal CTA) — 15 min, founder
- [ ] **T1-6** Confirm supplier Prop 65 + allergen disclosures per SKU (Roots, Calm, Breath, Serum) — varies, founder+suppliers
- [ ] **T1-7** Verify Apple Pay live-mode domain in Stripe Dashboard UI (API mirror done, UI re-confirm) — 5 min, founder
- [ ] **T1-8** Create `/legal/cookie-policy/` page — 30 min, dev
- [ ] **T1-9** Install cookie consent banner (Termly $10/mo or Cookiebot free) — 1 hr, dev
- [ ] **T1-10** Product liability insurance bound (Hiscox / Next Insurance, $1M coverage, ~$1.5-4K/yr) — 1 hr, founder

### Tier 2 — DAYS 1–30 (launch window — high ROI SEO/GEO + trust signals)
- [ ] **T2-1** Drop `website/llms.txt` (template in LAUNCH-READINESS Appendix A) — 30 min
- [ ] **T2-2** Update `website/robots.txt` with explicit AI crawler Allow directives (Appendix B) — 10 min
- [ ] **T2-3** Add FAQPage JSON-LD to `/faq/index.html` (Appendix C) — 30 min — **highest-ROI single fix**
- [ ] **T2-4** Add Person JSON-LD for founder on `/about/index.html` (Appendix D) — 30 min
- [ ] **T2-5** Add `AggregateRating` + `Review` JSON-LD scaffold to PDPs (will be empty Day 1, fills as reviews come in) — 1 hr
- [ ] **T2-6** Fix `website/sitemap.xml`: add `<lastmod>`, image namespace (Appendix F) — 30 min
- [ ] **T2-7** Add `website/_headers` (CSP, HSTS, X-CTO, Referrer-Policy, Permissions-Policy) (Appendix E) — 1 hr
- [ ] **T2-8** Build branded 404 page at `website/404.html` — 1 hr
- [ ] **T2-9** Install Junip free tier; wire JSON API on PDPs — 2 hrs
- [ ] **T2-10** Meta Pixel + Meta CAPI (Stripe webhook → CAPI Purchase event) — 4 hrs
- [ ] **T2-11** Install Microsoft Clarity (free heatmap; one JS snippet) — 10 min
- [ ] **T2-12** Verify Google Search Console; submit sitemap — 15 min, founder
- [ ] **T2-13** Verify Bing Webmaster Tools; submit sitemap — 15 min, founder
- [ ] **T2-14** COA links on supplement PDPs (Roots, Calm, Breath) — 1 hr/SKU, supplier-dependent
- [ ] **T2-15** Add "Reviewed by Zachary Poll, [credentials]" byline + dateModified on `/biology` and `/evidence` — 30 min
- [ ] **T2-16** Update `README.md` (GitHub Pages → Cloudflare Pages) — 5 min
- [ ] **T2-17** Build `review-request` email template; wire T+10-day send — 2 hrs (requires `delivered_at` column add)
- [ ] **T2-18** Back-in-stock waitlist (extend newsletter_subscribers or new table) — 4 hrs
- [ ] **T2-19** Stripe Checkout `consent_collection.promotion_codes` enabled when first promo campaign launches — 15 min
- [ ] **T2-20** Stock decrement on `payment_intent.succeeded` and `checkout.session.completed` webhook handlers — 1 hr — **critical for inventory accuracy**

### Tier 3 — DAYS 31–90 (growth stack)
- [ ] **T3-1** ESP migration decision: stay on Resend Broadcasts vs migrate to Klaviyo — 1 day decision; 1-2 wk migration
- [ ] **T3-2** Marketing flows: cart-abandon, browse-abandon, post-purchase nurture (Day 7/21/45), replenishment (Day 25), win-back (Day 60), VIP, sunset — 2-4 weeks
- [ ] **T3-3** Postscript SMS at footer + checkout opt-in — 4 hrs ($25/mo)
- [ ] **T3-4** Help Scout helpdesk + 20 macros — 4 hrs ($25/user/mo)
- [ ] **T3-5** Aftersell post-purchase upsell page — 4 hrs ($30/mo)
- [ ] **T3-6** Friendbuy / ReferralCandy referral program (Give-$10/Get-$10) — 4 hrs ($49/mo)
- [ ] **T3-7** Branded order-tracking page (Wonderment) — 4 hrs ($30/mo)
- [ ] **T3-8** Blog at `/journal/`: first 3 pillar posts (Skin, Hair, Nausea) live by Day 30 — 1 week
- [ ] **T3-9** Press kit / EPK PDF — 4 hrs
- [ ] **T3-10** Founder Reddit / community presence (r/Ozempic etc.) — 30 min/day ongoing
- [ ] **T3-11** HARO / Help A B2B Writer subscription — 30 min ($19/mo)
- [ ] **T3-12** Niche podcast guest pitch (3-5 targeted shows) — ongoing
- [ ] **T3-13** A/B testing infra (Intelligems / Visually.io) — 4 hrs ($200+/mo)
- [ ] **T3-14** Migrate to Recharge / Skio when customers ask for pause/swap — 1 week ($99+/mo)
- [ ] **T3-15** Admin polish: CSV export, customer detail view, inventory editor — 1-2 days
- [ ] **T3-16** TikTok Pixel + Events API (if running TikTok ads) — 2 hrs
- [ ] **T3-17** Google Ads Enhanced Conversions (if running Google Ads) — 2 hrs
- [ ] **T3-18** Founder video (60s on `/about/`) — 1 day
- [ ] **T3-19** Sourcing / manufacturing transparency page (`/sourcing/`) — 4 hrs

### Tier 4 — POST-90 (scale + polish)
- [ ] **T4-1** Triple Whale / Polar Analytics blended ROAS (when >$30K/mo revenue)
- [ ] **T4-2** Customer Data Platform (Segment / RudderStack) — when stack >5 tools
- [ ] **T4-3** Trustpilot / Google Reviews integration — after 50+ Loox reviews
- [ ] **T4-4** Affiliate program (ShareASale / Impact / Refersion) — post-PMF
- [ ] **T4-5** International shipping infrastructure (UK first)
- [ ] **T4-6** Federal trademark on APLOMB. word mark — $350 filing + ~$1K atty
- [ ] **T4-7** MoCRA registration for The Serum (or CMO confirms responsible party)
- [ ] **T4-8** DSHEA AER workflow + FDA 3500A docs on hand
- [ ] **T4-9** Loyalty program — only if data says it lifts retention; brand-wise probably skip
- [ ] **T4-10** Multi-currency Stripe — when international traffic >5%

### Pre-flight ops checklist for founder (Day 1 worklist — ≤3 hours)
- [ ] Stripe LIVE-mode Apple Pay dashboard re-confirmation
- [ ] Production deploy of `0d0d821` verified
- [ ] Companion Cron Worker created in Cloudflare Dashboard
- [ ] CF Access `/admin` smoke-test (incognito → Google sign-in)
- [ ] `/account` magic-link smoke-test (real email → orders + portal)
- [ ] Plausible account confirmed real (site ID matches)
- [ ] Sentry account confirmed real (DSN matches)
- [ ] Pirate Ship signup + USPS link
- [ ] Per-SKU supplier confirmations: COA + allergen + Prop 65
- [ ] Hiscox / Next Insurance product liability quote → bind $1M coverage
- [ ] Termly or Cookiebot signup → cookie banner snippet → cookie policy page

---

## Session 2026-05-14 (continued) — Tier 1+2 dev landed locally

All Tier 1+2 items doable without founder credentials are now in the working tree. Verified locally on `wrangler pages dev`.

### Shipped (code + content)
- [x] **T1-1** sitemap.xml — removed `/daily/` 404, added `<lastmod>`, image namespace, `<image:image>` per PDP
- [x] **T1-2** Companion Cron Worker scaffolded: `companion-worker/{wrangler.toml,src/index.js,README.md}` — 3 cron triggers (renewal-reminder 09:00 UTC, review-requests 09:15, welcome-series 09:30)
- [x] **T1-8** Cookie policy page at `website/legal/cookie-policy/index.html` with CCPA "Do Not Sell or Share" section
- [x] **T1-9** Custom cookie banner injected from `website/assets/analytics.js` (key `aplomb-cookie-consent`; "Accept all" / "Essential only"; respects GPC + DNT)
- [x] **T2-1** `website/llms.txt` per llmstxt.org
- [x] **T2-2** `website/robots.txt` with explicit Allows for all major AI crawlers
- [x] **T2-3** `FAQPage` JSON-LD on `/faq/` (19 Q&As)
- [x] **T2-4** `Person` JSON-LD on `/about/`
- [x] **T2-7** `website/_headers` — CSP report-only initially, HSTS, X-CTO, Referrer-Policy, Permissions-Policy, cache rules
- [x] **T2-8** Branded `website/404.html`
- [x] **T2-10** Meta Pixel + CAPI scaffold (gated on consent + meta tag presence); `sendMetaCapiEvent()` in webhook for Purchase + Subscribe
- [x] **T2-11** Microsoft Clarity loader (gated on consent + meta tag)
- [x] **T2-15** "Reviewed by" bylines + `Article` JSON-LD on `/biology/` and `/evidence/`
- [x] **T2-16** README.md fixed — GitHub Pages → Cloudflare Pages
- [x] **T2-17** Review-request email — migration 0004 + template + cron endpoint + worker wiring
- [x] **T2-19** Stripe `allow_promotion_codes: true` on subscription checkout
- [x] **T2-20** Inventory decrement on webhook (best-effort; DB constraint `on_hand >= 0` prevents negatives)

### Skipped this round (per founder)
- [x] **T2-5** AggregateRating / Review schema — skipped until reviews tool live
- [x] **T2-9** Reviews tool signup — skipped

### Local verification passed
- All endpoints respond cleanly; headers correct; JSON-LD detected on 4 pages
- 12/12 email templates render (was 11/11)
- Companion Worker source valid; SCHEDULE map ↔ wrangler.toml crons match

---

## 2026-05-16 — Inspiration-brand redesign mockups (design-scratch)
- [x] Built 7 standalone click-through redesign mockups + gallery in `design-scratch/redesign-mockups/`
- [x] Studies: 01 The Ordinary, 02 Augustinus Bader, 03 Aesop, 04 Hims, 05 Midi Health, 06 Function Health, 07 Maude
- [x] Hybrid fidelity: Cormorant Garamond + IBM Plex Sans + amber period constant; palette/grid/composition flex per brand
- [x] Reused existing on-brand Flux assets from `website/assets/` (no new generation needed) → shared `redesign-mockups/assets/`
- [x] Each: home + product PDP + science + about + FAQ + cart drawer + mock checkout via in-file hash router
- [x] Real APLOMB copy/pricing (Serum $129, Roots $39, Calm $35, Breath $35); content unchanged from live site
- [x] Static-clean: 0 em dashes, 0 drug trademarks, no Inter, no steel-blue/cool hexes, no emoji (all 8 files)
- [x] Verified in browser: routing, subscribe price calc, add-to-cart, cart persistence, checkout→confirmation, FAQ accordion — 0 console errors
- Note: Ozempic-titled citations genericized to "Cleveland Clinic · patient education" to honor BRAND.md trademark rule (live site still uses literal titles; mockups are conservative)
- Not deployed; design-evaluation artifact only
