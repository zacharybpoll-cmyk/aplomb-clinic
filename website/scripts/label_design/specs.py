"""
Per-SKU label specs for the four APLOMB. SKUs that have a confirmed
manufacturing partner (peptide serum / hair growth serum / chewables;
nausea is still TBD).

Each entry captures the exact artwork dimensions the supplier requires,
plus the printed-label content (product name, ingredients, dosing,
warnings, distributor block, FDA disclaimer where applicable).

Dimensions verified from supplier portals on 2026-05-07.
"""

from dataclasses import dataclass, field
from typing import Optional

# Brand tokens (verbatim from brand/BRAND.md)
AMBER_HEX = "#7A3D14"
INK_HEX   = "#1A1512"
BONE_HEX  = "#F7F1E6"
BG_HEX    = "#EFE8DC"
RULE_HEX  = "#D9CFBD"
MUTED_HEX = "#6B5D4C"

# Print constants
MM_PER_IN = 25.4
BLEED_MM  = 3.0  # 1/8 inch bleed
SAFE_MM   = 3.0  # 1/8 inch safe zone


@dataclass(frozen=True)
class LabelSpec:
    """Everything needed to render a supplier-ready label."""
    sku: str                # "peptide-serum" | "hair-growth-serum" | "chewables"
    folder_slug: str        # exact name of product designs/ subfolder
    title: str              # Front-of-label product name (line 1)
    subtitle: str           # Front-of-label sub-line (italic descriptor)
    supplier: str           # Cellular Cosmetics | Supliful
    upload_url: str         # supplier portal URL
    label_w_in: float       # label width in inches
    label_h_in: float       # label height in inches
    bottle_format: str      # "30 mL frosted dropper", "2 fl oz amber dropper", ...
    net_volume: str         # "30 mL / 1.01 fl oz", "2 fl oz / 59 mL", "30 chewables / 0.7 oz"
    ingredients: str        # INCI list or supplement-facts ingredient summary
    suggested_use: str      # 1-2 sentences
    warnings: str           # caution / external use / pregnancy / etc.
    fda_disclaimer: bool    # True for supplements (Supliful), False for cosmetics
    category: str           # "cosmetic" | "supplement"
    distributor: str        # legal address line
    badges: tuple = ()      # vegan / cruelty-free / paraben-free / etc.

    @property
    def label_w_mm(self) -> float:
        return self.label_w_in * MM_PER_IN

    @property
    def label_h_mm(self) -> float:
        return self.label_h_in * MM_PER_IN


# Aplomb business address — placeholder; user to confirm before final upload
DISTRIBUTOR_LINE = (
    "Distributed by APLOMB Laboratories, Inc.   "
    "  getaplomb.com"
)


PEPTIDE_SERUM = LabelSpec(
    sku="peptide-serum",
    folder_slug="peptide-serum",
    title="APLOMB.",
    subtitle="The Serum",
    supplier="Cellular Cosmetics",
    upload_url=(
        "https://www.cellular-cosmetics.com/products/"
        "anti-age-peptide-serum-private-label-skin-care"
    ),
    # Cellular Cosmetics 30 mL frosted glass bottle: 75 mm × 35 mm
    # = 2.953 in × 1.378 in
    label_w_in=75 / MM_PER_IN,
    label_h_in=35 / MM_PER_IN,
    bottle_format="30 mL / 1.01 fl oz frosted glass dropper",
    net_volume="30 mL  /  1.01 fl oz",
    # Cellular Cosmetics' published actives (private-label peptide serum)
    ingredients=(
        "Aqua, Glycerin, Palmitoyl Tripeptide-1, Palmitoyl Tetrapeptide-7, "
        "Palmitoyl Tripeptide-38, Centella Asiatica Extract, "
        "Terminalia Ferdinandiana Fruit Extract (Kakadu Plum), "
        "Arctostaphylos Uva Ursi Leaf Extract (Bearberry), "
        "Glycyrrhiza Glabra Root Extract (Licorice), "
        "Sodium Hyaluronate, Phenoxyethanol, Ethylhexylglycerin."
    ),
    suggested_use=(
        "Apply 1–2 drops to clean skin AM and PM, "
        "before moisturizer and SPF."
    ),
    warnings=(
        "For external use only. Discontinue if irritation occurs. "
        "Avoid contact with eyes."
    ),
    fda_disclaimer=False,  # cosmetic, not supplement
    category="cosmetic",
    distributor=DISTRIBUTOR_LINE,
    badges=("Vegan", "Cruelty-free", "Paraben-free", "Made in Australia"),
)


