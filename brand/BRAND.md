# APLOMB. — Brand Identity

> "Self-confidence; assurance; composure; grace under pressure."
> The brand promise: *preserving your self through GLP-1 use.*

APLOMB. is a products-led DTC brand. It is the destination for women on GLP-1 medications (Ozempic, Wegovy, Mounjaro, Zepbound) who are managing the side effects nobody warned them about — facial volume loss, hair thinning, nausea, oral health.

This document is the single source of truth for the visual and verbal identity. Read it before doing any design, copy, or asset work.

---

## 1. Logo system

The logo has two parts: a **mark** and a **wordmark**. Both are sacred. Both are amber-accented.

### 1a. The mark — plumb-bob

A vertical amber thread ending in a triangular plumb-bob plummet. It draws the etymology *à plomb* — "according to the plumb line, staying upright." The customer's psychological project, made visible.

Canonical SVG file: [`assets/aplomb-mark.svg`](../assets/aplomb-mark.svg). `currentColor` so it inherits any context's amber.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 64" aria-hidden="true">
  <line x1="12" y1="2" x2="12" y2="38" stroke="currentColor" stroke-width="1.4" stroke-linecap="square"/>
  <path d="M 12 38 L 17.5 46 L 12 60 L 6.5 46 Z" fill="currentColor"/>
</svg>
```

**Mark color:** always deep amber `#7a3d14` (or `--amber-light` `#d9a06b` on dark backgrounds, e.g. footer).
**Mark dimensions:** native viewBox `24×64`. Render at intended size — never stretch, never recolor outside palette.
**Mark alone:** allowed for favicon, social avatar, packaging emboss, foil stamp.

### 1b. The wordmark

**Aplomb.** in **Cormorant Garamond, italic, 500 weight**, with a deep amber **period**.

- Cap-A only at the start ("Aplomb.") in the wordmark.
- All-caps **APLOMB.** allowed in body copy headlines and product naming ("APLOMB. Daily.")
- The period is sacred. Always present, always amber.

### 1c. Lockups

| Lockup | Use | Composition |
|---|---|---|
| **Inline** (mark left, wordmark right) | Nav, header bars, horizontal compact contexts | Mark height ≈ wordmark cap height, gap 10px |
| **Stacked** (mark above, wordmark below) | Footer, hero, packaging front, brand presentation | Mark height ≈ 1.5× wordmark height, gap 6px |
| **Mark-only** | Favicon, social avatar, foil stamp, embossed seal | Mark centered, generous breathing room |

```html
<!-- Inline lockup (used in nav) -->
<div class="logo">
  <svg class="mark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 64" aria-hidden="true">
    <line x1="12" y1="2" x2="12" y2="38" stroke="currentColor" stroke-width="1.4" stroke-linecap="square"/>
    <path d="M 12 38 L 17.5 46 L 12 60 L 6.5 46 Z" fill="currentColor"/>
  </svg>
  <span class="word">Aplomb<span class="dot">.</span></span>
</div>
```

```css
.logo { display: inline-flex; align-items: center; gap: 10px;
        font-family: var(--serif); font-size: 28px; font-weight: 500;
        letter-spacing: -0.02em; font-style: italic; line-height: 1; }
.logo .mark { width: 12px; height: 32px; color: var(--amber); flex-shrink: 0; display: block; }
.logo .dot { color: var(--amber); font-style: normal; }
```

**Reference image:** `Logo Designs/02-plumb-line-mark.jpg` is the canonical hero treatment of the stacked lockup. Selected as the default logo on 2026-05-02.

## 2. Color Palette

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#efe8dc` | Page background |
| `--paper` | `#f7f1e6` | Cards, surfaces, "warm bone" |
| `--ink` | `#1a1512` | Primary text |
| `--amber` | `#7a3d14` | Brand period, accents, the strong-text color |
| `--muted` | warm taupe | Secondary text |
| Cream, soft sand, pale gold | — | Photographic still-life palette |

**Banned:** blue, teal, cool grey, neon, primary red, forest green, pure black. The palette is warm-bone and amber, full stop.

## 3. Typography

