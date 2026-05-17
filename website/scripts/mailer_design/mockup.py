"""
Editorial isometric mockups — the actual artwork warped onto box faces.

Two PNGs per size (1200x1500 each, 300dpi-equivalent):
  Aplomb_Mailer_<size>_Mockup_Closed.png
  Aplomb_Mailer_<size>_Mockup_Open.png

We render each visible face as a flat PIL image (with the correct artwork)
then perspective-warp it to a parallelogram in isometric space and
composite onto a bone-colored canvas. No AI-glow, no fantasy lighting —
clean editorial product render.
"""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging")
FONT_DIR = Path.home() / "Library" / "Fonts"

# Mockup canvas
CANVAS_W, CANVAS_H = 2000, 2400      # 1:1.2 portrait, prints at 8x10in @ 240dpi
DPI_RENDER = 240                      # internal resolution
PX_PER_IN = DPI_RENDER

# Isometric angles (classic 30° iso)
ISO_X_ANGLE = 30  # degrees from horizontal for X edges
ISO_Y_ANGLE = 30  # degrees from horizontal for Y (depth) edges


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _hex_rgb(hex_):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

BONE = _hex_rgb(g.BONE_HEX)
BG = _hex_rgb(g.BG_HEX)
INK = _hex_rgb(g.INK_HEX)
AMBER = _hex_rgb(g.AMBER_HEX)
RULE = _hex_rgb(g.RULE_HEX)
MUTED = _hex_rgb(g.MUTED_HEX)


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

_font_cache = {}

def _font(name_part, size, italic=False):
    """Look up an installed TTF, with `name_part` such as 'Cormorant' or 'Plex'."""
    key = (name_part, italic)
    path = _font_cache.get(key)
    if path is None:
        for ttf in FONT_DIR.glob("*.ttf"):
            n = ttf.name
            if name_part not in n:
                continue
            if italic and "Italic" not in n:
                continue
            if not italic and "Italic" in n:
                continue
            path = ttf
            break
        if path is None:
            raise RuntimeError(f"Font {name_part} (italic={italic}) not found in {FONT_DIR}")
        _font_cache[key] = path
    return ImageFont.truetype(str(path), size)


# ---------------------------------------------------------------------------
# Plumb-bob mark drawn into a PIL Image
# ---------------------------------------------------------------------------

def _draw_plumb_mark(draw, cx, cy, height, color):
    line_h = height * 0.58
    diamond_h = height * 0.42
    line_top = cy - height / 2
    line_bottom = line_top + line_h
    # Vertical line
    draw.line([(cx, line_top), (cx, line_bottom)],
              fill=color, width=max(2, int(height * 0.022)))
    # Diamond
    half_w = diamond_h * 0.18
    diamond_top = line_bottom
    diamond_mid_y = line_bottom + diamond_h * 0.35
    diamond_bottom = line_bottom + diamond_h
    draw.polygon([
        (cx, diamond_top),
        (cx - half_w, diamond_mid_y),
        (cx, diamond_bottom),
        (cx + half_w, diamond_mid_y),
    ], fill=color)


# ---------------------------------------------------------------------------
# Render a flat panel face at high DPI
# ---------------------------------------------------------------------------

