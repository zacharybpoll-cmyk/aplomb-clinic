#!/usr/bin/env python3
"""
APLOMB. site — regenerate every photo asset via Flux 2 Pro.

Sequential generation. Outputs land directly in
`aplomb.clinic/assets/`.

Run:
  source ~/.claude/secrets.env
  python3 gen-bundle-photos.py --test                 # bundle-rail only (test BFL endpoint)
  python3 gen-bundle-photos.py                        # all 5
  python3 gen-bundle-photos.py --only serum-rail      # one specific asset
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

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANTI_AI_TAIL = (
    " A real photograph — not AI-generated, not 3D render, not illustration. "
    "Indistinguishable from a Kinfolk-magazine still life or a documentary "
    "image in The Gentlewoman. Real materials, real surfaces, real natural "
    "light, real shadow detail. NOT plastic-looking, NOT waxy, NOT CGI, NOT "
    "AI-glossy, NOT oversaturated, NOT halo-effect, NOT lens flare, NOT "
    "fantasy lighting, NOT stock photography. Editorial commercial "
    "photography in Kinfolk magazine tonality, desaturated brand palette."
)

ANTI_AI_PERSON_TAIL = (
    " A real photograph of a real human being — not AI-generated, not "
    "illustration, not 3D render. Real skin with visible pores, real hair "
    "with stray strands, real fabric with creases, real eyes with imperfect "
    "catchlights. NOT plastic skin, NOT airbrushed, NOT waxy AI rendering, "
    "NOT perfect symmetry, NOT glowing highlights, NOT CGI render, NOT "
    "stock-photo lighting, NOT smoothed-over pores, NOT vacant model "
    "expression. Editorial documentary photography in The Gentlewoman, "
    "Aperture, NYT Style lineage."
)

CANDIDATES = [
    {
        "label": "face-volume-loss",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized scientific editorial illustration of an adult female "
            "face in three-quarter profile, showing the anatomy of facial "
            "fat-compartment depletion after rapid GLP-1 weight loss. The "
            "underlying buccal, malar, deep medial cheek, and periorbital "
            "fat compartments are rendered as translucent depleted "
            "shapes — sparse, hollowed, with collapsed volume. The mid-face "
            "is visibly hollow, the under-eye trough is deep, the jawline "
            "has lost its support, the nasolabial folds are deepened. "
            "Painted in gouache and ink on warm bone-colored paper, in the "
            "style of a premium scientific editorial illustration (Nature "
            "magazine cover art rendered in warm tones). Color palette "
            "strictly warm bone (#f7f1e6), cream, deep amber (#7a3d14), "
            "soft sand, pale gold — NO blue, NO teal, NO cool grey, NO "
            "neon. Soft directional light from upper-left, painterly "
            "shadows. No text, no labels, no diagrams, no callouts, no "
            "watermark. Editorial scientific art, not medical-textbook "
            "illustration. The mood: hollowed, depleted, aged ten years "
            "in twelve weeks."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "face-volume-preserved",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized scientific editorial illustration of an adult female "
            "face in three-quarter profile, showing the anatomy of "
            "preserved facial fat compartments — the same view, but with "
            "the buccal, malar, deep medial cheek, and periorbital fat "
            "compartments rendered as full, intact, plump translucent "
            "shapes supporting the overlying skin. The mid-face is full, "
            "the under-eye is smooth, the jawline holds its contour, the "
            "nasolabial folds are soft. Painted in gouache and ink on warm "
            "bone-colored paper, in the same style as the depleted "
            "companion frame: premium scientific editorial illustration "
            "(Nature magazine cover art rendered in warm tones). Color "
            "palette strictly warm bone (#f7f1e6), cream, deep amber "
            "(#7a3d14), soft sand, pale gold — NO blue, NO teal, NO cool "
            "grey, NO neon. Soft directional light from upper-left, "
            "painterly shadows. No text, no labels, no diagrams, no "
            "callouts, no watermark. The mood: intact, preserved, "
            "supported, the face still recognizable."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "serum-detail",
        "width": 1440,
        "height": 1800,
        "prompt": (
            "An intimate editorial product detail shot of the APLOMB. serum: "
            "a 30 mL amber-glass dropper bottle with a black rubber-bulb "
            "cap and a cream paper label reading 'APLOMB' in restrained "
            "black serif type with a small deep-amber period. The bottle "
            "sits at a slight angle on a folded piece of warm natural "
            "linen, with one or two amber-coloured oil droplets visible "
            "on the linen beside the bottle (suggesting a fresh "
            "application). Soft natural window light from the upper left, "
            "real warm shadows. Vertical 4:5 portrait composition, the "
            "bottle slightly off-center. Color palette: warm cream, deep "
            "amber, deep umber. Shot on Phase One IQ4 medium format, "
            "80mm macro lens, f/4. Editorial commercial photography in "
            "Kinfolk magazine tonality. Real glass, real linen, real oil."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "bundle-detail",
        "width": 1440,
        "height": 1800,
        "prompt": (
            "An intimate editorial product detail shot of two minimal "
            "wellness containers seen from a slightly elevated angle: on "
            "the left, a small white matte glass tub with a beige paper "
            "label reading 'APLOMB · COLLAGEN' in restrained black serif "
            "type with a small deep-amber period — the lid is set off to "
            "the side and a small cream china teaspoon rests across the "
            "open mouth of the tub. On the right, a tall amber-glass "
            "bottle with a black cap and matching cream paper label "
            "reading 'APLOMB · DAILY' in the same restrained typography. "
            "Both containers sit on a folded square of warm natural "
            "linen with subtle wrinkles. A single dried autumn branch "
            "with one russet leaf rests beside them. Soft natural window "
            "light from the upper left, real warm shadows falling to the "
            "right. Vertical 4:5 portrait composition. Color palette: "
            "warm cream, deep amber for the amber-glass bottle, deep "
            "umber shadows — no blue, no teal. Shot on Phase One IQ4 "
            "medium format, 80mm macro lens, f/4. Editorial commercial "
            "photography in Kinfolk magazine tonality. Real materials, "
            "real surfaces, real shadows."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "serum-rail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of a 30 mL amber-glass dropper "
            "bottle with a black rubber-bulb cap, cream rectangular paper "
            "label printed with the word 'APLOMB' in restrained black serif "
            "type followed by a small period in deep amber. The bottle sits "
            "on a slab of warm travertine stone in soft late-morning window "
            "light from the upper left. Beside the bottle: a single sprig of "
            "dried lavender or rosemary, a folded square of natural linen "
            "with subtle wrinkles, and a small bone-china saucer in "
            "off-white. Soft directional shadows fall to the right. Color "
            "palette strictly warm bone, cream, soft amber, warm taupe — no "
            "blue, no teal, no cool grey. Three-quarter angle on the bottle, "
            "shallow but realistic depth of field. Shot on Phase One IQ4 "
            "medium format, 80mm leaf-shutter lens, no flash."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "bundle-rail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of two minimal wellness "
            "containers side by side. On the left: a small white matte "
            "glass tub with a beige paper label reading 'APLOMB · COLLAGEN' "
            "in restrained black serif type with a small deep-amber period. "
            "On the right: a tall amber-glass capsule bottle with a black "
            "cap and matching cream paper label reading 'APLOMB · DAILY' in "
            "the same restrained typography. Both containers sit on warm "
            "natural linen with subtle wrinkles. Beside them: a single "
            "small autumn branch with one or two russet leaves, a folded "
            "cream paper card, and a bone-china saucer in off-white. Soft "
            "directional natural window light from the upper left, gentle "
            "shadows falling to the right. Color palette: warm bone, "
            "cream, soft amber, deep umber for the amber bottle — no blue, "
            "no teal. Three-quarter angle, real materials, real surfaces, "
            "realistic depth of field. Shot on Phase One IQ4 medium format, "
            "80mm leaf-shutter lens, no flash. Editorial commercial "
            "photography in Kinfolk magazine tonality."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "muscle-atrophy",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized scientific editorial illustration of an unhealthy, "
            "atrophied adult skeletal muscle cross-section — dramatically "
            "shrunken, irregular, sparse polygonal muscle fibers with "
            "large empty gaps of connective tissue and visible adipose "
            "infiltration replacing lost fiber volume. The hexagonal "
            "packing density has collapsed; the cross-section reads as "
            "clearly depleted and sarcopenic. Capillaries are sparse, "
            "thin, broken. Painted in gouache and ink on warm bone-colored "
            "paper, in the style of a premium scientific editorial "
            "illustration (Nature magazine cover art rendered in warm "
            "tones). Color palette strictly warm bone (#f7f1e6), cream, "
            "deep amber (#7a3d14), soft sand, pale gold — NO blue, NO "
            "teal, NO cool grey, NO neon. Soft directional light from "
            "upper-left, painterly shadows. No text, no labels, no "
            "diagrams, no callouts, no watermark, no scale bars. The "
            "mood: wasted, hollow, depleted."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "muscle-preserved",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized scientific editorial illustration of a healthy adult "
            "skeletal muscle cross-section — a dense hexagonal packing of "
            "large, plump, intact muscle fibers in warm cream and pale "
            "amber, each fiber rendered as a soft rounded polygon with "
            "thin warm-toned connective-tissue borders. Capillaries "
            "visible as fine amber threads weaving between fibers. "
            "Painted in gouache and ink on warm bone-colored paper, in "
            "the style of a premium scientific editorial illustration "
            "(Nature magazine cover art rendered in warm tones). Color "
            "palette strictly warm bone (#f7f1e6), cream, deep amber "
            "(#7a3d14), soft sand, pale gold — NO blue, NO teal, NO cool "
            "grey, NO neon. Soft directional light from upper-left, "
            "painterly shadows. No text, no labels, no diagrams, no "
            "callouts, no watermark, no scale bars. The mood: dense, "
            "substantial, intact, preserved."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "portrait-confident",
        "width": 1440,
        "height": 1440,
        "prompt": (
            "A documentary editorial portrait of one extremely attractive "
            "woman, age 58. Brunette hair gone partially silver at the "
            "temples and through one front section, shoulder-length, with "
            "natural movement and a few stray strands. Wearing tortoise-shell "
            "glasses. Visible fine lines at the corners of her eyes, faint "
            "laugh lines around her mouth. A small natural-looking earring. "
            "No makeup or barely any. She is seated in soft late-morning "
            "natural window light, looking just past the camera with a quiet "
            "self-possessed half-smile — the kind of woman who knows what "
            "she came for. Wearing a slightly creased cream linen shirt. "
            "Soft warm window light catches the side of her face. Shallow "
            "but realistic depth of field. Shot on Phase One IQ4 medium "
            "format, 85mm portrait lens, f/2.8, no flash. Color palette: "
            "warm cream highlights, soft amber midtones, deep umber "
            "shadows. The mood: contemplative, mid-life in command, the "
            "founder of something she built because nobody else would."
            + ANTI_AI_PERSON_TAIL
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
            sample = (data.get("result") or {}).get("sample")
            if not sample:
                sys.exit(f"[{label}] Ready but no sample")
            return sample
        if s in ("Error", "Failed", "Request Moderated", "Content Moderated"):
            sys.exit(f"[{label}] status={s}: {data}")
        print(f"  [{label}] status={s} -- polling...")
        time.sleep(2)
    sys.exit(f"[{label}] timed out")


def download(url, out):
    with urllib.request.urlopen(url, timeout=60) as r:
        out.write_bytes(r.read())
    print(f"  -> wrote {out.name} ({out.stat().st_size // 1024} KB)")


def gen(c):
    out = OUT_DIR / f"{c['label']}.jpg"
    print(f"[{c['label']}] {ENDPOINT} {c['width']}x{c['height']}")
    resp = post_json(
        ENDPOINT,
        {
            "prompt": c["prompt"],
            "width": c["width"],
            "height": c["height"],
        },
    )
    sample = poll(resp.get("polling_url", ""), resp["id"], c["label"])
    download(sample, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. 'bundle-rail'")
    ap.add_argument("--test", action="store_true", help="just do bundle-rail to verify endpoint")
    args = ap.parse_args()

    if args.test:
        targets = [c for c in CANDIDATES if c["label"] == "bundle-rail"]
    elif args.only:
        targets = [c for c in CANDIDATES if c["label"] == args.only]
    else:
        targets = CANDIDATES

    if not targets:
        sys.exit("no candidate matches selection")

    for c in targets:
        gen(c)
    print(f"\nDone. {len(targets)} image(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
