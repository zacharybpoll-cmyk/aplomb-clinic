#!/usr/bin/env python3
"""
APLOMB. Pharmaloz lozenge packaging mockup — generates a single editorial
still life of the proposed Aplomb halitosis-lozenge tin to attach to the
Pharmaloz RFQ email.

Usage:
  source ~/.claude/secrets.env
  python3 gen-pharmaloz-mockup.py
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

CANDIDATES = [
    {
        "label": "pharmaloz-tin-hero",
        "width": 1440,
        "height": 1080,
        "prompt": (
            "An editorial product still life of a small flat circular tin "
            "(about 60mm diameter, 18mm tall) lying flat on warm bone-colored "
            "linen paper. The tin is matte cream-painted metal, the colour of "
            "warm bone parchment. Centered on the lid: a single small "
            "embossed mark — a thin vertical line dropping into a triangular "
            "plumb-bob weight, all in deep amber tone (#7a3d14). Below the "
            "mark, in restrained Garamond italic black serif type, the "
            "wordmark 'Aplomb' followed by a small period in deep amber. "
            "Below the wordmark, in tiny letter-spaced sans-serif lowercase, "
            "the words 'composure lozenge · zinc + xylitol · 30 ct'. The lid "
            "edge has a subtle hairline groove. Beside the closed tin: an "
            "open second tin showing a neat tessellation of round pale "
            "cream-yellow pressed lozenges, each about 9mm wide, set in a "
            "single layer. A folded square of natural undyed linen and a "
            "single dried autumn leaf rest at the edge of the frame. Soft "
            "directional natural light from the upper-left, warm "
            "late-morning. Subtle realistic shadows fall to the right. Color "
            "palette strictly warm bone (#f7f1e6), cream, deep amber "
            "(#7a3d14), warm taupe — NO blue, NO teal, NO cool grey, NO "
            "neon, NO forest green. Three-quarter angle, shallow but "
            "realistic depth of field. Shot on Phase One IQ4 medium format, "
            "80mm leaf-shutter lens, no flash, f/4.5."
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
    for c in CANDIDATES:
        gen(c)
    print(f"\nDone. Image saved in {OUT_DIR}")


if __name__ == "__main__":
    main()
