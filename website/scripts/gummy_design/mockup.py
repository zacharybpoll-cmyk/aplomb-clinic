"""
Editorial product mockup — bottle render in PIL.

Two views per bottle SKU:
  Front view  — bottle facing the camera, label readable, cap visible
  3-up view   — bottle pair: closed bottle + tipped-open + a few gummies
                on the bone surface

These are not photo-real — they're the same editorial style used for the
Packlane mailers: bone background, subtle shadow, hairline ground line,
brand header/footer chrome, hand-drawn-looking precision.

Output: 2000 × 2400 px PNG per view.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")

# Canvas
CANVAS_W = 2000
CANVAS_H = 1800
PADDING = 200


# ----- Color helpers -------------------------------------------------------

def _hex(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


BG = _hex(g.BG_HEX)
BONE = _hex(g.BONE_HEX)
INK = _hex(g.INK_HEX)
AMBER = _hex(g.AMBER_HEX)
RULE = _hex(g.RULE_HEX)
MUTED = _hex(g.MUTED_HEX)
CAP = _hex(g.CAP_HEX)
GUMMY = _hex(g.GUMMY_HEX)


# ----- Font loader ---------------------------------------------------------

FONT_PATHS = {
    "cormorant":      "/Users/zacharypoll/Library/Fonts/CormorantGaramond-Italic.ttf",
    "cormorant_reg":  "/Users/zacharypoll/Library/Fonts/CormorantGaramond.ttf",
    "ibm":            "/Users/zacharypoll/Library/Fonts/IBMPlexSans.ttf",
    "ibm_med":        "/Users/zacharypoll/Library/Fonts/IBMPlexSans.ttf",
    "ibm_italic":     "/Users/zacharypoll/Library/Fonts/IBMPlexSans-Italic.ttf",
}


def _font(kind, size):
    """Load a font; fall back to PIL default if missing."""
    candidates = []
    if kind == "cormorant":
        candidates = [FONT_PATHS["cormorant"], FONT_PATHS["cormorant_reg"]]
    elif kind == "ibm":
        candidates = [FONT_PATHS["ibm"]]
    elif kind == "ibm_med":
        candidates = [FONT_PATHS["ibm_med"], FONT_PATHS["ibm"]]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ----- Page chrome ---------------------------------------------------------

def _draw_chrome(d: ImageDraw.ImageDraw, *, view_label, dim_label):
    f_word = _font("cormorant", 60)
    d.text((PADDING, 60), "Aplomb.", font=f_word, fill=AMBER)
    f_meta = _font("ibm", 28)
    meta = "Outer packaging  ·  Visual mockup  ·  v1"
    bbox = d.textbbox((0, 0), meta, font=f_meta)
    d.text((CANVAS_W - PADDING - (bbox[2] - bbox[0]), 80),
           meta, font=f_meta, fill=AMBER)
    # Top rule
    d.line([(PADDING, 145), (CANVAS_W - PADDING, 145)],
           fill=AMBER, width=1)

    # View label (compact, side-by-side with dim label)
    f_view = _font("cormorant", 56)
    d.text((PADDING, 165), view_label, font=f_view, fill=INK)

    # Dim label (subtitle, beneath)
    f_sub = _font("ibm", 24)
    d.text((PADDING, 240), dim_label, font=f_sub, fill=MUTED)

    # Bottom rule + caption
    d.line([(PADDING, CANVAS_H - 130), (CANVAS_W - PADDING, CANVAS_H - 130)],
           fill=AMBER, width=1)
    d.text((PADDING, CANVAS_H - 100),
           "Aplomb.", font=_font("cormorant", 44), fill=AMBER)


def _ground_line(d: ImageDraw.ImageDraw, y, x0, x1):
    d.line([(x0, y), (x1, y)], fill=RULE, width=1)


# ----- Bottle render -------------------------------------------------------

def _make_label_strip(bottle: g.BottleSpec, *, w_px, h_px):
    """Render the visible front-panel slice of the wraparound label.
    Returns an RGBA image of size (w_px, h_px) — bone background with
    front-panel artwork drawn on top."""
    img = Image.new("RGBA", (w_px, h_px), BONE + (255,))
    d = ImageDraw.Draw(img)
    cx = w_px // 2

    # Wordmark "Aplomb." (top, prominent)
    f_word = _font("cormorant", int(h_px * 0.16))
    word = "Aplomb."
    bbox = d.textbbox((0, 0), word, font=f_word)
    word_w = bbox[2] - bbox[0]
    word_h = bbox[3] - bbox[1]
    d.text((cx - word_w // 2, int(h_px * 0.06)),
           word, font=f_word, fill=AMBER)

    # Plumb mark (between wordmark and product name)
    pm_top = int(h_px * 0.27)
    pm_h = int(h_px * 0.10)
    line_h = int(pm_h * 0.58)
    diamond_h = pm_h - line_h
    d.line([(cx, pm_top), (cx, pm_top + line_h)],
           fill=AMBER, width=3)
    half = max(2, int(diamond_h * 0.22))
    diamond_top_y = pm_top + line_h
    diamond_mid_y = diamond_top_y + int(diamond_h * 0.35)
    diamond_bottom_y = diamond_top_y + diamond_h
    d.polygon([
        (cx, diamond_top_y),
        (cx - half, diamond_mid_y),
        (cx, diamond_bottom_y),
        (cx + half, diamond_mid_y),
    ], fill=AMBER)

    # Product name "Calm." — visual hero
    f_name = _font("cormorant", int(h_px * 0.40))
    name = "Calm."
    bbox = d.textbbox((0, 0), name, font=f_name)
    name_w = bbox[2] - bbox[0]
    d.text((cx - name_w // 2, int(h_px * 0.40)),
           name, font=f_name, fill=INK)

    # Hairline rule
    rule_y = int(h_px * 0.78)
    rule_w = int(w_px * 0.32)
    d.line([(cx - rule_w // 2, rule_y), (cx + rule_w // 2, rule_y)],
           fill=AMBER, width=1)

    # Tagline
    f_tag = _font("cormorant", int(h_px * 0.075))
    tag = "For nausea, on the drug."
    bbox = d.textbbox((0, 0), tag, font=f_tag)
    tag_w = bbox[2] - bbox[0]
    d.text((cx - tag_w // 2, int(h_px * 0.81)),
           tag, font=f_tag, fill=AMBER)

    # Spec line at bottom
    f_spec = _font("ibm_med", int(h_px * 0.055))
    spec = f"GINGER GUMMIES  ·  {bottle.count} CT"
    bbox = d.textbbox((0, 0), spec, font=f_spec)
    sw = bbox[2] - bbox[0]
    d.text((cx - sw // 2, int(h_px * 0.92)),
           spec, font=f_spec, fill=MUTED)
    return img


def _draw_bottle(canvas: Image.Image, *, bottle: g.BottleSpec,
                 cx, base_y, scale, tilt=0):
    """Draw a single bottle on `canvas` at (cx, base_y), scale = px/mm.
    `tilt` not implemented — kept as a hook for future open variant."""
    d = ImageDraw.Draw(canvas)

    body_dia = int(bottle.body_dia_mm * scale)
    body_h = int(bottle.body_h_mm * scale)
    shoulder_h = int(bottle.shoulder_h_mm * scale)
    neck_dia = int(bottle.neck_dia_mm * scale)
    neck_h = int(bottle.neck_h_mm * scale)
    cap_dia = int(bottle.cap_dia_mm * scale)
    cap_h = int(bottle.cap_h_mm * scale)

    half_body = body_dia // 2
    half_neck = neck_dia // 2
    half_cap = cap_dia // 2

    body_left = cx - half_body
    body_right = cx + half_body
    body_top = base_y - body_h
    shoulder_top = body_top - shoulder_h
    neck_top = shoulder_top - neck_h
    # Cap sits directly on the shoulder — only ~1mm of neck visible
    visible_neck_h = int(1 * scale)
    cap_bottom = shoulder_top - visible_neck_h
    cap_top = cap_bottom - cap_h

    # Soft drop shadow under the bottle (ellipse, blurred)
    shadow_w = int(body_dia * 1.15)
    shadow_h = int(body_dia * 0.20)
    sh = Image.new("RGBA", (shadow_w + 40, shadow_h + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse((20, 20, 20 + shadow_w, 20 + shadow_h),
               fill=(60, 50, 35, 80))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=10))
    canvas.alpha_composite(
        sh, (cx - shadow_w // 2 - 20, base_y - shadow_h // 2 - 5)
    )

    # ---- Body (rounded rectangle) ----
    radius = int(bottle.base_radius_mm * scale)
    d.rounded_rectangle(
        (body_left, body_top, body_right, base_y),
        radius=radius,
        fill=BONE, outline=INK, width=2,
    )

    # ---- Shoulder (trapezoid filled bone) ----
    d.polygon([
        (body_left, body_top),
        (cx - half_neck, shoulder_top),
        (cx + half_neck, shoulder_top),
        (body_right, body_top),
    ], fill=BONE, outline=INK)

    # ---- Neck ---- (PIL y grows DOWN; neck_top has smaller y than shoulder_top)
    d.rectangle((cx - half_neck, neck_top, cx + half_neck, shoulder_top),
                fill=BONE, outline=INK, width=2)
    # Thread ticks (inside neck region)
    for i in range(3):
        ty = neck_top + int(neck_h * (0.30 + 0.20 * i))
        d.line([(cx - half_neck + 2, ty), (cx + half_neck - 2, ty)],
               fill=MUTED, width=1)

    # ---- Cap (rounded rect, dark warm-black, overlaps neck) ----
    cap_radius = int(cap_h * 0.20)
    d.rounded_rectangle(
        (cx - half_cap, cap_top, cx + half_cap, cap_bottom),
        radius=cap_radius,
        fill=CAP, outline=INK, width=1,
    )
    # cap knurl (vertical fluting — typical CRC pattern)
    n_ticks = 32
    for i in range(n_ticks):
        xx = cx - half_cap + int((i + 0.5) * (cap_dia / n_ticks))
        d.line([(xx, cap_top + cap_radius), (xx, cap_bottom - 2)],
               fill=(50, 42, 30), width=1)

    # ---- Label (centered on body) ----
    label_h_px = int(bottle.label_h_mm * scale)
    label_y_offset = int(bottle.label_y_offset_mm * scale)
    label_top = base_y - label_y_offset - label_h_px
    label_left = body_left + 4
    label_right = body_right - 4
    label_strip = _make_label_strip(
        bottle,
        w_px=label_right - label_left,
        h_px=label_h_px,
    )
    canvas.alpha_composite(label_strip, (label_left, label_top))
    return cap_top  # for layout reference


# ----- Gummy render (small loose gummies for 3-up view) --------------------

def _draw_gummy(canvas, cx, cy, r):
    """A loose ginger gummy — orange-brown teardrop / pillow shape."""
    d = ImageDraw.Draw(canvas)
    # Pillow shape via rounded rectangle
    w = int(r * 2.2)
    h = int(r * 1.4)
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    d.rounded_rectangle(box, radius=int(h * 0.45),
                        fill=GUMMY,
                        outline=(140, 65, 25, 255), width=2)
    # Glossy highlight
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse((int(w * 0.15), int(h * 0.10),
                int(w * 0.55), int(h * 0.40)),
               fill=(255, 230, 200, 110))
    hl = hl.filter(ImageFilter.GaussianBlur(radius=3))
    canvas.alpha_composite(hl, (box[0], box[1]))
    # Sugar coating dots
    import random
    rnd = random.Random(cx + cy)
    for _ in range(int(w * h / 100)):
        sx = rnd.randint(box[0] + 4, box[2] - 4)
        sy = rnd.randint(box[1] + 4, box[3] - 4)
        d.ellipse((sx, sy, sx + 2, sy + 2),
                  fill=(255, 240, 210, 200))


# ----- Front view ----------------------------------------------------------

def render_front(bottle: g.BottleSpec, out_path: Path):
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG + (255,))
    d = ImageDraw.Draw(canvas)
    _draw_chrome(
        d,
        view_label=f"{bottle.sku.replace('Aplomb. ', '')}  ·  front",
        dim_label=f"{bottle.body_dia_mm:.0f}×{bottle.total_h_mm:.0f} mm  ·  "
                  f"{bottle.count} ct  ·  ginger gummy bottle, label as printed",
    )

    scale = 10.5   # px / mm — bottle ~118mm ⇒ ~1239px on canvas
    base_y = CANVAS_H - 200
    cx = CANVAS_W // 2
    _ground_line(d, base_y + 14, PADDING + 80, CANVAS_W - PADDING - 80)
    _draw_bottle(canvas, bottle=bottle, cx=cx,
                 base_y=base_y, scale=scale)

    # Caption under bottle
    f_cap = _font("ibm", 26)
    caption = ("Bone HDPE bottle  ·  matte CMYK label  ·  "
               "warm-black 38-400 induction-seal CRC closure")
    bbox = d.textbbox((0, 0), caption, font=f_cap)
    cw = bbox[2] - bbox[0]
    d.text((CANVAS_W // 2 - cw // 2, CANVAS_H - 175),
           caption, font=f_cap, fill=MUTED)

    canvas.convert("RGB").save(out_path, format="PNG", optimize=True)
    print(f"Wrote {out_path.name} ({out_path.stat().st_size // 1024} KB)")


# ----- 3-up "story" view ---------------------------------------------------

def render_threeup(bottle: g.BottleSpec, out_path: Path):
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG + (255,))
    d = ImageDraw.Draw(canvas)
    _draw_chrome(
        d,
        view_label=f"{bottle.sku.replace('Aplomb. ', '')}  ·  on shelf",
        dim_label=("Two bottles + a few loose gummies. "
                   "Same shot for hero photography, IG carousel slide 1."),
    )

    scale = 8.5   # smaller bottles (two of them on canvas)
    base_y = CANVAS_H - 250

    # Ground line
    _ground_line(d, base_y + 16, PADDING + 50, CANVAS_W - PADDING - 50)

    # Bottle 1 — left
    cx1 = int(CANVAS_W * 0.34)
    _draw_bottle(canvas, bottle=bottle, cx=cx1,
                 base_y=base_y, scale=scale)
    # Bottle 2 — right
    cx2 = int(CANVAS_W * 0.66)
    _draw_bottle(canvas, bottle=bottle, cx=cx2,
                 base_y=base_y, scale=scale)

    # Loose gummies in foreground (between & in front)
    gummy_r = 38
    positions = [
        (int(CANVAS_W * 0.50), base_y + 14, gummy_r),
        (int(CANVAS_W * 0.46), base_y + 64, gummy_r - 2),
        (int(CANVAS_W * 0.55), base_y + 56, gummy_r - 2),
        (int(CANVAS_W * 0.20), base_y + 40, gummy_r - 4),
        (int(CANVAS_W * 0.80), base_y + 60, gummy_r - 4),
    ]
    for (x, y, r) in positions:
        _draw_gummy(canvas, x, y, r)

    # Caption
    f_cap = _font("ibm", 26)
    caption = ("Two bottles plus scatter  ·  bone surface, soft afternoon light  ·  "
               "reference for product photography brief")
    bbox = d.textbbox((0, 0), caption, font=f_cap)
    cw = bbox[2] - bbox[0]
    d.text((CANVAS_W // 2 - cw // 2, CANVAS_H - 175),
           caption, font=f_cap, fill=MUTED)

    canvas.convert("RGB").save(out_path, format="PNG", optimize=True)
    print(f"Wrote {out_path.name} ({out_path.stat().st_size // 1024} KB)")


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for bottle in g.ALL_BOTTLES:
        suffix = bottle.sku.replace("Aplomb. ", "").replace(" ", "_")
        render_front(bottle, OUT_DIR / f"Aplomb_{suffix}_Gummy_Mockup_Front.png")
        render_threeup(bottle, OUT_DIR / f"Aplomb_{suffix}_Gummy_Mockup_Shelf.png")


if __name__ == "__main__":
    render_all()
