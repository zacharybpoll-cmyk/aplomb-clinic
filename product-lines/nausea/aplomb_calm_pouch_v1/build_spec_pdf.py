"""
Aplomb.Calm pouch v1 — supplier specification PDF.
Rendered with ReportLab to match brand tokens (Cormorant + IBM Plex Sans).
"""

from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    HRFlowable, KeepTogether, ListFlowable, ListItem,
)

PAPER = HexColor("#f7f1e6")
INK   = HexColor("#1a1512")
AMBER = HexColor("#7a3d14")
INK60 = HexColor("#6e6864")
GUIDE = HexColor("#d9cdb6")

OUT_DIR = Path(__file__).resolve().parent
PDF = OUT_DIR / "Aplomb_Calm_Pouch_v1_Supplier_Spec.pdf"


def register_fonts():
    """Find Cormorant + IBM Plex Sans on macOS user/system font dirs."""
    import matplotlib.font_manager as fm
    wanted = {
        "Cormorant-Italic":     ("Cormorant Garamond", "italic", 500),
        "Cormorant-Italic-Bold":("Cormorant Garamond", "italic", 700),
        "Cormorant-Reg":        ("Cormorant Garamond", "normal", 400),
        "PlexSans":             ("IBM Plex Sans",      "normal", 400),
        "PlexSans-Bold":        ("IBM Plex Sans",      "normal", 700),
        "PlexSans-Italic":      ("IBM Plex Sans",      "italic", 400),
    }
    for alias, (fam, style, weight) in wanted.items():
        try:
            path = fm.findfont(
                fm.FontProperties(family=fam, style=style, weight=weight),
                fallback_to_default=False,
            )
            pdfmetrics.registerFont(TTFont(alias, path))
        except Exception as e:
            print(f"⚠ {alias} not found: {e}")


def styles():
    base = ParagraphStyle(
        "base", fontName="PlexSans", fontSize=9.2, leading=13,
        textColor=INK, spaceAfter=4,
    )
    return {
        "h1": ParagraphStyle("h1", parent=base, fontName="Cormorant-Italic",
                             fontSize=22, leading=26, textColor=INK,
                             spaceBefore=2, spaceAfter=6),
        "h1amber": ParagraphStyle("h1a", parent=base, fontName="Cormorant-Italic",
                                  fontSize=22, leading=26, textColor=AMBER),
        "h2": ParagraphStyle("h2", parent=base, fontName="Cormorant-Italic",
                             fontSize=14, leading=18, textColor=INK,
                             spaceBefore=14, spaceAfter=4),
        "h3": ParagraphStyle("h3", parent=base, fontName="PlexSans-Bold",
                             fontSize=9.5, leading=13, textColor=INK,
                             spaceBefore=8, spaceAfter=2),
        "body": base,
        "small": ParagraphStyle("small", parent=base, fontSize=8, leading=11,
                                textColor=INK60),
        "smallI": ParagraphStyle("smallI", parent=base, fontSize=8, leading=11,
                                 fontName="PlexSans-Italic", textColor=INK60),
        "tag": ParagraphStyle("tag", parent=base, fontSize=8,
                              fontName="PlexSans", textColor=AMBER,
                              spaceBefore=0, spaceAfter=8),
        "callout": ParagraphStyle("callout", parent=base,
                                  fontName="PlexSans-Italic",
                                  textColor=INK60),
    }


def tbl(data, *, col_widths=None, header=True):
    style_cmds = [
        ("FONT", (0, 0), (-1, -1), "PlexSans", 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK if header else GUIDE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, GUIDE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, INK),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, INK),
    ]
    if header:
        style_cmds.append(("FONT", (0, 0), (-1, 0), "PlexSans-Bold", 9))
    t = Table(data, colWidths=col_widths, style=TableStyle(style_cmds))
    return t


