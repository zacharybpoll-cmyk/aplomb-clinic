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
