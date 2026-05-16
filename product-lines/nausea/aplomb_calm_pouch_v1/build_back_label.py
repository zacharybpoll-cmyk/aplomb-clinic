"""
Aplomb.Calm — back-of-pouch label generator
Renders print-ready SVG (glyphs outlined to paths) + PDF.

Canvas: 126 mm W x 196 mm H (120x190 face + 3mm bleed all sides).
Safe zone: 6mm inside the bleed = 114 x 184 mm.

Brand tokens come from BRAND.md. CMYK conversions live in the spec PDF;
the SVG/PDF here are sRGB so they preview correctly in Preview/browsers.
The supplier converts to CMYK at the prepress step using values in the spec.
"""

from __future__ import annotations

import matplotlib as mpl

mpl.rcParams["svg.fonttype"] = "path"  # outline glyphs in SVG
mpl.rcParams["pdf.fonttype"] = 42       # TrueType subset in PDF
mpl.rcParams["text.usetex"] = False

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon
from matplotlib.lines import Line2D
from pathlib import Path

# ---------- brand tokens ----------
PAPER = "#f7f1e6"     # pouch substrate (matches front)
INK   = "#1a1512"     # body type
AMBER = "#7a3d14"     # brand period, rules, plumb-bob
INK60 = "#6e6864"     # ~60% ink, for FDA disclaimer
SERIF = "Cormorant Garamond"
SANS  = "IBM Plex Sans"

# ---------- canvas ----------
MM_TO_IN = 1.0 / 25.4
W_MM, H_MM = 126.0, 196.0   # bleed canvas
BLEED = 3.0
SAFE  = 6.0                 # gutter from bleed edge
FACE_W = W_MM - 2 * BLEED   # 120
FACE_H = H_MM - 2 * BLEED   # 190

# inner safe-area corners (in mm, measured from canvas origin lower-left)
SX0 = BLEED + SAFE          # 9
SY0 = BLEED + SAFE          # 9
SX1 = W_MM - BLEED - SAFE   # 117
SY1 = H_MM - BLEED - SAFE   # 187
SW  = SX1 - SX0             # 108
SH  = SY1 - SY0             # 178

OUT_DIR = Path(__file__).resolve().parent
SVG_OUT = OUT_DIR / "Aplomb_Calm_Back_Label.svg"
PDF_OUT = OUT_DIR / "Aplomb_Calm_Back_Label.pdf"
PNG_OUT = OUT_DIR / "Aplomb_Calm_Back_Label.png"  # for compositing

# ---------- content ----------
BRAND_PARAGRAPH = (
    "A daily ginger gummy for the nausea that arrives with GLP-1 medications. "
    "Cochrane-grade evidence. Editorial in tone, clinical in formulation."
)

SUPP_FACTS = {
    "serving_size": "2 gummies (6 g)",
    "servings_per": "15",
    "rows": [
        ("Calories", "20", ""),
        ("Total Carbohydrate", "5 g", "2%*"),
        ("   Total Sugars", "3 g", "†"),
        ("        Incl. Added Sugars", "3 g", "6%*"),
    ],
    "actives": [
        ("Ginger Root Extract (Zingiber officinale)\n5% gingerols, std.", "1 g", "†"),
    ],
    "footnotes": [
        "* Percent Daily Values are based on a 2,000-calorie diet.",
        "† Daily Value not established.",
    ],
}

OTHER_INGREDIENTS = (
    "Tapioca syrup, organic cane sugar, pectin (citrus peel), citric acid, "
    "natural ginger flavor, carrot juice concentrate (color), sunflower oil, "
    "carnauba wax."
)

ALLERGENS = "Contains no Big-9 allergens. Vegan. Gluten-free. Dairy-free."

DIRECTIONS = (
    "Take 1 to 2 gummies 30 minutes before injection, "
    "and as needed for nausea (max 4 per day)."
)

WARNINGS = (
    "Consult physician if pregnant or on anticoagulants. "
    "Not for under 18. Discontinue if reactions occur."
)

STORAGE = "Store cool and dry, away from direct light. Reseal pouch after use."

