#!/usr/bin/env python3
"""
Generate 8 identity-locked variations of the podcast-host woman shown in
the two reference images, to fill out a HeyGen Photo Avatar training set
(2 refs the user already has + 8 new = 10 total).

Identity lock via Flux 2 Pro `input_image` + `input_image_2` (both refs
sent as base64). Same wardrobe + studio + camera/aesthetic across all 8;
only pose/expression varies. The aesthetic block reuses the user's
validated v5-documentary winner.

Run:
  python3 gen-avatar-8.py
  python3 gen-avatar-8.py --only 03-frontal-open-smile
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
OUT_DIR = Path("/Users/zacharypoll/Desktop/heygen-avatar-set")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1024  # HeyGen-friendly square

REF_1 = Path("/Users/zacharypoll/Desktop/heygen test/teacher-tests/v5-documentary-still.jpg")
REF_2 = Path("/Users/zacharypoll/Desktop/generation-db006de8-362b-4bb6-a8e7-2c08f5675c77.png")
for r in (REF_1, REF_2):
    if not r.exists():
        sys.exit(f"reference image missing: {r}")
REF_1_B64 = base64.b64encode(REF_1.read_bytes()).decode("ascii")
REF_2_B64 = base64.b64encode(REF_2.read_bytes()).decode("ascii")

SUBJECT_AND_SETTING = (
    "The exact same woman shown in the reference images: early-30s, "
    "warm-but-sharp, light-to-medium brown hair with sun-kissed "
    "highlights, shoulder-length and softly waved, half pulled back "
    "from her face, hazel eyes, defined cheekbones, full natural lips. "
    "Wearing the same fitted cream silk blouse with the top buttons "
    "undone, delicate gold chain necklace, small gold stud earrings, "
    "tortoise-shell glasses pushed up on top of her head. Sitting at "
    "the polished walnut podcast desk in the same high-production "
    "studio: walnut acoustic-slat wall behind her, low-amber LED "
    "strip-light along the floor and ceiling, a Shure SM7B on a "
    "Yellowtec mika boom in front of her, a second matching mic out "
    "of focus on the right edge of frame indicating a co-host seat, "
    "a small succulent and a black leather notebook on the desk."
)

CAMERA_AESTHETIC = (
    "A documentary frame captured by a photojournalist embedded with "
    "the show. Ambient studio light only, no added key, no fill — "
    "exactly the light the room actually has. Shot on a Leica SL2 "
    "with a Summilux 50mm at f/2, ISO 1600, mild natural sensor noise "
    "in the shadows. The kind of unstaged photo of a real moment."
)


def build(pose_and_expression: str) -> str:
    return SUBJECT_AND_SETTING + " " + pose_and_expression + " " + CAMERA_AESTHETIC


SHOTS = [
    {
        "label": "01-frontal-neutral",
        "prompt": build(
            "Pose: head straight on to the camera, both hands resting "
            "lightly on the desk in front of her, shoulders square, eyes "
            "engaged with the lens. Expression: closed mouth, calm, "
            "completely relaxed, no smile — the canonical reference frame."
        ),
    },
    {
        "label": "02-frontal-soft-smile",
        "prompt": build(
            "Pose: head straight on, both hands resting on the desk, "
            "shoulders square, eyes engaged with the lens. Expression: a "
            "soft warm closed-mouth smile, slight crinkle at the corners "
            "of her eyes, genuine warmth, not posed."
        ),
    },
    {
        "label": "03-frontal-open-smile",
        "prompt": build(
            "Pose: head straight on, one hand gesturing slightly at the "
            "desk mid-explanation, eyes engaged with the lens. "
            "Expression: a natural open smile with upper teeth lightly "
            "visible, eyes crinkled with warmth, mid-conversation energy."
        ),
    },
    {
        "label": "04-three-quarter-left",
        "prompt": build(
            "Pose: head and shoulders turned approximately 30 degrees to "
            "her own left (camera sees more of the right side of her "
            "face), eyes turned back to the camera lens, hands resting on "
            "the desk. Expression: a subtle closed-mouth smile, calm and "
            "engaged."
        ),
    },
    {
        "label": "05-three-quarter-right",
        "prompt": build(
            "Pose: head and shoulders turned approximately 30 degrees to "
            "her own right (camera sees more of the left side of her "
            "face), eyes turned back to the camera lens, hands resting on "
            "the desk. Expression: a subtle closed-mouth smile, calm and "
            "engaged."
        ),
    },
    {
        "label": "06-speaking-mid-vowel",
        "prompt": build(
            "Pose: head straight on, eyes engaged with the lens, hands "
            "relaxed on the desk. Expression: caught mid-word in natural "
            "speech — lips parted in an open 'ah' or 'oh' viseme, lower "
            "jaw slightly dropped, the relaxed mouth shape of someone "
            "speaking a vowel mid-sentence. The rest of her face alert "
            "and engaged."
        ),
    },
    {
        "label": "07-laughing",
        "prompt": build(
            "Pose: head tilted slightly back, eyes mostly to the camera "
            "but partially crinkled shut from genuine laughter, shoulders "
            "relaxed, one hand near her chest mid-laugh. Expression: a "
            "real, joyful laugh — open mouth with upper teeth showing "
            "naturally, deep eye crinkles, full laugh lines lit up. "
            "Caught at the peak of a real laugh."
        ),
    },
    {
        "label": "08-looking-at-notes",
        "prompt": build(
            "Pose: head tilted slightly down, eyes drifting to the black "
            "leather notebook on the desk in front of her, one hand "
            "resting on the page as if she has just glanced at her notes. "
            "Expression: focused and present, slight closed-mouth smile, "
            "mid-thought."
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


def gen(shot):
    out = OUT_DIR / f"{shot['label']}.jpg"
    print(f"[{shot['label']}] {ENDPOINT} {WIDTH}x{HEIGHT} (2 refs, prompt_upsampling=False)")
    payload = {
        "prompt": shot["prompt"],
        "input_image": REF_1_B64,
        "input_image_2": REF_2_B64,
        "width": WIDTH,
        "height": HEIGHT,
        "prompt_upsampling": False,
    }
    resp = post_json(ENDPOINT, payload)
    if "_http_error" in resp:
        print(f"  [{shot['label']}] HTTP {resp['_http_error']}: {resp['_body'][:300]}")
        return False
    sample = poll(resp.get("polling_url", ""), resp["id"], shot["label"])
    if sample is None:
        return False
    download(sample, out)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one label, e.g. '03-frontal-open-smile'")
    args = ap.parse_args()
    targets = [s for s in SHOTS if (args.only is None or s["label"] == args.only)]
    if not targets:
        sys.exit("no match. Available: " + ", ".join(s["label"] for s in SHOTS))
    rejected = []
    for s in targets:
        if not gen(s):
            rejected.append(s["label"])
    print(f"\nDone. {len(targets) - len(rejected)} / {len(targets)} succeeded.")
    if rejected:
        print(f"Moderated/failed: {', '.join(rejected)}")


if __name__ == "__main__":
    main()
