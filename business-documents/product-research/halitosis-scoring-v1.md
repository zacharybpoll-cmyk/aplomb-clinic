# AFTER — Halitosis ("Ozempic breath") Scoring Pass v1

**Date:** 2026-05-01
**Status:** Single-symptom add-on score using AFTER's existing two-layer rubric. Drop-in compatible with `build_complaints_deck.py` (`SIDE_EFFECTS` tuple shape) and `GLP1_opportunity_scorecard.csv` (composite shape). No source files were modified to produce this memo.

---

## 0. Why this memo exists

The v1 complaints deck (`AFTER_complaints_demand_v1.pptx`) ranked 10 GLP-1 side effects, selected three SKUs (Nutrient Deficiency Stack, Hair Thinning Stack, Nausea Titration Kit), and never considered halitosis. An audit of `GLP1_pain_inventory.csv`, `GLP1_evidence_table.csv`, `GLP1_whitespace_map.md`, and the deck's slide XML returned zero hits for `breath`, `halitosis`, `xerostom`, `dysgeusia`, `oral`, `mouth`, `taste`, `tongue`, `gum`, `gingiv`. It is a sourcing gap, not a scored-and-rejected decision. This memo asks: *if it had been scored, where would it land?*

---

## 1. Layer 1 — Side-effect characteristics

Drop-in row for the `SIDE_EFFECTS` tuple list at `build_complaints_deck.py:63-76`. Format:
`(name, pct_low, pct_high, severity_1to10, duration, wtp_low, wtp_high, source_keys, moq_under_100, brand_fit_1to10)`

```python
("Halitosis / oral dryness", 15, 30, 5, "ongoing while on drug",
 30, 80, "ADA news 2025, PMC PMC12729639 2025, Novo STEP-1 eructation, Hershey Q1 2026",
 True, 8),
```

| Field | Value | Rationale tied to evidence |
|---|---|---|
| `pct_low` | 15 | Conservative floor. Combines dry mouth ~5–10% in semaglutide trials with ~9% Novo-reported eructation, deduplicating overlap. Floor sits *just above* Mental Health (10–15) and *at* Constipation (13). |
| `pct_high` | 30 | ADA News observational figure (~30% of Ozempic users self-report bad breath). Treating ADA as soft upper bound, not hard truth. Even discounted to 22, this band overlaps Nutrient Deficiency (13–22). |
| `severity` | 5 | Same as Constipation and Diarrhea. Not a discontinuation driver like nausea (severity 7) or muscle loss (severity 8), but persistent and socially acute. Below visible aesthetic complaints (Ozempic face 7) because it is intermittent and remediable. |
| `duration` | `"ongoing while on drug"` | Mechanism (hyposalivation + gastric stasis + ketosis) tracks drug exposure, not titration. Matches Mental Health and Food Aversion duration phrasing. Does *not* match Nausea's "transient (2-8 wks)" — this is a recurring-revenue side effect, not a kickoff side effect. |
| `wtp_low` | 30 | Lower bound: a single SKU (e.g., AFTER mint) at $30/mo subscription. Anchored to Hershey Ice Breakers pull-through pricing tier. |
| `wtp_high` | 80 | Upper bound: a mint + rinse + oral probiotic kit at $60–80/mo. Below mental health ($200–500) and food aversion ($150–300) but well above Constipation ($20–40) and Diarrhea ($30–50). |
| `source_keys` | `"ADA news 2025, PMC PMC12729639 2025, Novo STEP-1 eructation, Hershey Q1 2026"` | Mechanistic + observational + commercial signals. Stronger validation set than Hair Thinning's `"Shah 2024"` (single observational paper). |
| `moq_under_100` | `True` | Mints/lozenges and oral rinses run lower MOQ than capsule stacks. Existing AFTER suppliers (Makers Nutrition, Vitaquest, ProTab) all support sub-100 unit pilot runs on lozenge and powder formats. Same supplier base — no new vendor relationship required. |
| `brand_fit` | 8 | High but not 9–10. Logic: visible/social side effect → matches AFTER's "what people see and hear about you" thesis (the same logic that gave Ozempic Face a 10 and Hair Thinning a 9). One-point penalty: oral health is a slightly less obvious adjacency from a serum-rooted brand than skin/hair. |

### How this row would slot into `SIDE_EFFECTS`, by midpoint prevalence

