---
title: "Aplomb.Calm · Ginger Gummy Pouch — Supplier Specification v1"
date: 2026-05-11
---

# Aplomb.Calm — Supplier Specification

Stand-up pouch, 30-count ginger gummy. This document is the source of truth for the supplier on every fabrication, print, and label-content decision. The accompanying artwork files are authoritative for typography and layout; this document is authoritative for material, dimension, and process.

## 1. SKU summary

| Attribute | Value |
|---|---|
| SKU | APL-CALM-30P-V1 |
| Product name | Aplomb.Calm (ginger gummies for GLP-1 nausea) |
| Net weight | 90 g |
| Count | 30 gummies @ ~3 g each |
| Serving | 2 gummies (15 servings per pouch) |
| Shelf life target | 24 months from manufacture date |
| Storage | Cool, dry, out of direct light |

## 2. Pouch fabrication

| Attribute | Value |
|---|---|
| Format | Stand-up flat-bottom pouch (gusseted) |
| Face dimensions | **120 mm W × 190 mm H** |
| Gusset depth | **50 mm** |
| Bleed | **3 mm all sides** (artwork canvas 126 × 196 mm) |
| Safe zone | 6 mm inset from bleed (typesetting area 114 × 178 mm) |
| Substrate | PET 12 µm / Alu 8 µm / LDPE 100 µm laminate |
| Outer finish | **Matte** (no gloss varnish) |
| Recyclability target | CEFLEX-compatible mono-material laminate where feasible |
| Closure | Press-to-close zip-lock |
| Tamper evidence | Tear-notch, right edge, **35 mm from top** |
| Hang hole | Optional — top-center, 6 mm Ø, 4 mm from bleed edge |

## 3. Print specification

| Attribute | Value |
|---|---|
| Process | 4-color CMYK process |
| Finish | Matte varnish overall |
| Foils / spot colors | None |
| Bleed | 3 mm on every edge |
| Registration tolerance | ±0.3 mm |
| Maximum total ink coverage | 280% |

### Color values (CMYK · sRGB reference)

| Token | sRGB hex | CMYK | Where used |
|---|---|---|---|
| Bone substrate | `#f7f1e6` | 3 / 4 / 10 / 0 | pouch background |
| Ink | `#1a1512` | 47 / 45 / 44 / 55 | body type, Supp Facts panel rules and type |
| Amber | `#7a3d14` | 0 / 60 / 94 / 37 | brand period, plumb-bob mark, section rules |
| Ink at 60% | `#6e6864` | 28 / 27 / 26 / 33 | FDA disclaimer only |

> sRGB hex values are provided for digital reference; **CMYK is authoritative** for press. Convert using GRACoL 2013 (CRPC6) characterized reference printing condition. Pure black (CMYK 0/0/0/100) is **not used anywhere** — Ink is a warm rich black.

## 4. Typography

| Use | Font | Weight | Style |
|---|---|---|---|
| Wordmark · "Aplomb." | Cormorant Garamond | 500 | Italic |
| Section labels · "Why Calm.", "Directions.", "Warnings." | Cormorant Garamond | 500 | Italic |
| Supplement Facts headers and body | IBM Plex Sans | 700 / 400 | Roman |
| All body copy | IBM Plex Sans | 400 / 500 | Roman |
| FDA disclaimer | IBM Plex Sans | 400 | Italic |

**Minimum type sizes (hard limits):**

- 5 pt — FDA disclaimer
- 6 pt — all other body copy
- 8 pt — Supplement Facts column headers and primary nutrient labels

**Glyphs are outlined to paths** in the submitted SVG and PDF. There is no live text in the artwork files; the supplier does not need to install fonts. Confirm in Acrobat: File → Properties → Fonts list is empty.

## 5. Label content (back panel)

The back panel reproduces, in order:

1. Plumb-bob mark + "Aplomb." wordmark + "Ginger gummies for GLP-1 nausea" tracked subhead
2. *Why Calm.* — one-paragraph brand line
3. **Supplement Facts** panel (FDA 21 CFR 101.36 format)
4. **Other Ingredients** line
5. Allergen + format declaration
6. *Directions.* and *Warnings.* — two adjacent columns
7. Storage line · *Made in [COUNTRY — TBD]* · Distributed-by block
8. FDA disclaimer (italic, 60% ink)
9. UPC imprint zone (36 × 14 mm, dashed outline)
10. Lot / Best-By imprint zone (50 × 14 mm, dashed outline)

## 6. File checklist (delivered)

| File | Purpose |
|---|---|
| `Aplomb_Calm_Back_Label.svg` | Vector source, glyphs outlined |
| `Aplomb_Calm_Back_Label.pdf` | Print-ready PDF, embedded subset fonts |
| `Aplomb_Calm_Back_Label.png` | High-res raster preview |
| `Aplomb_Calm_Pouch_Schematic.pdf` | Dieline + bleed/safe diagram with dimensions |
| `mockup_back_composite.jpg` | Photoreal back-of-pouch reference |
| `mockup_front_back_hero.jpg` | Photoreal front+back marketing reference (not for print) |

The supplier should not receive any source PSD, AI, or Sketch file — there are none. All artwork is generated programmatically from `build_back_label.py` and `build_schematic.py` in the project repository.

## 7. Pre-press checklist (supplier confirms before plate)

- [ ] CMYK conversion applied with GRACoL 2013 reference profile
- [ ] All four color values match the table above within ΔE < 3
- [ ] Bleed verified at 3 mm on all four edges
- [ ] Tear notch position centered on right edge, 35 mm from top
- [ ] UPC imprint zone left as dashed-outline placeholder (supplier prints actual UPC)
- [ ] Lot / Best-By imprint zone left as dashed-outline placeholder (supplier prints variable data at fill)
- [ ] Matte varnish overall, no glossy spot UV
- [ ] No live text in PDF (Acrobat font list empty)

## 8. Open items — Aplomb Health to confirm before plate

These are bracketed `[TBD]` in the current artwork and must be filled before the supplier commits to plate:

1. **Distributed-by entity** — legal entity name and US street address for the "Distributed by" block.
2. **Country of manufacture** — *Made in [COUNTRY]* string.
3. **UPC / GTIN** — 12-digit GS1 code if pre-assigned, otherwise confirm supplier-imprint flow.
4. **Lot / Best-By print flow** — confirm whether supplier ink-jets at fill, or whether Aplomb supplies pre-printed pouches with this data pre-applied.
5. **Per-gummy ginger extract dose** — current artwork states 1 g (1000 mg) ginger root extract (5% gingerols) per 2-gummy serving = 500 mg per gummy. Confirm with formulator before plate.
6. **Customer service contact** — confirm `hello@getaplomb.com` is the surfaced contact, or supply an alternative.
7. **Country-of-origin label compliance** — if manufactured outside the US, confirm Customs and Border Protection country-of-origin marking position and language.

## 9. Aplomb Health — point of contact

- Brand owner: Aplomb Health, Inc. (operating brand name **APLOMB.**)
- Website: getaplomb.com
- Email: hello@getaplomb.com
- Project lead for this SKU: [PROJECT LEAD — TBD]
