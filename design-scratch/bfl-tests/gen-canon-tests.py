#!/usr/bin/env python3
"""
BFL Flux 2 Pro photoreal canon — 5-image validation test.

Each prompt strictly follows the new canon synthesized from BFL official
guidance + community research:
  - Subject -> Action -> Style -> Context order
  - 50-70 words total
  - Subject identity in first 10-15 tokens
  - NO inline negation (no "NOT X", "no Y") — encoders latch on
  - Biological-skin language: visible pores, subsurface scattering,
    vellus hair, freckles, fine lines
  - Forbidden: "smooth", "flawless", "perfect skin"
  - Specific camera body + lens
  - Descriptive lighting (direction + falloff + what it does)
  - Explicit catchlights + single pupil
  - prompt_upsampling=False
  - 1024x1280 (3:4 portrait)
  - Closed-mouth smiles (more stable than open)
  - Head-and-shoulders or seated — avoid hands-in-frame failure modes

Run:
  python3 gen-canon-tests.py
  python3 gen-canon-tests.py --only 03-redhead-kitchen
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
OUT_DIR = Path("/Users/zacharypoll/Desktop/bfl-canon-tests")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1280  # 3:4 portrait, optimal per research

TESTS = [
    {
        "label": "01-brunette-window",
        "prompt": (
            "A late-20s brunette woman with striking bone structure, "
            "hazel-green eyes, faint freckles across her nose, sitting on "
            "a linen sofa with knees pulled up, slight closed-mouth smile. "
            "Documentary editorial portrait. Warm morning window light "
            "from camera-left with soft falloff into shadow on the right "
            "side of her face, strong natural catchlights, single pupil, "
            "visible pores, subsurface scattering, fine vellus hair on "
            "her cheek. Sony A7IV with 85mm f/1.8 lens."
        ),
    },
    {
        "label": "02-blonde-cafe",
        "prompt": (
            "An early-30s blonde woman with model bone structure, honey "
            "hair, green eyes, light tan, freckled shoulders, sitting at "
            "an outdoor cafe marble table with a flat white, slight "
            "closed-mouth smile. Late afternoon sun behind her creating "
            "warm rim light on her hair and bounced amber fill from the "
            "white tabletop, amber catchlights, single pupil, visible "
            "pores, subsurface scattering at her ears, fine vellus hair. "
            "Fujifilm X-T5 with 56mm f/1.2."
        ),
    },
    {
        "label": "03-redhead-kitchen",
        "prompt": (
            "A late-20s redhead woman, uncommonly beautiful, copper-auburn "
            "hair in a loose low bun, blue eyes, fair freckled skin, "
            "leaning against a kitchen island in a linen apron, slight "
            "closed-mouth smile. Soft window light from camera-right "
            "blending with warm pendant overhead, split lighting, cool "
            "window catchlights, single pupil, visible pores and dense "
            "natural freckling, subsurface scattering at her ears, fine "
            "vellus hair. Hasselblad GFX100S with 80mm f/2.8."
        ),
    },
    {
        "label": "04-black-gym",
        "prompt": (
            "A mid-30s woman with magazine-cover bone structure, "
            "jet-black hair in a high ponytail, brown eyes, lithe "
            "athletic build, in a black sports bra mid-stretch on a gym "
            "mat, slight closed-mouth smile. Hard fluorescent overhead "
            "light casting subtle top shadows under her brow and jaw, "
            "slight sweat sheen on her collarbone, overhead catchlights, "
            "single pupil, visible pores, natural cheek flush from "
            "exertion, fine vellus hair. Sony A7IV with 50mm f/1.4."
        ),
    },
    {
        "label": "05-brown-restaurant",
        "prompt": (
            "An early-30s woman with classic Italian-Vogue beauty, warm "
            "light-brown hair in soft waves, warm brown eyes, sitting in "
            "a leather restaurant booth, slight closed-mouth smile. Low "
            "warm tungsten overhead and a single candle on the table "
            "casting flickering amber catchlights and warm rim on her "
            "cheekbones, single pupil, visible pores, slight subsurface "
            "glow in her ears from the candle, fine vellus hair. Leica "
            "Q2 28mm fixed lens at f/1.7."
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
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return {"_http_error": e.code, "_body": body}


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
                raise RuntimeError(f"[{label}] Ready but no sample")
            return sample
        if s in ("Request Moderated", "Content Moderated"):
            print(f"  [{label}] MODERATED: {s}")
            return None
        if s in ("Error", "Failed"):
            raise RuntimeError(f"[{label}] status={s}: {data}")
        print(f"  [{label}] status={s} -- polling...")
        time.sleep(2)
    raise RuntimeError(f"[{label}] timed out")


def download(url, out):
    with urllib.request.urlopen(url, timeout=60) as r:
        out.write_bytes(r.read())
    print(f"  -> wrote {out.name} ({out.stat().st_size // 1024} KB)")


def gen(test):
    out = OUT_DIR / f"{test['label']}.jpg"
    word_count = len(test["prompt"].split())
    print(f"[{test['label']}] {ENDPOINT} {WIDTH}x{HEIGHT} ({word_count} words, no input_image, prompt_upsampling=False)")
    payload = {
        "prompt": test["prompt"],
        "width": WIDTH,
        "height": HEIGHT,
        "prompt_upsampling": False,
    }
    resp = post_json(ENDPOINT, payload)
    if "_http_error" in resp:
        print(f"  [{test['label']}] HTTP {resp['_http_error']}: {resp['_body'][:300]}")
        return False
    sample = poll(resp.get("polling_url", ""), resp["id"], test["label"])
    if sample is None:
        return False
    download(sample, out)
    (out.with_suffix(".prompt.txt")).write_text(test["prompt"] + "\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one label, e.g. '03-redhead-kitchen'")
    args = ap.parse_args()
    targets = [t for t in TESTS if (args.only is None or t["label"] == args.only)]
    if not targets:
        sys.exit("no match. Available: " + ", ".join(t["label"] for t in TESTS))
    rejected = []
    for t in targets:
        if not gen(t):
            rejected.append(t["label"])
    print(f"\nDone. {len(targets) - len(rejected)} / {len(targets)} succeeded.")
    if rejected:
        print(f"Moderated: {', '.join(rejected)}")


if __name__ == "__main__":
    main()
