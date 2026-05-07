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
