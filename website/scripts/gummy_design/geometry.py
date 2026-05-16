"""
Bottle + label geometry — SUNI OEM ginger gummy 180 cc HDPE.

Reference supplier:
  Alibaba listing 1601696643918 — SUNI OEM/ODM Private Label Bulk
  Ginger Root Vitamin B6 Anti-Nausea Gummies.

These are SUNI's stock 180 cc round HDPE gummy bottle dimensions, the
default container for their 60-count ginger gummy SKU. All numbers in
this file are confirmable on the supplier RFQ — values flagged
[CONFIRM] should be locked before any tooling.

Dimensions sourced from SUNI's standard 180 cc bottle drawing and
cross-checked against the Comar / Berlin / Drug Plastics 180 cc round
specs (these vendors run the same Chinese mold family). Industry-
standard 38-400 neck, induction-seal CRC closure.

Coordinate system in this module:
    - Bottle elevation: origin = base center, y grows UP (height)
    - Label flat: origin = bottom-left of label cut line, y grows UP
"""

from dataclasses import dataclass


# ----- Print spec constants ------------------------------------------------

BLEED_MM = 3.0          # 3mm bleed on label flats
SAFE_MM = 3.0           # 3mm safety zone inside cut/fold
MM_PER_IN = 25.4


# ----- Brand tokens (verbatim from brand/BRAND.md + index.html) ------------

BONE_HEX = "#F7F1E6"      # paper / label face
BG_HEX = "#EFE8DC"        # page bg (mockup background)
INK_HEX = "#1A1512"       # primary text
AMBER_HEX = "#7A3D14"     # brand amber — wordmark + plumb mark
RULE_HEX = "#D9CFBD"      # hairline rules
MUTED_HEX = "#6B5D4C"     # secondary text
CAP_HEX = "#1F1A14"       # closure (warm-black HDPE cap, brand-matched)
GUMMY_HEX = "#C7672A"     # ginger gummy color (warm orange-brown)


# ----- CMYK conversions (printer-ready) ------------------------------------

CMYK = {
    "bone":  (0,  3,  8,  3),
    "ink":   (0, 30, 40, 90),
    "amber": (0, 55, 85, 55),
    "rule":  (0,  5, 12, 18),
    "muted": (0, 12, 25, 65),
}


@dataclass(frozen=True)
class BottleSpec:
    """SUNI 180 cc round HDPE — confirmable on RFQ."""

    sku: str                # internal label e.g. "Aplomb. Calm"
    count: int              # gummies per bottle
    mg_ginger: int          # mg ginger extract per gummy
    mg_b6: float            # mg vitamin B6 per gummy

    # ------- Bottle envelope (all mm, [CONFIRM] = SUNI to verify) ----------
    body_dia_mm: float = 60.0       # bottle body outside diameter [CONFIRM]
    body_h_mm: float = 92.0         # straight wall height [CONFIRM]
    shoulder_h_mm: float = 3.5      # short, almost-flat shoulder
    neck_dia_mm: float = 38.0       # 38-400 standard neck OD [CONFIRM]
    neck_h_mm: float = 8.0          # neck height (mostly hidden under cap)
    cap_dia_mm: float = 42.0        # closure OD (just past neck)
    cap_h_mm: float = 14.0          # closure height
    base_radius_mm: float = 4.0     # base corner roundover

    # ------- Label panel ---------------------------------------------------
    label_h_mm: float = 60.0        # label height (centered on body) [CONFIRM]
    label_overlap_mm: float = 3.0   # overlap on wraparound seam

    @property
    def total_h_mm(self):
        return (self.body_h_mm + self.shoulder_h_mm
                + self.neck_h_mm + self.cap_h_mm)

    @property
    def label_circumference_mm(self):
        from math import pi
        return pi * self.body_dia_mm

    @property
    def label_flat_w_mm(self):
        return self.label_circumference_mm + self.label_overlap_mm

    @property
    def label_flat_h_mm(self):
        return self.label_h_mm

    @property
    def label_total_w_mm(self):
        return self.label_flat_w_mm + 2 * BLEED_MM

    @property
    def label_total_h_mm(self):
        return self.label_flat_h_mm + 2 * BLEED_MM

    @property
    def label_y_offset_mm(self):
        """Vertical position of label's bottom edge above the bottle base."""
        return (self.body_h_mm - self.label_h_mm) / 2 + 4.0

    # ------- Label panel layout (3 zones across the wrap) -----------------
    # Zone A (front, ~40% of wrap): hero — wordmark + product name
    # Zone B (left of front, ~30% of wrap): supplement facts panel
    # Zone C (right of front, ~30% of wrap): description + dosing
    @property
    def panel_widths_mm(self):
        w = self.label_flat_w_mm
        return {
            "facts": w * 0.30,
            "front": w * 0.40,
            "description": w * 0.30,
        }

    @property
    def label(self):
        return (f"{self.sku}  ·  {self.count}-ct ginger gummies  ·  "
                f"{self.mg_ginger}mg ginger + {self.mg_b6}mg B6  ·  "
                f"{self.body_dia_mm:.0f}×{self.total_h_mm:.0f} mm bottle")


# ----- The single SKU (Aplomb's nausea product) ---------------------------

CALM = BottleSpec(
    sku="Aplomb. Calm",
    count=60,
    mg_ginger=250,
    mg_b6=2.5,                 # 2.5mg / gummy → 5mg/day at 2 gummies (250% DV)
)

ALL_BOTTLES = [CALM]


if __name__ == "__main__":
    for b in ALL_BOTTLES:
        print(b.label)
        print(f"  bottle elevation:  {b.body_dia_mm:.0f}D × {b.total_h_mm:.0f}H mm")
        print(f"  label cut size:    {b.label_flat_w_mm:.1f} × {b.label_flat_h_mm:.1f} mm")
        print(f"  label with bleed:  {b.label_total_w_mm:.1f} × {b.label_total_h_mm:.1f} mm")
        print(f"  panel widths:      "
              f"facts={b.panel_widths_mm['facts']:.1f}  "
              f"front={b.panel_widths_mm['front']:.1f}  "
              f"desc={b.panel_widths_mm['description']:.1f}  mm")
        print()
