"""
Box geometry — Packlane standard mailer-box (RETT) dieline layout.

Packlane defines all box sizes by INSIDE dimensions L × W × D inches.
We model the flat dieline in INCHES (Packlane's authoritative unit) and
provide millimeter conversions for the schematic + spec sheet.

Standard mailer flat layout, viewed from the box exterior (lid panel reads
right-side-up to a recipient looking at it):

              ┌─────────────────────┐
              │    TUCK FLAP        │  tuck_h
              ├─────────────────────┤
              │       LID           │  D  (lid depth = box depth on close)
              ├─────────────────────┤
              │       BACK          │  D
        ┌─────┼─────────────────────┼─────┐
        │ DUST│                     │ DUST│  flaps fold inside
        │FLAP │                     │FLAP │
        ├─────┤                     ├─────┤
        │     │                     │     │
        │LEFT │       BOTTOM        │RIGHT│  bottom = L × W, sides = W × D
        │     │                     │     │
        ├─────┤                     ├─────┤
        │ DUST│                     │ DUST│
        │FLAP │                     │FLAP │
        └─────┼─────────────────────┼─────┘
              │       FRONT         │  D
              └─────────────────────┘

In the dieline, we orient the BOTTOM as the central horizontal panel,
LID + BACK above, FRONT below, LEFT/RIGHT to the sides. The TUCK FLAP
extends above the LID and folds INTO the front when the box closes.
"""

from dataclasses import dataclass


# ----- Packlane spec constants ---------------------------------------------

BLEED_IN = 0.25            # 0.25" bleed around outer cut line
SAFE_IN = 0.125            # 0.125" safety zone inside cut and fold lines
TOL_IN = 0.125             # ±0.125" Packlane manufacturing tolerance
MM_PER_IN = 25.4

# Flute thickness adds to dust-flap geometry; use 0.0625" (E-flute) by default
FLUTE_IN = 0.0625


# ----- Brand tokens (verbatim from brand/BRAND.md + index.html) ------------

BONE_HEX = "#F7F1E6"      # paper / exterior fill
BG_HEX = "#EFE8DC"        # page bg (mockup background)
INK_HEX = "#1A1512"       # primary text
AMBER_HEX = "#7A3D14"     # brand amber — wordmark + plumb mark
RULE_HEX = "#D9CFBD"      # hairline rules
MUTED_HEX = "#6B5D4C"     # secondary text


# ----- CMYK conversions (printer-ready) ------------------------------------
# These are the values Packlane prepress should use. Conversions follow
# US web-coated SWOP. Bone is a near-paper color so we leave it as zero
# coverage (k=0) and let the white paper show through.

CMYK = {
    "bone": (0, 3, 8, 3),       # very faint warm tint; mostly paper
    "ink":  (0, 30, 40, 90),    # near-black brown
    "amber": (0, 55, 85, 55),   # deep amber #7A3D14 in CMYK
    "rule": (0, 5, 12, 18),     # hairline tan
    "muted": (0, 12, 25, 65),   # warm grey
}