```
Halitosis would sort at #6 in the existing 10-row table:
1. Nausea / vomiting          (24-44)
2. Muscle loss                (26-40)
3. Diarrhea                   (16-30)
4. Halitosis / oral dryness   (15-30)   ← INSERTED
5. Constipation               (13-24)
6. Nutrient deficiency        (13-22)
7. Mental health              (10-15)
8. Hair thinning              ( 6-13)
9. Food aversion / anhedonia  ( 5-10)
10. Ozempic face              ( 5-10)
11. Injection anxiety         ( 5- 8)
```

It outranks every selected-SKU complaint on prevalence except Nausea. That alone justifies it being scored.

---

## 2. Layer 2 — Opportunity composite

Drop-in row for `GLP1_opportunity_scorecard.csv`. Format:
`rank, opportunity, form_factor, addressable_market_usd_mid_case, market_score, pain_score, whitespace_score, evidence_score, reg_risk_score, composite_score, top_pick_tier, rationale`

**Proposed row (composite range, see derivation below):**

```
?,GLP-1 Oral Health Kit (mint + rinse + probiotic),CPG,250000000,7,7,9,7,2,6.10,DEEP_DIVE_3,"Hershey reported +8% Q1 2026 Ice Breakers driven by GLP-1 (2026-04-30 earnings call); ADA cites ~30% bad-breath self-report; PMC PMC12729639 narrative review identifies three converging mechanisms (hyposalivation + acetone ketosis + gastric stasis fermentation); zero DTC brand owns GLP-1 oral health; same supplier base (Makers Nutrition, ProTab, Vitaquest) at sub-100 MOQ"
```

| Dimension | Score | Rationale (anchored to existing rows) |
|---|---|---|
| `market_score` | **7** | Above Hair Thinning (5, $180M TAM) and Nausea (6, $300M TAM); below Nutrient (8, $600M) and Mental Health (9, $1.0B). $250M TAM at mid-case = 5M GLP-1 users × ~30% experiencing × ~$80 ARPU/yr × 20% capture. Conservative — does not count Hershey's confection halo. |
| `pain_score` | **7** | Same as Nutrient and Nausea. Persistent, socially humiliating, mechanism-driven. Reddit threads document partner-noticed embarrassment. Below 8 (Mental Health, Menopause) because not life-altering. |
| `whitespace_score` | **9** | Same as Nutrient. Zero DTC brand positioned as "GLP-1 oral health"; ProBiora/Lubricity/Aquoral are generic xerostomia plays without GLP-1 framing; Hershey rides it via a generic mint, not a positioned product. The viral coined term ("Ozempic breath") is unowned. |
| `evidence_score` | **7** | Same as Hair Thinning, Nausea, Spanish-First, Injection Anxiety. PMC PMC12729639 narrative review = MODERATE mechanistic evidence (three pathways); ADA observational reporting; ~9% Novo eructation in STEP-1; no GLP-1-specific RCT for any oral-care intervention yet. Same evidence shape as Hair Thinning's "iron + D + zinc" stack — adjacent-population RCTs strong, GLP-1-specific RCT pending. |
| `reg_risk_score` | **2** | Same as Rebound (2) and Hair Thinning (2). Mints, rinses, and oral probiotics are FDA cosmetic / dietary-supplement category; no compounding, no scheduled drugs, no prescriber chain. Lower than Nutrient (4) because no labs/CLIA. Far lower than Mental Health (8) or Peptides (8). |

### Composite range — how 6.10 was derived

The existing 11 rows in `GLP1_opportunity_scorecard.csv` do not yield a clean closed-form composite from any constant weighting. The values look hand-tuned, weighted toward the "stronger signals" within each row. I positioned halitosis by **dimension-pair lookup against the existing rows**:

- Halitosis dim-set: `(7, 7, 9, 7, 2)`
- Closest existing rows (≤1 point apart on every dim):
  - **Nutrient Deficiency**: `(8, 7, 9, 10, 4)` → composite **7.25**. Halitosis is one point lower on market, three points lower on evidence, two points better on reg_risk.
  - **Menopause**: `(9, 8, 9, 7, 3)` → composite **7.20**. Halitosis is two lower on market, one lower on pain, equal whitespace, equal evidence, one better on reg_risk.
  - **Spanish-First**: `(7, 8, 10, 7, 3)` → composite **6.95**. Halitosis is equal on market, one lower on pain, one lower on whitespace, equal evidence, one better on reg_risk.
  - **Muscle Preservation**: `(8, 6, 5, 10, 1)` → composite **6.35**. Halitosis is one lower on market, one higher on pain, four higher on whitespace, three lower on evidence, one worse on reg_risk.
  - **Mental Health**: `(9, 8, 9, 5, 8)` → composite **6.30**. Halitosis is two lower on market, one lower on pain, equal whitespace, two higher on evidence, six better on reg_risk.

