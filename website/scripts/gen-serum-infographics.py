#!/usr/bin/env python3
"""
APLOMB. The Serum — PDP infographics (brand-native, PIL).

Two conversion assets, rendered 2x-supersampled then LANCZOS-downscaled for
crisp type, in the house system (bone canvas, amber sole accent, ink text,
Cormorant Garamond display + IBM Plex Sans body):

  serum-mechanism.png  The two-driver model: volumetric half (fillers) vs
                        dermal half (where the Serum acts).
  serum-timeline.png    What to expect, weeks 0 to 16.

House rules honoured: no em dashes, no editorial eyebrows, no banned colours
(amber/bone/ink/muted only), hedged claims, no GLP-1 drug brand names.

Run: python3 website/scripts/gen-serum-infographics.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/Get-Aplomb")
OUT = REPO / "website" / "assets"
FONTS = Path.home() / "Library" / "Fonts"

BG      = (239, 232, 220)   # --bg  #efe8dc
PAPER   = (247, 241, 230)   # --paper #f7f1e6
INK     = (26, 21, 18)      # --ink #1a1512
AMBER   = (122, 61, 20)     # --amber #7a3d14
AMBER_L = (217, 160, 107)   # --amber-light #d9a06b
RULE    = (217, 207, 189)   # --rule #d9cfbd
MUTED   = (107, 93, 76)     # --muted #6b5d4c

S = 2  # supersample factor
DISP_W = 1840
DISP_H = 1180


def F(name, size):
    return ImageFont.truetype(str(FONTS / name), size * S)

SERIF   = "CormorantGaramond.ttf"
SERIF_I = "CormorantGaramond-Italic.ttf"
SANS    = "IBMPlexSans.ttf"


def canvas():
    img = Image.new("RGB", (DISP_W * S, DISP_H * S), BG)
    return img, ImageDraw.Draw(img)


def text(d, xy, s, font, fill, anchor="la", spacing=None, max_w=None):
    if max_w and spacing is None:
        # simple word wrap
        words, lines, cur = s.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= max_w * S:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        s = "\n".join(lines)
    d.multiline_text(xy, s, font=font, fill=fill, anchor=anchor,
                     spacing=(spacing or 0) * S)
    return s


def save(img, name):
    out = OUT / name
    img.resize((DISP_W, DISP_H), Image.LANCZOS).save(out, quality=95)
    print(f"  -> {name} ({out.stat().st_size // 1024} KB)")


def mechanism():
    img, d = canvas()
    M = 120
    d.text((M * S, 96 * S), "Two ways rapid weight loss",
            font=F(SERIF, 78), fill=INK, anchor="la")
    d.text((M * S, 176 * S), "changes the face.",
            font=F(SERIF_I, 78), fill=INK, anchor="la")
    text(d, (M * S, 300 * S),
         "Only one of the two is a layer a topical can reach.",
         F(SANS, 30), MUTED, anchor="la", max_w=900)

    # two stacked bands
    bx, bw = M, DISP_W - 2 * M
    by, bh, gap = 400, 290, 36

    # Band 1 — volumetric (neutral / not our layer)
    d.rectangle([bx * S, by * S, (bx + bw) * S, (by + bh) * S],
                fill=PAPER, outline=RULE, width=2 * S)
    d.rectangle([bx * S, by * S, (bx + 8) * S, (by + bh) * S], fill=RULE)
    d.text(((bx + 56) * S, (by + 56) * S), "The volumetric half",
           font=F(SERIF, 52), fill=INK)
    text(d, ((bx + 56) * S, (by + 130) * S),
         "Subcutaneous fat-pad volume, 50 to 100 mL, drawn down in the "
         "first 90 days. The visible hollowing.",
         F(SANS, 28), MUTED, max_w=820)
    d.text(((bx + bw - 56) * S, (by + bh - 52) * S),
           "Addressed by fillers, Sculptra, fat grafting",
           font=F(SANS, 25), fill=MUTED, anchor="rs")

    # Band 2 — dermal (amber, our layer)
    cy = by + bh + gap
    d.rectangle([bx * S, cy * S, (bx + bw) * S, (cy + bh) * S],
                fill=PAPER, outline=AMBER_L, width=2 * S)
    d.rectangle([bx * S, cy * S, (bx + 8) * S, (cy + bh) * S], fill=AMBER)
    d.text(((bx + 56) * S, (cy + 56) * S), "The dermal half",
           font=F(SERIF, 52), fill=AMBER)
    text(d, ((bx + 56) * S, (cy + 130) * S),
         "Collagen and matrix thinning under caloric restriction. Texture "
         "change, fine-line depth, the crepey quality above the cheekbone.",
         F(SANS, 28), INK, max_w=820)
    d.text(((bx + bw - 56) * S, (cy + bh - 52) * S),
           "Where The Serum acts",
           font=F(SANS, 26), fill=AMBER, anchor="rs")

    d.text((M * S, (DISP_H - 70) * S),
           "Extrapolated on the shared collagen-loss mechanism. "
           "Not a substitute for volume restoration.",
           font=F(SERIF_I, 26), fill=MUTED)
    save(img, "serum-mechanism.png")


def timeline():
    img, d = canvas()
    M = 120
    d.text((M * S, 96 * S), "What to expect,",
            font=F(SERIF, 78), fill=INK)
    d.text((M * S, 176 * S), "and when.",
            font=F(SERIF_I, 78), fill=INK)
    text(d, (M * S, 300 * S),
         "Twice daily, clean skin. The dermal layer turns over slowly, so "
         "the measured window is weeks, not days.",
         F(SANS, 30), MUTED, max_w=1000)

    ax0, ax1 = M + 210, DISP_W - M - 210
    axis_y = 720
    # gentle rising curve (quadratic-ish via points)
    pts = []
    nodes = [0.0, 0.25, 0.5, 0.75, 1.0]
    rise = [0.06, 0.20, 0.46, 0.80, 0.96]
    for t, r in zip(nodes, rise):
        x = ax0 + (ax1 - ax0) * t
        y = axis_y - 300 * r
        pts.append((x, y))
    # baseline axis
    d.line([ax0 * S, axis_y * S, ax1 * S, axis_y * S], fill=RULE, width=2 * S)
    # curve
    d.line([(p[0] * S, p[1] * S) for p in pts], fill=AMBER, width=5 * S,
           joint="curve")
    for (x, y) in pts:
        d.ellipse([(x - 9) * S, (y - 9) * S, (x + 9) * S, (y + 9) * S],
                  fill=BG, outline=AMBER, width=4 * S)

    labels = [
        ("Week 0", "Baseline. One to two drops,\nAM and PM."),
        ("Weeks 4 to 8", "Surface texture and\nhydration shift first."),
        ("Weeks 8 to 12", "The window cosmeceutical\ntrials measure: fine-line\ndepth, tonicity."),
        ("Weeks 12 to 16", "Continued use holds it.\nPairs with SPF and\ndietary protein."),
        ("Ongoing", "Maintenance,\nnot a course."),
    ]
    for (x, y), (head, body) in zip(pts, labels):
        ty = axis_y + 56
        d.text((x * S, ty * S), head, font=F(SANS, 27), fill=AMBER,
               anchor="ma")
        d.multiline_text((x * S, (ty + 42) * S), body, font=F(SANS, 24),
                         fill=MUTED, anchor="ma", align="center",
                         spacing=6 * S)

    d.text((M * S, (DISP_H - 70) * S),
           "Evidence is in general dermal-aging populations, extrapolated on "
           "the shared collagen-loss mechanism. Individual response varies.",
           font=F(SERIF_I, 26), fill=MUTED)
    save(img, "serum-timeline.png")


if __name__ == "__main__":
    print("Rendering Serum infographics...")
    mechanism()
    timeline()
    print("Done.")