| Use | Font |
|---|---|
| Display / wordmark | **Cormorant Garamond** (400, 500, 600 + italic 400, 500) |
| Body / UI | **IBM Plex Sans** (400, 500, 600, 700) |

**Inter is banned everywhere.** It reads as AI-default and undermines premium positioning. IBM Plex Sans is the drop-in replacement.

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

```css
:root {
  --serif: 'Cormorant Garamond', Garamond, 'Times New Roman', serif;
  --sans:  'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

## 4. Tone of Voice

**Editorial, clinical, restrained.** Reference brands: **Aesop**, **Augustinus Bader**, **The Ordinary**.

- Sentences are short. Verbs do work.
- No exclamation marks. No hype words ("revolutionary," "breakthrough," "miracle").
- Compliance-conscious: prefer "supports," "may appear to," "visibly," "the appearance of." Never claim to treat or cure.
- Write to a 50-year-old woman who reads The New Yorker, holds her own opinions, and resents being marketed at.

**Do say:**
- "The drug works. The side effects are devastating. APLOMB. exists for the four nobody is treating."
- "Begin APLOMB. now and you preserve what you have."

**Don't say:**
- "Game-changing peptide stack!"
- "Reverse Ozempic face!"
- "Transform your body!"

## 5. Photography Direction

- **Lookbook reference:** Kinfolk magazine, The Gentlewoman, Cereal magazine.
- **Camera reference:** Phase One IQ4 medium-format, 80mm leaf-shutter lens, no flash.
- **Light:** soft late-morning natural window light from upper-left, painterly shadows fall to the right.
- **Surface:** warm travertine stone slab, natural linen, bone-china.
- **Palette in-frame:** warm bone, cream, soft amber, warm taupe, deep umber. NO blue, NO teal, NO cool grey.

**Anti-AI directives** (always include in BFL prompts):
> "A real photograph — not AI-generated, not 3D render, not illustration. Indistinguishable from a Kinfolk-magazine still life. NOT plastic-looking, NOT waxy, NOT CGI, NOT AI-glossy, NOT oversaturated, NOT halo-effect, NOT lens flare, NOT fantasy lighting, NOT stock photography."

## 6. Illustration Direction

For mechanism diagrams (roots, calm, breath):

- **Medium:** gouache and ink on warm bone-colored paper.
- **Reference:** Nature magazine cover art rendered in warm tones; Beatrix Potter botanical studies.
- **Palette:** warm bone (#f7f1e6), cream, deep amber (#7a3d14), soft sand, pale gold.
- No text, no labels, no callouts, no scale bars on the illustration itself.

## 7. Image Generation

All product photography and mechanism illustrations are generated via **Black Forest Labs Flux 2 Pro** (`flux-2-pro` endpoint). Never older Flux models.

```bash
source ~/.claude/secrets.env
cd scripts
python3 gen-bundle-photos.py     # 5 photographic stills (serum, bundle, face)
python3 gen-fourpack-photos.py   # 3 product rails + 3 mechanism illustrations
```

Flux 2 Pro can occasionally misspell "APLOMB" on labels. Inspect each output; regenerate up to 2x with seed variation if label text is mangled.

## 8. Do / Don't Quick Reference

| Do | Don't |
|---|---|
| Use IBM Plex Sans for body | Use Inter (banned) |
| Use deep amber `#7a3d14` for the period | Use red, forest green, or steel-blue |
| Refer to GLP-1 as a generic class | Use trademarks: Ozempic, Wegovy, Mounjaro, Zepbound, semaglutide, tirzepatide |
| Position as "GLP-1 aftercare destination" | Position as "Ozempic-face serum" (too narrow) |
| Use compliance hedging ("supports," "may appear to") | Make medical claims |
| Keep photography Kinfolk-warm, no blue | Use cool studio lighting or stock photography |
| Generate images with Flux 2 Pro | Use Flux 1.1, Imagen, DALL-E |

## 9. Trademark Caveat

Never use these in domain names, copy, or asset filenames — they are Novo Nordisk and Eli Lilly trademarks:
- Ozempic, Wegovy (Novo Nordisk)
- Mounjaro, Zepbound (Eli Lilly)
- Semaglutide, Tirzepatide

"GLP" and "GLP-1" are generic class names — safe to use freely.