DISTRIBUTED = (
    "Distributed by Aplomb Health, Inc. · 4140 Glencoe Ave, Apt 503, "
    "Marina del Rey, CA 90292 · getaplomb.com · hello@getaplomb.com"
)

DISCLAIMER = (
    "These statements have not been evaluated by the Food and Drug "
    "Administration. This product is not intended to diagnose, treat, "
    "cure, or prevent any disease."
)


# ---------- helpers ----------
def setup_axes():
    fig = plt.figure(figsize=(W_MM * MM_TO_IN, H_MM * MM_TO_IN), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_MM)
    ax.set_ylim(0, H_MM)
    ax.set_aspect("equal")
    ax.axis("off")
    # pouch substrate
    ax.add_patch(Rectangle((0, 0), W_MM, H_MM, facecolor=PAPER, edgecolor="none"))
    return fig, ax


def amber_rule(ax, y, x0=SX0, x1=SX1, lw=0.6):
    ax.add_line(Line2D([x0, x1], [y, y], color=AMBER, linewidth=lw, solid_capstyle="butt"))


def plumb_bob(ax, cx, cy_top, height=10.0, color=AMBER):
    """Mini plumb-bob mark, scaled. Top of thread at cy_top, total height=height mm."""
    thread_h = height * 0.58
    bob_h    = height * 0.42
    bob_half = bob_h * 0.42  # half-width
    cy_thread_bot = cy_top - thread_h
    cy_bob_bot    = cy_thread_bot - bob_h
    # thread
    ax.add_line(Line2D([cx, cx], [cy_thread_bot, cy_top],
                       color=color, linewidth=0.65, solid_capstyle="butt"))
    # bob: diamond pointing down
    bob = Polygon(
        [(cx, cy_thread_bot),
         (cx + bob_half, cy_thread_bot - bob_h * 0.32),
         (cx, cy_bob_bot),
         (cx - bob_half, cy_thread_bot - bob_h * 0.32)],
        closed=True, facecolor=color, edgecolor="none",
    )
    ax.add_patch(bob)


def text(ax, x, y, s, *, size=7, weight="regular", style="normal",
         color=INK, ha="left", va="baseline", family=SANS, spacing=1.2):
    """Wrapper around ax.text using points for font size."""
    ax.text(x, y, s, fontsize=size, fontweight=weight, fontstyle=style,
            color=color, ha=ha, va=va, family=family, linespacing=spacing,
            transform=ax.transData)


def wrap_text(ax, x, y, s, *, width_mm, size=7, color=INK,
              family=SANS, leading=None, weight="regular", style="normal"):
    """Manual word-wrap then render line by line. Returns new y (bottom after last line)."""
    import textwrap
    # rough char-per-mm: at 7pt IBM Plex Sans ~ 1.55 mm per char average
    char_mm = size * 0.22
    chars_per_line = max(10, int(width_mm / char_mm))
    leading_mm = (leading if leading else size * 0.40)
    lines = []
    for para in s.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=chars_per_line)) or lines.append("")
    yi = y
    for ln in lines:
        text(ax, x, yi, ln, size=size, color=color, family=family,
             weight=weight, style=style, va="top")
        yi -= leading_mm
    return yi