HAIR_GROWTH_SERUM = LabelSpec(
    sku="hair-growth-serum",
    folder_slug="hair-growth-serum",
    title="APLOMB.",
    subtitle="Roots — Botanical Hair Serum",
    supplier="Supliful",
    upload_url=(
        "https://supliful.com/myproducts/eaf8b496-aab8-4be6-93ba-6302c1c31ace"
    ),
    # Supliful: 2"H × 4.25"W
    label_w_in=4.25,
    label_h_in=2.0,
    bottle_format="2 fl oz amber dropper bottle",
    net_volume="2 fl oz  /  59 mL",
    # Supliful's published INCI for this stock SKU (truncated trailing items)
    ingredients=(
        "Water, Glycerin, Rosmarinus Officinalis (Rosemary) Leaf Extract, "
        "Propanediol, Chlorella Emersonii / Spirulina Maxima Extract "
        "(Densidyl), Sodium Hyaluronate, Salicylic Acid, "
        "Caffeine, Niacinamide, Phenoxyethanol, Ethylhexylglycerin."
    ),
    suggested_use=(
        "Apply a few drops directly to clean scalp once daily. "
        "Massage in gently. Do not rinse."
    ),
    warnings=(
        "For external use only. Keep out of reach of children. "
        "Store in a cool, dry place."
    ),
    fda_disclaimer=False,  # topical cosmetic
    category="cosmetic",
    distributor=DISTRIBUTOR_LINE,
    badges=("Vegan", "Cruelty-free", "Sulfate-free", "Paraben-free", "Made in USA"),
)


CHEWABLES = LabelSpec(
    sku="chewables",
    folder_slug="chewables",
    title="APLOMB.",
    subtitle="Breath — Dental & Oral Health Chewables",
    supplier="Supliful",
    upload_url=(
        "https://app.supliful.com/myproducts/566d653b-55ca-4287-82d2-a55a9b3194e8"
    ),
    # Supliful: 2.5"H × 6"W
    label_w_in=6.0,
    label_h_in=2.5,
    bottle_format="30-count chewable tablet jar",
    net_volume="30 chewables  /  net wt 0.7 oz (19 g)",
    ingredients=(
        "Dental Support Blend: Xylitol (direct compressible), "
        "Guava Fruit Powder (325 mg), 3-Strain Probiotic Blend "
        "(Lactobacillus salivarius, Lactobacillus paracasei, "
        "Lactobacillus reuteri), Zinc Acetate, Green Tea Extract, "
        "Natural Mint Flavor, Magnesium Stearate."
    ),
    suggested_use=(
        "As a dietary supplement, adults chew one (1) tablet daily "
        "after meals. Chew thoroughly before swallowing."
    ),
    warnings=(
        "Do not exceed recommended dose. If pregnant, nursing, under 18, "
        "or under medical care, consult a physician before use. "
        "Keep out of reach of children."
    ),
    fda_disclaimer=True,  # dietary supplement
    category="supplement",
    distributor=DISTRIBUTOR_LINE,
    badges=("Vegan", "Gluten-free", "Lactose-free", "Non-GMO", "Made in USA"),
)


ALL_SPECS = [PEPTIDE_SERUM, HAIR_GROWTH_SERUM, CHEWABLES]


if __name__ == "__main__":
    for s in ALL_SPECS:
        print(
            f"{s.folder_slug:>22}  {s.label_w_in:.2f}\"W × {s.label_h_in:.2f}\"H "
            f"({s.label_w_mm:.1f} × {s.label_h_mm:.1f} mm)  →  {s.supplier}"
        )
