"""
Build the single PDF to upload at Packlane's per-order upload form.

Packlane's checkout upload only accepts ONE file. For this pilot we're
only printing the EXTERIOR of the mailer (no interior print), so the
upload is simply a copy of the exterior artwork PDF — exact Packlane
dieline size with 0.25" bleed, glyphs outlined.

Run: python3 -m scripts.mailer_design.build_packlane_upload
Output: Get-Aplomb/product-lines/packaging/Aplomb_Mailer_Small_PACKLANE_UPLOAD.pdf
"""

import shutil
from pathlib import Path

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "Get-Aplomb/product-lines/packaging")

OUTSIDE_PDF = OUT_DIR / "Aplomb_Mailer_Small_6x4x3_Artwork_Outside.pdf"
OUTPUT = OUT_DIR / "Aplomb_Mailer_Small_PACKLANE_UPLOAD.pdf"


def main():
    if not OUTSIDE_PDF.exists():
        raise SystemExit(f"Missing: {OUTSIDE_PDF}")
    shutil.copyfile(OUTSIDE_PDF, OUTPUT)
    kb = OUTPUT.stat().st_size // 1024
    print(f"Wrote {OUTPUT.name} ({kb} KB)  ·  1 page (exterior only)")


if __name__ == "__main__":
    main()
