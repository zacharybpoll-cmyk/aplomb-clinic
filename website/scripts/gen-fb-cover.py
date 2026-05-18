#!/usr/bin/env python3
"""
APLOMB. — generate Facebook Page cover-photo candidates via Flux 2 Pro.

Three on-brand, TEXT-FREE Kinfolk-style still lifes (the brand mark lives in
the Page's profile picture, not the cover). 1640x924 = Facebook's recommended
cover upload size; focal subject centered with generous bone negative space so
it survives FB's safe-zone crop (desktop crops top/bottom, mobile the sides).

Outputs to `website/assets/fb-cover/`:
  cover-01-serum-travertine.jpg + .prompt.txt
  cover-02-botanical-stillife.jpg + .prompt.txt
  cover-03-plumb-bob.jpg + .prompt.txt

Run:
  source ~/.claude/secrets.env
  python3 gen-fb-cover.py                              # all (skips existing)
  python3 gen-fb-cover.py --only cover-03-plumb-bob    # one
  python3 gen-fb-cover.py --force                      # regen all
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

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fb-cover"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Facebook recommended cover upload size (~16:9). Focal subject centered.
WIDTH, HEIGHT = 1640, 924

# Brand envelope — appended to every concept (BRAND.md sections 2 + 5).
BRAND = (
    "Shot on a Phase One IQ4 medium-format camera with an 80mm leaf-shutter "
    "lens, no flash. Soft late-morning natural window light entering from the "
    "upper-left, painterly shadows falling gently to the right. Strictly warm "
    "palette only: warm bone #efe8dc, paper cream #f7f1e6, deep warm ink "
    "#1a1512, deep amber #7a3d14, warm taupe, soft sand, pale gold, deep "
    "umber. ABSOLUTELY NO blue, NO teal, NO cool grey, NO neon, NO primary "
    "red, NO forest green, NO pure black. Wide horizontal composition with "
    "the focal subject centered and generous warm bone negative space on all "
    "sides. Restrained, editorial, clinical, quiet — the visual language of "
    "Kinfolk, The Gentlewoman and Cereal magazine, in the lineage of Aesop "
    "and Augustinus Bader."
)

# No-text decision: forbid any rendered text so Flux cannot sneak garbled
# letters in (mark lives in the profile picture). Plus the BRAND.md anti-AI
# directive verbatim.
NO_TEXT = (
    "There is absolutely no text, no letters, no words, no numbers, no "
    "labels, no lettering on any object, no signage, no watermark, no logo "
    "anywhere in the image."
)
ANTI_AI = (
    "A real photograph — not AI-generated, not 3D render, not illustration. "
    "Indistinguishable from a Kinfolk-magazine still life. NOT plastic-"
    "looking, NOT waxy, NOT CGI, NOT AI-glossy, NOT oversaturated, NOT halo-"
    "effect, NOT lens flare, NOT fantasy lighting, NOT stock photography."
)


def _prompt(concept):
    return f"{concept} {BRAND} {NO_TEXT} {ANTI_AI}"


CANDIDATES = [
    {
        "label": "cover-01-serum-travertine",
        "prompt": _prompt(
            "An editorial still-life banner: a single minimalist amber-glass "
            "apothecary dropper bottle with a smooth matte black-free warm "
            "bronze dropper cap and a completely blank, label-free unmarked "
            "surface, standing upright and centered on a warm honey-toned "
            "travertine stone slab. A loosely folded panel of natural "
            "oatmeal linen drapes to one side. A few soft shadows and one "
            "faint caustic of amber light through the glass. Calm, premium, "
            "apothecary-clinical."
        ),
    },
    {
        "label": "cover-02-botanical-stillife",
        "prompt": _prompt(
            "An editorial still-life banner with no product: a single slim "
            "sprig of fresh olive branch with a few almond-shaped leaves "
            "resting across the rim of a simple bone-china dish, set on a "
            "warm travertine stone surface beside a fold of natural linen. "
            "One small ceramic vessel in soft sand tone sits slightly behind, "
            "out of focus. Sparse, botanical, breathing room everywhere."
        ),
    },
    {
        "label": "cover-03-plumb-bob",
        "prompt": _prompt(
            "An editorial still-life banner: an aged solid-brass surveyor's "
            "plumb-bob plummet — a precise machined teardrop weight in warm "
            "antique brass — resting on a fold of natural oatmeal linen on a "
            "warm travertine slab, its fine waxed cord coiled loosely beside "
            "it. Scientific-instrument minimalism, the object reading as a "
            "quiet emblem of composure and exactness. Warm brass only, never "
            "cool steel or chrome."
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
    img_out = OUT_DIR / f"{c['label']}.jpg"
    prompt_out = OUT_DIR / f"{c['label']}.prompt.txt"
    print(f"[{c['label']}] {ENDPOINT} {WIDTH}x{HEIGHT}")
    prompt_out.write_text(c["prompt"])
    resp = post_json(
        ENDPOINT,
        {
            "prompt": c["prompt"],
            "width": WIDTH,
            "height": HEIGHT,
        },
    )
    sample = poll(resp.get("polling_url", ""), resp["id"], c["label"])
    download(sample, img_out)
    return img_out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. 'cover-03-plumb-bob'")
    ap.add_argument("--force", action="store_true", help="regen even if the .jpg exists")
    args = ap.parse_args()

    if args.only:
        targets = [c for c in CANDIDATES if c["label"] == args.only]
        if not targets:
            sys.exit(f"no candidate matches. Valid: {[c['label'] for c in CANDIDATES]}")
    else:
        targets = CANDIDATES

    done, skipped = [], []
    for c in targets:
        img_out = OUT_DIR / f"{c['label']}.jpg"
        if img_out.exists() and not args.force and not args.only:
            print(f"[{c['label']}] exists -- skip (use --force to regen)")
            skipped.append(c["label"])
            continue
        gen(c)
        done.append(c["label"])

    print(f"\nDone. {len(done)} generated, {len(skipped)} skipped, in {OUT_DIR}")
    if done:
        print("  generated: " + ", ".join(done))
    if skipped:
        print("  skipped:   " + ", ".join(skipped))


if __name__ == "__main__":
    main()
