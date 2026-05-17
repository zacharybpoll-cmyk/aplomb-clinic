"""
Submission spec sheet — one editorial PDF for the SUNI RFQ.

Sections:
  - Bottle (180 cc HDPE, 38-400 neck, CRC induction-seal)
  - Gummy formulation (per gummy + per serving + per bottle)
  - Label print spec (CMYK swatches, fonts, finish)
  - Artwork inventory (files we provide to SUNI)
  - Items to confirm with SUNI on RFQ (the [CONFIRM] flags)
  - Next steps

Output: business documents/packaging/gummy/Aplomb_Calm_SUNI_Submission_Spec.pdf
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")

PAGE_W = 11.0
PAGE_H = 17.0   # tabloid


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",
    })


def render(out_path: Path):
    _set_style()
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=300, facecolor=g.BG_HEX)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    LM = 0.65   # left margin (in)
    RM = 0.65
    text_w = PAGE_W - LM - RM

    # ---- Header ---------------------------------------------------------
    y = PAGE_H - 0.7
    ax.text(LM, y, "Aplomb.",
            family="Cormorant Garamond", fontsize=22,
            fontstyle="italic", color=g.AMBER_HEX)
    ax.text(PAGE_W - RM, y,
            "§ Outer packaging  ·  SUNI submission spec  ·  v1",
            family="IBM Plex Sans", fontsize=10,
            color=g.AMBER_HEX, ha="right")
    ax.plot([LM, PAGE_W - RM], [y - 0.20, y - 0.20],
            color=g.AMBER_HEX, linewidth=0.5)
    y -= 0.65

    ax.text(LM, y, "Aplomb. Calm",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=32, color=g.INK_HEX)
    y -= 0.40
    ax.text(LM, y,
            "60-count ginger gummies for nausea on GLP-1 medications  ·  "
            "Private-label submission to SUNI",
            family="IBM Plex Sans", fontsize=10, color=g.MUTED_HEX)
    y -= 0.55

    # ---- Helper to render a section -------------------------------------
    def section(title, body_lines, *, y0):
        yy = y0
        ax.text(LM, yy, title,
                family="Cormorant Garamond", fontstyle="italic",
                fontsize=18, color=g.AMBER_HEX)
        yy -= 0.10
        ax.plot([LM, LM + 2.8], [yy, yy],
                color=g.AMBER_HEX, linewidth=0.5)
        yy -= 0.30
        for kind, text in body_lines:
            if kind == "kv":
                key, val = text
                ax.text(LM, yy, key,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.MUTED_HEX, va="top")
                ax.text(LM + 2.5, yy, val,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.INK_HEX, va="top")
                yy -= 0.22
            elif kind == "p":
                ax.text(LM, yy, text,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.INK_HEX, va="top")
                yy -= 0.24
            elif kind == "bullet":
                ax.text(LM + 0.18, yy, "·",
                        family="IBM Plex Sans", fontsize=14,
                        color=g.AMBER_HEX, va="top")
                ax.text(LM + 0.40, yy, text,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.INK_HEX, va="top")
                yy -= 0.22
            elif kind == "gap":
                yy -= 0.18
            elif kind == "swatch":
                name, hex_v, cmyk = text
                # Draw swatch
                ax.add_patch(Rectangle(
                    (LM, yy - 0.20), 0.30, 0.20,
                    facecolor=hex_v, edgecolor=g.RULE_HEX, linewidth=0.5,
                ))
                ax.text(LM + 0.40, yy - 0.06, name,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.INK_HEX, va="center")
                ax.text(LM + 1.7, yy - 0.06, hex_v,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.MUTED_HEX, va="center")
                ax.text(LM + 2.6, yy - 0.06, cmyk,
                        family="IBM Plex Sans", fontsize=9.5,
                        color=g.MUTED_HEX, va="center")
                yy -= 0.32
        return yy - 0.20

    bottle = g.CALM

    # ---- 1. Bottle ------------------------------------------------------
    y = section("1  Bottle", [
        ("kv", ("Type",       "180 cc round HDPE  ·  white opaque, FDA-grade")),
        ("kv", ("Body Ø × H", f"{bottle.body_dia_mm:.0f} × {bottle.body_h_mm:.0f} mm  [CONFIRM]")),
        ("kv", ("Total height", f"{bottle.total_h_mm:.0f} mm")),
        ("kv", ("Neck finish", f"38-400  ·  Ø {bottle.neck_dia_mm:.0f} mm")),
        ("kv", ("Closure",    "38-400 black HDPE child-resistant cap with "
                              "pressure-sensitive induction seal liner")),
        ("kv", ("Stock SKU",  "SUNI 180 cc gummy bottle (their default for the "
                              "60-ct ginger gummy listing)")),
        ("gap", ""),
        ("p", "We will accept SUNI's stock 180 cc bottle as-is. No bottle "
              "tooling. The design language lives entirely in the cap color, "
              "label, and outer mailer."),
    ], y0=y)

    # ---- 2. Formulation -------------------------------------------------
    y = section("2  Gummy formulation", [
        ("kv", ("Daily dose",  "2 gummies in the morning of injection day "
                               "(may add a third before evening meal)")),
        ("kv", ("Per gummy",   f"{bottle.mg_ginger} mg ginger root extract "
                               f"(5% gingerols)  +  "
                               f"{bottle.mg_b6:.1f} mg vitamin B6 (P-5-P)")),
        ("kv", ("Per serving (2 gummies)",
                f"{bottle.mg_ginger * 2} mg ginger  +  "
                f"{bottle.mg_b6 * 2:.0f} mg B6  (294% DV)")),
        ("kv", ("Per bottle",  f"{bottle.count} gummies  ·  ~30-day supply")),
        ("kv", ("Flavor",      "Cinnamon-ginger, light. Natural color (carrot juice).")),
        ("kv", ("Other ingred.", "Tapioca syrup, cane sugar, pectin, citric acid, "
                                 "natural ginger flavor")),
        ("kv", ("Allergens",   "None of the Big-9. Confirm on SUNI CoA.")),
        ("kv", ("Shelf life",  "24 months from manufacture  [CONFIRM]")),
    ], y0=y)

    # ---- 3. Label print spec --------------------------------------------
    y = section("3  Label", [
        ("kv", ("Stock",       "Pressure-sensitive matte uncoated paper, "
                               "FSC-certified preferred")),
        ("kv", ("Cut size",    f"{bottle.label_flat_w_mm:.1f} × "
                               f"{bottle.label_flat_h_mm:.1f} mm  "
                               f"(wraparound, {bottle.label_overlap_mm:.0f} mm overlap)")),
        ("kv", ("Bleed / safe", f"{g.BLEED_MM:.0f} mm bleed  ·  "
                                f"{g.SAFE_MM:.0f} mm safety zone")),
        ("kv", ("Print",       "4-color CMYK process  ·  matte varnish overall")),
        ("kv", ("Finishing",   "Die-cut to outline  ·  permanent adhesive")),
        ("gap", ""),
        ("swatch", ("Bone (paper face)", g.BONE_HEX, "C0  M3  Y8  K3")),
        ("swatch", ("Amber (display + accent)", g.AMBER_HEX, "C0  M55  Y85  K55")),
        ("swatch", ("Ink (body copy)", g.INK_HEX, "C0  M30  Y40  K90")),
        ("swatch", ("Rule (hairlines)", g.RULE_HEX, "C0  M5  Y12  K18")),
        ("swatch", ("Muted (secondary)", g.MUTED_HEX, "C0  M12  Y25  K65")),
    ], y0=y)

    # ---- 4. Typography --------------------------------------------------
    y = section("4  Typography", [
        ("kv", ("Wordmark + display",
                "Cormorant Garamond Italic (variable, weight 500–600)")),
        ("kv", ("Body / nutrition panel",
                "IBM Plex Sans Regular  ·  bold for column headers")),
        ("kv", ("Min text size",
                "5 pt nutrition panel  ·  6 pt all other body  "
                "(both above SUNI's 4 pt minimum)")),
        ("kv", ("Files",
                "All glyphs outlined to paths in SVG; no live text")),
    ], y0=y)

    # ---- 5. Artwork inventory -------------------------------------------
    y = section("5  Artwork inventory", [
        ("bullet", "Aplomb_Calm_Gummy_Schematic.pdf  ·  bottle elevation + "
                   "label dieline with full dimension callouts"),
        ("bullet", "Aplomb_Calm_Gummy_Label.pdf  ·  flat label artwork at "
                   "exact cut size + 3 mm bleed (CMYK-ready)"),
        ("bullet", "Aplomb_Calm_Gummy_Label.svg  ·  same artwork, "
                   "Illustrator-importable, glyphs outlined"),
        ("bullet", "Aplomb_Calm_Gummy_Mockup_Front.png  ·  visual reference "
                   "for SUNI's prepress team (NOT for print use)"),
        ("bullet", "Aplomb_Calm_Gummy_Mockup_Shelf.png  ·  marketing reference"),
        ("bullet", "Aplomb_Calm_SUNI_Submission_Spec.pdf  ·  this document"),
    ], y0=y)

    # ---- 6. Confirm with SUNI -------------------------------------------
    y = section("6  Confirm with SUNI on RFQ", [
        ("bullet", "Stock 180 cc bottle exact dimensions "
                   "(currently estimated 63 × 88 mm body)"),
        ("bullet", "Stock cap availability in matte warm-black HDPE "
                   "(or matched custom run, MOQ permitting)"),
        ("bullet", "Min label height + safety zone for 38-400 neck "
                   "to avoid label slipping past the shoulder"),
        ("bullet", "MOQ at 60-ct  ·  unit cost at 500 / 1,000 / 2,500"),
        ("bullet", "Lead time for stock bottle + custom label, vs. fully bespoke"),
        ("bullet", "CoA + GMP certification + DSHEA-compliant claims review"),
    ], y0=y)

    # ---- 7. Next steps --------------------------------------------------
    y = section("7  Next steps", [
        ("bullet", "Send this spec + the 5 artwork files to SUNI sales contact"),
        ("bullet", "Request quote at 500 / 1,000 / 2,500 unit MOQ tiers"),
        ("bullet", "Request paper proof + bottle sample before tooling"),
        ("bullet", "Once approved, lock variant and order pilot (500 units)"),
    ], y0=y)

    # ---- Footer ---------------------------------------------------------
    ax.plot([LM, PAGE_W - RM], [0.55, 0.55],
            color=g.AMBER_HEX, linewidth=0.4)
    ax.text(LM, 0.30, "Aplomb.",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=12, color=g.AMBER_HEX)
    ax.text(PAGE_W - RM, 0.30,
            "Generated 2026-05-06  ·  scripts/gummy_design/",
            family="IBM Plex Sans", fontsize=8,
            color=g.MUTED_HEX, ha="right")

    fig.savefig(out_path, format="pdf",
                facecolor=g.BG_HEX, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {out_path.name} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render(OUT_DIR / "Aplomb_Calm_SUNI_Submission_Spec.pdf")