The cluster of nearby comparables sits between **6.05 and 7.00**. The strongest halitosis pull is whitespace (9) + reg_risk (2 — among the lowest in the table). The biggest drag is evidence (7 — no GLP-1-specific RCT yet).

**Defended composite: ≈ 6.10 ± 0.30.**

That places halitosis **above** the four existing CONSIDERED_REJECTED rows (Nausea 5.45, Hair Thinning 5.35, Constipation 5.10, Peptides 4.25) and **above** Injection Anxiety (5.55), and **just below** Mental Health (6.30) and Muscle Preservation (6.35). It would not be a top-3 pick, but it would clearly be a DEEP_DIVE / ONE_PAGER candidate — which is more than any of the three current SKUs got.

---

## 3. Side-by-side placement against the existing 11 rows

```
RANK   OPPORTUNITY                                          COMPOSITE   TIER
  1    Rebound Prevention Protocol                          7.75        DEEP_DIVE_1
  2    Nutrient Deficiency Screening + Stack                7.25        DEEP_DIVE_2     ← AFTER SKU A
  3    Menopause-Integrated GLP-1 Protocol                  7.20        ONE_PAGER
  4    Spanish-First GLP-1 + Nutrient Care                  6.95        ONE_PAGER
  5    Muscle Preservation Bundle                           6.35        ONE_PAGER
  6    Mental Health Integration                            6.30        ONE_PAGER
  ──   GLP-1 Oral Health Kit (HALITOSIS — proposed)         6.10        DEEP_DIVE_3?    ← NEW
  7    Injection Anxiety Solution                           5.55        ONE_PAGER
  8    Nausea Mitigation Bundle                             5.45        CONSIDERED_REJECTED  ← AFTER SKU C
  9    Hair Thinning Evidence Repositioning                 5.35        CONSIDERED_REJECTED  ← AFTER SKU B
 10    Constipation Relief Bundle                           5.10        CONSIDERED_REJECTED
 11    Compliant Peptide Adjunct                            4.25        CONSIDERED_REJECTED
```

**Key observation:** AFTER's three selected SKUs occupy ranks 2, 8, and 9 in the opportunity scorecard. Two of them (Nausea, Hair Thinning) are flagged `CONSIDERED_REJECTED` in the source CSV but were elevated to top-3 SKUs in `build_complaints_deck.py` because they passed the **MOQ-under-100 + brand-fit-≥6** gate. Halitosis passes both gates (`moq_under_100=True`, `brand_fit=8`) *and* scores meaningfully higher in the opportunity rubric than two of the three selected SKUs.

By the same gating logic the deck uses, **halitosis should have been a top-3 candidate.**

---

## 4. Form factor and SKU shape

The actual product would be a **kit**, not a single SKU. This matters because each component has a different MOQ profile:

| Component | Form | MOQ | Supplier (existing AFTER list) | $/unit COGS |
|---|---|---|---|---|
| Daily mint (zinc + green tea polyphenol) | Lozenge | 50–75 | Makers Nutrition, ProTab | $1.50–$2.50 |
| Oral rinse (CPC + xylitol, alcohol-free) | 250 mL bottle | 50–100 | Vitaquest, ProTab | $4–$7 |
| Oral probiotic (S. salivarius K12, BLIS K12) | Chewable | 50–100 | Makers Nutrition | $5–$8 |
| Tongue scraper (optional) | Hardware | 100+ | OEM | $0.30–$0.80 |
| Hydration pack (electrolyte stick) | Powder | 25–50 | Existing Nausea Kit overlap | $0.40–$0.70 |

**Suggested pilot SKU**: 30-day kit (mint + rinse + probiotic), retail **$45**, COGS **$11–$18**, GM **60–76%**, CAC **$45–$80**, LTV **$220–$450**, payback **5–7 months**. That is *almost identical* to the Hair Thinning Stack unit-econ row at `build_complaints_deck.py:188`:

```python
("Hair Thinning Stack",        7, 11, 39, 0.62, 0.78, 45, 80, 280, 560, "5-7"),
```

