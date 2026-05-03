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