@dataclass(frozen=True)
class BoxSize:
    """Packlane mailer box, all measurements in INCHES (interior)."""

    sku: str        # human label e.g. "Small (6x4x3)"
    L: float        # length (front-to-back when closed and viewed from above)
    W: float        # width (side-to-side)
    D: float        # depth (height when closed, lid-to-bottom)
    fits: list      # SKUs this box accommodates
    tuck_in: float = 1.5    # tuck flap height (Packlane standard ~1.5" for D=3)
    dust_in: float = 1.0    # dust flap depth
    glue_tab_in: float = 0.5  # glue tab width on outer edge of side panels

    @property
    def L_mm(self): return self.L * MM_PER_IN

    @property
    def W_mm(self): return self.W * MM_PER_IN

    @property
    def D_mm(self): return self.D * MM_PER_IN

    @property
    def label(self):
        return (f"{self.sku}  ·  {self.L:.0f}×{self.W:.0f}×{self.D:.0f} in  "
                f"·  {self.L_mm:.0f}×{self.W_mm:.0f}×{self.D_mm:.0f} mm")

    # ------- Flat-dieline bounding box (excludes bleed) --------------------

    @property
    def flat_width_in(self):
        # left-side (W) + bottom (L) + right-side (W) + 2× glue tabs
        return self.W + self.L + self.W + 2 * self.glue_tab_in

    @property
    def flat_height_in(self):
        # tuck flap + lid (D) + back (D) + bottom (W) + front (D)
        return self.tuck_in + self.D + self.D + self.W + self.D

    @property
    def total_width_in(self):
        return self.flat_width_in + 2 * BLEED_IN

    @property
    def total_height_in(self):
        return self.flat_height_in + 2 * BLEED_IN

    # ------- Panel rectangles (origin = bottom-left of dieline excl. bleed) -

    def panel_rects(self):
        """Return dict of panel name -> (x, y, w, h) in inches.
        Origin is bottom-left of the dieline cut area (not the bleed bbox).
        Y grows upward."""
        # x-axis layout
        x_glue_l = 0.0
        x_left = self.glue_tab_in
        x_bottom = x_left + self.W
        x_right = x_bottom + self.L
        x_glue_r = x_right + self.W
        # y-axis layout (bottom up)
        y_front = 0.0
        y_bottom = y_front + self.D
        y_back = y_bottom + self.W
        y_lid = y_back + self.D
        y_tuck = y_lid + self.D

        return {
            # Center column (vertical strip)
            "front":   (x_bottom, y_front, self.L, self.D),
            "bottom":  (x_bottom, y_bottom, self.L, self.W),
            "back":    (x_bottom, y_back, self.L, self.D),
            "lid":     (x_bottom, y_lid, self.L, self.D),
            "tuck":    (x_bottom, y_tuck, self.L, self.tuck_in),
            # Side wings (only run alongside the bottom panel)
            "left":    (x_left, y_bottom, self.W, self.W),
            "right":   (x_right, y_bottom, self.W, self.W),
            # Glue tabs on far outside edges of the side panels
            "glue_l":  (x_glue_l, y_bottom, self.glue_tab_in, self.W),
            "glue_r":  (x_glue_r, y_bottom, self.glue_tab_in, self.W),
            # Dust flaps — small rectangles above and below LEFT and RIGHT sides
            "dust_lt": (x_left, y_bottom + self.W, self.W, self.dust_in),
            "dust_lb": (x_left, y_bottom - self.dust_in, self.W, self.dust_in),
            "dust_rt": (x_right, y_bottom + self.W, self.W, self.dust_in),
            "dust_rb": (x_right, y_bottom - self.dust_in, self.W, self.dust_in),
        }

    def fold_lines(self):
        """List of (x1, y1, x2, y2) fold-line segments in inches."""
        rects = self.panel_rects()
        bottom = rects["bottom"]
        bx, by, bw, bh = bottom
        lines = [
            # Left edge of bottom (between left side and bottom)
            (bx, by, bx, by + bh),
            # Right edge of bottom
            (bx + bw, by, bx + bw, by + bh),
            # Top edge of bottom (between bottom and back)
            (bx, by + bh, bx + bw, by + bh),
            # Bottom edge of bottom (between bottom and front)
            (bx, by, bx + bw, by),
            # Top of back (between back and lid)
            (bx, by + bh + self.D, bx + bw, by + bh + self.D),
            # Top of lid (between lid and tuck flap)
            (bx, by + bh + 2 * self.D, bx + bw, by + bh + 2 * self.D),
            # Bottom of front (between front and… well it's the cut line, no fold)
            # Glue tab folds: between left and glue_l, right and glue_r
            (rects["glue_l"][0] + rects["glue_l"][2], rects["glue_l"][1],
             rects["glue_l"][0] + rects["glue_l"][2], rects["glue_l"][1] + rects["glue_l"][3]),
            (rects["glue_r"][0], rects["glue_r"][1],
             rects["glue_r"][0], rects["glue_r"][1] + rects["glue_r"][3]),
            # Dust flap folds (between left/right and dust flaps above + below)
            (rects["left"][0], rects["left"][1] + rects["left"][3],
             rects["left"][0] + rects["left"][2], rects["left"][1] + rects["left"][3]),
            (rects["left"][0], rects["left"][1],
             rects["left"][0] + rects["left"][2], rects["left"][1]),
            (rects["right"][0], rects["right"][1] + rects["right"][3],
             rects["right"][0] + rects["right"][2], rects["right"][1] + rects["right"][3]),
            (rects["right"][0], rects["right"][1],
             rects["right"][0] + rects["right"][2], rects["right"][1]),
        ]
        return lines


# ----- Two production sizes ------------------------------------------------

SMALL = BoxSize(
    sku="Small (6×4×3)",
    L=6.0, W=4.0, D=3.0,
    fits=["Aplomb. Serum (30mL dropper)",
          "Aplomb. Daily (capsule bottle, 30-ct)",
          "Aplomb. Roots (capsule bottle, 30-ct)",
          "Aplomb. Composure Lozenge (60mm tin)"],
    tuck_in=1.5, dust_in=1.0, glue_tab_in=0.5,
)

LARGE = BoxSize(
    sku="Large (7×5×3)",
    L=7.0, W=5.0, D=3.0,
    fits=["Aplomb. Calm (30-day kit)"],
    tuck_in=1.5, dust_in=1.0, glue_tab_in=0.5,
)

ALL_SIZES = [SMALL, LARGE]


if __name__ == "__main__":
    for box in ALL_SIZES:
        print(box.label)
        print(f"  flat dieline: {box.flat_width_in:.2f} × {box.flat_height_in:.2f} in")
        print(f"  with bleed:   {box.total_width_in:.2f} × {box.total_height_in:.2f} in")
        print(f"  fits: {', '.join(box.fits)}")
        print()
