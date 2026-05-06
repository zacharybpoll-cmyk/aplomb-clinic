#!/usr/bin/env python3
"""
Generate 10 identity-locked SCENE images of the same woman for HeyGen
avatar deployment context. Uses Flux 2 Pro with two reference images
(input_image + input_image_2) for identity preservation, varying
environment, framing, and shot type per shot.

Calibrated to RESEARCH_video_creative_analysis.md — semi-pro / phone-shot
UGC tier, kitchens / bedrooms / bathrooms / walks / home offices, the
settings the research showed convert for women 50-65 in this category.

Run:
  source ~/.claude/secrets.env
  python3 gen-heygen-scenes-set.py
  python3 gen-heygen-scenes-set.py --only scene-01-kitchen-counter-talking-head
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
WIDTH, HEIGHT = 1024, 1024

# --- Reference images (identity lock) --------------------------------------
REF_1 = PROJECT_DIR / "generation-5706d2ba-6bd8-4c82-b615-6b15eb8a843d.png"
REF_2 = PROJECT_DIR / "generation-844dcc55-58ee-4f1c-9fe7-4bbe3d68e3b8.png"

for r in (REF_1, REF_2):
    if not r.exists():
        sys.exit(f"reference image missing: {r}")

REF_1_B64 = base64.b64encode(REF_1.read_bytes()).decode("ascii")
REF_2_B64 = base64.b64encode(REF_2.read_bytes()).decode("ascii")

# --- Subject identity (verbatim from gen-heygen-avatar-set.py:57-70) -------
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

# --- Production / camera direction (UGC tier — DIFFERENT from avatar set) --
# The avatar script uses Phase One medium-format editorial. THIS script
# explicitly forces phone-shot UGC tier because the research showed UGC
# converts in this category for paid social.
CAMERA_UGC = (
    "Shot on a smartphone (iPhone 15 Pro) or a compact mirrorless camera in "
    "natural ambient light. NOT a medium-format studio camera, NOT polished, "
    "NOT magazine-glossy, NOT editorial fashion photography. Phone-shot "
    "user-generated-content quality with natural light only — the kind of "
    "video frame a real woman would actually shoot of herself for an "
    "Instagram Reel or a Facebook story. Slight, natural sensor noise. "
    "Imperfect handheld framing. Real ambient color cast from the room (warm "
    "incandescent lamps, cool daylight from windows, no color correction). "
    "Square 1024x1024 composition, person clearly the focus."
)

ANTI_STAGED = (
    " She is in her own home doing a normal thing — she did not arrange the "
    "room for the shot. Real lived-in setting with normal everyday clutter "
    "and personal objects. NOT a styled showroom, NOT a Pinterest-aesthetic "
    "kitchen, NOT a designer interior, NOT an Architectural Digest interior, "
    "NOT a brand-content set, NOT an Airbnb-staged room. Real used cabinets, "
    "real wear on surfaces, real lived-in textures."
)

ANTI_AI_TAIL = (
    " A real photograph of a real human being — not AI-generated, not "
    "illustration, not 3D render. Indistinguishable from a candid phone "
    "photo a real 58-year-old woman would take of herself in her own home. "
    "Real skin with visible pores, real hair with stray strands and natural "
    "fly-aways, real fabric with creases and wear, real eyes with imperfect "
    "catchlights, real lips without gloss-uniformity. NOT plastic skin, NOT "
    "airbrushed, NOT waxy AI rendering, NOT perfect bilateral facial "
    "symmetry, NOT glowing highlights, NOT halo effect, NOT lens flare, "
    "NOT fantasy lighting, NOT CGI render, NOT 3D product visualization, "
    "NOT oversaturated, NOT yellow-washed, NOT digital artifact, NOT "
    "AI-generated look, NOT glossy lifestyle-brand finish, NOT stock-photo "
    "lighting, NOT soft-box catchlights, NOT smoothed-over pores, NOT "
    "retouched, NOT Instagram-filter aesthetic, NOT vacant model expression. "
    "Authentic everyday smartphone photography."
)


def build(setting_and_pose: str) -> str:
    return (
        "A candid documentary smartphone photograph of "
        + SUBJECT
        + " "
        + setting_and_pose
        + " "
        + CAMERA_UGC
        + ANTI_STAGED
        + ANTI_AI_TAIL
    )


# --- The 10 scene shots (research-calibrated) ------------------------------
SHOTS = [
    {
        "label": "scene-01-kitchen-counter-talking-head",
        "prompt": build(
            "Setting: she is standing at the counter in her own kitchen — "
            "neutral white or warm-wood cabinetry, a real coffee mug visible "
            "in the foreground, a window out of frame to camera-left "
            "providing soft morning daylight. Pose: chest-up, head and "
            "shoulders to camera, eyes directly at the lens. Expression: a "
            "warm closed-mouth smile, calm and direct, the kind of look "
            "someone gives at the start of a conversation. Framing: tight "
            "chest-up talking-head, eye-level, eyes on the upper third of "
            "the frame."
        ),
    },
    {
        "label": "scene-02-kitchen-counter-laughing",
        "prompt": build(
            "Setting: same kitchen as scene-01 — warm-wood / neutral "
            "cabinetry, soft window daylight from camera-left, kitchen "
            "details (mug, cutting board, fruit bowl) visible but soft in "
            "the background. Pose: chest-up, head tilted very slightly back, "
            "shoulders relaxed. Expression: caught at the peak of a real "
            "joyful laugh — open mouth with upper teeth showing naturally, "
            "deep eye crinkles, full laugh lines lit up. NOT posed, NOT a "
            "forced grin. Framing: tight chest-up, eye-level."
        ),
    },
    {
        "label": "scene-03-bathroom-mirror-selfie",
        "prompt": build(
            "Setting: she is in her own bathroom holding her phone up to the "
            "mirror — a real lived-in bathroom with a neutral counter, a "
            "small plant, a glimpse of a folded towel. Soft natural daylight "
            "from a window. Pose: phone-held-up selfie angle, the camera is "
            "slightly above eye-level (held at chin height pointed up). She "
            "is facing the mirror, eyes meeting her own reflection through "
            "the camera. Expression: contemplative, lips slightly parted as "
            "if mid-thought. Framing: tight face close-up, head and "
            "shoulders fill the frame, the phone partially visible at the "
            "bottom edge."
        ),
    },
    {
        "label": "scene-04-bedroom-seated-on-edge",
        "prompt": build(
            "Setting: she is sitting on the edge of her own made bed — soft "
            "linen bedding in cream and oat tones, a single pillow visible, "
            "a nightstand out of frame, soft warm morning light from a "
            "window. Pose: mid-shot seated, body angled very slightly to "
            "camera-left, shoulders relaxed, hands resting in her lap. "
            "Expression: vulnerable but calm — a soft closed-mouth smile, "
            "the kind of expression of someone about to share something "
            "honest. Framing: mid-shot from waist up, eye-level, slight "
            "negative space above her head."
        ),
    },
    {
        "label": "scene-05-living-room-sofa-relaxed",
        "prompt": build(
            "Setting: her own living room — she is seated on a neutral linen "
            "or oat-colored sofa, a textured throw blanket draped behind her, "
            "soft afternoon light from a window to camera-right, a coffee "
            "table edge just visible at the bottom of the frame. Pose: mid-"
            "shot seated, leaning very slightly forward toward the camera, "
            "elbows on knees or resting on the sofa arm. Expression: engaged "
            "listening, head tilted very slightly to one side, soft warm "
            "look. Framing: mid-shot from waist up, eye-level."
        ),
    },
    {
        "label": "scene-06-walking-and-talking-hallway",
        "prompt": build(
            "Setting: she is walking through her own home hallway — past a "
            "doorway, with the corner of a framed picture visible on the "
            "wall behind her, warm interior light. Pose: walking-and-talking "
            "with the camera following her at slightly below eye-level (as "
            "if a friend held the phone). Mid-stride, body angled three-"
            "quarters to camera. Expression: caught mid-sentence, mouth "
            "slightly open mid-word, animated, looking just slightly past "
            "the camera as if making a point. Subtle motion blur in the "
            "background indicating real movement. Framing: chest-up, slight "
            "tilt to the camera angle, walking-and-talking format."
        ),
    },
    {
        "label": "scene-07-outdoor-park-walking",
        "prompt": build(
            "Setting: she is standing in her own private backyard garden — "
            "soft greenery and a wooden fence in soft focus behind her, late "
            "morning sun filtering through the leaves of a tree overhead, "
            "warm dappled light on her hair and shoulders. Pose: standing, "
            "body angled three-quarters to camera, head turned to face the "
            "lens. Expression: a warm closed-mouth smile, eye crinkles, the "
            "calm look of someone in a quiet moment in her garden. Framing: "
            "mid-shot from waist up, eye-level, garden softly out of focus "
            "behind her."
        ),
    },
    {
        "label": "scene-08-home-office-desk",
        "prompt": build(
            "Setting: her own home office — a warm-wood or oak desk, a "
            "shelf of books and a small ceramic mug visible behind her in "
            "soft focus, a desk lamp providing warm interior light, soft "
            "daylight from a window adding fill. Pose: chest-up seated at "
            "the desk, body angled very slightly off-axis, one hand resting "
            "on the desk surface, the other partly visible mid-gesture. "
            "Expression: open and engaged, eyebrows slightly raised as if "
            "explaining something, soft smile. Framing: chest-up seated, "
            "eye-level."
        ),
    },
    {
        "label": "scene-09-kitchen-table-morning-coffee",
        "prompt": build(
            "Setting: her own kitchen / dining area — she is seated at a "
            "wooden kitchen table with a real cup of morning coffee in front "
            "of her, an open notebook or newspaper soft in the background, "
            "soft morning window light from camera-left. Pose: mid-shot "
            "seated at the table, body slightly angled, hands resting near "
            "the coffee cup. The camera is slightly above eye-level (as if "
            "a partner or family member is talking to her). Expression: "
            "pensive and listening, a soft closed-mouth smile, looking up "
            "at the camera. Framing: mid-shot from waist up, slight "
            "downward camera angle."
        ),
    },
    {
        "label": "scene-10-podcast-desk-soft-light",
        "prompt": build(
            "Setting: a small home podcast or recording setup — a "
            "professional condenser microphone on a boom arm visible in the "
            "lower foreground (just the upper part of the mic in frame), a "
            "warm desk lamp providing key light, a shelf of books in soft "
            "focus behind her, warm wood textures. NOT a fully professional "
            "studio — feels like someone's home setup. Pose: chest-up "
            "seated, eyes directly at the camera (as if speaking on a "
            "podcast). Expression: engaged, mid-word, lips parted slightly, "
            "the alert look of someone in conversation. Framing: chest-up "
            "seated, eye-level, microphone occupying the lower-left quarter "
            "of the frame."
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
    ap.add_argument("--only", help="regen one label, e.g. 'scene-03-bathroom-mirror-selfie'")
    args = ap.parse_args()
    targets = [s for s in SHOTS if (args.only is None or s["label"] == args.only)]
    if not targets:
        sys.exit(f"no match for label '{args.only}'. Available: " + ", ".join(s["label"] for s in SHOTS))
    for s in targets:
        gen(s)
    print(f"\nDone. {len(targets)} image(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
