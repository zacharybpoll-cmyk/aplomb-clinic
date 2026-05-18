# Aplomb Project — Lessons Learned

## 2026-05-03 — PowerPoint Build Pattern for Supplier Decks

**Key Pattern Verified:**
- python-pptx post-save scrub is non-negotiable for professional decks
- The 4 artifacts (sldSz type, printerSettings, stale date, smtClean) will cause PowerPoint repair prompt
- Pattern from build_complaints_deck.py (verified working 2026-04-28) is reusable across all python-pptx projects
- Hyperlinked tables work correctly in python-pptx via `run.hyperlink.address`

**Supplier Data Consolidation:**
- Parallel research agents can validate supplier URLs and MOQ constraints
- Manual consolidation into JSON is faster than parsing agent JSONL output when agents don't return structured format
- URL validation via WebFetch is critical before embedding supplier links in deck

**MOQ Gate Logic:**
- Hard constraint: MOQ ≤ 100 units OR total MOQ cost < $250
- All 15 suppliers across 5 categories must be verified against this gate before deck generation
- Post-generation audit confirms compliance

**Design & Brand Compliance:**
- Bone canvas (#F5F4F0) + near-black text (#1A1D21) + monochrome design = strong visual consistency
- Playfair Display (54pt bold) for slide titles, Inter (14-24pt) for body creates clear hierarchy
- Tables with 8 columns fit cleanly in 10" × 5.625" slides (16:9) without overflow

---

## 2026-05-06 — Parallel Multi-Lane Research Consolidation Pattern

**Context**
Conducted three-lane parallel research for hair-loss product sourcing (Lane A: Supliful + low-MOQ suppliers; Lane B: multi-deficiency collagen; Lane C: topical serums + format-shifters). User required sourcing to respect hard MOQ constraint (≤100 units OR <$250 total cost) and beat Vox baseline (46/100) on 7-dimension rubric.

**Pattern Verified**
- **Two-tier sourcing model works:** Trial tier (MOQ-gate compliant) vs. scale-up tier (exceeds gate but superior clinical profile). Custom Nutra 48-unit trial ($84) gates entry; Lief Labs 10K unit run ($10K) becomes post-validation scale-up.
- **Consolidation before Lane A completion is viable:** Even with one lane pending, consolidating completed lanes + flagging pending lane creates actionable report ready for Phase 1 execution. Final merge-pass can be deferred.
- **Critical Gate Identification:** Only 2 of 9 candidates pass hard MOQ constraint (Custom Nutra, FormuNova marginal). Identifying this early shaped all strategic recommendations. Reporting constraint tension explicitly (not hiding it) is essential.
- **Biotin threshold analysis (2.5mg assay-interference cutoff) should be documented per-candidate:** Creates defensible clinical safety rationale for each formulation.
- **SMP Nutra reformulation request is highest-impact opportunity identified:** Gummy format + 22-point rubric boost if reformulation approved. Worth prioritizing supplier outreach.

**Recommendations for Future Multi-Lane Research**
1. Consolidate as lanes complete (don't wait for all three)
2. Explicitly flag pending lanes with expected deliverables documented
3. Frame MOQ gate tension as strategic choice (trial + scale-up) not as failure
4. Perform clinical evidence consolidation as research progresses (don't defer)
5. Include Phase 1 action list in consolidated report, ready for execution without further planning

**Errors to Avoid**
- Don't hide MOQ gate compliance failures; make them explicit and frame as design choice
- Don't bury reformulation opportunities; surface highest-impact suppliers immediately
- Don't assume Lane completion will happen on schedule; design reporting for partial delivery

---

## 2026-05-15 — Production smoke harness (scripts/smoke*.{sh,mjs})

**Reusable verification patterns:**
- `npm run smoke` / `:browser` / `:webhook` re-runs the full launch battery; run it after any prod-affecting change before claiming done.
- getaplomb.com is an SPA 200-fallback: assert on response **body** (page-unique marker), never status code. A 404-that-200s passes a status check silently.
- CF zone clamps asset `max-age` (0 → 14400). Assert `cache-control` *contains* `must-revalidate` (the directive `_headers` controls), never an exact max-age. A lingering pre-fix `immutable` entry on the *bare* asset URL is a WARN, not FAIL — live HTML is `DYNAMIC` and references the `?v=` URL.

**Bugs to avoid (cost iterations this session):**
- `set -o pipefail` + `curl | grep -q`: grep -q exits on first match, SIGPIPEs curl (141), pipefail false-fails large pages. Always capture body to a var, then match.
- Meta CAPI access tokens are event-ingestion-scoped: dataset-node GET → `(#100) Missing Permission`. Liveness probe = `POST /events` with a `test_event_code` (any string; Test Events tab only, zero pollution).
- `wrangler dev` scheduled triggers need `--test-scheduled` AND ~8s workerd cold-start before `/__scheduled?cron=...` works; a POST-only Pages fn 404s on a GET readiness probe (probe with POST).
- Tier W against PROD Supabase is safe ONLY with synthetic sentinel rows + a `trap` teardown that runs on ANY exit; ALWAYS independently re-query post-run to prove zero residue + inventory restored. Never solicit `SUPABASE_SERVICE_ROLE_KEY` into chat (full-DB credential); env-gate + SKIP instead.

---

## 2026-05-15 — Apple Pay on a Stripe + custom-domain (CF Pages) site

**Root cause of `canMakePayment()` → `{"applePay":false,...}` despite Stripe Dashboard showing the domain "enabled":**
- Apple verifies the domain by fetching `https://<domain>/.well-known/apple-developer-merchantid-domain-association`. If that path 404s, Apple never verifies → `applePay:false` forever, even with the payment method toggled on and the domain listed in Stripe.
- Stripe's modern Payment Method Domains flow ("Stripe handles merchant validation behind the scenes", no Dashboard download button) does **NOT** auto-host this file for a custom Cloudflare Pages domain. You MUST self-host it.
- The file is Stripe's **canonical public blob**, identical for every merchant: `curl https://stripe.com/files/apple-pay/apple-developer-merchantid-domain-association` (9094 bytes, hex `{"pspId":...}`). Not a secret — safe to commit.
- Serve it as a **direct 200, `text/plain`, NO redirect** (a redirect fails Apple's check). On CF Pages: a real static file at `website/.well-known/...` + a `_headers` content-type rule (mirror the `/llms.txt` rule).

**Process errors that cost this + prior sessions (do not repeat):**
- NEVER conclude "the 404 on .well-known is fine / Stripe auto-hosts it." That theory was wrong and caused multi-session whiplash. Verify the authoritative signal first: `canMakePayment()` in real Safari + `curl` the well-known path. Two facts (path 404 + `applePay:false`) = definitive.
- The bare `paymentRequest().canMakePayment()` snippet is the right isolator (account+domain+device only, no PaymentIntent). `link:true` proves Stripe.js + publishable key are fine, so a `false` alongside it points at domain/account config, not code.
- Stripe Dashboard is MCP-navigation-blocked (financial-site safety). Don't promise to "look at it via MCP" — pull the fix from official docs / Stripe's canonical file URL and DO it in the repo instead.
- Production deploy of an agent-inferred fix to a live commerce site needs **explicit founder approval in chat** (the auto-mode classifier will and should block auto-merge). Stage everything in an isolated `git worktree` off `main` (never disturb founder WIP), open the PR, then wait for "merge it."

---

## Session 2026-05-17 — Midi redesign (live site)

- **Scripted copy cleanup must be LOCALIZED.** A global `re.sub(r' {2,}', ' ', s)` added as a "punctuation tidy" in an em-dash purge collapsed every HTML indentation run → a 3900-line whitespace-mangle commit. Caught only because the diff stat read `3900 insertions / 3900 deletions` (1:1 = mass reformat, not targeted). RULE: after any scripted multi-file edit, sanity-check `git diff --stat`; a balanced huge count means you reformatted, not edited. Replacement regexes must match the token + its *immediately adjacent* whitespace only (`r' ?(&mdash;|—) ?'`), never a global whitespace normalizer on source files.
- **Re-skinning a mature stylesheet: override surface, never fight mechanics.** Appending a Midi layer (later same-specificity rules win) was the right low-risk move over a destructive rewrite. But my `.product-modal{position:fixed;inset:0;display:flex}` override fought the un-overridden original `translate(-50%,-50%)`+opacity centering mechanic and broke the modal. RULE: when restyling a pre-existing component you didn't fully read, change colors/radius/spacing only; leave position/transform/display/`.is-open` mechanics alone (new tokens flow into them automatically).
- **Inverting a section's bg requires resetting inherited `color`.** The dark→light footer flip left original `.foot{color:var(--paper)}` in force → wordmark/newsletter text invisible (light-on-light). Always reset `color` when you flip a background light/dark.
- **Cloudflare Pages Preview ≠ Production env.** Stripe/Supabase secrets bound to the Production environment are absent in branch/preview deployments (`metaKey:null` on preview, `present` on prod). A preview can't fully exercise gated commerce; this is config scoping, not a code regression. Verify such flows on production post-merge instead.
- **Check real branch/tree state before executing a plan that assumed clean main.** Repo was on `wip/product-brand` (5 ahead/10 behind, a "do NOT merge" logo commit, uncommitted edits). Stopped and asked rather than building on it; branched fresh off `origin/main`, parked the WIP in a labeled stash. Plan assumptions about VCS state are assumptions, not facts.
- **NEVER declare "fixed/verified" on local-only state when the user is judging a deployed preview.** Spent multiple rounds fixing the hero locally + screenshotting localhost and telling the user "it matches the mockup," while the user kept staring at the stale `midi-feedback-fixes` preview that had NONE of the fixes (probed live: still `min-height:780px`, `<br>`, serif lede). The user (rightly) concluded I "keep messing up." RULE: the source of truth for "done" is the **deployed preview rendered side-by-side with the design target**, not localhost. Don't report progress on invisible local state; either deploy it or say "fixed locally, not yet deployed — you can't see it yet."
- **Browser HTTP-caches `site.css` when linked with no `?v=`.** `index.html` links `/css/site.css` (no version query). `python3 -m http.server` serves fresh from disk, but the browser cache keyed the plain URL → Playwright kept rendering the OLD CSS after edits (`min-height:780px` persisted in computed style despite the file on disk being correct; page height identical pre/post edit was the tell). RULE: for local CSS verification serve with `Cache-Control: no-store` (one-liner: `H.end_headers=lambda s:(s.send_header('Cache-Control','no-store'),BaseHTTPRequestHandler.end_headers(s))`), and confirm a change took via `getComputedStyle`, never by screenshot alone.
- **Fidelity work needs a computed-style audit harness, not eyeballing.** Reactively finding one leaking original rule at a time (min-height, then hero-text padding, then lede font-family…) is endless whack-a-mole that reads as "rushing." RULE: when re-skinning to match a design source, render the source and the live page at the same viewport in Playwright and `getComputedStyle`-diff every layout-critical prop for every selector; fix every divergence in one pass; re-run until the diff is empty at 768/1440/1920. The override layer is correct architecture (JS mechanics live in the original CSS); the bug is that it was *incomplete*, and only an exhaustive diff proves completeness.

---

## 2026-05-17 — Serif-italic leak class + audit gotchas (post-deploy correction)

- **The "leaking original rule" bug has a SIGNATURE: every `.*-lede`/tag/sub paragraph where the Midi override set only color/size.** After the hero-lede fix shipped, a from-production computed-style sweep found 3 MORE identical leaks (`.cta-lede`, `.foot-tag`, `.checkout-modal .sub`). All rendered Cormorant-italic where the mockup is IBM Plex Sans normal, because the Midi override rule set color/font-size/margin but never re-stated font-family/font-style, so the original `font-family:var(--serif);font-style:italic` cascaded through (same specificity, earlier source). RULE: when you fix ONE leaking-serif-italic element, immediately sweep EVERY text element for `getComputedStyle().fontStyle==='italic'` plus a Cormorant/Garamond family check, and fix the whole class in one pass. Never assume the one you saw is the only one. Fix is to append `font-family:var(--sans);font-style:normal` to that component's existing Midi-layer rule (source-order wins; zero mechanics).
- **Always verify against the mockup before "fixing" a serif-italic, some are intentional.** `.cart-empty` ("Your bag is empty.") computes Cormorant-italic on prod AND in the mockup (mockup line 156 sets it on purpose). The detector is a candidate-finder; the mockup is the arbiter. `.confirm p` (mockup) has NO font override so it inherits sans-normal, making the live `.checkout-success p` Cormorant-italic a real defect. Decide each flagged element by the mockup's computed value, not the detector alone.
- **`/serif/.test(fontFamily)` FALSE-MATCHES `sans-serif`.** A leak-detector regex of `Cormorant|Garamond|serif` flags every sans element because the computed `font-family` string ends in `sans-serif`. The real signal is the first family token plus `fontStyle`. Detect with `fontStyle==='italic'` or a cormorant/garamond test on token[0]; drop bare `serif`. A regex that flags 100% of elements is the tell.
- **Changed-file safety greps need pre-existing-vs-introduced disambiguation.** Bumping the `?v=` css-link on 27 HTML files makes every page a "changed file"; a blanket drug/Inter/em-dash grep then lights up on pre-existing cited-trial titles (STEP-1, the Cleveland Clinic article links), benign `setInterval`/`Intervention`, and an old em-dash elsewhere in a 3000-line CSS. RULE: scope the regression grep to **added lines only** (`git diff | grep '^+'`), not whole changed files, before claiming a violation. Cited third-party article/trial names in an evidence section are approved content, not an APLOMB drug-naming violation.
- **CF asset cache makes a same-URL CSS redeploy invisible.** PR #43 added `?v=20260517`; a later PR changed `site.css` again but the URL `?v=20260517` was already CF-cached (max-age clamped 0 to 14400). A CSS content change with an unchanged `?v=` does NOT reach returning visitors for ~4h. RULE: every `site.css` content change must also bump the `?v=` token in the same commit, or the deploy is a silent no-op for exactly the people judging it.

---

## 2026-05-17 — Conversion remaining-5: verify state in code, never trust the audit summary

- **Migration numbering: never trust an Explore/summary count — `ls` the dir.** The exploration report said migrations were `0001–0004`; the tree actually had `0005_newsletter_welcome_sent_at.sql`. Had I trusted the summary, `0006_reviews.sql` would have collided as a second `0005`. RULE: before adding migration N+1, `ls supabase/migrations` in the worktree and take max+1 from the filesystem, not from any prose.
- **The first-order discount code is `APLOMB10`, not `WELCOME10`.** The plan/summary assumed `WELCOME10`; the live `newsletter-welcome` + `welcome-day-7` emails (and `_lib/newsletter.js`) already promise **`APLOMB10` — 10% off first order**, with zero redemption mechanism anywhere. PR-B (#8) MUST honor the code customers were already told (`WELCOME_COUPON_CODE` default `APLOMB10`, `WELCOME_COUPON_PCT` default `10`), and the Stripe promotion_code for the subscription path must be `APLOMB10`. Inventing `WELCOME10` would orphan every welcome email already sent.
- **`functions/checkout/_middleware.js` only injects the Turnstile site key for `/checkout/*`.** A reviews form on a PDP can't rely on Turnstile (no site-key meta there). The signed per-order HMAC token (`?rt=`) is the correct, stronger gate for PDP review submission — no CAPTCHA plumbing, no email enumeration. Turnstile-on-checkout server-verification is a real but *separate* gap (Explore found it) — track it as its own follow-up, do NOT bundle a payment-path change into the reviews PR.

---
