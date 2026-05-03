#!/usr/bin/env python3
"""
Realism A/B test #2: hot-teacher persona, professional podcast studio,
TEXT-TO-IMAGE ONLY (no reference photo / no input_image).

Same SUBJECT description across all 5 — only the camera / aesthetic
vocabulary varies. Goal: find the prompt language that yields the most
believably-real "professional podcast headshot" output.

Run:
  python3 gen-teacher-tests.py
  python3 gen-teacher-tests.py --only v2-bts-laugh
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
OUT_DIR = Path("/Users/zacharypoll/Desktop/heygen test/teacher-tests")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1024

# Common subject — held constant across all 5 tests. "Hot teacher" archetype
# tuned for a 30-year-old male audience: warm-but-sharp, smart, the
# professor-on-TikTok energy. Confident, fitted clothing, tasteful sex
# appeal — not glam-model, not lifestyle-influencer.
SUBJECT = (
    "An early-30s American woman, the 'hot teacher' archetype — warm but "
    "sharp, intelligent, confident. Light-to-medium brown hair with sun-kissed "
    "highlights, shoulder-length and softly waved, half pulled back from her "
    "face with a few loose pieces framing her cheekbones. Bright hazel eyes "
    "with thick lashes, a slight knowing smile, full natural lips. Defined "
    "cheekbones and a graceful jaw. Healthy real skin with a few faint "
    "freckles across her nose, fine natural laugh lines at the corners of "
    "her eyes — kept, not retouched. Subtle, flattering makeup: a soft eye, "
    "a touch of warm blush, balmy lips. Tortoise-shell rectangular reading "
    "glasses pushed up on top of her head or sitting low on her nose. Wearing "
    "a fitted cream silk blouse, top two buttons undone, collarbone and a "
    "hint of décolletage visible. Delicate gold chain necklace. Small gold "
    "stud earrings. Sitting at the podcast desk, hands lightly resting on "
    "the wood surface. Head and shoulders to mid-torso composition, eyes "
    "engaged with the camera lens."
)

# Studio setting — held constant. Real professional podcast studio, in the
# tonal register of Diary of a CEO / Smartless / Call Her Daddy production.
STUDIO = (
    "She is in a high-production professional podcast studio: floor-to-ceiling "
    "warm walnut acoustic-slat wall directly behind her, tasteful low-amber "
    "neon strip-light running along the floor and ceiling, a Shure SM7B on "
    "a Yellowtec mika boom arm in front of her, a second matching mic "
    "out-of-focus on the right edge of frame indicating a co-host seat, a "
    "polished walnut podcast desk with a single small succulent plant and "
    "a black leather notebook visible. The room reads as expensive, "
    "engineered, and lit for video — not a home setup."
)

# The 5 competing aesthetics. Each is the COMPLETE prompt suffix.
TESTS = [
    {
        "label": "v1-pro-headshot",
        "tail": (
            "Promotional press headshot for a top-charting Spotify podcast. "
            "Shot on a Sony A7 IV with a Sony 85mm f/1.4 GM lens at f/2, ISO "
            "400, two-light setup: large 4-foot Profoto octobox as soft key "
            "from camera-left at 45 degrees, gridded strip-box as edge kicker "
            "from behind camera-right, dim ambient room fill. Real medium "
            "depth of field with creamy fall-off behind her. Real catchlights, "
            "natural skin pore detail, photographic micro-contrast. The kind "
            "of headshot that runs on the show's About page and on the "
            "iTunes podcast cover."
        ),
    },
    {
        "label": "v2-bts-laugh",
        "tail": (
            "A behind-the-scenes still pulled from the podcast's 4K B-roll "
            "camera between takes. She is mid-laugh at something her "
            "co-host said off-camera, eyes crinkled, head tilted slightly "
            "back, caught completely off-guard — not posed, not looking at "
            "the camera. Real studio key light from the show's actual LED "
            "panels, natural depth of field from a Sony FX3 cinema camera "
            "with a 35mm prime. The kind of frame the social-media editor "
            "would screenshot for a Reels clip."
        ),
    },
    {
        "label": "v3-iphone-studio",
        "tail": (
            "An iPhone 15 Pro snapshot a producer took of her sitting at "
            "the podcast desk five minutes before going live. On-camera "
            "flash firing directly at her, harsh flat flash light on her "
            "face, slight over-exposure on her cheekbones, JPEG "
            "compression, the unmistakable look of a phone photo. Casual, "
            "imperfect framing. The studio is gorgeous in the background "
            "but the photo itself is texted-from-a-phone casual. Real "
            "photo, not professional photography."
        ),
    },
    {
        "label": "v4-medium-format-editorial",
        "tail": (
            "Editorial portrait shot for a Fast Company / The Information "
            "feature on the future of podcasting. Shot on a Hasselblad "
            "H6D-100c medium format with the HC 100mm f/2.2 lens at f/4, "
            "single Profoto B10 with a 5-foot Westcott Rapid Box octa as "
            "the only key light, deep natural fall-off into the studio "
            "shadows. Real medium-format dynamic range and tonal "
            "smoothness, real skin pore detail, real micro-imperfections — "
            "indistinguishable from a press portrait shot by a working "
            "editorial photographer in 2024."
        ),
    },
    {
        "label": "v5-documentary-still",
        "tail": (
            "A documentary frame captured by a photojournalist who is "
            "embedded with the show for a New York Times Magazine profile. "
            "She is mid-thought, listening to a guest, hand resting "
            "thoughtfully against her chin. Ambient studio light only, no "
            "added key, no fill, no stylist intervention — exactly the "
            "light the room actually has. Shot on a Leica SL2 with a "
            "Summilux 50mm at f/2, ISO 1600, mild natural sensor noise "
            "in the shadows. The kind of unstaged photo that wins World "
            "Press Photo entries — clearly a real moment, clearly a real "
            "human being."
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
    full_prompt = SUBJECT + " " + STUDIO + " " + test["tail"]
    print(f"[{test['label']}] {ENDPOINT} {WIDTH}x{HEIGHT} (text-only, no input_image)")
    payload = {
        "prompt": full_prompt,
        "width": WIDTH,
        "height": HEIGHT,
    }
    resp = post_json(ENDPOINT, payload)
    if "_http_error" in resp:
        print(f"  [{test['label']}] HTTP {resp['_http_error']}: {resp['_body'][:300]}")
        return False
    sample = poll(resp.get("polling_url", ""), resp["id"], test["label"])
    if sample is None:
        return False
    download(sample, out)
    # Save the exact prompt next to the image so user can copy/paste into the playground.
    (out.with_suffix(".prompt.txt")).write_text(full_prompt + "\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one label, e.g. 'v2-bts-laugh'")
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