# ---------- supplement facts panel ----------
def draw_supp_facts(ax, x, y, w):
    """FDA 21 CFR 101.36 layout, content-driven height. Returns box bottom y."""
    yi = y - 1.6
    text(ax, x + 2.0, yi, "Supplement Facts",
         size=10.5, weight="bold", family=SANS, va="top", color=INK)
    yi -= 5.4
    text(ax, x + 2.0, yi, f"Serving Size  {SUPP_FACTS['serving_size']}",
         size=6.8, family=SANS, va="top", color=INK)
    yi -= 3.0
    text(ax, x + 2.0, yi, f"Servings Per Container  {SUPP_FACTS['servings_per']}",
         size=6.8, family=SANS, va="top", color=INK)
    yi -= 2.0
    ax.add_line(Line2D([x + 1.0, x + w - 1.0], [yi, yi],
                       color=INK, linewidth=2.0, solid_capstyle="butt"))
    yi -= 2.8
    text(ax, x + 2.0, yi, "Amount Per Serving",
         size=6.4, weight="bold", family=SANS, va="top", color=INK)
    text(ax, x + w - 2.0, yi, "% Daily Value",
         size=6.4, weight="bold", family=SANS, va="top", color=INK, ha="right")
    yi -= 1.4
    ax.add_line(Line2D([x + 1.0, x + w - 1.0], [yi, yi],
                       color=INK, linewidth=0.5, solid_capstyle="butt"))
    yi -= 2.6
    for label, amount, dv in SUPP_FACTS["rows"]:
        text(ax, x + 2.0, yi, label, size=6.4, family=SANS, va="top", color=INK)
        text(ax, x + w * 0.66, yi, amount, size=6.4, family=SANS, va="top", color=INK)
        text(ax, x + w - 2.0, yi, dv, size=6.4, family=SANS, va="top", color=INK, ha="right")
        yi -= 3.2
        ax.add_line(Line2D([x + 1.0, x + w - 1.0], [yi + 0.4, yi + 0.4],
                           color=INK, linewidth=0.25, solid_capstyle="butt"))
        yi -= 0.4
    yi -= 0.4
    ax.add_line(Line2D([x + 1.0, x + w - 1.0], [yi, yi],
                       color=INK, linewidth=1.2, solid_capstyle="butt"))
    yi -= 2.8
    for label, amount, dv in SUPP_FACTS["actives"]:
        lines = label.split("\n")
        for j, ln in enumerate(lines):
            text(ax, x + 2.0, yi - j * 2.8, ln,
                 size=6.4, weight="bold" if j == 0 else "regular",
                 family=SANS, va="top", color=INK)
        text(ax, x + w * 0.66, yi, amount,
             size=6.4, weight="bold", family=SANS, va="top", color=INK)
        text(ax, x + w - 2.0, yi, dv,
             size=6.4, family=SANS, va="top", color=INK, ha="right")
        yi -= 2.8 * len(lines)
    yi -= 0.4
    ax.add_line(Line2D([x + 1.0, x + w - 1.0], [yi, yi],
                       color=INK, linewidth=0.5, solid_capstyle="butt"))
    yi -= 2.6
    for fn in SUPP_FACTS["footnotes"]:
        text(ax, x + 2.0, yi, fn, size=5.8, family=SANS, va="top", color=INK)
        yi -= 2.4
    bottom = yi - 0.6
    # outer box, drawn from y (top) down to actual content bottom
    ax.add_patch(Rectangle((x, bottom), w, y - bottom,
                           facecolor="none", edgecolor=INK, linewidth=0.8))
    return bottom


def label_block(ax, x, y, w, h_box, label_text, fill="white"):
    """Dashed-outline imprint zone for supplier (LOT / Best-By)."""
    rect = Rectangle((x, y - h_box), w, h_box,
                     facecolor=fill, edgecolor=INK,
                     linewidth=0.8, linestyle=(0, (2.0, 1.6)))
    ax.add_patch(rect)
    text(ax, x + w / 2, y - h_box / 2, label_text,
         size=6.4, family=SANS, ha="center", va="center",
         color=INK, style="italic")


