#!/usr/bin/env python3
"""
APLOMB. Calm — stand-up pouch gummy mockup set.

Format-pivot exploration: shows the proposed nausea product as a
ginger gummy in a matte bone-cream stand-up pouch (replacing the
current capsule + electrolyte kit).

Generates 5 editorial scenes via BFL Flux 2 Pro, each answering a
distinct visual question (hero, spill, flatlay, in-hand, label detail).

Usage:
  source ~/.claude/secrets.env
  python3 gen-pouch-mockups.py
"""
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

# The pouch and label spec is held constant across all 5 scenes so the
# product reads consistently. Reused as a string fragment in each prompt.
POUCH_SPEC = (
    "The product is a matte uncoated stand-up pouch about 90mm wide and "
    "165mm tall, in a warm bone-cream color (#efe8dc) with a barely "
    "perceptible heathered fiber texture suggesting recyclable kraft "
    "lamination - NOT shiny plastic, NOT glossy, NOT mylar. The pouch "
    "stands upright on a flat gusseted base. Across the top there is a "
    "subtle pressed ziplock closure visible as two horizontal lines, and "
    "above it a small clean punched hang-hole centered. The front of the "
    "pouch is printed flat (no embossing, no foil, no metallic): centered "
    "near the top a single small mark in deep amber (#7a3d14) - a thin "
    "vertical line dropping into a triangular plumb-bob weight. Below the "
    "mark, in restrained Cormorant Garamond italic 500 black serif type "
    "(#1a1512), the wordmark 'Aplomb' followed by a small period in deep "
    "amber. Below the wordmark in slightly smaller Cormorant Garamond "
    "italic, the single word 'Calm'. Below 'Calm', a thin amber hairline "
    "rule. Below the rule, in tiny letter-spaced IBM Plex Sans regular "
    "uppercase, the words 'GINGER GUMMIES FOR GLP-1 NAUSEA'. Near the "
    "bottom of the printed area, in tiny IBM Plex Sans regular, "
    "'30 gummies / 1 g ginger root extract per gummy / Net wt 90 g'. "
    "Type is crisp, restrained, well-spaced, with generous margins on the "
    "front of the pouch. "
)

PALETTE_AND_LIGHT = (
    "Color palette strictly warm bone (#f7f1e6), cream, deep amber "
    "(#7a3d14), warm taupe, soft sand - NO blue, NO teal, NO cool grey, "
    "NO neon, NO red, NO forest green, NO pure black. Soft directional "
    "natural window light from the upper-left, warm late-morning, "
    "painterly shadows fall to the right. Shot on Phase One IQ4 medium "
    "format, 80mm leaf-shutter lens, no flash, f/4.5, shallow but "
    "realistic depth of field."
)

GUMMY_SPEC = (
    "The gummies are small soft cubes about 12mm on a side, amber and "
    "honey-translucent like raw honey or unfiltered ginger syrup, with "
    "very faint suspended ginger fiber inclusions visible inside. The "
    "gummies catch the warm light softly. They read adult and clinical, "
    "NOT candy-bright, NOT artificially red, NOT neon orange, NOT shiny. "
)

CANDIDATES = [
    {
        "label": "calm-pouch-hero",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life. "
            + POUCH_SPEC
            + "The pouch stands alone in three-quarter front view, "
            "centered in frame on a warm travertine stone slab with a "
            "single fold of natural undyed linen at the lower edge. "
            "A single small dried ginger root knob rests on the linen "
            "near the base of the pouch. Generous negative space above. "
            + PALETTE_AND_LIGHT
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "calm-pouch-spill",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life. "
            + POUCH_SPEC
            + "The pouch stands upright with the ziplock at the top "
            "open and slightly relaxed. About eight amber ginger gummies "
            "have spilled from the pouch onto warm undyed linen beside "
            "it - some clustered, some single, naturally arranged. "
            + GUMMY_SPEC
            + "A small dried ginger root knob and one folded square of "
            "linen sit at the edge of the frame. The whole scene rests "
            "on a warm travertine surface. Three-quarter angle, eye "
            "level slightly above the gummies. "
            + PALETTE_AND_LIGHT
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "calm-pouch-flatlay",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial top-down flat-lay still life, camera "
            "directly overhead. "
            + POUCH_SPEC
            + "The pouch lies flat on a warm travertine stone slab with "
            "the front face up. To one side: a small shallow bone-china "
            "dish holding about six amber ginger gummies. "
            + GUMMY_SPEC
            + "On the other side: two thin slices of fresh ginger root "
            "and a small folded square of natural undyed linen. The "
            "composition is restrained and editorial, with generous "
            "negative space. "
            + PALETTE_AND_LIGHT
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "calm-pouch-in-hand",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product photograph. A woman's hand - extremely "
            "attractive, warm Mediterranean skin, plain unpainted short "
            "natural nails, no jewelry, plain natural undyed linen "
            "sleeve at the wrist - holds the pouch upright at counter "
            "height in front of a warm travertine kitchen surface. "
            + POUCH_SPEC
            + "The hand grips the pouch gently from one side, the front "
            "face turned just slightly toward the camera at three-"
            "quarter angle, the wordmark and label fully legible. Soft "
            "out-of-focus warm domestic kitchen background suggesting "
            "morning. "
            + PALETTE_AND_LIGHT
            + ANTI_AI_TAIL
        ),
    },
    {
        "label": "calm-pouch-detail",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial macro close-up product photograph framed "
            "tighter than a hero shot but not so close that small type "
            "is unreadable. The crop shows the pressed ziplock seam at "
            "the very top, the punched hang-hole above it, and the "
            "complete printed front label area with all of its "
            "typography crisp and legible. "
            + POUCH_SPEC
            + "Type accuracy is critical and must not be misspelled, "
            "garbled, or replaced with random letterforms - render "
            "exactly: 'Aplomb' with a deep amber period adjacent to "
            "the b, the word 'Calm' below in italic, a thin amber "
            "hairline rule, the descriptor 'GINGER GUMMIES FOR GLP-1 "
            "NAUSEA' in small letter-spaced uppercase sans-serif, and "
            "the dose line '30 gummies / 1 g ginger root extract per "
            "gummy / Net wt 90 g' in tiny sans-serif. Every word legible. "
            "The pouch is angled very slightly off-axis so light rakes "
            "across the matte uncoated lamination without glare or "
            "shine. The matte fiber texture of the bone-cream surface "
            "is just visible. "
            + PALETTE_AND_LIGHT
            + ANTI_AI_TAIL
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
    only = set(sys.argv[1:])
    for c in CANDIDATES:
        if only and c["label"] not in only:
            continue
        gen(c)
    print(f"\nDone. Images saved in {OUT_DIR}")


if __name__ == "__main__":
    main()
