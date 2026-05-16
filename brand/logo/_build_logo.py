"""
Build the canonical Aplomb logo SVGs.

Outputs (all in this directory):
  aplomb-logo.svg          — primary lockup, mark + wordmark, OUTLINED paths
  aplomb-wordmark.svg      — wordmark only, OUTLINED paths
  aplomb-mark.svg          — mark only (copy of the canonical mark)
  aplomb-logo-web.svg      — mark + live <text> wordmark, for web use

Run from this directory: `python3 _build_logo.py`
"""

import os
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _mark_data import VIEWBOX as MARK_VB, TRANSFORM as MARK_TRANSFORM, PATH_D as MARK_PATH_D

FONT_PATH = os.path.join(HERE, "CormorantGaramond-MediumItalic.ttf")

INK = "#1a1512"
AMBER = "#7a3d14"
TEXT = "Aplomb."

# Mark viewBox + bob path are traced by _trace_mark.py from the source JPG.
# MARK_VB = (0, 0, 140, 430). The line+bob fill the full viewBox vertically.
MARK_VB_X, MARK_VB_Y, MARK_VB_W, MARK_VB_H = MARK_VB
MARK_VISIBLE_H = MARK_VB_H  # potrace cropped exactly to content

# Proportions cribbed from Logo Designs/02-plumb-line-mark.jpg:
#   mark_height ≈ 4.0 × wordmark_height  (line is long; bob is small)
#   gap ≈ 0.5 × wordmark_height
MARK_RATIO = 4.0
GAP_RATIO = 0.5


def get_glyph(font, glyph_set, ch):
    cmap = font.getBestCmap()
    gname = cmap[ord(ch)]
    path_pen = SVGPathPen(glyph_set)
    glyph_set[gname].draw(path_pen)
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[gname].draw(bounds_pen)
    adv = font["hmtx"][gname][0]
    return path_pen.getCommands(), bounds_pen.bounds, adv


def build_wordmark_glyphs():
    """Return (upem, glyphs[], wordmark_bbox)."""
    font = TTFont(FONT_PATH)
    upem = font["head"].unitsPerEm
    glyph_set = font.getGlyphSet()

    x = 0
    glyphs = []
    for ch in TEXT:
        d, bbox, adv = get_glyph(font, glyph_set, ch)
        glyphs.append({"ch": ch, "d": d, "x": x, "bbox": bbox, "adv": adv})
        x += adv

    bboxes = [
        (g["x"] + g["bbox"][0], g["bbox"][1], g["x"] + g["bbox"][2], g["bbox"][3])
        for g in glyphs
        if g["bbox"]
    ]
    wxmin = min(b[0] for b in bboxes)
    wxmax = max(b[2] for b in bboxes)
    wymin = min(b[1] for b in bboxes)
    wymax = max(b[3] for b in bboxes)
    return upem, glyphs, (wxmin, wymin, wxmax, wymax)


def mark_svg_elements(scale, tx, ty, color=AMBER):
    """Render the canonical plumb-bob mark (traced from source JPG), scaled and positioned.

    The mark's natural viewBox is (0,0, MARK_VB_W, MARK_VB_H). The path data is in
    potrace's internal scale, with TRANSFORM mapping it back into the viewBox.
    Wrap both transforms so the mark renders at (tx, ty) with the requested scale.
    """
    return [
        f'  <g transform="translate({tx:.2f},{ty:.2f}) scale({scale:.6f})" fill="{color}">',
        f'    <g transform="{MARK_TRANSFORM}">',
        f'      <path d="{MARK_PATH_D}"/>',
        '    </g>',
        '  </g>',
    ]


def wordmark_svg_elements(glyphs, wbox, tx, ty):
    """Render the outlined wordmark, baseline anchored at (tx, ty)."""
    wxmin, wymin, wxmax, wymax = wbox
    # Center glyphs horizontally around tx using the bbox center.
    origin_x = tx - (wxmin + wxmax) / 2
    out = [f'  <g transform="translate({origin_x:.2f},{ty:.2f}) scale(1,-1)">']
    for g in glyphs:
        fill = AMBER if g["ch"] == "." else INK
        out.append(
            f'    <path d="{g["d"]}" transform="translate({g["x"]},0)" fill="{fill}"/>'
        )
    out.append('  </g>')
    return out


def write_svg(filename, content_lines):
    path = os.path.join(HERE, filename)
    with open(path, "w") as f:
        f.write("\n".join(content_lines) + "\n")
    size = os.path.getsize(path)
    print(f"  wrote {filename}  ({size:,} bytes)")


