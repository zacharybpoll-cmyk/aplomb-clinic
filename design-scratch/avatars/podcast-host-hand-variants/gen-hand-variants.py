#!/usr/bin/env python3
"""
Generate 6 hand-position variants of the podcast-host portrait.

Source image has the host's right hand resting under her chin, which breaks
HeyGen image-to-video lip-sync. This script regens 6 variants where ONLY the
right hand changes to a HeyGen-friendly pose; everything else (face, hair,
sunglasses, blouse, jewelry, mics, desk, backdrop) is preserved via Flux 2 Pro
input_image conditioning.

Run:
  source ~/.claude/secrets.env
  python3 gen-hand-variants.py
  python3 gen-hand-variants.py --only 04-right-hand-holding-coffee-mug
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# --- API key ---------------------------------------------------------------
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
PROJECT_DIR = Path(__file__).resolve().parent
OUT_DIR = PROJECT_DIR
WIDTH, HEIGHT = 1120, 1408  # matches source aspect exactly

SOURCE = Path("/Users/zacharypoll/Desktop/generation-db006de8-362b-4bb6-a8e7-2c08f5675c77.png")
if not SOURCE.exists():
    sys.exit(f"source image missing: {SOURCE}")
SOURCE_B64 = base64.b64encode(SOURCE.read_bytes()).decode("ascii")

# --- Preservation block (shared across all variants) ------------------------
PRESERVE = (
    "An extremely attractive woman in her late 20s seated at a podcast desk, "
    "matching the reference image exactly. Long wavy honey-blonde / brunette "
    "balayage hair falling over her shoulders, tortoiseshell sunglasses pushed "
    "up onto the top of her head, soft glam makeup with peachy lipstick, small "
    "gold stud earrings, fine gold chain necklace with a small pendant, "
    "small dark forearm tattoo on her right inner wrist. She wears the same "
    "loose champagne / cream silk satin blouse with V-neckline and small "
    "buttons, slightly unbuttoned at the collar, sleeves cuffed at the wrists. "
    "Two large black Shure broadcast microphones on boom arms flank her — one "
    "on each side of the frame — and a yellow boom-arm clamp is just visible "
    "at the upper-left edge. She is seated behind a warm walnut-wood podcast "
    "desk; behind her is a vertical wood slat acoustic backdrop in warm walnut "
    "with soft warm uplighting glowing along the lower edge of the wall. The "
    "back of a black mesh Herman Miller chair is just visible behind her left "
    "shoulder. Soft warm key light from camera-front, eye-level framing, "
    "shallow depth of field. Photorealistic professional editorial portrait "
    "photograph. The face, hair, sunglasses, makeup, jewelry, blouse, "
    "microphones, desk, backdrop, and lighting must remain identical to the "
    "reference image. The ONLY change is the position of her right hand "
    "(camera-left) — it must NOT touch, rest on, or be near her face, jaw, "
    "chin, neck, mouth, or hair."
)

NEGATIVE_TAIL = (
    " Do not place either hand at, near, or touching the face, jaw, chin, "
    "neck, mouth, or hair. Do not change the face, hair, sunglasses, blouse, "
    "jewelry, microphones, desk, chair, or background. Photorealistic, sharp "
    "focus, real skin with natural pores and texture — not airbrushed, not "
    "AI-glossy, not 3D-rendered, no plastic skin, no extra fingers, no "
    "deformed hands, anatomically correct hands with five fingers each."
)


def hand(clause: str) -> str:
    return PRESERVE + " " + clause + NEGATIVE_TAIL


SHOTS = [
    {
        "label": "01-both-hands-flat-on-desk",
        "prompt": hand(
            "Right-hand pose: her right hand rests flat on the surface of the "
            "walnut desk, palm down, fingers relaxed and slightly spread, "
            "wrist straight, mirroring her left hand which is also flat on "
            "the desk. Both forearms rest comfortably on the desk surface. "
            "Both hands well below the chin line and clearly separated from "
            "her face."
        ),
    },
    {
        "label": "02-hands-clasped-on-desk",
        "prompt": hand(
            "Right-hand pose: both hands gently clasped together, fingers "
            "lightly interlocked, resting on the surface of the walnut desk "
            "in front of her at chest level, forearms resting on the desk. "
            "Hands well below the chin line, clearly separated from her "
            "face."
        ),
    },
    {
        "label": "03-right-hand-on-desk-near-mic",
        "prompt": hand(
            "Right-hand pose: her right hand rests flat on the walnut desk "
            "surface near the base of the right microphone stand, palm "
            "down, fingers relaxed and naturally splayed, forearm resting "
            "on the desk. Her left hand is also resting on the desk in the "
            "same place as the reference. Both hands well below the chin "
            "line and clearly separated from her face."
        ),
    },
    {
        "label": "04-right-hand-holding-coffee-mug",
        "prompt": hand(
            "Right-hand pose: her right hand loosely cradles a plain "
            "ceramic off-white coffee mug placed on the walnut desk in "
            "front of her between her body and the right microphone, "
            "fingers wrapped naturally around the side of the mug, thumb "
            "resting on the rim, forearm on the desk. Her left hand rests "
            "on the desk as in the reference. Hands well below the chin "
            "line, clearly separated from her face."
        ),
    },
    {
        "label": "05-right-hand-out-of-frame",
        "prompt": hand(
            "Right-hand pose: her right arm hangs naturally at her side "
            "with her right hand resting in her lap, fully BELOW the desk "
            "surface and completely OUT OF FRAME. Only her left hand is "
            "visible, resting on the desk surface as in the reference. Her "
            "right shoulder posture should look natural and relaxed, not "
            "raised or twisted."
        ),
    },
    {
        "label": "06-right-hand-resting-on-left-forearm",
        "prompt": hand(
            "Right-hand pose: her right forearm lies across the front of "
            "the walnut desk, with her right hand resting palm-down gently "
            "on top of her left forearm / left blouse cuff. Both hands and "
            "forearms are visible on the desk surface, fingers relaxed, "
            "wrists straight. Hands well below the chin line, clearly "
            "separated from her face."
        ),
    },
]


# --- API plumbing ----------------------------------------------------------
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


def gen(shot):
    out = OUT_DIR / f"variant-{shot['label']}.jpg"
    print(f"[{shot['label']}] {ENDPOINT} {WIDTH}x{HEIGHT}")
    payload = {
        "prompt": shot["prompt"],
        "input_image": SOURCE_B64,
        "width": WIDTH,
        "height": HEIGHT,
    }
    resp = post_json(ENDPOINT, payload)
    sample = poll(resp.get("polling_url", ""), resp["id"], shot["label"])
    download(sample, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. '04-right-hand-holding-coffee-mug'")
    args = ap.parse_args()
    targets = [s for s in SHOTS if (args.only is None or s["label"] == args.only)]
    if not targets:
        sys.exit(f"no match for label '{args.only}'. Available: " + ", ".join(s["label"] for s in SHOTS))
    for s in targets:
        gen(s)
    print(f"\nDone. {len(targets)} image(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
