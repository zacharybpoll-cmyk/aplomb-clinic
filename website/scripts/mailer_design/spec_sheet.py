"""
Packlane Submission Spec — one-page editorial PDF summarizing the brief.

Lists everything Packlane prepress will need:
- Two box sizes + interior dimensions
- Material + finish + print method
- CMYK conversion values per brand color
- Font specs (outlined glyphs)
- File-delivery list with path + size
- Bleed / safety zone numbers
- Packlane prepress contact + dieline request URL

Output: business documents/packaging/Aplomb_Packlane_Submission_Spec.pdf
"""

from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging")


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "font.size": 9,
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",
    })


def _file_inventory():
    """List every file we expect to be in the packaging folder."""
    files = []
    for size_label, suffix in [("Small (6×4×3)", "Small_6x4x3"),
                               ("Large (7×5×3)", "Large_7x5x3")]:
        files.append((size_label, "Schematic (annotated dieline)",
                      f"Aplomb_Mailer_{suffix}_Schematic.pdf"))
        files.append((size_label, "Production artwork — outside",
                      f"Aplomb_Mailer_{suffix}_Artwork_Outside.pdf"))
        files.append((size_label, "Production artwork — outside (SVG)",
                      f"Aplomb_Mailer_{suffix}_Artwork_Outside.svg"))
        files.append((size_label, "Production artwork — inside",
                      f"Aplomb_Mailer_{suffix}_Artwork_Inside.pdf"))
        files.append((size_label, "Production artwork — inside (SVG)",
                      f"Aplomb_Mailer_{suffix}_Artwork_Inside.svg"))
        files.append((size_label, "Visual mockup — closed",
                      f"Aplomb_Mailer_{suffix}_Mockup_Closed.png"))
        files.append((size_label, "Visual mockup — opened",
                      f"Aplomb_Mailer_{suffix}_Mockup_Open.png"))
    return files


def _draw_section_title(ax, x, y, text):
    ax.text(x, y, text, family="IBM Plex Sans", fontsize=8.5,
            fontweight="bold", color=g.AMBER_HEX,
            transform=ax.transAxes, ha="left", va="bottom")
    ax.add_artist(Line2D([x, x + 0.30], [y - 0.012, y - 0.012],
                         transform=ax.transAxes,
                         color=g.RULE_HEX, linewidth=0.5))