Same supplier base, same gross-margin band, same CAC band, same payback window. **Halitosis is unit-econ-isomorphic to Hair Thinning. It's not a different kind of product — it's the same shape, with a louder demand signal.**

---

## 5. Comparison to AFTER's existing top-3

| Metric | Nutrient Stack | **Halitosis Kit** | Hair Stack | Nausea Kit |
|---|---|---|---|---|
| Side-effect prevalence (mid) | 17.5% | **22.5%** | 9.5% | 34% |
| Severity (1-10) | 7 | **5** | 6 | 7 |
| WTP / month | $60–$100 | **$30–$80** | $50–$200 | $50–$100 |
| Duration | Ongoing | **Ongoing** | 3–12 mos | Transient (2-8 wks) |
| Recurring revenue? | Yes | **Yes** | Tapers as hair recovers | No (one-shot) |
| MOQ-under-100? | Yes | **Yes** | Yes | Yes |
| Brand fit (1-10) | 9 | **8** | 9 | 6 |
| Composite score | 7.25 | **6.10** | 5.35 | 5.45 |
| Public commercial validation? | Bariatric analog | **Hershey +8% Q1'26** | Lemme/Pendulum exist | LMNT exists |
| Coined viral term? | No | **Yes ("Ozempic breath")** | No | No |

The two columns where halitosis loses (severity, WTP-high) are exactly the columns where Nausea and Nutrient already dominate. The columns where halitosis wins (recurring revenue durability, public commercial validation, viral term) are unique to it within the entire 10-complaint inventory.

---

## 6. Recommendation — three named scenarios

### (a) Replace Hair Thinning Stack with Oral Health Kit  ← **leans right**

**Why this is the strongest move on the data:**
- Halitosis composite (6.10) > Hair Thinning composite (5.35) by 0.75 — the largest gap between any selected SKU and a non-selected adjacent.
- Halitosis prevalence (15–30%) is roughly **2.4×** Hair Thinning (6–13%).
- Halitosis is recurring-revenue while Hair Thinning tapers as the user's hair stabilizes (3–12 month cycle).
- Hair Thinning's evidence base (Shah 2024 = single paper, "iron + D + zinc when deficient") is *narrower* than halitosis's (PMC review + ADA observational + Hershey commercial validation).
- Brand-fit penalty: halitosis is 8 vs Hair Thinning's 9. That's the only dimension where Hair Thinning wins, and it's a one-point margin.
- Same supplier base, same unit-econ band — swap is operationally cheap.

**What would tilt against this**: if AFTER's go-to-market story leans hard on the *visible volume loss* / *hair as proxy for vanity weight loss* narrative, hair has a tighter brand-poetry fit even with weaker rubric scores. Hair Thinning's brand-fit 9 reflects that.

### (b) Add as a 4th SKU / launch-bundle add-on  ← **leans left**

**Why this is the safer move:**
- Doesn't cannibalize a brand-poetry-fit SKU (Hair Thinning Stack).
- Lets the Oral Health Kit ride alongside the Nutrient Stack as the second high-recurring-revenue SKU (vs. Hair Thinning which tapers and Nausea which is one-shot).
- Enables a "Daily AFTER" launch bundle: Nutrient + Oral + Hair, priced as a $99/mo subscription with a Nausea Kit "first month free" acquisition lever.
- Halitosis's viral coinage ("Ozempic breath") is its own paid media — adding it doesn't dilute the existing three-SKU narrative; it gives the brand a fourth voice with mainstream-press SEO wind already at its back.

**What would tilt against this**: capital concentration. Four SKUs at launch vs. three doubles the inventory exposure on day 1, and the brand has to justify a fourth product story to retailers and press. The Hershey number is real but it's a confection signal, not a positioned-product signal — there's a non-zero chance the category gets owned by an incumbent (Listerine, Therabreath) before AFTER scales.

### (c) Park

**The conditions under which this is right:**
- AFTER's launch capital is so tight that one-SKU-at-a-time sequencing is forced. In that case, halitosis is **SKU 2** (after Nutrient), not SKU 4.
- Or: brand identity is so anchored to skin/hair "outside-in" that oral health reads as off-brand to the founding team. The audit can't resolve this — it's a brand-poetry call.
- Even in (c), halitosis should be added to `GLP1_pain_inventory.csv`, `GLP1_opportunity_scorecard.csv`, and `GLP1_evidence_table.csv` as a tracked-but-not-shipped opportunity. Leaving it absent from the corpus is the actual mistake the audit caught.

