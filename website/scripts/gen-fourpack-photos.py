#!/usr/bin/env python3
"""
APLOMB. four-pack expansion - generate the new SKUs' product photography.

Three product rails (Nutrient Stack, Hair Stack, Nausea Kit) and three
mechanism illustrations (nutrient depletion, hair follicle thinning,
GI/nausea wave) - all matched to the existing brand aesthetic
(warm bone, deep amber, gouache illustration / Phase-One Kinfolk
photography).

Usage:
  source ~/.claude/secrets.env
  python3 gen-fourpack-photos.py                  # all 6 images
  python3 gen-fourpack-photos.py --only daily-rail
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
    " A real photograph - not AI-generated, not 3D render, not illustration. "
    "Indistinguishable from a Kinfolk-magazine still life or a documentary "
    "image in The Gentlewoman. Real materials, real surfaces, real natural "
    "light, real shadow detail. NOT plastic-looking, NOT waxy, NOT CGI, NOT "
    "AI-glossy, NOT oversaturated, NOT halo-effect, NOT lens flare, NOT "
    "fantasy lighting, NOT stock photography. Editorial commercial "
    "photography in Kinfolk magazine tonality, desaturated brand palette."
)

ANTI_AI_ART = (
    " Painted in gouache and ink on warm bone-colored paper, in the style "
    "of a premium scientific editorial illustration (Nature magazine cover "
    "art rendered in warm tones). Color palette strictly warm bone "
    "(#f7f1e6), cream, deep amber (#7a3d14), soft sand, pale gold - NO "
    "blue, NO teal, NO cool grey, NO neon. Soft directional light from "
    "upper-left, painterly shadows. No text, no labels, no diagrams, no "
    "callouts, no watermark, no scale bars."
)

CANDIDATES = [
    # ------------------------------------------------------------------
    # PRODUCT RAILS - photographic still lifes for each new SKU
    # ------------------------------------------------------------------
    {
        "label": "daily-rail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of a tall amber-glass apothecary "
            "jar (about 90mm tall) with a matte black screw cap. The jar "
            "wears a cream rectangular paper label printed with the word "
            "'APLOMB' in restrained black serif type, followed by a small "
            "period in deep amber, then below it, in smaller letter-spaced "
            "sans, the word 'DAILY'. The jar sits on a slab of warm "
            "travertine stone in soft late-morning natural window light from "
            "the upper-left. Beside the jar: a folded square of natural "
            "linen with subtle wrinkles, a small bone-china saucer in "
            "off-white, and a single dried autumn leaf resting on the saucer. "
            "Soft directional shadows fall to the right. Color palette "
            "strictly warm bone, cream, soft amber, warm taupe - no blue, "
            "no teal, no cool grey. Three-quarter angle on the jar, shallow "
            "but realistic depth of field. Shot on Phase One IQ4 medium "
            "format, 80mm leaf-shutter lens, no flash."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "roots-rail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of a tall amber-glass apothecary "
            "jar (about 90mm tall) with a matte black screw cap, sitting on "
            "warm travertine stone in soft late-morning natural window light "
            "from the upper-left. The jar wears a cream rectangular paper "
            "label printed with the word 'APLOMB' in restrained black serif "
            "type, followed by a small period in deep amber, then below it, "
            "in smaller letter-spaced sans, the word 'ROOTS'. Beside the "
            "jar: a small cluster of dried wheat stalks tied with natural "
            "twine, a folded cream linen napkin, and a small bone-china "
            "saucer in off-white. Soft directional shadows fall to the "
            "right. Color palette strictly warm bone, cream, soft amber, "
            "warm taupe, deep umber - no blue, no teal, no cool grey. "
            "Three-quarter angle on the jar, shallow but realistic depth of "
            "field. Shot on Phase One IQ4 medium format, 80mm leaf-shutter "
            "lens, no flash."
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "calm-rail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of a low rectangular cream "
            "paperboard wellness kit box (about 180mm wide, 90mm deep, 30mm "
            "tall) lying open on warm travertine stone in soft late-morning "
            "natural window light from the upper-left. The box lid bears, "
            "in restrained black serif type, the word 'APLOMB' followed by a "
            "small period in deep amber, then below it, in smaller "
            "letter-spaced sans, the word 'CALM'. Inside the open box, "
            "neatly arranged: three slim cream-paper sachets (each about "
            "90mm long, plain cream paper with deep amber printing), a "
            "small frosted-glass apothecary jar with a black cap, and a "
            "single folded cream paper instruction card. Beside the box, "
            "on the stone surface: one dried lemon slice, a small sprig of "
            "fresh ginger root, and a folded square of natural linen with "
            "subtle wrinkles. Soft directional shadows fall to the right. "
            "Color palette strictly warm bone, cream, soft amber, warm "
            "taupe, deep umber - no blue, no teal, no cool grey. Slightly "
            "elevated three-quarter angle, shallow but realistic depth of "
            "field. Shot on Phase One IQ4 medium format, 80mm leaf-shutter "
            "lens, no flash."
            + ANTI_AI_TAIL
        ),
    },

    # ------------------------------------------------------------------
    # MECHANISM ILLUSTRATIONS - gouache scientific editorial art
    # ------------------------------------------------------------------
    {
        "label": "nutrient-mech",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized botanical-scientific editorial illustration arranged "
            "as a horizontal triptych on warm bone-colored paper: on the "
            "left, a stylized iron-rich seed pod sliced open to show "
            "internal structure (warm rust tones); in the center, a "
            "branching root system with sparse fine tendrils tapering away; "
            "on the right, a honeycomb mineral lattice cross-section with "
            "softened sparse cells. All three rendered as quiet "
            "wellness-journal cover art, like a botanical study by a "
            "natural historian. The composition reads as a poetic still "
            "study of the building blocks the body needs."
            + ANTI_AI_ART
        ),
    },
    {
        "label": "roots-mech",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized botanical-scientific editorial illustration on warm "
            "bone-colored paper showing two side-by-side root systems of "
            "the same plant: on the left, a sparse spindly root system "
            "with thin tapering tendrils and a few faded leaves at the "
            "soil line; on the right, the same plant but with a dense, "
            "robust root system, thick branching roots, and a full healthy "
            "leaf canopy at the soil line. The visual metaphor is hair "
            "follicles - sparse vs full - rendered as botanical diagrams "
            "rather than anatomical ones. Painted as a quiet wellness-"
            "journal study, like Beatrix Potter botanical art rendered in "
            "warm amber tones."
            + ANTI_AI_ART
        ),
    },
    {
        "label": "calm-mech",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "Stylized editorial illustration on warm bone-colored paper of "
            "a single ginger root with delicate stems and soft fronds, "
            "rendered as the central focal point. Around the ginger, soft "
            "concentric ripple lines emanate outward like calm wave "
            "patterns. In the upper right corner, a small abstract honey-"
            "lemon shape. The mood is restorative, herbal, settling - "
            "the visual sense of nausea calming. Painted as a quiet "
            "botanical-medicinal still study, like a vintage apothecary "
            "label rendered in modern warm tones."
            + ANTI_AI_ART
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
            print(f"[{label}] status={s}: {data}")
            return None
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
    if not sample:
        print(f"  [{c['label']}] skipped (moderated)")
        return None
    download(sample, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. 'daily-rail'")
    args = ap.parse_args()

    if args.only:
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
