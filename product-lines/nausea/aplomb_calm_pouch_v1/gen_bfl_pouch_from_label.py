#!/usr/bin/env python3
"""
One-shot BFL Flux 2 Pro generation: pouch + label, no compositing.

Passes the real label PNG (Aplomb_Calm_Back_Label.png) as `image_prompt`
to Flux 2 Pro so the model treats the actual label artwork as the print
on the back of the pouch — not a style hint, but the real content.

Output: bfl_pouch_v2.jpg
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

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

LABEL = HERE / "Aplomb_Calm_Back_Label.png"
OUT   = HERE / "bfl_pouch_v3.jpg"


PROMPT = (
    "An editorial product still life photograph, camera straight-on, "
    "centered. A single matte uncoated stand-up flat-bottom pouch fills "
    "most of the frame vertically. The pouch is approximately 120 mm wide "
    "and 190 mm tall (about 1.6 times taller than wide), in warm bone-cream "
    "color with a barely perceptible heathered fiber texture suggesting "
    "recyclable kraft lamination — NOT shiny plastic, NOT glossy, NOT mylar. "
    "It stands upright on a flat gusseted base. Across the top is a subtle "
    "pressed ziplock closure visible as two faint horizontal lines. "
    "THE FULL BACK FACE OF THE POUCH IS PRINTED, EDGE TO EDGE, with the "
    "exact label artwork shown in the reference image: the Aplomb italic "
    "serif wordmark with amber period and plumb-bob mark at top, "
    "GINGER GUMMIES FOR GLP-1 NAUSEA tracked subhead, amber horizontal "
    "rule, 'Why Calm.' italic heading and brand paragraph, full "
    "Supplement Facts panel with Calories 20, Total Carbohydrate 5g, "
    "Total Sugars 3g, Added Sugars 3g, and Ginger Root Extract 1g, "
    "Other Ingredients block, allergens line, Storage line, Distributed-by "
    "line with 4140 Glencoe Ave Marina del Rey address, amber rule, "
    "Directions and Warnings two-column boxed panel, footer tagline band "
    "'30 GUMMIES · 1 G GINGER PER SERVING · NET WT 90 G' between amber "
    "rules, italic FDA disclaimer, dashed LOT / BEST BY box, and a small "
    "centered amber plumb-bob mark at the very bottom. The label print is "
    "in dark warm-black ink (#1a1512) on the bone substrate with amber "
    "(#7a3d14) accents. Crisp, restrained, editorial typography like a "
    "high-end Aesop or Augustinus Bader supplement label. The pouch sits "
    "on a warm travertine stone slab. Generous negative space at top. "
    "Soft directional natural window light from the upper-left, warm "
    "late-morning, painterly shadows fall to the right. Shot on Phase One "
    "IQ4 medium format, 80mm leaf-shutter lens, no flash, f/4.5, shallow "
    "realistic depth of field. A real photograph - NOT AI-generated, NOT "
    "a 3D render, NOT illustration. Indistinguishable from a Kinfolk "
    "magazine still life. Real materials, real surfaces, real natural "
    "light, real shadow detail. Color palette strictly warm bone, cream, "
    "deep amber, warm taupe, soft sand — NO blue, NO teal, NO cool grey, "
    "NO neon, NO red, NO forest green, NO pure black."
)


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def post_json(path, payload):
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"POST {path} -> {e.code}: {body}")


def poll(polling_url, request_id, label):
    url = polling_url or f"{BASE}/get_result?id={request_id}"
    deadline = time.time() + 300
    while time.time() < deadline:
        req = urllib.request.Request(url, headers={"x-key": API_KEY})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        s = data.get("status")
        if s == "Ready":
            return (data.get("result") or {}).get("sample")
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


def main():
    if not LABEL.exists():
        sys.exit(f"label PNG not found: {LABEL}")

    img_b64 = encode_image(LABEL)
    print(f"label PNG encoded: {len(img_b64) // 1024} KB base64")

    payload = {
        "prompt": PROMPT,
        "width": 1024,
        "height": 1408,
        "image_prompt": img_b64,
        "image_prompt_strength": 0.95,
        "prompt_upsampling": False,
        "safety_tolerance": 2,
        "output_format": "jpeg",
    }

    print(f"[bfl_pouch_v2] {ENDPOINT} {payload['width']}x{payload['height']} "
          f"image_prompt_strength={payload['image_prompt_strength']}")
    resp = post_json(ENDPOINT, payload)
    sample = poll(resp.get("polling_url", ""), resp["id"], "bfl_pouch_v2")
    if not sample:
        sys.exit("generation failed")
    download(sample, OUT)
    print(f"\nDone: {OUT}")


if __name__ == "__main__":
    main()
