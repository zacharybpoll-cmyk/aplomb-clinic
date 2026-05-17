"""
Production artwork — flat dieline at exact dimensions with bleed.

For each box size produces TWO files: outside and inside.

Per Packlane's "Setting up artwork for digital printing" docs:
- 0.25" bleed past cut lines
- 0.125" safety zone
- Min text 10pt for corrugated
- Outline all text (svg.fonttype = "path")
- Embed all images
- CMYK profile (matplotlib's PDF backend writes RGB; we approximate with
  values calibrated to convert cleanly to the CMYK numbers in the spec sheet)

Output goes to business documents/packaging/. Two formats per file:
- .pdf (preview / share)
- .svg (Illustrator-importable; user drops onto official Packlane dieline)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from . import geometry as g
from ._svg_logo import draw_svg_logo

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "Get-Aplomb/product-lines/packaging")

BRAND_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
                 "Get-Aplomb/brand/logo")
LOGO_SVG = BRAND_DIR / "aplomb-logo.svg"          # mark + wordmark, stacked
WORDMARK_SVG = BRAND_DIR / "aplomb-wordmark.svg"  # wordmark only


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",   # outlined glyphs in SVG
    })


def _make_canvas(box: g.BoxSize):
    """Create a figure sized to exactly the dieline + bleed (in inches)."""
    w_in = box.total_width_in
    h_in = box.total_height_in
    fig = plt.figure(figsize=(w_in, h_in), dpi=300, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-g.BLEED_IN, box.flat_width_in + g.BLEED_IN)
    ax.set_ylim(-g.BLEED_IN, box.flat_height_in + g.BLEED_IN)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


def _bone_fill(ax, x, y, w, h, *, bleed=0):
    """Fill a panel area with the bone color, extending into bleed if at edge."""
    ax.add_patch(Rectangle(
        (x - bleed, y - bleed),
        w + 2 * bleed,
        h + 2 * bleed,
        facecolor=g.BONE_HEX, edgecolor="none", zorder=1,
    ))


def _plumb_mark(ax, cx, top_y, height, color):
    line_h = height * 0.58
    diamond_h = height * 0.42
    line_top = top_y
    line_bottom = top_y - line_h
    ax.plot([cx, cx], [line_bottom, line_top],
            color=color, linewidth=1.5, zorder=10,
            solid_capstyle="butt")
    half_w = diamond_h * 0.18
    diamond_top = line_bottom
    diamond_bottom = diamond_top - diamond_h
    diamond_mid_y = diamond_top - diamond_h * 0.35
    ax.fill(
        [cx, cx - half_w, cx, cx + half_w],
        [diamond_top, diamond_mid_y, diamond_bottom, diamond_mid_y],
        color=color, zorder=10,
    )


def _fill_outside(box: g.BoxSize, ax):
    rects = box.panel_rects()
    # ---- bone fill across the entire dieline footprint --------------------
    # Each panel's bone color, plus dust/glue tabs (slightly tinted in
    # schematic but solid bone here — printer will see one continuous fill)
    for name, (x, y, w, h) in rects.items():
        # For panels that touch the outer edge of the dieline, extend bone
        # into the 0.25" bleed area.
        bleed_extension = 0
        if name in ("front", "lid", "tuck"):
            # front sticks out the bottom; lid+tuck stick out the top
            bleed_extension = g.BLEED_IN
        _bone_fill(ax, x, y, w, h, bleed=bleed_extension)
    # also fill the bleed extensions at left and right for the side wings
    left = rects["left"]; right = rects["right"]
    glue_l = rects["glue_l"]; glue_r = rects["glue_r"]
    for name, r in [("left", left), ("glue_l", glue_l),
                    ("right", right), ("glue_r", glue_r)]:
        _bone_fill(ax, *r, bleed=g.BLEED_IN)
    # ensure the very corners of the bleed are also bone
    ax.add_patch(Rectangle(
        (-g.BLEED_IN, -g.BLEED_IN),
        box.flat_width_in + 2 * g.BLEED_IN,
        box.flat_height_in + 2 * g.BLEED_IN,
        facecolor=g.BONE_HEX, edgecolor="none", zorder=0,
    ))

    # ---- LID artwork (hero face) -----------------------------------------
    # Stacked canonical logo: plumb-bob mark above the "Aplomb." wordmark.
    # SVG aspect ≈ 1 : 1.77 (tall); at h*0.78 height the logo width is
    # ≈ 1.32" — comfortable inside the lid panel.
    x, y, w, h = rects["lid"]
    cx, cy = x + w / 2, y + h / 2
    draw_svg_logo(ax, LOGO_SVG,
                  anchor_xy=(cx, cy),
                  target_height_in=h * 0.78,
                  ha="center", va="center")

    # ---- FRONT — tagline -------------------------------------------------
    x, y, w, h = rects["front"]
    cx, cy = x + w / 2, y + h / 2
    ax.plot([x + w * 0.30, x + w * 0.70], [cy + 0.28, cy + 0.28],
            color=g.AMBER_HEX, linewidth=0.6, zorder=10)
    fontsize_front = 17 if box is g.SMALL else 19
    ax.text(cx, cy + 0.06, "Preserving your self",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=fontsize_front,
            color=g.AMBER_HEX, zorder=10)
    ax.text(cx, cy - 0.30, "through GLP-1 use.",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=fontsize_front,
            color=g.AMBER_HEX, zorder=10)

    # ---- BACK — wordmark + URL ------------------------------------------
    x, y, w, h = rects["back"]
    cx, cy = x + w / 2, y + h / 2
    draw_svg_logo(ax, WORDMARK_SVG,
                  anchor_xy=(x + w * 0.22, cy),
                  target_height_in=0.22,
                  ha="right", va="center")
    ax.plot([x + w * 0.30, x + w * 0.65], [cy, cy],
            color=g.RULE_HEX, linewidth=0.7, zorder=10)
    ax.text(x + w * 0.78, cy, "Get Aplomb.",
            ha="left", va="center", family="IBM Plex Sans",
            fontsize=11, color=g.AMBER_HEX, zorder=10)

    # ---- SIDE panels — canonical plumb-bob mark ------------------------
    # Canonical mark from brand/logo/aplomb-mark.svg (amber). Sized so it
    # echoes the lid hero proportions without competing with it.
    BRAND_MARK = BRAND_DIR / "aplomb-mark.svg"
    for side_key in ("left", "right"):
        x, y, w, h = rects[side_key]
        cx, cy = x + w / 2, y + h / 2
        draw_svg_logo(ax, BRAND_MARK,
                      anchor_xy=(cx, cy),
                      target_height_in=h * 0.40,
                      ha="center", va="center")

    # ---- BOTTOM — function copy + label space ---------------------------
    x, y, w, h = rects["bottom"]
    cx, cy = x + w / 2, y + h / 2
    aw, ah = w * 0.50, h * 0.45
    ax.add_patch(Rectangle(
        (cx - aw / 2, cy - ah / 2 + 0.08), aw, ah,
        facecolor="none", edgecolor=g.RULE_HEX,
        linestyle=(0, (3, 3)), linewidth=0.6, zorder=10,
    ))
    ax.text(cx, cy - ah / 2 + 0.08 - 0.18, "shipping label area",
            ha="center", va="top", family="IBM Plex Sans",
            fontsize=7, color=g.MUTED_HEX, alpha=0.85, zorder=10)
    ax.text(cx, y + 0.30,
            "Designed in Los Angeles · Printed on FSC paperboard · "
            "Recycle this carton.",
            ha="center", va="center", family="IBM Plex Sans",
            fontsize=8, color=g.MUTED_HEX, zorder=10)


def _fill_inside(box: g.BoxSize, ax):
    """Inside artwork: bone fill everywhere, with a printed message on the
    LID interior. Lid copy is rotated 180° so it reads correctly when the
    box is opened (lid flips back over the BACK panel)."""
    # Fill entire footprint with bone (including bleed)
    ax.add_patch(Rectangle(
        (-g.BLEED_IN, -g.BLEED_IN),
        box.flat_width_in + 2 * g.BLEED_IN,
        box.flat_height_in + 2 * g.BLEED_IN,
        facecolor=g.BONE_HEX, edgecolor="none", zorder=0,
    ))

    rects = box.panel_rects()

    # ---- LID INTERIOR — hero reveal on open ------------------------------
    # Rotate copy 180° so it reads right-side-up to recipient when opened.
    x, y, w, h = rects["lid"]
    cx, cy = x + w / 2, y + h / 2
    fontsize_int = 16 if box is g.SMALL else 19
    ax.text(cx, cy + h * 0.18, "Carry your bearing.",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=fontsize_int + 4,
            color=g.AMBER_HEX, rotation=180, zorder=10)
    # Hairline rule
    ax.plot([cx - w * 0.20, cx + w * 0.20], [cy + h * 0.04, cy + h * 0.04],
            color=g.AMBER_HEX, linewidth=0.5, zorder=10)
    # Body copy
    body = "Stay your best self"
    ax.text(cx, cy - h * 0.10, body,
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic",
            fontsize=fontsize_int, color=g.INK_HEX, rotation=180,
            zorder=10)

    # ---- BOTTOM INTERIOR — tiny mark only --------------------------------
    x, y, w, h = rects["bottom"]
    cx, cy = x + w / 2, y + h / 2
    _plumb_mark(ax, cx, cy + 0.20, 0.55, g.RULE_HEX)


def _save_pair(fig, base: Path):
    """Save both PDF and SVG."""
    pdf_path = base.with_suffix(".pdf")
    svg_path = base.with_suffix(".svg")
    fig.savefig(pdf_path, format="pdf", facecolor=g.BONE_HEX,
                bbox_inches=None, pad_inches=0)
    fig.savefig(svg_path, format="svg", facecolor=g.BONE_HEX,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB) + "
          f"{svg_path.name} ({svg_path.stat().st_size // 1024} KB)")


def render(box: g.BoxSize, side: str, out_path: Path):
    _set_style()
    fig, ax = _make_canvas(box)
    if side == "outside":
        _fill_outside(box, ax)
    else:
        _fill_inside(box, ax)
    _save_pair(fig, out_path)


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for box in g.ALL_SIZES:
        suffix = "Small_6x4x3" if box is g.SMALL else "Large_7x5x3"
        render(box, "outside",
               OUT_DIR / f"Aplomb_Mailer_{suffix}_Artwork_Outside")
        render(box, "inside",
               OUT_DIR / f"Aplomb_Mailer_{suffix}_Artwork_Inside")


if __name__ == "__main__":
    render_all()
