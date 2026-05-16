"""
Aplomb.Calm pouch schematic / dieline.
Renders both faces (front + back) with bleed, safe zone, tear-notch position,
gusset note, and dimension callouts. PDF + SVG output.
"""

from __future__ import annotations

import matplotlib as mpl
mpl.rcParams["svg.fonttype"] = "path"
mpl.rcParams["pdf.fonttype"] = 42

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon
from matplotlib.lines import Line2D
from pathlib import Path

PAPER = "#f7f1e6"
INK   = "#1a1512"
AMBER = "#7a3d14"
GUIDE = "#a89a7a"
INK60 = "#6e6864"
SANS  = "IBM Plex Sans"
SERIF = "Cormorant Garamond"

MM_TO_IN = 1.0 / 25.4

# Page: A3-ish landscape so we can show both faces side-by-side with dimensioning
PAGE_W, PAGE_H = 380.0, 290.0   # mm

# Pouch dims
FACE_W, FACE_H = 120.0, 190.0
BLEED = 3.0
SAFE = 6.0
GUSSET = 50.0

OUT_DIR = Path(__file__).resolve().parent
PDF_OUT = OUT_DIR / "Aplomb_Calm_Pouch_Schematic.pdf"
SVG_OUT = OUT_DIR / "Aplomb_Calm_Pouch_Schematic.svg"
PNG_OUT = OUT_DIR / "Aplomb_Calm_Pouch_Schematic.png"


def text(ax, x, y, s, *, size=8, color=INK, ha="left", va="baseline",
         family=SANS, style="normal", weight="regular"):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, family=family,
            fontstyle=style, fontweight=weight, transform=ax.transData)


def dim_h(ax, x0, x1, y, label, *, offset=4.0):
    """Horizontal dimension line with arrows + tick marks + label centered."""
    ax.add_line(Line2D([x0, x0], [y - 1.6, y + 1.6], color=INK60, linewidth=0.4))
    ax.add_line(Line2D([x1, x1], [y - 1.6, y + 1.6], color=INK60, linewidth=0.4))
    ax.add_line(Line2D([x0, x1], [y, y], color=INK60, linewidth=0.4))
    text(ax, (x0 + x1) / 2, y + offset, label, size=7, ha="center", color=INK60)


def dim_v(ax, y0, y1, x, label, *, offset=4.0, label_rot=90):
    ax.add_line(Line2D([x - 1.6, x + 1.6], [y0, y0], color=INK60, linewidth=0.4))
    ax.add_line(Line2D([x - 1.6, x + 1.6], [y1, y1], color=INK60, linewidth=0.4))
    ax.add_line(Line2D([x, x], [y0, y1], color=INK60, linewidth=0.4))
    ax.text(x - offset, (y0 + y1) / 2, label, fontsize=7, color=INK60,
            ha="center", va="center", rotation=label_rot, family=SANS,
            transform=ax.transData)


def draw_pouch_face(ax, x0, y0, *, title):
    """Draw one face with bleed/safe outlines and dimension lines."""
    # bleed rect
    bleed_w = FACE_W + 2 * BLEED
    bleed_h = FACE_H + 2 * BLEED
    ax.add_patch(Rectangle((x0, y0), bleed_w, bleed_h,
                           facecolor="none", edgecolor=AMBER,
                           linewidth=0.6, linestyle=(0, (4, 2))))
    # face rect (cut line)
    ax.add_patch(Rectangle((x0 + BLEED, y0 + BLEED), FACE_W, FACE_H,
                           facecolor=PAPER, edgecolor=INK,
                           linewidth=0.9))
    # safe zone
    sx0 = x0 + BLEED + SAFE
    sy0 = y0 + BLEED + SAFE
    sw = FACE_W - 2 * SAFE
    sh = FACE_H - 2 * SAFE
    ax.add_patch(Rectangle((sx0, sy0), sw, sh, facecolor="none",
                           edgecolor=GUIDE, linewidth=0.4,
                           linestyle=(0, (1.5, 1.5))))
    # zipper seal indicator (top 8mm)
    seal_y = y0 + BLEED + FACE_H - 8.0
    ax.add_line(Line2D([x0 + BLEED, x0 + BLEED + FACE_W],
                       [seal_y, seal_y], color=GUIDE, linewidth=0.4,
                       linestyle=(0, (2, 2))))
    text(ax, x0 + BLEED + FACE_W - 1.0, seal_y + 1.2,
         "zipper seal · 8 mm", size=6.4, color=GUIDE, ha="right")

    # tear notch (right edge, 35mm from top)
    notch_y = y0 + BLEED + FACE_H - 35.0
    notch_x = x0 + BLEED + FACE_W
    tri = Polygon([(notch_x, notch_y - 2.0),
                   (notch_x - 4.0, notch_y),
                   (notch_x, notch_y + 2.0)],
                  closed=True, facecolor=AMBER, edgecolor="none", alpha=0.85)
    ax.add_patch(tri)
    text(ax, notch_x + 2.0, notch_y, "tear notch  35 mm",
         size=6.4, color=AMBER, va="center")

    # title below face
    text(ax, x0 + bleed_w / 2, y0 - 14.0, title,
         size=11, family=SERIF, style="italic", color=INK, ha="center")

    # dim: face width (below face)
    dim_h(ax, x0 + BLEED, x0 + BLEED + FACE_W, y0 - 4.0, "120 mm face", offset=-4.0)
    # bleed width (above face)
    dim_h(ax, x0, x0 + bleed_w, y0 + bleed_h + 2.0, "126 mm bleed", offset=2.0)
    # face height (right side)
    dim_v(ax, y0 + BLEED, y0 + BLEED + FACE_H,
          x0 + bleed_w + 10.0, "190 mm face", offset=-4.0)
    # bleed height (further right)
    dim_v(ax, y0, y0 + bleed_h, x0 + bleed_w + 22.0, "196 mm bleed", offset=-4.0)

    # legend lines for safe zone
    text(ax, sx0 + 2.0, sy0 + 3.0, "Safe area (114 × 178 mm)",
         size=6.4, color=GUIDE, family=SANS)


