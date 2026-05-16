"""
Technical schematic — flat dieline with dimensions, fold/cut/bleed lines,
panel labels, and design-element placement overlay. One PDF per size.

Output goes to business documents/packaging/.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging")

PAGE_W_IN = 17.0
PAGE_H_IN = 22.0


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "font.size": 9,
        "axes.edgecolor": g.RULE_HEX,
        "axes.linewidth": 0.5,
        "pdf.fonttype": 3,   # embed full font subset (vector glyphs)
        "ps.fonttype": 3,
        "svg.fonttype": "path",  # outline paths in SVG
    })


def _draw_panel(ax, name, x, y, w, h, *, label=None, color=g.BONE_HEX,
                dims_label=None, label_position="corner"):
    rect = Rectangle((x, y), w, h, facecolor=color, edgecolor="none",
                     alpha=1.0, zorder=1)
    ax.add_patch(rect)
    cut = Rectangle((x, y), w, h, facecolor="none",
                    edgecolor=g.INK_HEX, linewidth=1.0, zorder=4)
    ax.add_patch(cut)
    if label is None:
        label = name
    if label_position == "corner":
        # Subtle top-left tag — doesn't compete with design overlay
        pad = min(w, h) * 0.06 + 0.04
        ax.text(x + pad, y + h - pad, label,
                ha="left", va="top",
                family="IBM Plex Sans", fontsize=6.5,
                color=g.MUTED_HEX, alpha=0.75, zorder=5)
        if dims_label:
            ax.text(x + pad, y + h - pad - 0.18, dims_label,
                    ha="left", va="top",
                    family="IBM Plex Sans", fontsize=5.5,
                    color=g.MUTED_HEX, alpha=0.55, zorder=5)
    else:
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center",
                family="IBM Plex Sans", fontsize=9,
                color=g.MUTED_HEX, alpha=0.75, zorder=5)


def _draw_fold(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color="#C2392E", linestyle=(0, (3, 2)),
            linewidth=0.7, zorder=6)


def _draw_bleed(ax, x, y, w, h):
    bx = x - g.BLEED_IN
    by = y - g.BLEED_IN
    bw = w + 2 * g.BLEED_IN
    bh = h + 2 * g.BLEED_IN
    rect = Rectangle((bx, by), bw, bh, facecolor="none",
                     edgecolor="#3F8C4A", linestyle=(0, (4, 2)),
                     linewidth=0.7, zorder=2)
    ax.add_patch(rect)


def _draw_safety(ax, x, y, w, h):
    sx = x + g.SAFE_IN
    sy = y + g.SAFE_IN
    sw = w - 2 * g.SAFE_IN
    sh = h - 2 * g.SAFE_IN
    rect = Rectangle((sx, sy), sw, sh, facecolor="none",
                     edgecolor=g.MUTED_HEX, linestyle=":",
                     linewidth=0.4, zorder=3, alpha=0.6)
    ax.add_patch(rect)


def _draw_dimension(ax, x1, y1, x2, y2, text, *, offset=0.18,
                    side="bottom"):
    """Annotate a dimension between (x1,y1) and (x2,y2). side: top/bottom/left/right."""
    if side == "bottom":
        oy = -offset
        ax.annotate("", xy=(x1, y1 + oy), xytext=(x2, y2 + oy),
                    arrowprops=dict(arrowstyle="<->", color=g.AMBER_HEX,
                                    lw=0.7, shrinkA=0, shrinkB=0))
        ax.text((x1 + x2) / 2, y1 + oy - 0.10, text,
                ha="center", va="top",
                family="IBM Plex Sans", fontsize=8,
                color=g.AMBER_HEX, fontweight="medium")
    elif side == "top":
        oy = offset
        ax.annotate("", xy=(x1, y1 + oy), xytext=(x2, y2 + oy),
                    arrowprops=dict(arrowstyle="<->", color=g.AMBER_HEX,
                                    lw=0.7, shrinkA=0, shrinkB=0))
        ax.text((x1 + x2) / 2, y1 + oy + 0.10, text,
                ha="center", va="bottom",
                family="IBM Plex Sans", fontsize=8,
                color=g.AMBER_HEX, fontweight="medium")
    elif side == "left":
        ox = -offset
        ax.annotate("", xy=(x1 + ox, y1), xytext=(x2 + ox, y2),
                    arrowprops=dict(arrowstyle="<->", color=g.AMBER_HEX,
                                    lw=0.7, shrinkA=0, shrinkB=0))
        ax.text(x1 + ox - 0.10, (y1 + y2) / 2, text,
                ha="right", va="center", rotation=90,
                family="IBM Plex Sans", fontsize=8,
                color=g.AMBER_HEX, fontweight="medium")
    else:  # right
        ox = offset
        ax.annotate("", xy=(x1 + ox, y1), xytext=(x2 + ox, y2),
                    arrowprops=dict(arrowstyle="<->", color=g.AMBER_HEX,
                                    lw=0.7, shrinkA=0, shrinkB=0))
        ax.text(x1 + ox + 0.10, (y1 + y2) / 2, text,
                ha="left", va="center", rotation=90,
                family="IBM Plex Sans", fontsize=8,
                color=g.AMBER_HEX, fontweight="medium")


def _plumb_mark(ax, cx, top_y, height, color=None):
    """Draw the Aplomb plumb-bob: vertical line + diamond weight.
    Mark anchored at cx, with TOP at top_y, total height = `height`."""
    if color is None:
        color = g.AMBER_HEX
    # Vertical line takes ~58% of height; diamond weight ~42%.
    line_h = height * 0.58
    diamond_h = height * 0.42
    line_top = top_y
    line_bottom = top_y - line_h
    # Vertical thread
    ax.plot([cx, cx], [line_bottom, line_top],
            color=color, linewidth=1.2, zorder=10,
            solid_capstyle="butt")
    # Diamond weight
    half_w = diamond_h * 0.18
    diamond_top = line_bottom
    diamond_bottom = diamond_top - diamond_h
    diamond_mid_y = diamond_top - diamond_h * 0.35
    ax.fill(
        [cx, cx - half_w, cx, cx + half_w],
        [diamond_top, diamond_mid_y, diamond_bottom, diamond_mid_y],
        color=color, zorder=10,
    )


def _design_overlay_lid(ax, x, y, w, h):
    """LID — the hero face, visible immediately on arrival.
    Layout: plumb mark above, Aplomb. wordmark below, tagline beneath."""
    cx, cy = x + w / 2, y + h / 2
    mark_h = h * 0.34
    _plumb_mark(ax, cx, cy + mark_h * 0.65, mark_h)
    # Wordmark below the mark
    word_y = cy - h * 0.05
    ax.text(cx - 0.04, word_y, "Aplomb",
            ha="right", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="medium",
            fontsize=22, color=g.AMBER_HEX, zorder=10)
    ax.text(cx - 0.04, word_y, ".",
            ha="left", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="bold",
            fontsize=22, color=g.AMBER_HEX, zorder=10)


def _design_overlay_front(ax, x, y, w, h):
    """FRONT — the editorial tagline reveal."""
    cx, cy = x + w / 2, y + h / 2
    # Hairline rule above text
    ax.plot([x + w * 0.30, x + w * 0.70], [cy + 0.20, cy + 0.20],
            color=g.AMBER_HEX, linewidth=0.4, zorder=10)
    ax.text(cx, cy - 0.04, "Preserving your self",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=14, color=g.AMBER_HEX, zorder=10)
    ax.text(cx, cy - 0.30, "through GLP-1 use.",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=14, color=g.AMBER_HEX, zorder=10)


def _design_overlay_back(ax, x, y, w, h):
    """BACK — quiet utility face. Logo + URL only."""
    cx, cy = x + w / 2, y + h / 2
    # Small wordmark left
    ax.text(x + w * 0.22, cy, "Aplomb",
            ha="right", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="medium",
            fontsize=11, color=g.MUTED_HEX, zorder=10)
    ax.text(x + w * 0.22, cy, ".",
            ha="left", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="bold",
            fontsize=11, color=g.AMBER_HEX, zorder=10)
    # Hairline center rule
    ax.plot([x + w * 0.30, x + w * 0.65], [cy, cy],
            color=g.RULE_HEX, linewidth=0.6, zorder=10)
    # URL right
    ax.text(x + w * 0.78, cy, "aplomb.clinic",
            ha="left", va="center", family="IBM Plex Sans",
            fontsize=9, color=g.AMBER_HEX, zorder=10)


def _design_overlay_side(ax, x, y, w, h):
    """LEFT / RIGHT side — quiet hairline + small mark only."""
    cx, cy = x + w / 2, y + h / 2
    # A single small plumb mark, centered, low key
    _plumb_mark(ax, cx, cy + h * 0.13, h * 0.26, color=g.RULE_HEX)


def _design_overlay_bottom(ax, x, y, w, h):
    """BOTTOM — function-only. Address window placeholder + made-with copy."""
    cx, cy = x + w / 2, y + h / 2
    # Address window outline (dashed)
    aw, ah = w * 0.45, h * 0.40
    ax.add_patch(Rectangle((cx - aw / 2, cy - ah / 2 + 0.05), aw, ah,
                           facecolor="none", edgecolor=g.RULE_HEX,
                           linestyle=(0, (2, 2)), linewidth=0.5, zorder=10))
    ax.text(cx, cy - ah / 2 + 0.05 - 0.18, "shipping label area",
            ha="center", va="top", family="IBM Plex Sans", fontsize=6,
            color=g.MUTED_HEX, alpha=0.7, zorder=10)
    ax.text(cx, y + 0.25,
            "Designed in New York · Printed on FSC paperboard · "
            "Recycle this carton.",
            ha="center", va="center", family="IBM Plex Sans",
            fontsize=6.5, color=g.MUTED_HEX, alpha=0.85, zorder=10)


def render(box: g.BoxSize, out_path: Path):
    _set_style()
    fig = plt.figure(figsize=(PAGE_W_IN, PAGE_H_IN), dpi=300,
                     facecolor=g.BG_HEX)
    ax = fig.add_axes([0.05, 0.06, 0.90, 0.78])
    ax.set_facecolor(g.BG_HEX)
    ax.set_aspect("equal")

    # Compute view limits with margin
    view_pad = 0.7
    view_w = box.flat_width_in + 2 * view_pad
    view_h = box.flat_height_in + 2 * view_pad
    ax.set_xlim(-view_pad, box.flat_width_in + view_pad)
    ax.set_ylim(-view_pad - 0.5, box.flat_height_in + view_pad + 0.3)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    rects = box.panel_rects()
    # ----- bleed boundary (around the entire dieline footprint) -----------
    _draw_bleed(ax, 0, 0, box.flat_width_in, box.flat_height_in)

    # ----- panels --------------------------------------------------------
    panel_labels = {
        "front":   "FRONT",
        "bottom":  "BOTTOM",
        "back":    "BACK",
        "lid":     "LID · top",
        "tuck":    "tuck flap",
        "left":    "LEFT side",
        "right":   "RIGHT side",
        "glue_l":  "glue tab",
        "glue_r":  "glue tab",
        "dust_lt": "dust flap",
        "dust_lb": "dust flap",
        "dust_rt": "dust flap",
        "dust_rb": "dust flap",
    }
    panel_dims = {
        "front":  f"{box.L:.0f}× {box.D:.0f} in",
        "bottom": f"{box.L:.0f}× {box.W:.0f} in",
        "back":   f"{box.L:.0f}× {box.D:.0f} in",
        "lid":    f"{box.L:.0f}× {box.D:.0f} in",
        "left":   f"{box.W:.0f}× {box.W:.0f} in",
        "right":  f"{box.W:.0f}× {box.W:.0f} in",
    }
    for name, (x, y, w, h) in rects.items():
        if name.startswith("glue") or name.startswith("dust"):
            color = "#EAE2D0"  # darker tint to read as "fold tab"
        else:
            color = g.BONE_HEX
        _draw_panel(ax, name, x, y, w, h, label=panel_labels.get(name, name),
                    color=color, dims_label=panel_dims.get(name))
        if name in ("lid", "front", "back", "left", "right", "bottom"):
            _draw_safety(ax, x, y, w, h)

    # ----- folds ---------------------------------------------------------
    for x1, y1, x2, y2 in box.fold_lines():
        _draw_fold(ax, x1, y1, x2, y2)

    # ----- design layout overlay -----------------------------------------
    _design_overlay_lid(ax, *rects["lid"])
    _design_overlay_front(ax, *rects["front"])
    _design_overlay_back(ax, *rects["back"])
    _design_overlay_side(ax, *rects["left"])
    _design_overlay_side(ax, *rects["right"])
    _design_overlay_bottom(ax, *rects["bottom"])

    # ----- dimensions ----------------------------------------------------
    bx, by, bw, bh = rects["bottom"]
    fx, fy, fw, fh = rects["front"]
    lx, ly, lw, lh = rects["left"]
    # Bottom width L (under front panel)
    _draw_dimension(ax, bx, fy, bx + bw, fy,
                    f"L = {box.L:.0f} in  ·  {box.L_mm:.0f} mm",
                    offset=0.55, side="bottom")
    # Bottom height W (left of left side)
    _draw_dimension(ax, lx, ly, lx, ly + lh,
                    f"W = {box.W:.0f} in  ·  {box.W_mm:.0f} mm",
                    offset=0.55, side="left")
    # Side depth W (already labeled by W on left)
    # Front depth D (right of right side)
    rx, ry, rw, rh = rects["right"]
    _draw_dimension(ax, rx + rw, fy, rx + rw, fy + fh,
                    f"D = {box.D:.0f} in  ·  {box.D_mm:.0f} mm",
                    offset=0.55, side="right")

    # Outer flat dieline overall
    _draw_dimension(ax, 0, box.flat_height_in, box.flat_width_in,
                    box.flat_height_in,
                    f"flat dieline: {box.flat_width_in:.2f} in × "
                    f"{box.flat_height_in:.2f} in",
                    offset=1.0, side="top")

    # ----- header chrome -------------------------------------------------
    fig.text(0.05, 0.945, "Aplomb",
             family="Cormorant Garamond", fontstyle="italic",
             fontweight="medium", fontsize=22, color=g.INK_HEX)
    fig.text(0.097, 0.945, ".", family="Cormorant Garamond",
             fontstyle="italic", fontweight="bold", fontsize=22,
             color=g.AMBER_HEX)
    fig.text(0.05, 0.918, "Mailer schematic — for Packlane prepress",
             family="IBM Plex Sans", fontsize=10, color=g.MUTED_HEX)
    fig.text(0.05, 0.895, box.label,
             family="IBM Plex Sans", fontsize=12, color=g.INK_HEX,
             fontweight="medium")
    fig.text(0.95, 0.945, "§ Outer packaging  ·  v1",
             family="IBM Plex Sans", fontsize=9, color=g.AMBER_HEX,
             ha="right")
    # Hairline rule under header
    fig.add_artist(Line2D([0.05, 0.95], [0.880, 0.880],
                          color=g.RULE_HEX, linewidth=0.5))

    # ----- legend --------------------------------------------------------
    legend_y = 0.04
    legend_handles = [
        mpatches.Patch(facecolor=g.BONE_HEX, edgecolor=g.INK_HEX,
                       label="Bone fill #F7F1E6 (panel surface)"),
        Line2D([0], [0], color=g.INK_HEX, lw=1.0,
               label="Cut line (knife)"),
        Line2D([0], [0], color="#C2392E", lw=0.7, linestyle=(0, (3, 2)),
               label="Fold / crease line"),
        Line2D([0], [0], color="#3F8C4A", lw=0.7, linestyle=(0, (4, 2)),
               label="Bleed boundary (extend artwork to here, +0.25\" past cut)"),
        Line2D([0], [0], color=g.MUTED_HEX, lw=0.4, linestyle=":",
               label="Safety zone (keep type 0.125\" inside cut + crease)"),
        Line2D([0], [0], color=g.AMBER_HEX, lw=0.7,
               label="Dimension callout (inside dimension, ±0.125\" tolerance)"),
    ]
    fig.legend(handles=legend_handles, loc="lower left",
               bbox_to_anchor=(0.05, legend_y), frameon=False, fontsize=8,
               labelcolor=g.INK_HEX)

    # ----- footer copy ---------------------------------------------------
    fig.text(0.05, 0.018,
             "Material — White HDPrint matte paperboard · Print method — "
             "C500 single-pass digital · CMYK · 0.25\" bleed · 0.125\" safety  ·  "
             "request official dieline at packlane.com/dieline-request",
             family="IBM Plex Sans", fontsize=8, color=g.MUTED_HEX)

    fig.savefig(out_path, format="pdf", facecolor=g.BG_HEX,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {out_path.name}  ({out_path.stat().st_size // 1024} KB)")


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for box in g.ALL_SIZES:
        suffix = "Small_6x4x3" if box is g.SMALL else "Large_7x5x3"
        out = OUT_DIR / f"Aplomb_Mailer_{suffix}_Schematic.pdf"
        render(box, out)


if __name__ == "__main__":
    render_all()
