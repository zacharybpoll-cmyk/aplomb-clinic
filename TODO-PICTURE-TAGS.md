# TODO: Migrate `<img>` to `<picture>` Tags

**Status**: WebP variants have been generated. The following HTML files need `<img>` → `<picture>` migration.

## Files Requiring Update

1. **index.html** — product cards, hero images, about section
2. **checkout/index.html** — order summary product images
3. Any other HTML files with `<img src="/assets/*.{jpg,png}">`

## Migration Pattern

Replace:
```html
<img src="/assets/foo.jpg" alt="..." width="..." height="..." loading="lazy">
```

With:
```html
<picture>
  <source srcset="/assets/foo.webp 1x, /assets/foo.webp 2x" type="image/webp">
  <img src="/assets/foo.jpg" alt="..." width="..." height="..." loading="lazy">
</picture>
```

**Notes:**
- WebP 2x file is at `/assets/foo.webp` (full resolution, used for both 1x and 2x DPI)
- WebP 1x file is at `/assets/foo-1x.webp` (50% width, for lower-bandwidth clients)
- Original JPG/PNG files are kept as fallback for legacy browsers (~5% traffic)
- Use `srcset` with media queries if different crops are needed per breakpoint (e.g., hero on mobile vs. desktop)

## WebP Browser Support
- Chrome/Edge 25+: ✓
- Firefox 65+: ✓
- Safari 16+: ✓
- Mobile: ~95% coverage

Fallback to JPG/PNG for remaining 5%.
