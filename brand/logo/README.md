# Aplomb — Brand Logo

Canonical, font-independent vector files for the Aplomb logo. Use these for everything outside the website (packaging, vendor handoffs, decks, social, email signatures, favicons, product labels, etc.).

## Files

| File | Use it for | Notes |
|---|---|---|
| `aplomb-logo.svg` | The default. Anywhere you need the full Aplomb logo. | Outlined paths — no font dependency. Renders identically in any tool. ~4 KB. |
| `aplomb-wordmark.svg` | Tight horizontal layouts where the plumb-bob mark would crowd or where you're showing the mark separately. | Outlined paths. ~4 KB. |
| `aplomb-mark.svg` | The plumb-bob alone — favicons, social avatars, ornament inside a layout. | The canonical mark, amber. ~300 B. (For the web/inline-CSS version that inherits `currentColor`, use `/assets/aplomb-mark.svg` in the site repo instead.) |
| `aplomb-logo-web.svg` | Web only, when Cormorant Garamond is already loaded by the page. | Uses `<text>` — much smaller (~600 B) but only renders correctly with the font available. **Don't** send this to a printer or a third-party vendor. |

All files have **transparent backgrounds**. Drop them onto bone, white, or any light surface. For dark backgrounds, the ink letters won't be readable — request a reversed variant.

## Brand spec (source of truth)

| Token | Hex | Used for |
|---|---|---|
| Ink | `#1a1512` | Wordmark letters |
| Amber | `#7a3d14` | Plumb-bob mark + period |
| Bone | `#efe8dc` | Recommended background |

**Wordmark:** "Aplomb." (capital A, lowercase p-l-o-m-b, period) — Cormorant Garamond, italic, weight 500 (Medium Italic).

These tokens also live in `css/site.css:1-10` for the website.

## Rebuilding

Two scripts live in this folder:

- **`_trace_mark.py`** — vectorizes the plumb-bob mark from `Logo Designs/02-plumb-line-mark.jpg` using `potrace`. Produces `aplomb-mark.svg` plus `_mark_data.py` (the path data the lockup script consumes). Only needs to be re-run if the source mark image changes.
- **`_build_logo.py`** — outlines the "Aplomb." wordmark from `CormorantGaramond-MediumItalic.ttf` using `fontTools.pens.svgPathPen` and composes the four deliverables.

```bash
python3 _trace_mark.py   # if the source bob image ever changes
python3 _build_logo.py   # to rebuild all four logo SVGs
```

Requires `fonttools`, `opencv-python`, `numpy`, and the `potrace` CLI (`brew install potrace`). The font TTF and the source JPG (`../../Logo Designs/02-plumb-line-mark.jpg`) are read directly.
