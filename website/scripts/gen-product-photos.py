#!/usr/bin/env python3
"""
Photoreal product mockups for the 3 confirmed APLOMB. SKUs.

Generates one Kinfolk-magazine-style still life per SKU via BFL Flux 2
Pro, with the bottle described in detail and a cream paper label
showing the product wordmark. Note: Flux can render short legible
labels but long INCI lists tend to come out garbled — if final
marketing photos need pixel-perfect labels, composite the SVG label
artwork onto the bottle in post.

Usage:
  source ~/.claude/secrets.env
  python3 scripts/gen-product-photos.py             # all 3 SKUs
  python3 scripts/gen-product-photos.py peptide-serum
"""
import argparse
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
            if line.startswith("BFL_API_KEY=") or line.startswith("export BFL_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                break
if not API_KEY:
    sys.exit("BFL_API_KEY not set.")


BASE = "https://api.bfl.ai/v1"
ENDPOINT = "flux-2-pro"
HEADERS = {"x-key": API_KEY, "Content-Type": "application/json"}

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "product designs"


ANTI_AI_TAIL = (
    " A real photograph - not AI-generated, not 3D render, not illustration. "
    "Indistinguishable from a Kinfolk-magazine still life or a documentary "
    "image in The Gentlewoman. Real materials, real surfaces, real natural "
    "light, real shadow detail. NOT plastic-looking, NOT waxy, NOT CGI, NOT "
    "AI-glossy, NOT oversaturated, NOT halo-effect, NOT lens flare, NOT "
    "fantasy lighting, NOT stock photography. Editorial commercial "
    "photography in Kinfolk magazine tonality, desaturated brand palette."
)


CANDIDATES = [
    {
        "sku": "peptide-serum",
        "filename": "Aplomb_Peptide_Serum_Photo_1.jpg",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Editorial product still life of a 30 mL frosted-glass cosmetic "
            "dropper bottle with a matte black dropper cap, photographed on a "
            "warm travertine stone slab in soft late-morning natural window "
            "light from the upper-left. The bottle wears a small cream paper "
            "label printed with the word 'Aplomb' in restrained black serif "
            "italic type, followed by a small period in deep amber, then a "
            "thin horizontal hairline rule, then the words 'THE SERUM' in "
            "small letter-spaced sans-serif beneath. Beside the bottle: a "
            "folded square of natural linen with subtle wrinkles, a single "
            "olive branch with a few muted-green leaves, a small bone-china "
            "saucer in cream. The palette is warm bone, cream, soft sand, "
            "deep amber, warm umber. NO blue, NO teal, NO cool grey. Soft "
            "painterly shadows fall to the lower-right. Phase One IQ4 medium-"
            "format aesthetic, 80mm leaf-shutter lens, no flash, no CGI."
            + ANTI_AI_TAIL
        ),
    },
    {
        "sku": "hair-growth-serum",
        "filename": "Aplomb_Hair_Growth_Serum_Photo_1.jpg",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Editorial product still life of a 2 fl oz amber-glass dropper "
            "bottle with a matte black dropper bulb, photographed on a warm "
            "travertine stone slab in soft late-morning natural window light "
            "from the upper-left. The bottle wears a wraparound cream paper "
            "label printed with the word 'Aplomb' in restrained black serif "
            "italic type, followed by a small period in deep amber, then a "
            "fine hairline rule, then 'ROOTS — BOTANICAL HAIR SERUM' in small "
            "letter-spaced sans-serif beneath. Beside the bottle: a small "
            "bundle of dried wheat stalks lying on natural linen, a sprig of "
            "rosemary on a bone-china saucer in cream. Palette: warm bone, "
            "cream, soft sand, deep amber, warm umber, the warm honey of the "
            "amber glass. NO blue, NO teal, NO cool grey. Painterly shadows "
            "fall to the lower-right. Phase One IQ4 medium-format aesthetic, "
            "80mm leaf-shutter lens, no flash."
            + ANTI_AI_TAIL
        ),
    },
    {
        "sku": "chewables",
        "filename": "Aplomb_Chewables_Photo_1.jpg",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Editorial product still life of a 30-count cylindrical dietary-"
            "supplement jar in cream-glazed ceramic with a matte black "
            "screw cap. The jar is photographed on a warm travertine stone "
            "slab in soft late-morning natural window light from the upper-"
            "left. The jar wears a wraparound cream paper label. The label "
            "has the brand wordmark APLOMB (six letters: A-P-L-O-M-B) "
            "rendered in black serif italic type, followed immediately by "
            "a single small period in deep amber color. Below the wordmark "
            "is a thin horizontal hairline rule, and beneath that, in small "
            "letter-spaced sans-serif, the words 'BREATH — DENTAL & ORAL "
            "HEALTH CHEWABLES'. The wordmark must be spelled correctly: "
            "A, then P, then L, then O, then M, then B — APLOMB. "
            "Beside the jar: a small open vintage apothecary tin tipped "
            "slightly forward to show two or three round mint-green-cream "
            "chewable tablets resting inside, a single sprig of fresh "
            "peppermint with two small leaves, a folded square of natural "
            "linen. Palette: warm bone, cream, pale sage, soft sand, deep "
            "amber, warm umber. NO bright blue, NO teal, NO cool grey. "
            "Painterly shadows fall to the lower-right. Phase One IQ4 "
            "medium-format aesthetic, 80mm leaf-shutter lens, no flash."
            + ANTI_AI_TAIL
        ),
    },
]


def post(path, body):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), headers=HEADERS,
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def generate(c):
    body = {
        "prompt": c["prompt"],
        "width": c["width"],
        "height": c["height"],
        "prompt_upsampling": False,
        "safety_tolerance": 2,
        "output_format": "jpeg",
    }
    print(f"[{c['sku']}] submitting...")
    j = post(f"/{ENDPOINT}", body)
    if "polling_url" not in j:
        print(f"[{c['sku']}] unexpected response: {j}")
        return None
    poll = j["polling_url"]
    for i in range(180):  # up to 6 minutes
        time.sleep(2)
        try:
            r = get(poll)
        except urllib.error.HTTPError as e:
            print(f"[{c['sku']}] poll error: {e}")
            return None
        status = r.get("status")
        if status == "Ready":
            url = r["result"]["sample"]
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            out_dir = PRODUCTS_DIR / c["sku"]
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / c["filename"]
            out.write_bytes(data)
            print(f"[{c['sku']}] saved → {out.relative_to(ROOT)}")
            return out
        if status == "Error" or status == "Failed":
            print(f"[{c['sku']}] {status}: {r}")
            return None
        # otherwise: Pending
    print(f"[{c['sku']}] timed out")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sku", nargs="?", help="single SKU slug")
    args = ap.parse_args()

    targets = CANDIDATES
    if args.sku:
        targets = [c for c in CANDIDATES if c["sku"] == args.sku]
        if not targets:
            sys.exit(f"unknown sku: {args.sku}")

    for c in targets:
        generate(c)


if __name__ == "__main__":
    main()