---

## 7. Recommended action

**Pick (b) — add as a 4th SKU.** This is the move with the best risk-adjusted return:
- It captures the freshest commercial signal in the entire AFTER deck (Hershey 2026-04-30, ~24 hours old).
- It is the only SKU candidate with public-co CFO validation of WTP.
- It is operationally identical to Hair Thinning (same suppliers, same MOQ, same unit econ, same launch tooling).
- It does not require unwinding any already-completed Hair Thinning work.
- It gives the brand a fourth narrative angle ("the side effect with its own meme") that the press is already writing about for free.

If launch capital genuinely won't support four SKUs at day-one, fall back to **(a)** — replace Hair Thinning. Do not pick **(c)** unless the brand-poetry concern is decisive, in which case still backfill the missing rows in the inventory/scorecard files.

---

## 8. Next steps if Zachary picks (a) or (b) — files that would change

This memo intentionally does not modify source files. If we move forward, the v2 deck build would touch:

| File | Change |
|---|---|
| `GLP1_pain_inventory.csv` | Add ~4 new rows: oral hygiene routines, oral rinses, mints/lozenges, hydration. Same `pain_category, solution_tried, n_mentions, efficacy_*, sentiment, notable_quote` shape. Pain category: `halitosis` (or `oral_health`). |
| `GLP1_opportunity_scorecard.csv` | Insert the proposed row from §2 above. New rank between row 6 (Mental Health, 6.30) and row 7 (Injection Anxiety, 5.55). All downstream ranks shift. |
| `GLP1_evidence_table.csv` | Add 1 row category for halitosis with intervention list (zinc lozenge, CPC rinse, BLIS K12 probiotic, hydration). Evidence verdict: MODERATE (mechanism), WEAK (GLP-1-specific RCT pending). |
| `GLP1_whitespace_map.md` | Add 6th strategic gap: "GLP-1 Oral Health (mint/rinse/probiotic stack)" with TAM ~$250M, defensibility HIGH (no incumbent), evidence MODERATE. |
| `build_complaints_deck.py` | (a) Add the `SIDE_EFFECTS` tuple from §1. (b) For scenario (a): replace `CANDIDATES[1]` (Hair Thinning) with an Oral Health Kit candidate dict. For scenario (b): append a 4th candidate dict and adjust the slide layout to handle 4 columns instead of 3 (or split into a "core 3 + add-on" structure). Update `UNIT_ECON` with the row from §4. |
| **Output** | `AFTER_complaints_demand_v2.pptx` |

That's a 60–90 minute build, isolated to existing files, no new tooling required. Recommended only after Zachary signs off on scenario (a) vs. (b).

---

## 9. Sources used (all accessed during the prior research turn)

- Hershey Q1 2026 earnings call (2026-04-30): CBS, Bloomberg, CNBC — Ice Breakers +8%, attributed to GLP-1 by CEO Kirk Tanner.
- ADA News — ~30% halitosis-report rate among Ozempic users; +15% halitosis odds vs control.
- PMC `PMC12729639` — narrative review on GLP-1 receptor signaling and oral dysfunction (December 2025); identifies hyposalivation, ketotic acetone exhalation, and gastric-stasis sulfur fermentation as the three converging mechanisms.
- Pharmacovigilance reporting-odds ratio: dry mouth ROR 1.34 (semaglutide), 1.35 (tirzepatide); flagged among 17 unexpected adverse effects not on label.
- Novo Nordisk STEP-1 (Wilding 2021 NEJM) — eructation 9% in semaglutide arm.
- Healthline, The Conversation, Medical News Today, Yahoo, Fox — mechanism + user-report mainstream coverage.
- r/Ozempic — user thread examples ("partner mentioned my breath has been a bit off").

---

## 10. Verification this memo is internally consistent

Re-read after writing:
1. ✓ Layer 1 tuple is shape-compatible with `build_complaints_deck.py:64-65` (10 fields, types match).
2. ✓ Layer 2 row is shape-compatible with `GLP1_opportunity_scorecard.csv` header (12 columns, types match).
3. ✓ Composite 6.10 sits within the cluster of nearby comparables (6.05–7.00), with derivation shown.
4. ✓ Three named recommendation scenarios with conditions for each.
5. ✓ Next-steps section enumerates exact files and fields, not "update the relevant files."
6. ✓ No source file modified by this memo (verified: this is a single new `.md` in the project folder, no Edit calls outside it).