def gusset_diagram(ax, cx, cy):
    """Small inset showing gusset depth and pouch capacity."""
    # rectangle for the gusset cross-section
    w = 42.0
    h = 22.0
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h,
                           facecolor=PAPER, edgecolor=INK, linewidth=0.8))
    # gusset triangles at sides
    ax.add_patch(Polygon([(cx - w / 2, cy - h / 2),
                          (cx - w / 2 + 14, cy),
                          (cx - w / 2, cy + h / 2)],
                         closed=True, facecolor=GUIDE, alpha=0.25,
                         edgecolor=GUIDE, linewidth=0.4))
    ax.add_patch(Polygon([(cx + w / 2, cy - h / 2),
                          (cx + w / 2 - 14, cy),
                          (cx + w / 2, cy + h / 2)],
                         closed=True, facecolor=GUIDE, alpha=0.25,
                         edgecolor=GUIDE, linewidth=0.4))
    text(ax, cx, cy + h / 2 + 5, "Cross-section (top view)",
         size=8, family=SERIF, style="italic", color=INK, ha="center")
    text(ax, cx, cy - h / 2 - 5, "50 mm gusset · ~ 90 g capacity",
         size=6.8, color=INK60, ha="center")


def callout_box(ax, x, y, w, h, lines, *, title):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=PAPER,
                           edgecolor=INK60, linewidth=0.4))
    text(ax, x + 3, y + h - 5, title, size=9,
         family=SERIF, style="italic", color=INK)
    yi = y + h - 11
    for ln in lines:
        text(ax, x + 3, yi, ln, size=6.6, color=INK, family=SANS)
        yi -= 3.2


def build():
    fig = plt.figure(figsize=(PAGE_W * MM_TO_IN, PAGE_H * MM_TO_IN), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), PAGE_W, PAGE_H, facecolor="white", edgecolor="none"))

    # header
    text(ax, 18, PAGE_H - 14, "Aplomb", size=18,
         family=SERIF, style="italic", color=INK)
    text(ax, 47.5, PAGE_H - 14, ".", size=18,
         family=SERIF, style="italic", color=AMBER)
    text(ax, 18, PAGE_H - 21,
         "Calm · pouch schematic & dieline · v1", size=9,
         family=SERIF, style="italic", color=INK60)
    text(ax, PAGE_W - 18, PAGE_H - 14,
         "Stand-up pouch · 120 × 190 × 50 mm · matte CMYK",
         size=9, family=SANS, color=INK60, ha="right")
    text(ax, PAGE_W - 18, PAGE_H - 21,
         "Bleed 3 mm · Safe 6 mm · Tear notch 35 mm from top",
         size=8, family=SANS, color=INK60, ha="right")

    ax.add_line(Line2D([18, PAGE_W - 18], [PAGE_H - 28, PAGE_H - 28],
                       color=AMBER, linewidth=0.5))

    # two faces (more vertical room: faces shorter Y, titles below them)
    fy = 58
    draw_pouch_face(ax,  44, fy, title="Front face · as printed")
    draw_pouch_face(ax, 210, fy, title="Back face · as printed")

    # gusset diagram between faces at mid-height
    gusset_diagram(ax, PAGE_W / 2, fy + (FACE_H + 2 * BLEED) / 2)

    # specs callout (bottom strip)
    callout_box(
        ax, 18, 12, PAGE_W - 36, 18,
        [
            "Substrate: PET 12 µm / Alu 8 µm / LDPE 100 µm laminate · matte external finish · CEFLEX-recyclable target",
            "Closure: zip-lock + tamper-evident tear notch (right edge, 35 mm from top) · Print: 4-color CMYK · matte varnish overall · no foil",
            "Type minimums: 5 pt disclaimer · 6 pt body · 8 pt Supplement Facts headers · all glyphs outlined to paths in SVG/PDF",
        ],
        title="Production specifications",
    )

    fig.savefig(PDF_OUT, format="pdf", facecolor="white")
    fig.savefig(SVG_OUT, format="svg", facecolor="white")
    fig.savefig(PNG_OUT, format="png", facecolor="white", dpi=240)
    plt.close(fig)
    print(f"✓ wrote {PDF_OUT.name}, {SVG_OUT.name}, {PNG_OUT.name}")


if __name__ == "__main__":
    build()
