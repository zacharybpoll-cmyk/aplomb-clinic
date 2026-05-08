# aplomb.clinic — canonical site source

Static, single-file marketing + commerce site for **APLOMB.**, the GLP-1 side-effect line for women.

This folder is the canonical source. The previous `AFTER.` and `KEEP.` iterations are deprecated — do not rebrand from those, rebrand from here.

## What's here

```
aplomb.clinic/
├── README.md                  # this file
├── index.html                 # full site, monolithic (CSS + JS embedded)
├── brand/
│   └── BRAND.md               # palette, type, voice, photo direction, do/don't
├── assets/                    # 15 images
│   ├── (4 portraits)          founder-zachary, hero-two-women, portrait-confident, woman-50s-portrait
│   ├── (3 mechanism art)      roots-mech, calm-mech, breath-mech (gouache illustrations)
│   ├── (2 face stills)        face-volume-loss, face-volume-preserved
│   └── (6 product rails)      serum-detail, serum-rail, bundle-detail, daily-rail, roots-rail, calm-rail
└── scripts/
    ├── gen-bundle-photos.py   # 5 photographic stills (serum + bundle + face)
    └── gen-fourpack-photos.py # 3 rails + 3 mechanism illustrations
```

## Local preview

```bash
open index.html
```

The site is static and self-contained — no build step, no server needed.

## Regenerate brand-bearing images

All product photography and mechanism art is generated via **Black Forest Labs Flux 2 Pro**. The API key lives in `~/.claude/secrets.env` as `BFL_API_KEY` (already sourced by `~/.zshrc`).

```bash
cd scripts
source ~/.claude/secrets.env

# All bundle photos (face + serum + bundle), 5 images, ~10 min:
python3 gen-bundle-photos.py

# All four-pack assets (3 rails + 3 mechanism), 6 images, ~12 min:
python3 gen-fourpack-photos.py

# Single image regen:
python3 gen-bundle-photos.py     --only serum-rail
python3 gen-fourpack-photos.py   --only daily-rail
```

Outputs land directly in `assets/`. Flux 2 Pro can occasionally misspell "APLOMB" on labels — inspect each generated image, regenerate up to 2x with a different seed if a label is mangled.

## Brand rules

See [`brand/BRAND.md`](brand/BRAND.md) for the canonical brand spec. Highlights:

- **Wordmark:** `Aplomb.` in Cormorant Garamond italic 500, with an amber `.` (`#7a3d14`).
- **Body font:** **IBM Plex Sans only.** Inter is banned everywhere.
- **Palette:** warm bone, deep amber, cream — no blue, no teal, no cool grey.
- **Tone:** editorial, clinical, restrained — Aesop / Augustinus Bader / The Ordinary.
- **Trademarks:** never use Ozempic / Wegovy / Mounjaro / Zepbound / semaglutide / tirzepatide in copy or domain names. "GLP-1" is the generic class name — safe.

## Deploy

Live at **https://getaplomb.com** (GitHub Pages serving from `main` branch root; DNS on Cloudflare in gray-cloud / DNS-only mode so GitHub manages the Let's Encrypt cert directly).

Custom domain is set via the repo-root `CNAME` file (single line: `getaplomb.com`). Pages rebuilds on every push to `main`; takes ~1–2 min. The old project URL `https://zacharybpoll-cmyk.github.io/aplomb-clinic/` now 301-redirects to the custom domain automatically.

## Lineage

- Predecessor: `~/Desktop/Documents/Claude Code/glp-1 support/websites/after-bundle-site/` (rebranded into this folder on 2026-05-01)
- Domain research and rebrand plan: `~/.claude/plans/https-zacharybpoll-cmyk-github-io-after-virtual-naur.md`
- Brand pivot history: `AFTER.` → `KEEP.` → `APLOMB.` (final)
