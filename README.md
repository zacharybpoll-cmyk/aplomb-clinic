# aplomb.clinic — canonical site source

Static, single-file marketing + commerce site for **APLOMB.**, the GLP-1 side-effect line for women.

This folder is the canonical source. The previous `AFTER.` and `KEEP.` iterations are deprecated — do not rebrand from those, rebrand from here.

## What's here

```
Get-Aplomb/
├── README.md                  # this file
├── COMMERCE-RUNBOOK.md        # checkout / Stripe operational notes
├── wrangler.toml              # Cloudflare Pages config (build dir = website/)
├── package.json               # npm scripts (dev, deploy)
├── CNAME                      # custom domain binding
│
├── website/                   # THE LIVE SITE — what Cloudflare Pages serves
│   ├── index.html             # full homepage, monolithic
│   ├── about/, account/, admin/, biology/, breath/, calm/, checkout/,
│   │   contact/, email-preferences/, evidence/, faq/, legal/, roots/, serum/
│   ├── assets/                # images + cart.js, checkout.js, analytics.js
│   ├── css/                   # site.css
│   ├── scripts/               # image-gen pipeline (Flux 2 Pro)
│   ├── sitemap.xml, robots.txt
│
├── functions/                 # CF Pages Functions (must stay at repo root)
├── supabase/                  # database migrations + config
│
├── brand/                     # canonical brand identity
│   ├── BRAND.md               # palette, type, voice, photo direction
│   └── logo/                  # logo SVGs + build scripts
│
├── product-lines/             # per-product mockups, labels, supplier specs
│   ├── chewables/
│   ├── hair-growth-serum/
│   ├── nausea/                # includes aplomb_calm_pouch_v1
│   ├── packaging/             # mailer artwork
│   └── peptide-serum/
│
├── business-documents/        # research + supplier work + corporate
│   ├── corporate/             # EIN
│   ├── product-research/      # category analyses, private-label catalog
│   └── supplier-analysis/     # alternates, mitigation, RFQs, audits
│       └── correspondence/    # supplier shortlist, zone snapshots, sessions
│
├── social-media/              # drafts and assets for IG/TikTok/X (placeholder)
│
├── design-scratch/            # design experiments — not production
│   ├── avatars/               # heygen avatar generation outputs
│   ├── logo-iterations/       # earlier logo design rounds
│   ├── bfl-tests/             # BFL canon test renders
│   └── TODO-PICTURE-TAGS.md
│
└── tasks/                     # project tasks + lessons
```

## Local preview

```bash
npm run dev
# → boots `wrangler pages dev website` on http://localhost:8788
```

Functions (`/api/...`, `/cron/...`, `/admin/...`) auto-load from the root-level
`functions/` directory. Static pages live in `website/`. Both are served
together at localhost.

## Regenerate brand-bearing images

All product photography and mechanism art is generated via **Black Forest Labs Flux 2 Pro**. The API key lives in `~/.claude/secrets.env` as `BFL_API_KEY` (already sourced by `~/.zshrc`).

```bash
cd website/scripts
source ~/.claude/secrets.env

# All bundle photos (face + serum + bundle), 5 images, ~10 min:
python3 gen-bundle-photos.py

# All four-pack assets (3 rails + 3 mechanism), 6 images, ~12 min:
python3 gen-fourpack-photos.py

# Single image regen:
python3 gen-bundle-photos.py     --only serum-rail
python3 gen-fourpack-photos.py   --only daily-rail
```

Outputs land directly in `website/assets/` (the scripts compute the target dir relative to their own location). Flux 2 Pro can occasionally misspell "APLOMB" on labels — inspect each generated image, regenerate up to 2x with a different seed if a label is mangled.

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
