"""
Composite the back-label PNG onto the BFL empty-pouch photograph.

Approach:
  1. Identify the four corners of the visible front face (below zipper,
     above gusset base, between the side seams).
  2. Inset a few percent so a hint of bone material remains around the print —
     realistic for full-bleed pouch printing where the side seam stays unprinted.
  3. Perspective-warp the back-label PNG onto that quad.
  4. Luminosity transfer: the pouch's shadows and creases modulate the printed
     label so it doesn't look pasted on. Bounded so small type stays readable.
  5. Feather the mask edges so the boundary doesn't read as a sticker rim.

Output: mockup_back_composite.jpg
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

HERE = Path(__file__).resolve().parent
POUCH = HERE / "bfl_empty_pouch_back.jpg"
LABEL = HERE / "Aplomb_Calm_Back_Label.png"
OUT   = HERE / "mockup_back_composite.jpg"

# Corners of the visible front face in the BFL image (native 1152 x 1536).
# We upscale the pouch 2x to 2304x3072 before compositing so the label warp
# happens at native label resolution (label PNG is 2083 x 3239, similar scale),
# which keeps 6pt body type readable. Corner coords below are at the 2x scale.
SCALE = 2
TL = (290 * SCALE, 275 * SCALE)
TR = (665 * SCALE, 275 * SCALE)
BR = (675 * SCALE, 845 * SCALE)
BL = (282 * SCALE, 845 * SCALE)

# No inset — full-bleed printing across the entire visible face.
INSET = 0.00

# Crop margin around the pouch when producing the final output, at 2x scale.
CROP_MARGIN = 80 * SCALE


def shrink_quad(quad, inset):
    cx = sum(p[0] for p in quad) / 4
    cy = sum(p[1] for p in quad) / 4
    return tuple(
        (p[0] + (cx - p[0]) * inset, p[1] + (cy - p[1]) * inset)
        for p in quad
    )


def perspective_coeffs(dst_corners, src_corners):
    """PIL maps OUTPUT pixel -> SOURCE pixel, so solve dst->src."""
    matrix = []
    rhs = []
    for (dx, dy), (sx, sy) in zip(dst_corners, src_corners):
        matrix.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        matrix.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])
        rhs.extend([sx, sy])
    A = np.array(matrix, dtype=float)
    B = np.array(rhs, dtype=float)
    coeffs, *_ = np.linalg.lstsq(A, B, rcond=None)
    return coeffs.tolist()


def main():
    pouch = Image.open(POUCH).convert("RGB")
    label = Image.open(LABEL).convert("RGB")

    # Upscale the BFL pouch so the composite renders at native label resolution.
    new_size = (pouch.size[0] * SCALE, pouch.size[1] * SCALE)
    pouch = pouch.resize(new_size, Image.Resampling.LANCZOS)

    pw, ph = pouch.size
    lw, lh = label.size

    quad = shrink_quad((TL, TR, BR, BL), INSET)
    qTL, qTR, qBR, qBL = quad

    src_corners = [(0, 0), (lw, 0), (lw, lh), (0, lh)]
    dst_corners = [qTL, qTR, qBR, qBL]
    coeffs = perspective_coeffs(dst_corners, src_corners)

    warped = label.transform(
        (pw, ph),
        Image.Transform.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(247, 241, 230),
    )

    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).polygon([qTL, qTR, qBR, qBL], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    mask_arr = np.asarray(mask, dtype=np.float32)[..., None] / 255.0

    pouch_arr = np.asarray(pouch, dtype=np.float32) / 255.0
    label_arr = np.asarray(warped, dtype=np.float32) / 255.0

    # Treat the label as a multiplicative ink layer on the bone substrate.
    # Where the label is bone-colored (#f7f1e6), the multiplier is 1.0, so the
    # pouch pixel passes through UNCHANGED — every crease, every shadow, every
    # natural variation in the BFL photograph stays visible.
    # Where the label has ink (dark text, supp-facts rules, panel border),
    # the multiplier drops below 1.0 and darkens the pouch toward the ink colour.
    # This is the same maths as real printing on matte paper: ink absorbs light,
    # the substrate is still there underneath.
    BONE = np.array([247.0, 241.0, 230.0]) / 255.0   # label paper colour
    multiplier = label_arr / BONE
    # Apply a slight gamma so middle tones (the small body type) print
    # noticeably darker, matching how ink absorption looks on matte paper.
    # gamma > 1 darkens the midtones without crushing pure bone (=1) or
    # pure ink (≈0.08).
    multiplier = np.where(
        multiplier < 1.0,
        np.power(np.clip(multiplier, 0.001, 1.0), 1.35),
        multiplier,
    )
    multiplier = np.clip(multiplier, 0.05, 1.0)

    printed = np.clip(pouch_arr * multiplier, 0, 1)

    # Feathered mask so the label fades into the bone at the natural side seams,
    # rather than terminating in a hard edge that would read as a sticker rim.
    soft_mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(soft_mask).polygon([qTL, qTR, qBR, qBL], fill=255)
    soft_mask = soft_mask.filter(ImageFilter.GaussianBlur(6))
    soft_mask_arr = np.asarray(soft_mask, dtype=np.float32)[..., None] / 255.0

    composite_arr = pouch_arr * (1 - soft_mask_arr) + printed * soft_mask_arr
    composite_arr = np.clip(composite_arr, 0, 1)
    composite = Image.fromarray((composite_arr * 255).astype(np.uint8), "RGB")

    # Do NOT crop into the pouch. We want the FULL pouch in context — top
    # zipper, gusset base, travertine surround. Earlier tight-crop attempts
    # produced something that read as "flat label on texture" rather than
    # "photo of a printed pouch." Keep the full BFL frame.
    print(f"output size: {composite.size}")

    composite.save(OUT, quality=94)
    print(f"✓ wrote {OUT.name}")


if __name__ == "__main__":
    main()
