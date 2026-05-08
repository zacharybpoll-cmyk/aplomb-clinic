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

from . import specs as S

ROOT = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/aplomb.clinic")
PRODUCTS_DIR = ROOT / "product designs"


# ----- helpers -------------------------------------------------------------


def _serif_title(ax, x, y, text, *, size, color=S.INK_HEX, italic=True):
    """Render the Aplomb wordmark with an amber period."""
    style = "italic" if italic else "normal"
    # We render "Aplomb" then a separately-colored "."
    ax.text(
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
    """Vertical thread + triangular plummet (the brand mark)."""
    color = color or S.AMBER_HEX
    line_h = h_mm * 0.58
    plum_h = h_mm * 0.42
    # thread
    ax.add_line(Line2D(
        [cx, cx], [cy + h_mm/2, cy + h_mm/2 - line_h],
        color=color, linewidth=0.7, solid_capstyle="butt", zorder=4,
    ))
    # plummet (triangle pointing down)
    top_y = cy + h_mm/2 - line_h
    bot_y = cy - h_mm/2
    half_w = h_mm * 0.10
    tri = plt.Polygon(
        [[cx - half_w, top_y], [cx + half_w, top_y], [cx, bot_y]],
        closed=True, facecolor=color, edgecolor="none", zorder=4,
    )
    ax.add_patch(tri)


def _wrap(text, width):
    return "\n".join(textwrap.wrap(text, width=width)) if text else ""


# ----- core layout ---------------------------------------------------------


def _figure(spec: S.LabelSpec):
    """Create a matplotlib figure sized to label cut + 3 mm bleed."""
    SCALE = 0.05  # 1 mm = 0.05 in (so a 152.4mm label → 7.62" canvas)
    bleed = S.BLEED_MM
    total_w_mm = spec.label_w_mm + 2 * bleed
    total_h_mm = spec.label_h_mm + 2 * bleed
    fig = plt.figure(
        figsize=(total_w_mm * SCALE, total_h_mm * SCALE),
        dpi=300, facecolor=S.BONE_HEX,
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
    for x in x_positions:
        ax.add_line(Line2D(
            [x, x], [S.SAFE_MM, spec.label_h_mm - S.SAFE_MM],
            color=S.RULE_HEX, linewidth=0.5, zorder=1,
        ))


def _front_panel(ax, spec: S.LabelSpec, x0, x1):
    """Center hero zone: plumb-mark + Aplomb. wordmark + product subtitle."""
    cx = (x0 + x1) / 2
    h = spec.label_h_mm
    # Plumb mark (size scales with label height)
    mark_h = max(8.0, h * 0.22)
    _plumb_mark(ax, cx, h * 0.78, h_mm=mark_h)
    # Wordmark — "Aplomb" with amber period
    word_size = max(18, int(h * 0.85))
    _serif_title(ax, cx - h * 0.05, h * 0.50, "Aplomb",
                 size=word_size, italic=True)
    _amber_period(ax, cx + h * 0.30, h * 0.50, size=word_size)
    # Subtitle (small caps via uppercase + IBM Plex)
    sub_size = max(7, int(h * 0.13))
    ax.text(
        cx, h * 0.20, spec.subtitle.upper(),
        ha="center", va="center",
        fontname="IBM Plex Sans", fontweight=600, fontsize=sub_size,
        color=S.INK_HEX, zorder=5,
        # tracked-out tracking — emulated via spaces
    )


def _facts_panel(ax, spec: S.LabelSpec, x0, x1):
    """Left zone: ingredients / supplement-facts callout."""
    pad = 2.0
    h = spec.label_h_mm
    title_size = max(7, int(h * 0.13))
    body_size = max(5, int(h * 0.075))
    if spec.category == "supplement":
        header = "SUPPLEMENT FACTS"
    else:
        header = "INGREDIENTS"
    ax.text(
        x0 + pad, h - pad - 1, header,
        ha="left", va="top",
        fontname="IBM Plex Sans", fontweight=700,
        fontsize=title_size, color=S.AMBER_HEX, zorder=5,
    )
    # Ingredient body — wrap to fit
    panel_w_mm = x1 - x0 - 2 * pad
    chars_per_line = max(20, int(panel_w_mm * 1.6))
    wrapped = _wrap(spec.ingredients, chars_per_line)
    ax.text(
        x0 + pad, h - pad - title_size * 0.55 - 2.5, wrapped,
        ha="left", va="top",
        fontname="IBM Plex Sans", fontweight=400,
        fontsize=body_size, color=S.INK_HEX, zorder=5,
        linespacing=1.25,
    )
    # Net volume at bottom of panel
    ax.text(
        x0 + pad, pad + 1, f"Net  {spec.net_volume}",
        ha="left", va="bottom",
        fontname="IBM Plex Sans", fontweight=600,
        fontsize=body_size + 1, color=S.INK_HEX, zorder=5,
    )


def _back_panel(ax, spec: S.LabelSpec, x0, x1):
    """Right zone: directions, warnings, distributor, FDA disclaimer."""
    pad = 2.0
    h = spec.label_h_mm
    is_small = h < 45  # peptide-serum (35 mm)
    title_size = max(6, int(h * 0.10 if is_small else h * 0.11))
    body_size = max(4, int(h * 0.065 if is_small else h * 0.075))
    block_gap = 1.4 if is_small else 2.5
    panel_w_mm = x1 - x0 - 2 * pad
    chars_per_line = max(20, int(panel_w_mm * (1.7 if is_small else 1.55)))
    y = h - pad - 1

    def _block(label_str, body_str, dy_after):
        nonlocal y
        ax.text(
            x0 + pad, y, label_str,
            ha="left", va="top",
            fontname="IBM Plex Sans", fontweight=700,
            fontsize=title_size, color=S.AMBER_HEX, zorder=5,
        )
        y -= title_size * 0.55 + 0.8
        wrapped = _wrap(body_str, chars_per_line)
        ax.text(
            x0 + pad, y, wrapped,
            ha="left", va="top",
            fontname="IBM Plex Sans", fontweight=400,
            fontsize=body_size, color=S.INK_HEX, zorder=5,
            linespacing=1.2,
        )
        y -= body_size * 0.55 * (wrapped.count("\n") + 1) + dy_after

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

    # Distributor + badges at the bottom — wrapped to fit the panel
    distributor_line = _wrap(spec.distributor, chars_per_line)
    badges_line = _wrap(" · ".join(spec.badges), chars_per_line)
    ax.text(
        x0 + pad, pad + 1,
        distributor_line + "\n" + badges_line,
        ha="left", va="bottom",
        fontname="IBM Plex Sans", fontweight=400,
        fontsize=body_size - 1, color=S.MUTED_HEX, zorder=5,
        linespacing=1.25,
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
    # 3-zone widths: 32% / 36% / 32%
    facts_x0 = 0.0
    facts_x1 = w * 0.32
    front_x0 = facts_x1
    front_x1 = w * 0.68
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

    fig.savefig(svg_path, format="svg", facecolor=S.BONE_HEX)
    fig.savefig(pdf_path, format="pdf", facecolor=S.BONE_HEX)
    # Also save as supplier-named upload (identical contents, friendlier name)
    fig.savefig(upload_path, format="pdf", facecolor=S.BONE_HEX)
    plt.close(fig)

    return {
        "svg": svg_path,
        "pdf": pdf_path,
        "upload": upload_path,
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
