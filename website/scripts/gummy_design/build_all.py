"""
Build the entire SUNI submission package end-to-end.

Run: python3 -m scripts.gummy_design.build_all

Generates 6 files in business documents/packaging/gummy/:
  - 1 schematic PDF (bottle elevation + label dieline)
  - 1 label artwork PDF + 1 SVG
  - 2 visual mockup PNGs (front + shelf)
  - 1 SUNI submission spec PDF
"""

from pathlib import Path

from . import schematic, artwork, mockup, spec_sheet

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("APLOMB CALM (GINGER GUMMY) DESIGN PIPELINE")
    print("Output:", OUT_DIR)
    print("=" * 70)

    print("\n[1/4] Schematic ----------------------------------------")
    schematic.render_all()

    print("\n[2/4] Production label artwork --------------------------")
    artwork.render_all()

    print("\n[3/4] Visual mockups ------------------------------------")
    mockup.render_all()

    print("\n[4/4] Submission spec sheet -----------------------------")
    spec_sheet.render(OUT_DIR / "Aplomb_Calm_SUNI_Submission_Spec.pdf")

    print("\n" + "=" * 70)
    print("Done. Files:")
    for f in sorted(OUT_DIR.iterdir()):
        if f.is_file():
            kb = f.stat().st_size // 1024
            print(f"  {f.name:<60s} {kb:>6d} KB")


if __name__ == "__main__":
    build()
