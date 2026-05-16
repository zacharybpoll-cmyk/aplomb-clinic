#!/usr/bin/env python3
"""
Aplomb.Calm pouch v1 — BFL Flux 2 Pro mockup generator.

Two outputs:
  bfl_empty_pouch_back.jpg     blank back face, for compositing the SVG label over
  mockup_front_back_hero.jpg   3/4 hero showing front + back, marketing reference
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_KEY = os.environ.get("BFL_API_KEY")
if not API_KEY:
    secrets = Path.home() / ".claude" / "secrets.env"
    if secrets.exists():
        for line in secrets.read_text().splitlines():
            line = line.strip()
            if line.startswith("BFL_API_KEY=") or line.startswith("export BFL_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                break
if not API_KEY:
    sys.exit("BFL_API_KEY not set.")

BASE = "https://api.bfl.ai/v1"
ENDPOINT = "flux-2-pro"
HEADERS = {"x-key": API_KEY, "Content-Type": "application/json"}

OUT_DIR = Path(__file__).resolve().parent

ANTI_AI = (
    " A real photograph - not AI-generated, not 3D render, not illustration. "
    "Indistinguishable from a Kinfolk-magazine still life or a documentary "
    "image in The Gentlewoman. Real materials, real surfaces, real natural "
    "light, real shadow detail. NOT plastic-looking, NOT waxy, NOT CGI, NOT "
    "AI-glossy, NOT oversaturated, NOT halo-effect, NOT lens flare, NOT "
    "fantasy lighting, NOT stock photography. Editorial commercial "
    "photography in Kinfolk magazine tonality, desaturated brand palette."
)

POUCH_BLANK = (
    "The product is a matte uncoated stand-up flat-bottom pouch, "
    "approximately 120 mm wide and 190 mm tall (about 1.6 times taller "
    "than wide - a balanced retail pouch, NOT a slim sachet). The pouch "
    "is in a warm bone-cream color (#efe8dc) with a barely perceptible "
    "heathered fiber texture suggesting recyclable kraft lamination - "
    "NOT shiny plastic, NOT glossy, NOT mylar. The pouch stands upright "
    "on a flat gusseted base. A subtle pressed ziplock closure is visible "
    "at the very top as two faint horizontal lines. "
    "CRITICAL: the pouch is ENTIRELY UNIFORM bone material. There is NO "
    "paper label, NO sticker, NO applied rectangle, NO secondary label "
    "area, NO printed area, NO patch of different color or texture. "
    "It is one continuous, uniform, unbroken bone-cream kraft surface "
    "from the zipper at the top all the way down to the gusset base. "
    "Completely blank and unprinted, the way a kraft pouch looks before "
    "any printing or labeling is applied. Clean uniform matte bone."
)

POUCH_PRINTED = (
    "The product is a matte uncoated stand-up flat-bottom pouch about 120 mm "
    "wide and 190 mm tall, in a warm bone-cream color (#efe8dc) with a barely "
    "perceptible heathered fiber texture suggesting recyclable kraft "
    "lamination - NOT shiny plastic, NOT glossy, NOT mylar. The pouch stands "
    "upright on a flat gusseted base. Across the top there is a subtle "
    "pressed ziplock closure visible as two horizontal lines. The front of "
    "the pouch is printed flat (no embossing, no foil, no metallic): "
    "centered near the top a single small mark in deep amber (#7a3d14) - a "
    "thin vertical line dropping into a triangular plumb-bob weight. Below "
    "the mark, in restrained Cormorant Garamond italic 500 black serif type "
    "(#1a1512), the wordmark 'Aplomb' followed by a small period in deep "
    "amber, and below that in slightly larger Cormorant Garamond italic the "
    "single word 'Calm'. Below the wordmark, a thin amber hairline rule. "
    "Below the rule, tiny letter-spaced IBM Plex Sans regular uppercase "
    "reading 'GINGER GUMMIES FOR GLP-1 NAUSEA'. Near the bottom of the "
    "printed area, tiny IBM Plex Sans regular reading "
    "'30 gummies / Net wt 90 g'. Type is crisp, restrained, well-spaced."
)

PALETTE_LIGHT = (
    "Color palette strictly warm bone (#f7f1e6), cream, deep amber "
    "(#7a3d14), warm taupe, soft sand - NO blue, NO teal, NO cool grey, "
    "NO neon, NO red, NO forest green, NO pure black. Soft directional "
    "natural window light from the upper-left, warm late-morning, "
    "painterly shadows fall to the right. Shot on Phase One IQ4 medium "
    "format, 80mm leaf-shutter lens, no flash, f/4.5, shallow but "
    "realistic depth of field."
)

POUCH_PRINTED_BACK = (
    "The product is a matte uncoated stand-up flat-bottom pouch, "
    "approximately 120 mm wide and 190 mm tall (about 1.6 times taller "
    "than wide). Warm bone-cream color (#efe8dc) with a barely perceptible "
    "heathered fiber texture suggesting recyclable kraft lamination. The "
    "front of the pouch is fully printed with a dietary supplement BACK "
    "LABEL, printed flat in dark warm-black ink (#1a1512) on the bone "
    "substrate (no foil, no metallic, no gloss): centered near the top a "
    "tiny amber plumb-bob mark with the italic serif wordmark 'Aplomb.' "
    "below it (the period in deep amber #7a3d14), followed by tracked-out "
    "small letter-spaced uppercase 'GINGER GUMMIES FOR GLP-1 NAUSEA'. "
    "Below that, a thin amber horizontal rule. Below the rule, an italic "
    "serif section heading 'Why Calm.' followed by three lines of small "
    "sans-serif body text. Below that, a rectangular SUPPLEMENT FACTS box "
    "with thin dark stroke containing a 'Supplement Facts' bold header, "
    "serving info, a thick horizontal rule, column headers 'Amount Per "
    "Serving' and '% Daily Value', then 4 rows of nutrition data with "
    "underrules, a thicker rule, then one active ingredient row 'Ginger "
    "Root Extract … 1 g'. Below the box, an 'Other Ingredients:' label "
    "and two lines of small sans-serif body text. Below that, an allergen "
    "line. Below another thin amber rule, two adjacent body-text columns "
    "headed 'Directions.' and 'Warnings.' in italic serif. Below another "
    "rule, a Storage line, a Distributed-by line with address. Below "
    "that, a 3-line italic FDA disclaimer in slightly lighter grey ink. "
    "At the very bottom, a single centered rectangular box outlined in "
    "dashed thin grey stroke labeled 'LOT / BEST BY' for the supplier "
    "imprint. The print is restrained, editorial, clinical - looks like "
    "a high-end Aesop or Augustinus Bader supplement label. NO photos, "
    "NO illustrations, NO emoji - purely typographic. The label fills "
    "the entire visible front face of the pouch with a thin bone-material "
    "margin at the side seams. Type is crisp and dark on bone."
)

CANDIDATES = [
    {
        "label": "bfl_pouch_with_label",
        "width": 1152,
        "height": 1536,
        "prompt": (
            "An editorial product still life, camera straight-on. "
            + POUCH_PRINTED_BACK
            + " The pouch stands alone on a warm travertine stone slab "
            "with a fold of natural undyed linen at the lower edge. Generous "
            "warm-bone backdrop. The printed label is the focus of the image. "
            + PALETTE_LIGHT
            + ANTI_AI
        ),
    },
    {
        "label": "bfl_empty_pouch_back",
        "width": 1152,
        "height": 1536,   # 3:4 portrait — wider canvas than before, still tall
        "prompt": (
            "An editorial product still life, camera nearly straight-on, "
            "centered. A single tall slim stand-up pouch fills most of the "
            "frame vertically, with the pouch height occupying about 80 "
            "percent of the image height. "
            + POUCH_BLANK
            + " The pouch stands alone on a warm travertine stone slab, "
            "with a single fold of natural undyed linen draped at the lower "
            "edge of the frame. Generous negative space at top. The full "
            "pouch face is visible and completely unprinted from top "
            "zipper down to the gusset base. "
            + PALETTE_LIGHT
            + ANTI_AI
        ),
    },
    {
        "label": "mockup_front_back_hero",
        "width": 1600,
        "height": 1280,   # 5:4 landscape
        "prompt": (
            "An editorial product still life. Two identical matte bone-"
            "cream stand-up flat-bottom pouches stand side-by-side on a "
            "warm travertine stone slab. "
            + POUCH_PRINTED
            + " The pouch on the left is angled in three-quarter front "
            "view, fully showing the printed front label - 'Aplomb.' "
            "wordmark in italic serif, 'Calm' below, plumb-bob mark above, "
            "GINGER GUMMIES FOR GLP-1 NAUSEA subhead, 30 gummies dose "
            "line. The pouch on the right is rotated 180 degrees in three-"
            "quarter back view, showing the back face which is also "
            "printed: it carries a small Supplement Facts box, several "
            "blocks of small dark serif and sans-serif body text, an "
            "Other Ingredients line, Directions, Warnings, a Distributed-"
            "by line, an FDA disclaimer in lighter ink, and two small "
            "rectangular zones at the bottom for UPC and a Lot/Best-By "
            "imprint - all the text crisp, restrained, real-looking, like "
            "a serious editorial dietary supplement label. Both pouches "
            "share matching matte fiber texture and identical bone color. "
            "Soft fold of natural undyed linen at the bottom edge between "
            "the two pouches. Generous negative space. "
            + PALETTE_LIGHT
            + ANTI_AI
        ),
    },
]


def post_json(path, payload):
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"POST {path} -> {e.code}: {e.read().decode(errors='replace')}")


def poll(polling_url, request_id, label):
    url = polling_url or f"{BASE}/get_result?id={request_id}"
    deadline = time.time() + 300
    while time.time() < deadline:
        req = urllib.request.Request(url, headers={"x-key": API_KEY})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        s = data.get("status")
        if s == "Ready":
            sample = (data.get("result") or {}).get("sample")
            return sample
        if s in ("Error", "Failed", "Request Moderated", "Content Moderated"):
            print(f"[{label}] status={s}: {data}")
            return None
        print(f"  [{label}] status={s} ... polling")
        time.sleep(2)
    sys.exit(f"[{label}] timed out")


def download(url, out):
    with urllib.request.urlopen(url, timeout=60) as r:
        out.write_bytes(r.read())
    print(f"  -> wrote {out.name} ({out.stat().st_size // 1024} KB)")


def gen(c):
    out = OUT_DIR / f"{c['label']}.jpg"
    print(f"[{c['label']}] {ENDPOINT} {c['width']}x{c['height']}")
    resp = post_json(ENDPOINT, {
        "prompt": c["prompt"],
        "width": c["width"],
        "height": c["height"],
    })
    sample = poll(resp.get("polling_url", ""), resp["id"], c["label"])
    if not sample:
        print(f"  [{c['label']}] skipped (moderated)")
        return None
    download(sample, out)
    return out


def main():
    only = set(sys.argv[1:])
    for c in CANDIDATES:
        if only and c["label"] not in only:
            continue
        gen(c)
    print(f"\nDone. Images in {OUT_DIR}")


if __name__ == "__main__":
    main()
