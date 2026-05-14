#!/usr/bin/env python3
"""
Realism A/B test for the HeyGen avatar prompt.

Same identity lock (MHIH ref via input_image), same pose (frontal-neutral),
same wardrobe. Only the CAMERA / AESTHETIC vocabulary varies. Goal: find
the prompt language that escapes Flux 2 Pro's glossy editorial mode.

Run:
  python3 gen-realism-tests.py
  python3 gen-realism-tests.py --only v3-film-flash
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
OUT_DIR = Path("/Users/zacharypoll/Desktop/heygen test/realism-tests")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1024

REF = Path(
    "/Users/zacharypoll/Desktop/Documents/Claude Code/MHIH/"
    "Photos of people wearing them/cleaned/"
    "5cd29e3c-8595-4d8d-abc3-cf625b6fc740.png"
)
REF_B64 = base64.b64encode(REF.read_bytes()).decode("ascii")

# Common subject + wardrobe + pose — held constant across all 5 tests.
SUBJECT_WARDROBE_POSE = (
    "A late-20s brunette woman, the same person shown in the reference "
    "image — wavy mid-brown hair parted to one side, hazel-green eyes, "
    "defined cheekbones, full natural lips. She is wearing a fitted "
    "low-cut black top with a deep sweetheart neckline. She is sitting in "
    "a small podcast room with a microphone visible at the edge of the "
    "frame. Head and shoulders, looking straight at the camera, calm "
    "neutral expression, closed mouth."
)

# The five competing aesthetics. Each one is the COMPLETE prompt — different
# in vocabulary, length, and what they emphasize.
TESTS = [
    {
        "label": "v1-iphone-flash",
        "prompt": (
            SUBJECT_WARDROBE_POSE
            + " Shot on iPhone with the on-camera flash, slightly "
            "overexposed, harsh flat flash light, mild lens compression, "
            "tiny digital noise in the shadows, JPEG compression artifacts. "
            "The kind of casual photo a friend would text you. Slightly "
            "imperfect framing. Real photo, not professional."
        ),
    },
    {
        "label": "v2-webcam",
        "prompt": (
            SUBJECT_WARDROBE_POSE
            + " A still frame captured from a Zoom or Riverside podcast "
            "recording. Soft webcam image quality, slight digital "
            "compression, fluorescent overhead room light, slight "
            "auto-exposure flatness, the muted color of a 1080p webcam "
            "sensor. Looks like a screenshot mid-recording."
        ),
    },
    {
        "label": "v3-film-flash",
        "prompt": (
            SUBJECT_WARDROBE_POSE
            + " A 35mm film snapshot on Kodak Gold 400, taken with a "
            "point-and-shoot disposable camera with the built-in flash "
            "firing directly at her. Visible film grain, slight color "
            "shift in the shadows, the flat hard look of direct on-camera "
            "flash, slight red catch in the eyes, mild scanning artifacts. "
            "Y2K disposable-camera aesthetic."
        ),
    },
    {
        "label": "v4-candid",
        "prompt": (
            SUBJECT_WARDROBE_POSE
            + " An unposed candid phone photo someone took of her between "
            "podcast takes. She is mid-glance toward the camera, not "
            "actually posing. Slight motion blur from her turning her head, "
            "mixed warm-tungsten and cool-fluorescent room lighting, an "
            "ordinary phone-camera look. Imperfect framing, no styling, "
            "the kind of photo nobody would publish but is obviously real."
        ),
    },
    {
        "label": "v5-minimal",
        "prompt": (
            SUBJECT_WARDROBE_POSE
            + " A regular photo. Real photo, not AI, not stylized."
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
    print(f"[{test['label']}] {ENDPOINT} {WIDTH}x{HEIGHT}")
    payload = {
        "prompt": test["prompt"],
        "input_image": REF_B64,
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
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one label, e.g. 'v3-film-flash'")
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
