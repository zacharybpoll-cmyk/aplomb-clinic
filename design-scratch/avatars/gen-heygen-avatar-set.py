#!/usr/bin/env python3
"""
Generate 10 identity-locked portraits of the same woman for HeyGen avatar
training. Uses Flux 2 Pro with two reference images (input_image +
input_image_2) for identity preservation, varying head pose and expression
across the set.

References baked in: the two existing portraits on the Desktop.

Run:
  source ~/.claude/secrets.env
  python3 gen-heygen-avatar-set.py
  python3 gen-heygen-avatar-set.py --only 03-frontal-open-smile
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
OUT_DIR = Path.home() / "Desktop" / "heygen-avatar-photos"
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1024

# --- Reference images (identity lock) --------------------------------------
DESKTOP = Path.home() / "Desktop"
REF_1 = DESKTOP / "generation-5706d2ba-6bd8-4c82-b615-6b15eb8a843d.png"
REF_2 = DESKTOP / "generation-844dcc55-58ee-4f1c-9fe7-4bbe3d68e3b8.png"

for r in (REF_1, REF_2):
    if not r.exists():
        sys.exit(f"reference image missing: {r}")

REF_1_B64 = base64.b64encode(REF_1.read_bytes()).decode("ascii")
REF_2_B64 = base64.b64encode(REF_2.read_bytes()).decode("ascii")

# --- Prompt building blocks ------------------------------------------------
SUBJECT = (
    "The exact same woman shown in the reference images: age approximately "
    "58. Shoulder-length straight bob hairstyle, dark brunette with prominent "
    "natural silver streaking — silver concentrated through the front section "
    "and at the temples, dark brown through the back, slight inward curl at "
    "the ends. Tortoise-shell browline / clubmaster glasses with a gold "
    "metal lower rim. Light hazel-green eyes. Defined cheekbones, a slim "
    "straight nose, full natural mouth. Fine lines at the corners of her "
    "eyes and faint laugh lines around her mouth — kept, not retouched. "
    "Pearl drop earrings. Cream / off-white loose-knit top, slightly "
    "off-shoulder. Natural ungroomed eyebrows, minimal makeup, healthy real "
    "skin with visible pores and faint freckles. Match the identity, hair, "
    "glasses, earrings, and clothing of the reference photographs exactly."
)

SETTING = (
    "Plain warm cream / putty-beige softly textured plaster wall directly "
    "behind her, no other objects in frame. Soft natural daylight from "
    "camera-left, gentle falloff to camera-right. Tight head-and-shoulders "
    "portrait crop, eyes roughly on the upper third of the frame. Square "
    "1024x1024 composition."
)

CAMERA = (
    "Shot on a Phase One IQ4 medium format with a Schneider 80mm leaf-shutter "
    "lens, natural window light, no flash, no fill. Real medium-format depth "
    "of field. Desaturated editorial color grade — warm cream highlights, "
    "soft amber midtones, deep umber shadows."
)

ANTI_AI_TAIL = (
    " A real photograph of a real human being — not AI-generated, not "
    "illustration, not 3D render. Indistinguishable from a documentary "
    "photograph in The Gentlewoman, Aperture, or NYT Style. Real skin "
    "with visible pores, real hair with stray strands and natural fly-aways, "
    "real fabric with creases and wear, real eyes with imperfect catchlights, "
    "real lips without gloss-uniformity. NOT plastic skin, NOT airbrushed, "
    "NOT waxy AI rendering, NOT perfect bilateral facial symmetry, NOT "
    "glowing highlights, NOT halo effect, NOT lens flare, NOT fantasy "
    "lighting, NOT CGI render, NOT 3D product visualization, NOT "
    "oversaturated, NOT yellow-washed, NOT digital artifact, NOT "
    "AI-generated look, NOT glossy lifestyle-brand finish, NOT stock-photo "
    "lighting, NOT soft-box catchlights, NOT smoothed-over pores, NOT "
    "retouched, NOT Instagram-filter aesthetic, NOT vacant model expression. "
    "Editorial commercial photography in Kinfolk magazine tonality."
)


def build(pose_and_expression: str) -> str:
    return (
        "A documentary editorial portrait of "
        + SUBJECT
        + " "
        + pose_and_expression
        + " "
        + SETTING
        + " "
        + CAMERA
        + ANTI_AI_TAIL
    )


# --- The 10 shots ----------------------------------------------------------
SHOTS = [
    {
        "label": "01-frontal-neutral",
        "prompt": build(
            "Pose: head straight on to the camera, eyes looking directly at "
            "the lens, shoulders square. Expression: closed mouth, completely "
            "relaxed, no smile, calm and direct — the canonical reference "
            "frame, the kind of frontal headshot used on a passport or ID."
        ),
    },
    {
        "label": "02-frontal-soft-smile",
        "prompt": build(
            "Pose: head straight on to the camera, eyes looking directly at "
            "the lens, shoulders square. Expression: a soft closed-mouth "
            "warm smile, eyes slightly crinkled at the corners, genuine "
            "warmth, not posed."
        ),
    },
    {
        "label": "03-frontal-open-smile",
        "prompt": build(
            "Pose: head straight on to the camera, eyes looking directly at "
            "the lens, shoulders square. Expression: an open smile with the "
            "upper teeth clearly but naturally visible, eyes crinkled with "
            "real warmth — the kind of smile that happens mid-conversation, "
            "not a forced studio grin."
        ),
    },
    {
        "label": "04-three-quarter-left",
        "prompt": build(
            "Pose: her head and shoulders are turned approximately 30 "
            "degrees to her own left (so the camera sees more of the right "
            "side of her face), but her eyes are looking back at the camera "
            "lens. Expression: a subtle closed-mouth smile, calm and engaged."
        ),
    },
    {
        "label": "05-three-quarter-right",
        "prompt": build(
            "Pose: her head and shoulders are turned approximately 30 "
            "degrees to her own right (so the camera sees more of the left "
            "side of her face), but her eyes are looking back at the camera "
            "lens. Expression: a subtle closed-mouth smile, calm and engaged."
        ),
    },
    {
        "label": "06-tilt-right-neutral",
        "prompt": build(
            "Pose: head facing the camera, with a subtle tilt toward her own "
            "right shoulder (about 8 degrees), eyes on the lens. Expression: "
            "neutral and contemplative, closed mouth, no smile."
        ),
    },
    {
        "label": "07-tilt-left-soft-smile",
        "prompt": build(
            "Pose: head facing the camera, with a subtle tilt toward her own "
            "left shoulder (about 8 degrees), eyes on the lens. Expression: "
            "a soft closed-mouth smile, gentle and approachable."
        ),
    },
    {
        "label": "08-speaking-mid-vowel",
        "prompt": build(
            "Pose: head straight on, eyes on the lens. Expression: caught "
            "mid-word in natural speech — lips parted in an open 'ah' or "
            "'oh' viseme, lower jaw slightly dropped, the relaxed mouth "
            "shape of someone speaking a vowel mid-sentence. Subtle and "
            "natural, NOT exaggerated, NOT a yawn, NOT a kissy face. The "
            "rest of her face is alert and engaged, eyebrows in a normal "
            "neutral position. CRITICAL: her hair is dark brunette with "
            "silver streaks at the front and temples — exactly as in the "
            "reference photographs. NOT blonde, NOT light blonde, NOT honey "
            "blonde, NOT bleached. Dark brown hair with silver streaking, "
            "matching the references."
        ),
    },
    {
        "label": "09-laughing",
        "prompt": build(
            "Pose: head tilted very slightly back, eyes mostly to the "
            "camera but partly crinkled shut from genuine laughter, "
            "shoulders relaxed. Expression: a real, joyful laugh — open "
            "mouth, upper teeth showing naturally, deep eye crinkles, full "
            "laugh lines lit up. Caught at the peak of a real laugh, NOT "
            "posed, NOT a forced smile."
        ),
    },
    {
        "label": "10-contemplative-serious",
        "prompt": build(
            "Pose: head straight on, eyes drifting slightly off-camera (just "
            "past the lens, as if listening to something off to her right), "
            "shoulders square. Expression: closed mouth, thoughtful, calm, "
            "no smile, brows softly relaxed — the contemplative listening "
            "face of someone considering an idea. Serious but not stern, "
            "warm but not smiling."
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
    out = OUT_DIR / f"{shot['label']}.jpg"
    print(f"[{shot['label']}] {ENDPOINT} {WIDTH}x{HEIGHT}")
    payload = {
        "prompt": shot["prompt"],
        "input_image": REF_1_B64,
        "input_image_2": REF_2_B64,
        "width": WIDTH,
        "height": HEIGHT,
    }
    resp = post_json(ENDPOINT, payload)
    sample = poll(resp.get("polling_url", ""), resp["id"], shot["label"])
    download(sample, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. '03-frontal-open-smile'")
    args = ap.parse_args()
    targets = [s for s in SHOTS if (args.only is None or s["label"] == args.only)]
    if not targets:
        sys.exit(f"no match for label '{args.only}'. Available: " + ", ".join(s["label"] for s in SHOTS))
    for s in targets:
        gen(s)
    print(f"\nDone. {len(targets)} image(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
