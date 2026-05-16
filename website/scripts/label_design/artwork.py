"""
Generate flat label artwork (SVG + PDF) for each APLOMB. SKU.

Layout: editorial 3-zone wraparound — facts | front | back — with
brand-applied typography (Cormorant Garamond italic wordmark + IBM
Plex Sans body, deep amber period) on a warm-bone canvas.

Output filenames in product designs/<sku>/:
    Aplomb_<Slug>_Artwork.svg                — vector source
    Aplomb_<Slug>_Artwork.pdf                — vector PDF (300 DPI)
    Aplomb_<Slug>_SUPPLIER_UPLOAD.pdf        — clearly named upload file
    Aplomb_<Slug>_Schematic.pdf              — dieline + bleed/safe-zone QC

Usage:
    cd ~/Desktop/Documents/Claude Code/aplomb.clinic
    python3 -m scripts.label_design.artwork           # all 3 SKUs
    python3 -m scripts.label_design.artwork chewables # one SKU
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np
from PIL import Image

from . import specs as S

ROOT = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/Get-Aplomb")
PRODUCTS_DIR = ROOT / "product-lines"
CANONICAL_MARK_JPG = ROOT / "design-scratch" / "logo-iterations" / "02-plumb-line-mark.jpg"


_mark_cache = None


def _load_canonical_mark():
    """Return a numpy RGB array containing just the thread + teardrop
    portion of the canonical brand lockup (Logo Designs/02-plumb-line-mark.jpg).
    The bottom half of the source image is the "Aplomb." wordmark, which we
    render separately in matplotlib at a larger size — so we slice it off.

    Detects the amber mark pixels strictly (R-channel < bone.R - 50) so JPG
    compression noise in the bone canvas does not bloat the crop bbox. After
    cropping, all non-amber pixels are recoloured to the exact BONE_HEX so
    the embedded image blends seamlessly with the label's bone canvas.
    """
    global _mark_cache
    if _mark_cache is not None:
        return _mark_cache
    img = np.array(Image.open(CANONICAL_MARK_JPG).convert("RGB"))
    # Take the top 65% of the image — this is wide enough to capture the
    # full thread + teardrop (the teardrop tip can extend past row 512), but
    # not so wide that it includes the "Aplomb." wordmark in the lower third.
    top = img[: int(img.shape[0] * 0.65)]
    bone_ref = top[0, 0].astype(int)
    # Amber pixels are substantially darker than bone in the R channel.
    amber_mask = top[:, :, 0].astype(int) < (bone_ref[0] - 50)
    # The full image bottom-region also contains a "." amber period at the
    # end of "Aplomb." — exclude any cluster that appears below a gap of
    # ≥30 pure-bone rows after the main mark, so we keep only the mark.
    if amber_mask.any():
        rows_with_amber = np.where(np.any(amber_mask, axis=1))[0]
        # Look for a vertical gap; if found, truncate amber_mask there.
        for i in range(1, len(rows_with_amber)):
            if rows_with_amber[i] - rows_with_amber[i - 1] >= 30:
                amber_mask[rows_with_amber[i]:] = False
                break
    if not amber_mask.any():
        _mark_cache = top
        return _mark_cache
    rows = np.any(amber_mask, axis=1)
    cols = np.any(amber_mask, axis=0)
    y0 = int(np.where(rows)[0][0])
    y1 = int(np.where(rows)[0][-1])
    x0 = int(np.where(cols)[0][0])
    x1 = int(np.where(cols)[0][-1])
    # Padding so anti-aliased edge pixels are not clipped at render time.
    # Slightly extra at the bottom to ensure the teardrop tip is visible.
    pad_px = 4
    pad_bottom = 12
    y0 = max(0, y0 - pad_px)
    y1 = min(top.shape[0] - 1, y1 + pad_bottom)
    x0 = max(0, x0 - pad_px)
    x1 = min(top.shape[1] - 1, x1 + pad_px)
    crop = top[y0 : y1 + 1, x0 : x1 + 1].copy()
    # Recolour every non-amber pixel to exact BONE_HEX so the embedded image
    # background matches the surrounding label canvas with no visible seam.
    crop_amber = crop[:, :, 0].astype(int) < (bone_ref[0] - 50)
    bone_rgb = np.array(
        [int(S.BONE_HEX[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8
    )
    crop[~crop_amber] = bone_rgb
    _mark_cache = crop
    return _mark_cache


# ----- helpers -------------------------------------------------------------


def _serif_title(ax, x, y, text, *, size, color=S.INK_HEX, italic=True):
    """Render the Aplomb wordmark; return the Text artist so the caller
    can measure its real extent and place the amber period precisely."""
    style = "italic" if italic else "normal"
    return ax.text(
        x, y, text, ha="center", va="center",
        fontname="Cormorant Garamond", fontstyle=style,
        fontweight=500, fontsize=size, color=color, zorder=5,
    )


def _amber_period(ax, x, y, *, size):
    ax.text(
        x, y, ".", ha="left", va="center",
        fontname="Cormorant Garamond", fontstyle="normal",
        fontweight=600, fontsize=size, color=S.AMBER_HEX, zorder=6,
    )


def _plumb_mark(ax, cx, cy, h_mm=10.0, color=None):
    """Embed the canonical APLOMB. plumb-line mark.

    Renders Logo Designs/02-plumb-line-mark.jpg (cropped to thread+teardrop)
    via ax.imshow. Width is derived from the cropped aspect ratio so the
    image is never stretched. The cy parameter is the vertical CENTER of
    the placed mark; h_mm is its full height.
    """
    mark = _load_canonical_mark()
    mark_h_px, mark_w_px = mark.shape[:2]
    aspect = mark_w_px / mark_h_px           # width / height (typically thin)
    w_mm = h_mm * aspect
    x0 = cx - w_mm / 2
    x1 = cx + w_mm / 2
    y0 = cy - h_mm / 2
    y1 = cy + h_mm / 2
    ax.imshow(
        mark,
        extent=(x0, x1, y0, y1),
        aspect="auto",  # axis is in mm; we've already computed correct mm ratio
        interpolation="bilinear",
        zorder=4,
    )


def _wrap(text, width):
    return "\n".join(textwrap.wrap(text, width=width)) if text else ""


# ----- core layout ---------------------------------------------------------


def _figure(spec: S.LabelSpec):
    """Create a matplotlib figure sized to label cut + 3 mm bleed."""
    SCALE = 1.0 / S.MM_PER_IN  # 1 mm = 1/25.4 in — correct physical scale
    bleed = S.BLEED_MM
    total_w_mm = spec.label_w_mm + 2 * bleed
    total_h_mm = spec.label_h_mm + 2 * bleed
    fig = plt.figure(
        figsize=(total_w_mm * SCALE, total_h_mm * SCALE),
        dpi=600, facecolor=S.BONE_HEX,
    )
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-bleed, spec.label_w_mm + bleed)
    ax.set_ylim(-bleed, spec.label_h_mm + bleed)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def _bone_fill(ax, spec: S.LabelSpec):
    bleed = S.BLEED_MM
    ax.add_patch(Rectangle(
        (-bleed, -bleed),
        spec.label_w_mm + 2 * bleed,
        spec.label_h_mm + 2 * bleed,
        facecolor=S.BONE_HEX, edgecolor="none", zorder=0,
    ))


def _hairline_separators(ax, spec: S.LabelSpec, x_positions):
    """Vertical hairline rules between zones."""
    inset = 0.0 if spec.label_h_mm < 45 else S.SAFE_MM
    for x in x_positions:
        ax.add_line(Line2D(
            [x, x], [inset, spec.label_h_mm - inset],
            color=S.RULE_HEX, linewidth=0.5, zorder=1,
        ))


def _front_panel(ax, spec: S.LabelSpec, x0, x1):
    """Center hero zone: plumb-mark + Aplomb. wordmark + product subtitle."""
    cx = (x0 + x1) / 2
    h = spec.label_h_mm
    is_small = h < 45  # peptide-serum (35 mm)
    # Plumb mark (size scales with label height)
    if is_small:
        mark_h = max(7.0, h * 0.22)
        plumb_y = h * 0.83
        word_size = max(20, int(h * 0.80))
        word_y = h * 0.45
        sub_size = max(6, int(h * 0.13))
        sub_y = h * 0.13
    else:
        mark_h = max(8.0, h * 0.22)
        plumb_y = h * 0.78
        word_size = max(18, int(h * 0.85))
        word_y = h * 0.50
        sub_size = max(7, int(h * 0.13))
        sub_y = h * 0.20
    _plumb_mark(ax, cx, plumb_y, h_mm=mark_h)
    # Wordmark — render "Aplomb", then measure its true rendered right
    # edge so the amber period sits just after the 'b' at any font size.
    word_x = cx - h * 0.05
    word_artist = _serif_title(ax, word_x, word_y, "Aplomb",
                               size=word_size, italic=True)
    fig = ax.figure
    fig.canvas.draw()
    bbox = word_artist.get_window_extent(renderer=fig.canvas.get_renderer())
    bbox_data = bbox.transformed(ax.transData.inverted())
    period_gap = word_size * 0.018  # small mm gap after the 'b'
    _amber_period(ax, bbox_data.x1 + period_gap, word_y, size=word_size)
    # Subtitle (small caps via uppercase + IBM Plex)
    ax.text(
        cx, sub_y, spec.subtitle.upper(),
        ha="center", va="center",
        fontname="IBM Plex Sans", fontweight=600, fontsize=sub_size,
        color=S.INK_HEX, zorder=5,
        # tracked-out tracking — emulated via spaces
    )


def _facts_panel(ax, spec: S.LabelSpec, x0, x1):
    """Left zone: ingredients / supplement-facts callout."""
    h = spec.label_h_mm
    is_small = h < 45
    pad = 0.3 if is_small else 2.0
    if is_small:
        title_size = max(6, int(h * 0.13))
        body_size = max(4, int(h * 0.075))
    else:
        title_size = max(7, int(h * 0.13))
        body_size = max(5, int(h * 0.075))
    if spec.category == "supplement":
        header = "SUPPLEMENT FACTS"
    else:
        header = "INGREDIENTS"
    title_top_offset = 0.3 if is_small else 1.0
    ax.text(
        x0 + pad, h - pad - title_top_offset, header,
        ha="left", va="top",
        fontname="IBM Plex Sans", fontweight=700,
        fontsize=title_size, color=S.AMBER_HEX, zorder=5,
    )
    # Ingredient body — wrap to fit
    panel_w_mm = x1 - x0 - 2 * pad
    chars_per_line = max(22, int(panel_w_mm * 1.55))
    wrapped = _wrap(spec.ingredients, chars_per_line)
    ax.text(
        x0 + pad, h - pad - title_size * 0.55 - 2.0, wrapped,
        ha="left", va="top",
        fontname="IBM Plex Sans", fontweight=400,
        fontsize=body_size, color=S.INK_HEX, zorder=5,
        linespacing=1.0 if is_small else 1.25,
    )
    # Net volume at bottom of panel — anchored to bottom-left corner
    ax.text(
        x0 + pad, 0.6, f"Net  {spec.net_volume}",
        ha="left", va="bottom",
        fontname="IBM Plex Sans", fontweight=600,
        fontsize=body_size + 1, color=S.INK_HEX, zorder=5,
    )


def _back_panel(ax, spec: S.LabelSpec, x0, x1):
    """Right zone: directions, warnings, distributor, FDA disclaimer."""
    h = spec.label_h_mm
    is_small = h < 45  # peptide-serum (35 mm)
    pad = 1.6 if is_small else 2.0
    title_size = max(6 if is_small else 6, int(h * 0.13 if is_small else h * 0.11))
    body_size = max(4 if is_small else 4, int(h * 0.075 if is_small else h * 0.075))
    block_gap = 0.5 if is_small else 2.5
    body_linespacing = 1.10 if is_small else 1.2
    title_to_body_gap = 0.3 if is_small else 0.8
    distributor_linespacing = 0.95 if is_small else 1.25
    distributor_y = 0.6 if is_small else pad + 1
    panel_w_mm = x1 - x0 - 2 * pad
    chars_per_line = max(22, int(panel_w_mm * (1.55 if is_small else 1.55)))
    y = h - pad - (0.3 if is_small else 1.0)

    def _block(label_str, body_str, dy_after):
        nonlocal y
        ax.text(
            x0 + pad, y, label_str,
            ha="left", va="top",
            fontname="IBM Plex Sans", fontweight=700,
            fontsize=title_size, color=S.AMBER_HEX, zorder=5,
        )
        y -= title_size * 0.55 + title_to_body_gap
        wrapped = _wrap(body_str, chars_per_line)
        ax.text(
            x0 + pad, y, wrapped,
            ha="left", va="top",
            fontname="IBM Plex Sans", fontweight=400,
            fontsize=body_size, color=S.INK_HEX, zorder=5,
            linespacing=body_linespacing,
        )
        y -= body_size * (0.50 if is_small else 0.55) * (wrapped.count("\n") + 1) + dy_after

    _block("DIRECTIONS",
           spec.suggested_use,
           dy_after=block_gap)
    _block("WARNING" if spec.category == "supplement" else "CAUTION",
           spec.warnings,
           dy_after=block_gap)

    # FDA disclaimer (supplements only) — manually wrapped
    if spec.fda_disclaimer:
        wrapped = _wrap(
            "*These statements have not been evaluated by the FDA. "
            "This product is not intended to diagnose, treat, cure, or "
            "prevent any disease.",
            chars_per_line,
        )
        ax.text(
            x0 + pad, y, wrapped,
            ha="left", va="top",
            fontname="IBM Plex Sans", fontstyle="italic", fontweight=400,
            fontsize=body_size - 1, color=S.MUTED_HEX, zorder=5,
            linespacing=1.2,
        )

    # Distributor + badges at the bottom — manufacturer asked for this block
    # larger and darker, so it renders one point above body and uses its own
    # narrower wrap (since wider glyphs at +1pt would otherwise bleed past
    # the right edge of the column).
    dist_size = body_size if is_small else body_size + 1
    dist_chars_per_line = max(22, int(panel_w_mm * (1.55 if is_small else 1.4)))
    distributor_line = _wrap(spec.distributor, dist_chars_per_line)
    badges_line = _wrap(" · ".join(spec.badges), dist_chars_per_line)
    ax.text(
        x0 + pad, distributor_y,
        distributor_line + "\n" + badges_line,
        ha="left", va="bottom",
        fontname="IBM Plex Sans", fontweight=500,
        fontsize=dist_size, color=S.INK_HEX, zorder=5,
        linespacing=distributor_linespacing,
    )


def render(spec: S.LabelSpec) -> dict:
    """Render label artwork; return dict of output paths."""
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",
    })
    fig, ax = _figure(spec)
    _bone_fill(ax, spec)

    w = spec.label_w_mm
    h = spec.label_h_mm
    # 3-zone widths: 27 / 45 / 28 for small labels (35 mm tall) — facts
    # column widened slightly so INGREDIENTS title clears the right separator;
    # front hosts the wordmark; back is the densest block. Else 32/36/32.
    if h < 45:
        facts_x1 = w * 0.27
        front_x1 = w * 0.72
    else:
        facts_x1 = w * 0.32
        front_x1 = w * 0.68
    facts_x0 = 0.0
    front_x0 = facts_x1
    back_x0 = front_x1
    back_x1 = w

    _hairline_separators(ax, spec, [facts_x1, front_x1])
    _front_panel(ax, spec, front_x0, front_x1)
    _facts_panel(ax, spec, facts_x0, facts_x1)
    _back_panel(ax, spec, back_x0, back_x1)

    # Output dir per SKU
    out_dir = PRODUCTS_DIR / spec.folder_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    base = f"Aplomb_{spec.folder_slug.replace('-', '_').title().replace('_', '_')}"
    # Friendlier base name
    base = "Aplomb_" + "_".join(w.capitalize() for w in spec.folder_slug.split("-"))

    svg_path = out_dir / f"{base}_Artwork.svg"
    pdf_path = out_dir / f"{base}_Artwork.pdf"
    upload_path = out_dir / f"{base}_SUPPLIER_UPLOAD.pdf"
    png_path = out_dir / f"{base}_Preview_2400dpi.png"

    fig.savefig(svg_path, format="svg", facecolor=S.BONE_HEX)
    fig.savefig(pdf_path, format="pdf", facecolor=S.BONE_HEX)
    # Supplier-named upload (identical contents, friendlier name)
    fig.savefig(upload_path, format="pdf", facecolor=S.BONE_HEX)
    # High-density PNG preview for supplier inspection (2400 DPI raster)
    fig.savefig(png_path, format="png", facecolor=S.BONE_HEX, dpi=2400)
    plt.close(fig)

    return {
        "svg": svg_path,
        "pdf": pdf_path,
        "upload": upload_path,
        "png": png_path,
    }


def render_schematic(spec: S.LabelSpec) -> Path:
    """Dieline + bleed + safe-zone overlay for QC review."""
    plt.rcParams.update({"font.family": "IBM Plex Sans"})
    fig, ax = _figure(spec)
    # white canvas
    bleed = S.BLEED_MM
    ax.add_patch(Rectangle(
        (-bleed, -bleed),
        spec.label_w_mm + 2 * bleed,
        spec.label_h_mm + 2 * bleed,
        facecolor="white", edgecolor="none", zorder=0,
    ))
    # bleed (red dashed)
    ax.add_patch(Rectangle(
        (-bleed, -bleed),
        spec.label_w_mm + 2 * bleed,
        spec.label_h_mm + 2 * bleed,
        facecolor="none", edgecolor="#d33", linewidth=0.6,
        linestyle=(0, (3, 2)), zorder=2,
    ))
    # cut (black solid)
    ax.add_patch(Rectangle(
        (0, 0), spec.label_w_mm, spec.label_h_mm,
        facecolor="none", edgecolor=S.INK_HEX, linewidth=1.0, zorder=3,
    ))
    # safe zone (grey dashed)
    ax.add_patch(Rectangle(
        (S.SAFE_MM, S.SAFE_MM),
        spec.label_w_mm - 2 * S.SAFE_MM,
        spec.label_h_mm - 2 * S.SAFE_MM,
        facecolor="none", edgecolor="#888", linewidth=0.5,
        linestyle=(0, (2, 2)), zorder=3,
    ))
    # dimension labels
    ax.text(
        spec.label_w_mm / 2, spec.label_h_mm + bleed / 2,
        f"{spec.label_w_mm:.1f} mm  /  {spec.label_w_in:.2f}\"",
        ha="center", va="center",
        fontname="IBM Plex Sans", fontsize=6, color=S.INK_HEX,
    )
    ax.text(
        spec.label_w_mm + bleed / 2, spec.label_h_mm / 2,
        f"{spec.label_h_mm:.1f} mm\n{spec.label_h_in:.2f}\"",
        ha="center", va="center",
        fontname="IBM Plex Sans", fontsize=6, color=S.INK_HEX,
        rotation=90,
    )
    ax.text(
        0, -bleed - 1.5,
        f"APLOMB. — {spec.subtitle}  |  Supplier: {spec.supplier}  |  "
        f"3 mm bleed (red dashed) · 3 mm safe zone (grey dashed)",
        ha="left", va="top",
        fontname="IBM Plex Sans", fontsize=5, color=S.MUTED_HEX,
    )
    out_dir = PRODUCTS_DIR / spec.folder_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    base = "Aplomb_" + "_".join(w.capitalize() for w in spec.folder_slug.split("-"))
    out = out_dir / f"{base}_Schematic.pdf"
    fig.savefig(out, format="pdf", facecolor="white")
    plt.close(fig)
    return out


def render_all():
    rows = []
    for spec in S.ALL_SPECS:
        artwork = render(spec)
        schematic = render_schematic(spec)
        rows.append((spec.folder_slug, artwork, schematic))
        print(f"[{spec.folder_slug:>22}]  artwork → {artwork['upload'].name}")
        print(f"[{spec.folder_slug:>22}]  schem.  → {schematic.name}")
    return rows


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        spec = next((s for s in S.ALL_SPECS if s.folder_slug == target), None)
        if spec is None:
            sys.exit(f"unknown sku: {target}")
        a = render(spec)
        sc = render_schematic(spec)
        print(f"artwork : {a['upload']}")
        print(f"schematic: {sc}")
    else:
        render_all()