def _render_lid(box, w_px, h_px, *, interior=False):
    """LID exterior or interior face."""
    img = Image.new("RGB", (w_px, h_px), BONE)
    d = ImageDraw.Draw(img)
    cx, cy = w_px // 2, h_px // 2
    if not interior:
        # Plumb mark + Aplomb. wordmark
        mark_h = int(h_px * 0.30)
        _draw_plumb_mark(d, cx, cy - int(h_px * 0.10), mark_h, AMBER)
        font_size = int(h_px * 0.22)
        f_word = _font("Cormorant", font_size, italic=True)
        word = "Aplomb"
        period = "."
        word_bbox = d.textbbox((0, 0), word, font=f_word)
        period_bbox = d.textbbox((0, 0), period, font=f_word)
        word_w = word_bbox[2] - word_bbox[0]
        period_w = period_bbox[2] - period_bbox[0]
        baseline_y = cy + int(h_px * 0.18)
        # Text height for vertical centering
        text_h = word_bbox[3] - word_bbox[1]
        ty = baseline_y - text_h // 2
        total_w = word_w + period_w
        wx = cx - total_w // 2
        d.text((wx, ty), word, font=f_word, fill=AMBER)
        d.text((wx + word_w, ty), period, font=f_word, fill=AMBER)
    else:
        # Interior reveal — Carry your bearing. + body copy
        f_hero = _font("Cormorant", int(h_px * 0.18), italic=True)
        hero = "Carry your bearing."
        bbox = d.textbbox((0, 0), hero, font=f_hero)
        d.text((cx - (bbox[2] - bbox[0]) // 2, cy - int(h_px * 0.27)),
               hero, font=f_hero, fill=AMBER)
        # Hairline rule
        rule_w = int(w_px * 0.30)
        rule_y = cy - int(h_px * 0.06)
        d.line([(cx - rule_w // 2, rule_y), (cx + rule_w // 2, rule_y)],
               fill=AMBER, width=2)
        # Body copy — single editorial line
        f_body = _font("Cormorant", int(h_px * 0.13), italic=True)
        body = "Stay your best self"
        bbox = d.textbbox((0, 0), body, font=f_body)
        d.text((cx - (bbox[2] - bbox[0]) // 2, cy + int(h_px * 0.05)),
               body, font=f_body, fill=INK)
    return img


def _render_front(box, w_px, h_px):
    img = Image.new("RGB", (w_px, h_px), BONE)
    d = ImageDraw.Draw(img)
    cx, cy = w_px // 2, h_px // 2
    # Hairline rule above
    rule_w = int(w_px * 0.36)
    rule_y = cy - int(h_px * 0.30)
    d.line([(cx - rule_w // 2, rule_y), (cx + rule_w // 2, rule_y)],
           fill=AMBER, width=2)
    # Two-line tagline
    f = _font("Cormorant", int(h_px * 0.20), italic=True)
    line1 = "Preserving your self"
    line2 = "through GLP-1 use."
    for i, line in enumerate([line1, line2]):
        bbox = d.textbbox((0, 0), line, font=f)
        ly = cy - int(h_px * 0.10) + i * int(h_px * 0.26)
        d.text((cx - (bbox[2] - bbox[0]) // 2, ly), line, font=f, fill=AMBER)
    return img


def _render_side(box, w_px, h_px):
    img = Image.new("RGB", (w_px, h_px), BONE)
    d = ImageDraw.Draw(img)
    cx, cy = w_px // 2, h_px // 2
    mark_h = int(h_px * 0.34)
    _draw_plumb_mark(d, cx, cy, mark_h, RULE)
    return img


def _render_back(box, w_px, h_px):
    img = Image.new("RGB", (w_px, h_px), BONE)
    d = ImageDraw.Draw(img)
    cx, cy = w_px // 2, h_px // 2
    f_word = _font("Cormorant", int(h_px * 0.22), italic=True)
    word = "Aplomb"; period = "."
    bw = d.textbbox((0, 0), word, font=f_word)
    pw = d.textbbox((0, 0), period, font=f_word)
    word_w = bw[2] - bw[0]; per_w = pw[2] - pw[0]
    text_h = bw[3] - bw[1]
    # Place small wordmark at left third
    word_x = int(w_px * 0.20)
    ty = cy - text_h // 2
    d.text((word_x, ty), word, font=f_word, fill=MUTED)
    d.text((word_x + word_w, ty), period, font=f_word, fill=AMBER)
    # Hairline rule
    rule_x1 = int(w_px * 0.42); rule_x2 = int(w_px * 0.58)
    d.line([(rule_x1, cy), (rule_x2, cy)], fill=RULE, width=2)
    # URL
    f_url = _font("Plex", int(h_px * 0.13))
    d.text((int(w_px * 0.66), cy - int(h_px * 0.08)), "aplomb.clinic",
           font=f_url, fill=AMBER)
    return img


# ---------------------------------------------------------------------------
# Perspective transform (warp a flat image to an arbitrary quad)
# ---------------------------------------------------------------------------

def _find_coeffs(target_quad, source_size):
    """Compute the 8 PERSPECTIVE coefficients to map source rectangle (size)
    to destination quad. target_quad order: top-left, top-right, bottom-right,
    bottom-left."""
    sw, sh = source_size
    src = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
    dst = list(target_quad)

    # Solve for the 8 coeffs: PIL applies inverse mapping, so we want
    # the matrix that maps DST -> SRC (PIL transform expects this).
    matrix = []
    for (sx, sy), (dx, dy) in zip(src, dst):
        matrix.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        matrix.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])

    # Convert to numpy-free linear solve
    import numpy as np
    A = np.array(matrix, dtype=float)
    B = np.array([sx for (sx, sy) in src for sx in (sx, sy)], dtype=float)
    res = np.linalg.solve(A, B)
    return tuple(res)


def _warp_to_quad(face_img, target_quad, canvas_size):
    """Warp face_img onto target_quad on a transparent canvas of canvas_size."""
    coeffs = _find_coeffs(target_quad, face_img.size)
    warped = face_img.convert("RGBA").transform(
        canvas_size, Image.PERSPECTIVE, coeffs,
        resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    return warped


# ---------------------------------------------------------------------------
# Compose isometric closed-box mockup
# ---------------------------------------------------------------------------

def _iso_closed(box: g.BoxSize, canvas_w=CANVAS_W, canvas_h=CANVAS_H):
    """3/4 isometric view of the closed box with the lid on top."""
    canvas = Image.new("RGBA", (canvas_w, canvas_h), BG + (255,))
    # Anchor the box near canvas center, slightly above center
    cx, cy = canvas_w // 2, int(canvas_h * 0.55)
    # Box edges in pixel space — bigger boxes take more canvas
    scale = 130   # px per inch (a 6" box is ~780px along its length axis)
    L = box.L * scale
    W = box.W * scale
    D = box.D * scale
    # Iso angles
    ax_rad = math.radians(ISO_X_ANGLE)
    ay_rad = math.radians(ISO_Y_ANGLE)
    # Edge vectors
    vx = (L * math.cos(ax_rad), -L * math.sin(ax_rad))   # length axis (front-to-back when viewed top-down)
    vy = (W * math.cos(ay_rad), W * math.sin(ay_rad))    # width axis (side-to-side)
    vz = (0, -D)                                         # depth axis (vertical)
    # Origin = front-bottom-left corner of box
    ox = cx - (vx[0] + vy[0]) / 2
    oy = cy + (vx[1] + vy[1]) / 2 + D / 2
    def pt(a, b, c):
        """Box-space (x along L, y along W, z along D) -> canvas (px)."""
        return (
            ox + a * vx[0] / L + b * vy[0] / W + c * vz[0] / D,
            oy + a * vx[1] / L + b * vy[1] / W + c * vz[1] / D,
        )
    # Eight corners
    p000 = pt(0, 0, 0)            # front-bottom-left
    p100 = pt(L, 0, 0)            # back-bottom-left
    p010 = pt(0, W, 0)            # front-bottom-right
    p110 = pt(L, W, 0)            # back-bottom-right
    p001 = pt(0, 0, D)            # front-top-left
    p101 = pt(L, 0, D)            # back-top-left
    p011 = pt(0, W, D)            # front-top-right
    p111 = pt(L, W, D)            # back-top-right
    # Visible faces (in painter's order):
    #  - LID (top): p001, p011, p111, p101
    #  - FRONT: p001, p011, p010, p000
    #  - RIGHT side: p011, p111, p110, p010
    # Render each face image at native resolution then warp.

    # Native resolutions for each face — keep aspect ratio matching panel
    res_per_in = 200
    lid_img = _render_lid(box, int(box.L * res_per_in), int(box.W * res_per_in))
    front_img = _render_front(box, int(box.L * res_per_in), int(box.D * res_per_in))
    right_img = _render_side(box, int(box.W * res_per_in), int(box.D * res_per_in))
    # When warping LID we need source corners → TL, TR, BR, BL of the source
    # rect to map onto destination quad in the same order.
    # Source for LID: rectangle with TL=(0,0), TR=(L_px, 0), BR=(L_px, W_px), BL=(0, W_px)
    # Destination on canvas: corresponding to box surface corners.
    # We want LID's "top edge" (as viewed in face image) to be the back edge
    # of the box (p101->p111). And LID image bottom = front edge (p001->p011).
    # So map: TL=p101, TR=p111, BR=p011, BL=p001
    lid_warped = _warp_to_quad(lid_img,
                               (p101, p111, p011, p001),
                               (canvas_w, canvas_h))
    # FRONT: TL=p001, TR=p011, BR=p010, BL=p000
    front_warped = _warp_to_quad(front_img,
                                 (p001, p011, p010, p000),
                                 (canvas_w, canvas_h))
    # RIGHT: TL=p011, TR=p111, BR=p110, BL=p010
    right_warped = _warp_to_quad(right_img,
                                 (p011, p111, p110, p010),
                                 (canvas_w, canvas_h))
    # Composite (back-to-front)
    canvas.alpha_composite(lid_warped)
    canvas.alpha_composite(front_warped)
    canvas.alpha_composite(right_warped)
    # Subtle shadow under box
    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    s_y = max(p000[1], p010[1], p110[1])
    sd.ellipse([(cx - L * 0.55, s_y + 4),
                (cx + L * 0.55, s_y + 30)],
               fill=(20, 18, 16, 38))
    canvas = Image.alpha_composite(shadow, canvas)
    # Edge strokes (subtle ink lines between faces for definition)
    edge_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    el = ImageDraw.Draw(edge_layer)
    edges = [
        # Top face outline
        (p001, p011), (p011, p111), (p111, p101), (p101, p001),
        # Front face outline
        (p001, p000), (p000, p010), (p010, p011),
        # Right side outline
        (p111, p110), (p110, p010),
    ]
    for a, b in edges:
        el.line([a, b], fill=INK + (110,), width=2)
    canvas = Image.alpha_composite(canvas, edge_layer)
    return canvas


def _iso_open(box: g.BoxSize, canvas_w=CANVAS_W, canvas_h=CANVAS_H):
    """3/4 view with lid flipped open (interior reveal visible)."""
    canvas = Image.new("RGBA", (canvas_w, canvas_h), BG + (255,))
    # Open view needs slightly less centered anchor — lid extends UP-RIGHT
    cx, cy = int(canvas_w * 0.40), int(canvas_h * 0.65)
    scale = 110
    L = box.L * scale
    W = box.W * scale
    D = box.D * scale
    ax_rad = math.radians(ISO_X_ANGLE)
    ay_rad = math.radians(ISO_Y_ANGLE)
    vx = (L * math.cos(ax_rad), -L * math.sin(ax_rad))
    vy = (W * math.cos(ay_rad), W * math.sin(ay_rad))
    vz = (0, -D)
    ox = cx - (vx[0] + vy[0]) / 2
    oy = cy + (vx[1] + vy[1]) / 2 + D / 2
    def pt(a, b, c):
        return (
            ox + a * vx[0] / L + b * vy[0] / W + c * vz[0] / D,
            oy + a * vx[1] / L + b * vy[1] / W + c * vz[1] / D,
        )
    p000 = pt(0, 0, 0); p100 = pt(L, 0, 0); p010 = pt(0, W, 0); p110 = pt(L, W, 0)
    p001 = pt(0, 0, D); p101 = pt(L, 0, D); p011 = pt(0, W, D); p111 = pt(L, W, D)
    # Lid is hinged at the back edge p101→p111. When flipped open 180° around
    # that hinge, its corners become:
    #   was p001 → reflected over the hinge plane to "back-back":
    #   new position = p101 + (p101 - p001) ... but in the painter view we
    #   approximate by rotating around the back edge in screen space.
    # Simpler: place lid as a parallelogram extending behind the box,
    # flush with the back top edge (p101→p111), going further "back" by L
    # in box-space.
    p001_open = pt(2 * L, 0, D)
    p011_open = pt(2 * L, W, D)

    res_per_in = 200
    lid_int = _render_lid(box, int(box.L * res_per_in),
                          int(box.W * res_per_in), interior=True)
    bottom_img = Image.new("RGB", (int(box.L * res_per_in),
                                   int(box.W * res_per_in)), BONE)
    front_int = _render_front(box, int(box.L * res_per_in),
                              int(box.D * res_per_in))
    right_int = _render_side(box, int(box.W * res_per_in),
                             int(box.D * res_per_in))

    # Lid flipped open: source TL must map to FAR-LEFT of the flipped lid
    # (so source TOP = far edge from viewer = where the title reads).
    # Quad order TL, TR, BR, BL ->
    #   TL = far-left  = p001_open
    #   TR = far-right = p011_open
    #   BR = near-right (hinge right) = p111
    #   BL = near-left  (hinge left)  = p101
    lid_warped = _warp_to_quad(lid_int,
                               (p001_open, p011_open, p111, p101),
                               (canvas_w, canvas_h))
    # BOTTOM (interior, viewed looking down into box): TL=p001 TR=p011 BR=p010 BL=p000
    # Bottom is essentially blank bone for now.
    bottom_warped = _warp_to_quad(bottom_img,
                                  (p001, p011, p010, p000),
                                  (canvas_w, canvas_h))
    # Right side EXTERIOR still visible: TL=p011, TR=p111, BR=p110, BL=p010
    right_warped = _warp_to_quad(right_int,
                                 (p011, p111, p110, p010),
                                 (canvas_w, canvas_h))
    # Front EXTERIOR still visible: TL=p001, TR=p011, BR=p010, BL=p000
    front_warped = _warp_to_quad(front_int,
                                 (p001, p011, p010, p000),
                                 (canvas_w, canvas_h))
    canvas.alpha_composite(lid_warped)
    canvas.alpha_composite(front_warped)
    canvas.alpha_composite(right_warped)
    canvas.alpha_composite(bottom_warped)

    # Edge strokes
    edge_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    el = ImageDraw.Draw(edge_layer)
    edges = [
        # Lid (open) outline
        (p101, p111), (p111, p011_open), (p011_open, p001_open), (p001_open, p101),
        # Visible interior bottom outline
        (p001, p011), (p011, p010), (p010, p000), (p000, p001),
        # Front face
        (p001, p000), (p000, p010),
        # Right side
        (p111, p110), (p110, p010),
    ]
    for a, b in edges:
        el.line([a, b], fill=INK + (110,), width=2)
    canvas = Image.alpha_composite(canvas, edge_layer)
    return canvas


# ---------------------------------------------------------------------------
# Editorial chrome around the rendered box
# ---------------------------------------------------------------------------

def _add_chrome(canvas: Image.Image, *, title: str, subtitle: str,
                caption: str):
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    # Hairline rule near top
    margin = int(w * 0.06)
    d.line([(margin, int(h * 0.07)), (w - margin, int(h * 0.07))],
           fill=RULE, width=2)
    # Eyebrow text top-right
    f_eyebrow = _font("Plex", int(h * 0.014))
    eyebrow = "§ Outer packaging  ·  Visual mockup  ·  v1"
    bbox = d.textbbox((0, 0), eyebrow, font=f_eyebrow)
    d.text((w - margin - (bbox[2] - bbox[0]), int(h * 0.05)),
           eyebrow, font=f_eyebrow, fill=AMBER)
    # Wordmark top-left
    f_word = _font("Cormorant", int(h * 0.030), italic=True)
    bbox = d.textbbox((0, 0), "Aplomb", font=f_word)
    d.text((margin, int(h * 0.04)), "Aplomb", font=f_word, fill=INK)
    bbox2 = d.textbbox((0, 0), ".", font=f_word)
    d.text((margin + (bbox[2] - bbox[0]), int(h * 0.04)),
           ".", font=f_word, fill=AMBER)

    # Title block (below rule, above box)
    f_title = _font("Cormorant", int(h * 0.038), italic=True)
    f_sub = _font("Plex", int(h * 0.014))
    d.text((margin, int(h * 0.085)), title, font=f_title, fill=INK)
    d.text((margin, int(h * 0.130)), subtitle, font=f_sub, fill=MUTED)

    # Caption at bottom
    f_cap = _font("Plex", int(h * 0.013))
    # Bottom rule
    d.line([(margin, int(h * 0.93)), (w - margin, int(h * 0.93))],
           fill=RULE, width=1)
    d.text((margin, int(h * 0.95)), caption, font=f_cap, fill=MUTED)
    return canvas


# ---------------------------------------------------------------------------
# Per-box render
# ---------------------------------------------------------------------------

def render(box: g.BoxSize, view: str, out_path: Path):
    if view == "closed":
        canvas = _iso_closed(box).convert("RGB")
        title = f"{box.sku} · closed"
        subtitle = (f"Bone exterior · amber type · "
                    f"{box.L:.0f}×{box.W:.0f}×{box.D:.0f} in interior "
                    f"({box.L_mm:.0f}×{box.W_mm:.0f}×{box.D_mm:.0f} mm)")
        caption = ("White HDPrint matte paperboard · CMYK single-color amber "
                   "+ ink body  ·  3/4 isometric view · scale ≈ 1:2")
    else:
        canvas = _iso_open(box).convert("RGB")
        title = f"{box.sku} · opened"
        subtitle = ("Lid flipped back to reveal interior message — "
                    "\"Carry your bearing.\"")
        caption = ("Interior copy is rotated 180° on the flat artwork so it "
                   "reads right-side-up to recipient on open. Bottom and side "
                   "interiors print bone (no ink) for cost.")
    canvas = _add_chrome(canvas, title=title, subtitle=subtitle,
                         caption=caption)
    canvas.save(out_path, format="PNG", optimize=True)
    print(f"Wrote {out_path.name}  ({out_path.stat().st_size // 1024} KB)")


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for box in g.ALL_SIZES:
        suffix = "Small_6x4x3" if box is g.SMALL else "Large_7x5x3"
        render(box, "closed",
               OUT_DIR / f"Aplomb_Mailer_{suffix}_Mockup_Closed.png")
        render(box, "open",
               OUT_DIR / f"Aplomb_Mailer_{suffix}_Mockup_Open.png")


if __name__ == "__main__":
    render_all()
