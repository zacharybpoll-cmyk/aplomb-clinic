"""
Build the entire Packlane submission package end-to-end.

Run: python3 -m scripts.mailer_design.build_all

Generates 15 files in business documents/packaging/:
  - 2 schematic PDFs (Small + Large)
  - 4 production-artwork PDFs (Small/Large × Outside/Inside)
  - 4 production-artwork SVGs (same)
  - 4 isometric mockup PNGs (Small/Large × Closed/Open)
  - 1 submission spec PDF
"""

from pathlib import Path

from . import schematic, artwork, mockup, spec_sheet

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging")


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("APLOMB MAILER DESIGN PIPELINE")
    print("Output:", OUT_DIR)
    print("=" * 70)

    print("\n[1/4] Schematics ----------------------------------------")
    schematic.render_all()

    print("\n[2/4] Production artwork --------------------------------")
    artwork.render_all()

    print("\n[3/4] Visual mockups ------------------------------------")
    mockup.render_all()

    print("\n[4/4] Submission spec sheet -----------------------------")
    spec_sheet.render(OUT_DIR / "Aplomb_Packlane_Submission_Spec.pdf")

    print("\n" + "=" * 70)
    print("Done. Files:")
    for f in sorted(OUT_DIR.iterdir()):
        if f.is_file():
            kb = f.stat().st_size // 1024
            print(f"  {f.name:<60s} {kb:>6d} KB")


if __name__ == "__main__":
    build()
