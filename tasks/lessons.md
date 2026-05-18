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

## 2026-05-16 — Design-mockup builds: bake brand bans into the template, not the cleanup
- Wrote file 01 with em dashes + literal "Ozempic"-titled citations, then had to scrub. Cost a fix pass before replicating.
- **Rule**: before forking a reference mockup into N variants, run the banned-token grep (em dash `—`, drug trademarks, `Inter`, `#5B8DB8`/cool hexes, emoji/arrows) on the reference FIRST and fix there, so the corrected copy propagates. En dashes in numeric ranges (`2169–2178`, `30–50%`) are correct typography, not the AI tell — keep them; only em dashes are banned.
- Playwright MCP profile can be locked ("Browser is already in use"); never pkill it. Fall back to claude-in-chrome MCP. `localhost` navigates without the 127.0.0.1 permission prompt.
- Slide-in drawer screenshots taken immediately after the open click look "clipped/undimmed" — it's mid-transition, not a bug. Confirm with getBoundingClientRect (left/right vs innerWidth) before chasing a phantom overflow.