def build_full_lockup(glyphs, wbox):
    """Mark + outlined wordmark, transparent background."""
    wxmin, wymin, wxmax, wymax = wbox
    wmark_width = wxmax - wxmin
    wmark_height = wymax - wymin

    mark_height = wmark_height * MARK_RATIO
    gap = wmark_height * GAP_RATIO
    mark_scale = mark_height / MARK_VISIBLE_H
    mark_total_w = MARK_VB_W * mark_scale

    content_w = max(wmark_width, mark_total_w)
    pad_x = content_w * 0.12
    pad_y = wmark_height * 0.45

    canvas_w = content_w + 2 * pad_x
    canvas_h = mark_height + gap + wmark_height + 2 * pad_y
    cx = canvas_w / 2

    # Mark: top at y=pad_y, centered horizontally.
    mark_tx = cx - (MARK_VB_W / 2) * mark_scale
    mark_ty = pad_y

    # Wordmark baseline: positioned so the top of letters (font y=wymax)
    # lands at SVG y = pad_y + mark_height + gap.
    wb_y = pad_y + mark_height + gap + wymax

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.1f} {canvas_h:.1f}" role="img" aria-label="Aplomb">',
        '  <title>Aplomb</title>',
    ]
    out += mark_svg_elements(mark_scale, mark_tx, mark_ty)
    out += wordmark_svg_elements(glyphs, wbox, cx, wb_y)
    out.append('</svg>')
    return out


def build_wordmark_only(glyphs, wbox):
    """Outlined wordmark only, transparent background."""
    wxmin, wymin, wxmax, wymax = wbox
    wmark_width = wxmax - wxmin
    wmark_height = wymax - wymin

    pad_x = wmark_width * 0.06
    pad_y = wmark_height * 0.20

    canvas_w = wmark_width + 2 * pad_x
    canvas_h = wmark_height + 2 * pad_y
    cx = canvas_w / 2
    wb_y = pad_y + wymax

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.1f} {canvas_h:.1f}" role="img" aria-label="Aplomb">',
        '  <title>Aplomb</title>',
    ]
    out += wordmark_svg_elements(glyphs, wbox, cx, wb_y)
    out.append('</svg>')
    return out


def build_mark_only():
    """Plumb-bob mark only (line + bob with notch), traced from the source JPG."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MARK_VB_W:g} {MARK_VB_H:g}" role="img" aria-label="Aplomb mark">',
        '  <title>Aplomb mark</title>',
        f'  <g transform="{MARK_TRANSFORM}" fill="{AMBER}">',
        f'    <path d="{MARK_PATH_D}"/>',
        '  </g>',
        '</svg>',
    ]


def build_web_lockup(glyphs, wbox):
    """Lockup with live <text> for wordmark — requires Cormorant Garamond at runtime."""
    wxmin, wymin, wxmax, wymax = wbox
    wmark_width = wxmax - wxmin
    wmark_height = wymax - wymin

    # Use the SAME geometry as the outlined lockup so the two are visually interchangeable.
    mark_height = wmark_height * MARK_RATIO
    gap = wmark_height * GAP_RATIO
    mark_scale = mark_height / MARK_VISIBLE_H

    content_w = max(wmark_width, MARK_VB_W * mark_scale)
    pad_x = content_w * 0.12
    pad_y = wmark_height * 0.45

    canvas_w = content_w + 2 * pad_x
    canvas_h = mark_height + gap + wmark_height + 2 * pad_y
    cx = canvas_w / 2

    mark_tx = cx - (MARK_VB_W / 2) * mark_scale
    mark_ty = pad_y

    # For <text>, place baseline at the same position the outlined wordmark uses.
    text_baseline_y = pad_y + mark_height + gap + wmark_height
    # Font size: the wordmark bbox height (cap-A top → "p"/"b" descender) ≈ 0.7..0.78 * em
    # for italic 500. Inverse: font-size ≈ wmark_height / 0.72 (empirical for Cormorant).
    font_size = wmark_height / 0.72

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.1f} {canvas_h:.1f}" role="img" aria-label="Aplomb">',
        '  <title>Aplomb</title>',
    ]
    out += mark_svg_elements(mark_scale, mark_tx, mark_ty)
    out.append(
        f'  <text x="{cx:.2f}" y="{text_baseline_y:.2f}" text-anchor="middle"'
        f' font-family="\'Cormorant Garamond\', \'EB Garamond\', Garamond, \'Times New Roman\', serif"'
        f' font-style="italic" font-weight="500" font-size="{font_size:.2f}" fill="{INK}">'
        f'Aplomb<tspan fill="{AMBER}">.</tspan></text>'
    )
    out.append('</svg>')
    return out


def main():
    print("Building Aplomb logo SVGs...")
    upem, glyphs, wbox = build_wordmark_glyphs()
    wxmin, wymin, wxmax, wymax = wbox
    print(f"  upem={upem}  wordmark bbox: x=[{wxmin:.0f},{wxmax:.0f}] y=[{wymin:.0f},{wymax:.0f}]  size={wxmax-wxmin:.0f}×{wymax-wymin:.0f}")

    write_svg("aplomb-logo.svg", build_full_lockup(glyphs, wbox))
    write_svg("aplomb-wordmark.svg", build_wordmark_only(glyphs, wbox))
    write_svg("aplomb-mark.svg", build_mark_only())
    write_svg("aplomb-logo-web.svg", build_web_lockup(glyphs, wbox))
    print("Done.")


if __name__ == "__main__":
    main()
