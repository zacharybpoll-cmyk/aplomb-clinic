"""
Generate a photo-realistic studio shot of the Aplomb. Calm bottle via
Black Forest Labs Flux 2 Pro, using the editorial vector mockup as a
visual reference (image-to-image).

Run: python3 scripts/gummy_design/generate_photoreal.py

Output: business documents/packaging/gummy/Aplomb_Calm_Photoreal.png
"""

import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib import request as urlreq, error as urlerr

API_KEY = os.environ.get("BFL_API_KEY")
if not API_KEY:
    sys.exit("BFL_API_KEY not set. source ~/.claude/secrets.env first.")

ENDPOINT = "https://api.bfl.ai/v1/flux-2-pro"
OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")
REFERENCE = OUT_DIR / "Aplomb_Calm_Gummy_Mockup_Front.png"
OUTPUT = OUT_DIR / "Aplomb_Calm_Photoreal.png"


PROMPT = (
    "Photo-realistic studio product photograph of a single supplement bottle, "
    "shot from straight-on at eye level. The bottle is a rectangular HDPE "
    "plastic vitamin bottle, approximately 60mm wide by 118mm tall, in soft "
    "warm cream / bone color (not pure white) — like unbleached paper. It "
    "sits on a smooth flat bone-cream surface against an out-of-focus "
    "matching bone-cream background. The bottle's cap is a low warm-black "
    "matte plastic 38-400 child-resistant closure with vertical fluting / "
    "knurled ridges around the perimeter — flat top, just slightly wider "
    "than the bottle neck, only the very top of the neck visible below it. "
    "The bottle body has a gentle rounded corner radius. \n\n"
    "A matte uncoated paper label wraps around the bottle front. The label "
    "is printed in this exact editorial layout, vertically centered: \n"
    "  · Top: the wordmark 'Aplomb.' in italic Cormorant Garamond serif, "
    "small, in deep amber / burnt-sienna ink color (#7A3D14). \n"
    "  · Below the wordmark: a simple plumb-mark logo — a thin vertical "
    "amber line ending in a tiny solid diamond. \n"
    "  · Center hero: the product name 'Calm.' in very large italic "
    "Cormorant Garamond display serif, in deep near-black ink. The "
    "lowercase 'a', 'l', 'm' are the visual hero. \n"
    "  · Below 'Calm.': a thin amber hairline rule. \n"
    "  · Below the rule: the italic amber tagline 'For nausea, on the drug.' "
    "  · At the bottom of the label: 'GINGER GUMMIES  ·  60 CT' in small "
    "muted sans-serif tracking. \n\n"
    "Lighting: soft natural daylight from upper left, gentle diffused "
    "shadow falling to lower right on the bone surface, no harsh "
    "specular highlights, no glow, no lens flare, no halos, matte paper "
    "label finish, matte plastic bottle finish. Warm afternoon light. "
    "Magazine editorial product photography. Apothecary-minimalist DTC "
    "wellness brand aesthetic, like Hims, Apothékary, Goop. Shallow depth "
    "of field with the bottle in sharp focus and the bone surface softly "
    "blurred behind it. \n\n"
    "Strictly no extra props, no other bottles, no hands, no people, no "
    "text other than the label copy described above, no AI-generated "
    "artifacts, no extra logos or brand marks. Realistic physical product "
    "with subtle paper texture on the label and subtle plastic surface "
    "on the bottle."
)


def b64_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def submit(payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-key": API_KEY,
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlreq.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urlerr.HTTPError as e:
        sys.exit(f"BFL submit error {e.code}: {e.read().decode('utf-8')[:1000]}")


def poll(polling_url: str, *, max_wait_s: int = 240) -> dict:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        req = urlreq.Request(
            polling_url,
            headers={"x-key": API_KEY, "Accept": "application/json"},
        )
        with urlreq.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        status = data.get("status")
        if status == "Ready":
            return data
        if status in ("Error", "Failed", "Content Moderated", "Request Moderated"):
            sys.exit(f"BFL job failed: {json.dumps(data, indent=2)}")
        print(f"  status: {status}  (waiting…)")
        time.sleep(3)
    sys.exit("BFL job timed out")


def download_to(url: str, path: Path):
    with urlreq.urlopen(url, timeout=60) as resp:
        path.write_bytes(resp.read())


def main():
    if not REFERENCE.exists():
        sys.exit(f"Reference mockup not found: {REFERENCE}")
    print(f"Using reference: {REFERENCE.name}")
    payload = {
        "prompt": PROMPT,
        "input_image": b64_image(REFERENCE),
        "width": 1024,
        "height": 1280,
        "output_format": "png",
        "safety_tolerance": 2,
    }
    print(f"Submitting to {ENDPOINT} …")
    submit_resp = submit(payload)
    polling_url = submit_resp.get("polling_url") or submit_resp.get("polling")
    if not polling_url:
        sys.exit(f"No polling_url in response: {json.dumps(submit_resp, indent=2)}")
    print(f"Job id: {submit_resp.get('id')}")
    print(f"Polling: {polling_url}")

    result = poll(polling_url)
    sample_url = result.get("result", {}).get("sample")
    if not sample_url:
        sys.exit(f"No sample URL in result: {json.dumps(result, indent=2)}")

    print(f"Downloading to {OUTPUT} …")
    download_to(sample_url, OUTPUT)
    kb = OUTPUT.stat().st_size // 1024
    print(f"Wrote {OUTPUT.name} ({kb} KB)")


if __name__ == "__main__":
    main()