def main():
    register_fonts()
    s = styles()
    PAGE_MARGIN = 18 * mm
    doc = SimpleDocTemplate(
        str(PDF), pagesize=LETTER,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN,
        title="Aplomb.Calm — Pouch v1 Supplier Specification",
        author="Aplomb Health, Inc.",
    )

    story = []

    # Masthead
    story.append(Paragraph(
        '<font name="Cormorant-Italic">Aplomb</font>'
        '<font name="Cormorant-Italic" color="#7a3d14">.</font>',
        s["h1"]))
    story.append(Paragraph(
        "Calm · pouch v1 · supplier specification", s["tag"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=AMBER,
                            spaceBefore=0, spaceAfter=12))

    # 1. SKU summary
    story.append(Paragraph("1. SKU summary", s["h2"]))
    story.append(tbl([
        ["Attribute", "Value"],
        ["SKU", "APL-CALM-30P-V1"],
        ["Product name", "Aplomb.Calm — ginger gummies for GLP-1 nausea"],
        ["Net weight", "90 g"],
        ["Count", "30 gummies @ ~3 g each"],
        ["Serving", "2 gummies (15 servings per pouch)"],
        ["Shelf life target", "24 months from manufacture date"],
        ["Storage", "Cool, dry, out of direct light"],
    ], col_widths=[58 * mm, 105 * mm]))

    # 2. Pouch fabrication
    story.append(Paragraph("2. Pouch fabrication", s["h2"]))
    story.append(tbl([
        ["Attribute", "Value"],
        ["Format", "Stand-up flat-bottom pouch (gusseted)"],
        ["Face dimensions", "120 mm W × 190 mm H"],
        ["Gusset depth", "50 mm"],
        ["Bleed", "3 mm all sides (artwork canvas 126 × 196 mm)"],
        ["Safe zone", "6 mm inset (typesetting area 114 × 178 mm)"],
        ["Substrate", "PET 12 µm / Alu 8 µm / LDPE 100 µm laminate"],
        ["Outer finish", "Matte (no gloss varnish)"],
        ["Recyclability target", "CEFLEX-compatible mono-material laminate where feasible"],
        ["Closure", "Press-to-close zip-lock"],
        ["Tamper evidence", "Tear-notch, right edge, 35 mm from top"],
        ["Hang hole", "Optional — top-center, 6 mm Ø, 4 mm from bleed edge"],
    ], col_widths=[58 * mm, 105 * mm]))

    # 3. Print spec
    story.append(Paragraph("3. Print specification", s["h2"]))
    story.append(tbl([
        ["Attribute", "Value"],
        ["Process", "4-color CMYK process"],
        ["Finish", "Matte varnish overall"],
        ["Foils / spot colors", "None"],
        ["Bleed", "3 mm on every edge"],
        ["Registration tolerance", "±0.3 mm"],
        ["Maximum total ink coverage", "280%"],
    ], col_widths=[58 * mm, 105 * mm]))

    story.append(Paragraph("Color values (CMYK · sRGB reference)", s["h3"]))
    story.append(tbl([
        ["Token", "sRGB hex", "CMYK", "Where"],
        ["Bone substrate", "#f7f1e6", "3 / 4 / 10 / 0", "pouch background"],
        ["Ink", "#1a1512", "47 / 45 / 44 / 55", "body type, Supp Facts rules and type"],
        ["Amber", "#7a3d14", "0 / 60 / 94 / 37", "brand period, plumb-bob, section rules"],
        ["Ink at 60%", "#6e6864", "28 / 27 / 26 / 33", "FDA disclaimer only"],
    ], col_widths=[34 * mm, 24 * mm, 36 * mm, 69 * mm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "sRGB hex values are reference; <b>CMYK is authoritative</b>. "
        "Convert using GRACoL 2013 (CRPC6) reference printing condition. "
        "Pure black (CMYK 0/0/0/100) is not used anywhere — Ink is a warm rich black.",
        s["small"]))

    # 4. Typography
    story.append(Paragraph("4. Typography", s["h2"]))
    story.append(tbl([
        ["Use", "Font", "Weight", "Style"],
        ['Wordmark · "Aplomb."', "Cormorant Garamond", "500", "Italic"],
        ['Section labels', "Cormorant Garamond", "500", "Italic"],
        ["Supplement Facts type", "IBM Plex Sans", "700 / 400", "Roman"],
        ["All body copy", "IBM Plex Sans", "400 / 500", "Roman"],
        ["FDA disclaimer", "IBM Plex Sans", "400", "Italic"],
    ], col_widths=[55 * mm, 50 * mm, 28 * mm, 30 * mm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Minimum type sizes (hard limits):</b> 5 pt FDA disclaimer · "
        "6 pt all other body · 8 pt Supplement Facts column headers and primary nutrient labels.",
        s["body"]))
    story.append(Paragraph(
        "<b>Glyphs are outlined to paths</b> in the SVG and PDF. There is no live text "
        "in the artwork files. Confirm in Acrobat: <i>File → Properties → Fonts</i> list is empty.",
        s["body"]))

    # 5. Label content order
    story.append(Paragraph("5. Label content (back panel, top to bottom)", s["h2"]))
    items = [
        'Plumb-bob mark + "Aplomb." wordmark + "Ginger gummies for GLP-1 nausea" subhead',
        "<i>Why Calm.</i> — one-paragraph brand line",
        "<b>Supplement Facts</b> panel (FDA 21 CFR 101.36 format)",
        "<b>Other Ingredients</b> line",
        "Allergen + format declaration",
        "<i>Directions.</i> and <i>Warnings.</i> — two adjacent columns",
        "Storage line · Distributed-by block (Aplomb Health, Inc., Marina del Rey, CA)",
        "FDA disclaimer (italic, 60% ink)",
        "Lot / Best-By imprint zone, centered at bottom (70 × 14 mm, dashed outline)",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(t, s["body"]), leftIndent=10) for t in items],
        bulletType="1", bulletFontName="PlexSans-Bold",
        bulletFontSize=9, bulletColor=AMBER,
    ))

    # 6. File checklist
    story.append(Paragraph("6. File checklist (delivered)", s["h2"]))
    story.append(tbl([
        ["File", "Purpose"],
        ["Aplomb_Calm_Back_Label.svg", "Vector source, glyphs outlined"],
        ["Aplomb_Calm_Back_Label.pdf", "Print-ready PDF, embedded subset fonts"],
        ["Aplomb_Calm_Back_Label.png", "High-res raster preview"],
        ["Aplomb_Calm_Pouch_Schematic.pdf", "Dieline + bleed/safe diagram with dimensions"],
        ["mockup_back_composite.jpg", "Photoreal back-of-pouch reference"],
        ["mockup_front_back_hero.jpg", "Photoreal front+back marketing reference (not for print)"],
    ], col_widths=[78 * mm, 85 * mm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Supplier receives no PSD, AI, or Sketch source — none exist. "
        "All artwork is generated from <i>build_back_label.py</i> and "
        "<i>build_schematic.py</i> in the project repository.",
        s["small"]))

    # 7. Pre-press checklist
    story.append(Paragraph("7. Pre-press checklist (supplier confirms before plate)", s["h2"]))
    checks = [
        "CMYK conversion applied with GRACoL 2013 reference profile",
        "All four color values match the table above within ΔE &lt; 3",
        "Bleed verified at 3 mm on all four edges",
        "Tear notch position centered on right edge, 35 mm from top",
        "UPC imprint zone left as dashed-outline placeholder (supplier prints actual UPC)",
        "Lot / Best-By imprint zone left as dashed-outline placeholder (supplier prints at fill)",
        "Matte varnish overall, no glossy spot UV",
        "No live text in PDF (Acrobat font list empty)",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(t, s["body"]), leftIndent=10) for t in checks],
        bulletType="bullet", bulletColor=AMBER,
        bulletFontName="PlexSans-Bold",
    ))

    # 8. Open items
    story.append(Paragraph("8. Open items — Aplomb Health to confirm before plate", s["h2"]))
    opens = [
        "<b>Lot / Best-By print flow</b> — supplier ink-jets variable data at fill into the dashed imprint zone at the bottom of the back panel.",
        "<b>Per-gummy ginger extract dose</b> — current artwork: 1 g (1000 mg) per 2-gummy serving = 500 mg per gummy. Formulator to confirm.",
        "<b>UPC</b> — intentionally omitted. The pouch is DTC-only (sold direct through getaplomb.com). No retail UPC required. Add later if going wholesale.",
        "<b>Country-of-origin marking</b> — current label does not include 'Made in' text. If the contract manufacturer is outside the US, CBP marking rules require it; confirm CM location before plate.",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(t, s["body"]), leftIndent=10) for t in opens],
        bulletType="1", bulletColor=AMBER,
        bulletFontName="PlexSans-Bold",
    ))

    # 9. Contact
    story.append(Paragraph("9. Aplomb Health — point of contact", s["h2"]))
    story.append(Paragraph(
        "Brand owner: Aplomb Health, Inc. (operating brand name <b>APLOMB.</b>)<br/>"
        "Website: getaplomb.com<br/>"
        "Email: hello@getaplomb.com<br/>"
        "Project lead for this SKU: [PROJECT LEAD — TBD]",
        s["body"]))

    doc.build(story)
    print(f"✓ wrote {PDF.name}")


if __name__ == "__main__":
    main()