def render(out_path: Path):
    _set_style()
    # Multiplier on every fractional decrement to fit on one tall page.
    # All decrements are scaled so the whole spec fits in y=[0.05, 0.97].
    K = 0.78
    fig = plt.figure(figsize=(11, 24), dpi=300, facecolor=g.BG_HEX)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_facecolor(g.BG_HEX)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # ----- HEADER --------------------------------------------------------
    fig.text(0.06, 0.965, "Aplomb",
             family="Cormorant Garamond", fontstyle="italic",
             fontweight="medium", fontsize=26, color=g.INK_HEX)
    fig.text(0.111, 0.965, ".",
             family="Cormorant Garamond", fontstyle="italic",
             fontweight="bold", fontsize=26, color=g.AMBER_HEX)
    fig.text(0.06, 0.945, "Outer-packaging submission spec",
             family="IBM Plex Sans", fontsize=11, color=g.MUTED_HEX)
    fig.text(0.06, 0.928, "Vendor: Packlane (Arka)  ·  "
             "MOQ: 200 per SKU  ·  prepared "
             + datetime.now().strftime("%B %d, %Y"),
             family="IBM Plex Sans", fontsize=10, color=g.INK_HEX,
             fontweight="medium")
    fig.text(0.94, 0.965, "§ Outer packaging  ·  v1",
             family="IBM Plex Sans", fontsize=9, color=g.AMBER_HEX,
             ha="right")
    # Hairline rule under header
    fig.add_artist(Line2D([0.06, 0.94], [0.910, 0.910],
                          color=g.RULE_HEX, linewidth=0.5))

    # ----- 1. BOX SIZES --------------------------------------------------
    y = 0.880
    _draw_section_title(ax, 0.06, y, "01  ·  TWO PRODUCTION SIZES")
    y -= 0.022 * K
    box_data = [
        ("Small mailer", "6 × 4 × 3 in interior",
         "152 × 102 × 76 mm interior",
         "Fits Aplomb. Serum (30mL dropper), Daily / Roots bottles, "
         "Composure tin"),
        ("Large mailer", "7 × 5 × 3 in interior",
         "178 × 127 × 76 mm interior",
         "Fits Aplomb. Calm (30-day kit)"),
    ]
    for label, dim_in, dim_mm, fits in box_data:
        fig.text(0.06, y, f"{label}  ", family="IBM Plex Sans",
                 fontsize=10, fontweight="bold", color=g.INK_HEX)
        fig.text(0.20, y, f"{dim_in}  ·  {dim_mm}",
                 family="IBM Plex Sans", fontsize=10, color=g.AMBER_HEX)
        fig.text(0.20, y - 0.014, fits,
                 family="IBM Plex Sans", fontsize=9, color=g.MUTED_HEX)
        y -= 0.034 * K
    y -= 0.008 * K
    fig.text(0.06, y,
             "Both sizes use Packlane's standard mailer-box dieline. "
             "Manufacturing tolerance ±0.125\" applies to both. Source the "
             "official dielines per size at  packlane.com/dieline-request.",
             family="IBM Plex Sans", fontsize=9, color=g.INK_HEX)

    # ----- 2. MATERIAL + FINISH ------------------------------------------
    y -= 0.030 * K
    _draw_section_title(ax, 0.06, y, "02  ·  MATERIAL + FINISH")
    y -= 0.022 * K
    rows = [
        ("Material", "White HDPrint matte paperboard"),
        ("Flute", "E-flute (1/16\") corrugated single-wall"),
        ("Print method", "C500 single-pass digital  ·  CMYK process"),
        ("Finish", "Matte (no lamination, no UV gloss)"),
        ("Inside print", "YES — separate file per Packlane requirement"),
        ("Quantity per SKU", "300 units (within Packlane's 200-400 quote band)"),
    ]
    for k, v in rows:
        fig.text(0.07, y, k, family="IBM Plex Sans", fontsize=9.5,
                 color=g.MUTED_HEX)
        fig.text(0.22, y, v, family="IBM Plex Sans", fontsize=9.5,
                 color=g.INK_HEX, fontweight="medium")
        y -= 0.018 * K

    # ----- 3. BRAND COLORS + CMYK ----------------------------------------
    y -= 0.012 * K
    _draw_section_title(ax, 0.06, y, "03  ·  COLOR — CMYK CONVERSIONS")
    y -= 0.022 * K
    color_rows = [
        ("Bone (panel surface)", g.BONE_HEX, g.CMYK["bone"], "exterior fill"),
        ("Amber (brand mark)", g.AMBER_HEX, g.CMYK["amber"],
         "wordmark, plumb mark, tagline"),
        ("Ink (primary text)", g.INK_HEX, g.CMYK["ink"], "interior body copy"),
        ("Rule (hairlines)", g.RULE_HEX, g.CMYK["rule"], "dividers, side marks"),
        ("Muted (secondary)", g.MUTED_HEX, g.CMYK["muted"],
         "BACK panel wordmark, footer copy"),
    ]
    for name, hex_, cmyk, role in color_rows:
        # Color swatch
        ax.add_patch(Rectangle((0.07, y - 0.005), 0.025, 0.014,
                               facecolor=hex_, edgecolor=g.RULE_HEX,
                               linewidth=0.5, transform=ax.transAxes))
        fig.text(0.105, y, name, family="IBM Plex Sans", fontsize=9.5,
                 color=g.INK_HEX, fontweight="medium")
        fig.text(0.30, y, hex_, family="IBM Plex Sans", fontsize=9.5,
                 color=g.MUTED_HEX)
        cmyk_str = f"C{cmyk[0]} M{cmyk[1]} Y{cmyk[2]} K{cmyk[3]}"
        fig.text(0.40, y, cmyk_str, family="IBM Plex Sans", fontsize=9.5,
                 color=g.AMBER_HEX, fontweight="medium")
        fig.text(0.62, y, role, family="IBM Plex Sans", fontsize=9.5,
                 color=g.MUTED_HEX, style="italic")
        y -= 0.020 * K
    y -= 0.006 * K
    fig.text(0.06, y,
             "Black text uses pure K (0/0/0/100). Avoid rich black except "
             "in solid-fill areas (no rich black for type).",
             family="IBM Plex Sans", fontsize=9, color=g.INK_HEX, style="italic")

    # ----- 4. TYPOGRAPHY -------------------------------------------------
    y -= 0.024 * K
    _draw_section_title(ax, 0.06, y, "04  ·  TYPOGRAPHY")
    y -= 0.022 * K
    type_rows = [
        ("Display", "Cormorant Garamond — italic 500",
         "Wordmark, lid type, FRONT tagline, interior reveal."),
        ("Body / UI", "IBM Plex Sans — 400, 500",
         "URL, bottom copy, small annotations."),
        ("Min size", "10 pt for corrugated print",
         "All type meets this minimum."),
        ("Outlining", "All glyphs converted to vector paths",
         "SVG export uses fonttype=path; no live fonts ship to printer."),
    ]
    for label, value, role in type_rows:
        fig.text(0.07, y, label, family="IBM Plex Sans", fontsize=9.5,
                 color=g.MUTED_HEX)
        fig.text(0.22, y, value, family="IBM Plex Sans", fontsize=9.5,
                 color=g.INK_HEX, fontweight="medium")
        fig.text(0.22, y - 0.013, role, family="IBM Plex Sans",
                 fontsize=8.5, color=g.MUTED_HEX, style="italic")
        y -= 0.026 * K

    # ----- 5. ARTWORK SPEC -----------------------------------------------
    y -= 0.006 * K
    _draw_section_title(ax, 0.06, y, "05  ·  ARTWORK SPEC (PER PACKLANE)")
    y -= 0.022 * K
    spec_rows = [
        ("Bleed", "0.25 in past every cut line where artwork extends to edge"),
        ("Safety zone", "0.125 in inside cut lines AND inside fold/crease lines"),
        ("Tolerance", "±0.125 in manufacturing tolerance accounted for in safety zone"),
        ("File format", "PDF (preview) + SVG (vector source for Illustrator import)"),
        ("Resolution", "Vector — no raster; if any raster added, 300 ppi minimum"),
        ("Color profile", "CMYK (US Web Coated SWOP); no spot colors"),
        ("Layers / dieline",
         "Drop our artwork onto Packlane's official dieline — dieline on its own layer, do NOT remove or alter"),
        ("Files per size", "TWO (outside.pdf + inside.pdf) per Packlane's interior-print rule"),
    ]
    for k, v in spec_rows:
        fig.text(0.07, y, k, family="IBM Plex Sans", fontsize=9.5,
                 color=g.MUTED_HEX)
        fig.text(0.24, y, v, family="IBM Plex Sans", fontsize=9.5,
                 color=g.INK_HEX)
        y -= 0.017 * K

    # ----- 6. FILE INVENTORY ---------------------------------------------
    y -= 0.012 * K
    _draw_section_title(ax, 0.06, y,
                        "06  ·  DELIVERABLE FILE INVENTORY")
    y -= 0.022 * K
    files = _file_inventory()
    for size_label, role, fname in files:
        fig.text(0.07, y, size_label, family="IBM Plex Sans", fontsize=8.5,
                 color=g.MUTED_HEX)
        fig.text(0.22, y, role, family="IBM Plex Sans", fontsize=8.5,
                 color=g.INK_HEX)
        fig.text(0.50, y, fname, family="IBM Plex Sans", fontsize=8.5,
                 color=g.AMBER_HEX)
        # Check existence + size
        p = OUT_DIR / fname
        if p.exists():
            kb = p.stat().st_size // 1024
            fig.text(0.92, y, f"{kb} KB",
                     family="IBM Plex Sans", fontsize=8.5,
                     color=g.MUTED_HEX, ha="right")
        else:
            fig.text(0.92, y, "(missing)",
                     family="IBM Plex Sans", fontsize=8.5,
                     color="#C2392E", ha="right")
        y -= 0.0135 * K

    # ----- 7. PACKLANE CONTACT + NEXT STEPS ------------------------------
    y -= 0.012 * K
    _draw_section_title(ax, 0.06, y, "07  ·  PACKLANE CONTACT  ·  NEXT STEPS")
    y -= 0.022 * K
    next_steps = [
        ("1", "Email prepress@packlane.com with the chosen sizes "
              "(6×4×3 and 7×5×3) and request the official dielines."),
        ("2", "Place the SVG artwork in this package onto each dieline in "
              "Adobe Illustrator. Verify cut-line and fold-line "
              "alignment manually."),
        ("3", "Outline all type, embed images, flatten transparencies, "
              "export to PDF (CMYK)."),
        ("4", "Upload finished outside + inside PDFs through Packlane's "
              "online ordering tool. Order one sample carton of each size first."),
        ("5", "Approve sample, then place 300-unit order per SKU "
              "(600 cartons total) at the verified $3.40-$3.80/unit band."),
    ]
    for n, text in next_steps:
        fig.text(0.07, y, n, family="IBM Plex Sans", fontsize=10,
                 color=g.AMBER_HEX, fontweight="bold")
        fig.text(0.10, y, text, family="IBM Plex Sans", fontsize=9.5,
                 color=g.INK_HEX, wrap=True)
        y -= 0.024 * K

    # ----- FOOTER --------------------------------------------------------
    fig.add_artist(Line2D([0.06, 0.94], [0.030, 0.030],
                          color=g.RULE_HEX, linewidth=0.5))
    fig.text(0.06, 0.018,
             "Aplomb. Inc.  ·  Confidential supplier specification  ·  "
             "aplomb.clinic  ·  Designed for Packlane (Arka), San Francisco",
             family="IBM Plex Sans", fontsize=8, color=g.MUTED_HEX)
    fig.text(0.94, 0.018,
             f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             family="IBM Plex Sans", fontsize=8, color=g.MUTED_HEX,
             ha="right")

    fig.savefig(out_path, format="pdf", facecolor=g.BG_HEX,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {out_path.name} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render(OUT_DIR / "Aplomb_Packlane_Submission_Spec.pdf")