# ---------- build ----------
def build():
    fig, ax = setup_axes()

    # --- thin amber border around the entire safe zone.
    # Defines the print rectangle so the eye reads "the entire face is printed"
    # even where there's whitespace between text blocks. Drawn first so all
    # content sits on top.
    border_inset = 1.5   # small inward inset so content does not crowd the line
    ax.add_patch(Rectangle(
        (SX0 - border_inset, SY0 - border_inset),
        SW + 2 * border_inset, SH + 2 * border_inset,
        facecolor="none", edgecolor=AMBER, linewidth=0.5,
    ))

    # --- top: brand mark + wordmark, identical mood to front, smaller ---
    cx = W_MM / 2
    mark_top = SY1 - 2.0
    plumb_bob(ax, cx, mark_top, height=11.0, color=AMBER)

    word_y = mark_top - 14.5
    # wordmark "Aplomb." italic, amber period
    text(ax, cx - 0.4, word_y, "Aplomb", size=18, family=SERIF, style="italic",
         weight="medium", color=INK, ha="right", va="baseline")
    text(ax, cx - 0.4, word_y, ".", size=18, family=SERIF, style="italic",
         weight="medium", color=AMBER, ha="left", va="baseline")

    # subhead, mirrors front-of-pouch sub
    sub_y = word_y - 7.0
    text(ax, cx, sub_y, "G I N G E R   G U M M I E S   F O R   G L P-1   N A U S E A",
         size=6.0, family=SANS, color=AMBER, ha="center", va="baseline",
         weight="medium")

    # amber rule under header
    amber_rule(ax, sub_y - 3.5)

    # --- section: brand paragraph ---
    sec_label_y = sub_y - 7.5
    text(ax, SX0, sec_label_y, "Why Calm.",
         size=9.5, family=SERIF, style="italic", color=INK, va="top")
    body_y = sec_label_y - 3.6
    body_y = wrap_text(ax, SX0, body_y, BRAND_PARAGRAPH,
                      width_mm=SW, size=7.0, family=SANS, color=INK)

    # amber rule
    amber_rule(ax, body_y - 2.8)

    # --- supplement facts panel ---
    sf_top = body_y - 4.5
    sf_end = draw_supp_facts(ax, SX0, sf_top, SW)

    # --- Other Ingredients ---
    oi_y = sf_end - 3.6
    text(ax, SX0, oi_y, "Other Ingredients:",
         size=6.4, family=SANS, weight="bold", color=INK, va="top")
    oi_body_y = oi_y - 2.8
    oi_body_y = wrap_text(ax, SX0, oi_body_y, OTHER_INGREDIENTS,
                          width_mm=SW, size=6.4, family=SANS, color=INK,
                          leading=2.5)

    # Allergens
    al_y = oi_body_y - 1.6
    text(ax, SX0, al_y, ALLERGENS,
         size=6.4, family=SANS, color=INK, va="top", weight="medium")

    # Storage line (just below allergens, before D/W box).
    storage_y = al_y - 4.4
    text(ax, SX0, storage_y, STORAGE,
         size=6.2, family=SANS, color=INK, va="top")

    # Distributed-by (small two-line block, just below storage).
    import textwrap as _tw
    di_size = 6.0
    di_lead = 2.3
    di_char_mm = di_size * 0.22
    di_cpl = max(10, int(SW / di_char_mm))
    di_lines = _tw.wrap(DISTRIBUTED, width=di_cpl)
    di_top = storage_y - 3.6
    yi = di_top
    for ln in di_lines:
        text(ax, SX0, yi, ln, size=di_size, family=SANS, color=INK, va="top")
        yi -= di_lead
    di_bottom = yi + di_lead - 2.0   # approx bottom of last line

    # amber rule under the meta block
    amber_rule(ax, di_bottom - 1.5)

    # Anchor for the D/W box top — tight against the amber rule above.
    al_y = di_bottom - 2.5

    # --- Directions + Warnings, side-by-side, wrapped in a single bordered box.
    # The box gives the lower-mid section a visual anchor matching the Supp Facts
    # panel above, so the eye reads "this whole face is printed" not "top only".
    dw_pad_x = 2.5   # horizontal text inset from box edges
    dw_pad_top = 2.5
    dw_pad_bot = 2.0
    col_y = al_y - 2.0 - dw_pad_top
    col_inner_w = SW - 2 * dw_pad_x          # usable inner width
    col_w = (col_inner_w - 4.0) / 2          # each column width

    text(ax, SX0 + dw_pad_x, col_y, "Directions.",
         size=8.2, family=SERIF, style="italic", color=INK, va="top")
    dir_body_y = col_y - 3.0
    dir_body_y = wrap_text(ax, SX0 + dw_pad_x, dir_body_y, DIRECTIONS,
                           width_mm=col_w, size=5.4, family=SANS, color=INK,
                           leading=2.1)

    mid_x = SX0 + dw_pad_x + col_w + 4.0
    text(ax, mid_x, col_y, "Warnings.",
         size=8.2, family=SERIF, style="italic", color=INK, va="top")
    wn_body_y = col_y - 3.0
    wn_body_y = wrap_text(ax, mid_x, wn_body_y, WARNINGS,
                          width_mm=col_w, size=5.4, family=SANS, color=INK,
                          leading=2.1)

    block_bottom = min(dir_body_y, wn_body_y)

    # Draw the box around both columns + the vertical divider between them.
    box_top = col_y + dw_pad_top
    box_bot = block_bottom - dw_pad_bot
    ax.add_patch(Rectangle(
        (SX0, box_bot), SW, box_top - box_bot,
        facecolor="none", edgecolor=INK, linewidth=0.6,
    ))
    div_x = SX0 + dw_pad_x + col_w + 2.0
    ax.add_line(Line2D([div_x, div_x], [box_bot + 1.5, box_top - 1.5],
                       color=INK, linewidth=0.4, solid_capstyle="butt"))

    block_bottom = box_bot   # for downstream layout

    # --- Bottom-up layout, with bookend Aplomb mark + footer tagline band ---
    # Order from canvas bottom upward:
    #   bottom Aplomb plumb-bob mark
    #   LOT / BEST BY box
    #   footer band: amber rule + tracked tagline + amber rule
    #   FDA disclaimer
    #   Distributed-by
    #   Storage

    # 1. Bottom Aplomb plumb-bob mark (bookends the top mark).
    bot_mark_top = SY0 + 3.5
    plumb_bob(ax, W_MM / 2, bot_mark_top, height=3.5, color=AMBER)

    # 2. LOT / BEST BY imprint zone.
    lot_h = 9.0
    lot_w = 70.0
    lot_x = SX0 + (SW - lot_w) / 2
    lot_top = bot_mark_top + 1.5 + lot_h
    label_block(ax, lot_x, lot_top, lot_w, lot_h,
                "LOT / BEST BY  [supplier imprint]")

    # 3. FDA disclaimer — sits ABOVE the LOT box, BELOW the D/W box.
    fda_size = 5.0
    fda_lead = 2.0
    fda_text_h = 1.7
    fda_char_mm = fda_size * 0.22
    fda_cpl = max(10, int(SW / fda_char_mm))
    fda_lines = _tw.wrap(DISCLAIMER, width=fda_cpl)
    n_fda = len(fda_lines)
    fda_last_bottom = lot_top + 2.0       # 2mm above LOT box top edge
    fda_top = fda_last_bottom + (n_fda - 1) * fda_lead + fda_text_h
    yi = fda_top
    for ln in fda_lines:
        text(ax, SX0, yi, ln, size=fda_size, family=SANS, color=INK,
             style="italic", va="top")
        yi -= fda_lead

    # 4. Tagline rule + centered tagline (replaces the prior multi-rule band).
    #    This is a single visual element sitting between FDA and D/W box.
    tag_y = fda_top + 3.5
    amber_rule(ax, tag_y - 1.8)
    text(ax, W_MM / 2, tag_y, "30 GUMMIES   ·   1 G GINGER PER SERVING   ·   NET WT 90 G",
         size=6.4, family=SANS, color=AMBER, ha="center", va="center",
         weight="bold")
    amber_rule(ax, tag_y + 1.8)
    tag_top = tag_y + 1.8

    # Sanity check: the D/W box bottom must be ABOVE the tagline top rule.
    if block_bottom <= tag_top + 2.0:
        print(f"⚠ collision: D/W box bottom y={block_bottom:.1f}, tagline top y={tag_top:.1f}")

    # --- bleed/safe guides as a separate layer would be on the schematic,
    #     not on the artwork itself. Keep clean.

    # --- save ---
    fig.savefig(SVG_OUT, format="svg", facecolor=PAPER)
    fig.savefig(PDF_OUT, format="pdf", facecolor=PAPER)
    fig.savefig(PNG_OUT, format="png", facecolor=PAPER, dpi=420)
    plt.close(fig)
    print(f"✓ wrote {SVG_OUT.name}, {PDF_OUT.name}, {PNG_OUT.name}")


if __name__ == "__main__":
    build()
