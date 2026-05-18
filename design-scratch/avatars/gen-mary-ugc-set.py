#!/usr/bin/env python3
"""
Generate 10 identity-locked VERTICAL (9:16) UGC source frames of "Mary"
for HeyGen talking-head videos. Near-clone of gen-heygen-scenes-set.py:
same Flux 2 Pro pipeline, same two reference images (input_image +
input_image_2), same SUBJECT identity-lock and same UGC / anti-staged /
anti-AI envelope (so the look matches scene-05, the chosen favorite).

Deltas vs gen-heygen-scenes-set.py:
  - 1152x2048 vertical (exact 9:16, /32) instead of 1024x1024 square
  - outputs to ./mary-ugc-set/ (does not collide with the existing 20 files)
  - writes a <slug>.prompt.txt sidecar next to every <slug>.jpg
  - HeyGen-fit clause added to every prompt (face to camera, eyes open,
    mouth closed/neutral, hands away from face) for clean lip-sync
  - batch-resilient: a failed/moderated shot is logged and skipped, the
    batch continues, and a summary is printed at the end

Run:
  source ~/.claude/secrets.env
  python3 gen-mary-ugc-set.py
  python3 gen-mary-ugc-set.py --only mary-ugc-01-sofa-window-left
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
OUT_DIR = PROJECT_DIR / "mary-ugc-set"
WIDTH, HEIGHT = 1152, 2048  # exact 9:16, multiple of 32, ~2.36 MP

# --- Reference images (identity lock) --------------------------------------
REF_1 = PROJECT_DIR / "generation-5706d2ba-6bd8-4c82-b615-6b15eb8a843d.png"
REF_2 = PROJECT_DIR / "generation-844dcc55-58ee-4f1c-9fe7-4bbe3d68e3b8.png"

for r in (REF_1, REF_2):
    if not r.exists():
        sys.exit(f"reference image missing: {r}")

REF_1_B64 = base64.b64encode(REF_1.read_bytes()).decode("ascii")
REF_2_B64 = base64.b64encode(REF_2.read_bytes()).decode("ascii")

# --- Subject identity (verbatim from gen-heygen-scenes-set.py) -------------
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

# --- HeyGen-fit clause (added to EVERY prompt for clean lip-sync) ----------
HEYGEN_FIT = (
    "She faces the camera directly or at only a very slight angle, eyes open "
    "looking into the lens, mouth closed or barely parted in a relaxed "
    "neutral resting expression — not mid-word, not laughing, no visible "
    "teeth, no big smile. Both hands kept low or out of frame, away from her "
    "face and mouth. No hair falling across the face, no glare or reflection "
    "hiding the eyes behind the glasses. She is the only person in frame, "
    "nothing covering or cropping her head, comfortable headroom above her."
)

# --- Production / camera direction (UGC tier — vertical 9:16) --------------
# Same as gen-heygen-scenes-set.py except the final composition sentence is
# vertical 9:16 instead of square 1024x1024.
CAMERA_UGC = (
    "Shot on a smartphone (iPhone 15 Pro) or a compact mirrorless camera in "
    "natural ambient light. NOT a medium-format studio camera, NOT polished, "
    "NOT magazine-glossy, NOT editorial fashion photography. Phone-shot "
    "user-generated-content quality with natural light only — the kind of "
    "video frame a real woman would actually shoot of herself for an "
    "Instagram Reel or a Facebook story. Slight, natural sensor noise. "
    "Imperfect handheld framing. Real ambient color cast from the room (warm "
    "incandescent lamps, cool daylight from windows, no color correction). "
    "Vertical 9:16 portrait composition, she is centered with comfortable "
    "headroom, head and upper body clearly the focus."
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
        + HEYGEN_FIT
        + " "
        + CAMERA_UGC
        + ANTI_STAGED
        + ANTI_AI_TAIL
    )


# --- The 10 shots ----------------------------------------------------------
# 6 living-room-sofa (scene-05 family), 2 home-office-desk (scene-08 family),
# 2 fresh casual. Every expression is neutral / mouth-closed for HeyGen.
SHOTS = [
    {
        "label": "mary-ugc-01-sofa-window-left",
        "prompt": build(
            "Setting: her own living room — she is seated on a neutral linen "
            "or oat-colored sofa, a textured throw blanket draped behind her, "
            "soft morning light from a window to camera-left, a coffee table "
            "edge just visible at the bottom of the frame. Pose: mid-shot "
            "seated, leaning very slightly forward toward the camera, one "
            "elbow resting on the sofa arm. Expression: calm and neutral, "
            "mouth closed, a soft relaxed resting look, head level or tilted "
            "a hair to one side. Framing: vertical mid-shot from the waist "
            "up, eye-level."
        ),
    },
    {
        "label": "mary-ugc-02-sofa-afternoon-right",
        "prompt": build(
            "Setting: her own living room — she is seated back into a neutral "
            "linen sofa, a woven throw blanket draped across the back, warm "
            "late-afternoon light coming from a window to camera-right, light "
            "wood flooring edge visible at the bottom. Pose: mid-shot seated, "
            "back against the sofa, shoulders relaxed, hands resting in her "
            "lap. Expression: present and neutral, mouth closed with lips at "
            "rest, a calm warm gaze directly at the camera. Framing: vertical "
            "mid-shot from the waist up, eye-level."
        ),
    },
    {
        "label": "mary-ugc-03-sofa-overcast-soft",
        "prompt": build(
            "Setting: her own living room — she is seated on a cream or soft "
            "oat-colored sofa, a chunky knit throw blanket draped over one "
            "arm of the sofa, flat soft overcast daylight diffusing through "
            "the room, the corner of a bookshelf just out of focus at the "
            "top edge. Pose: mid-shot seated, body angled very slightly to "
            "camera-left, one hand resting on the blanket. Expression: "
            "composed and neutral, mouth closed or barely parted at rest, "
            "relaxed eyes on the camera. Framing: vertical mid-shot from the "
            "waist up, eye-level, slight room above the head."
        ),
    },
    {
        "label": "mary-ugc-04-sofa-side-glow",
        "prompt": build(
            "Setting: her own living room — seated on a taupe or oat linen "
            "sofa, a textured throw folded on the back of the sofa, soft warm "
            "light from a window to camera-left raking gently across her face "
            "and hair, the edge of a side table just visible at frame-left. "
            "Pose: mid-shot seated, leaning slightly forward with forearms on "
            "her knees, body centered, head held level. Expression: neutral "
            "and attentive, mouth closed at rest, eyes softly on the camera. "
            "Framing: vertical mid-shot from the upper thigh up, eye-level."
        ),
    },
    {
        "label": "mary-ugc-05-sofa-morning-ritual",
        "prompt": build(
            "Setting: her own living room — she is seated on a light neutral "
            "sofa, a soft-colored throw blanket loosely draped behind her, a "
            "coffee mug and a small notebook resting on a low table nearby, "
            "soft diffused morning light, a wall and bookshelf faint behind "
            "her. Pose: mid-shot seated, relaxed posture, one hand resting on "
            "the arm of the sofa, upper body squared to the camera. "
            "Expression: grounded and neutral, mouth closed, a calm steady "
            "presence, gentle eyes on the camera. Framing: vertical mid-shot "
            "from the waist up, eye-level, slight negative space at the top."
        ),
    },
    {
        "label": "mary-ugc-06-sofa-golden-warm",
        "prompt": build(
            "Setting: her own living room — she is seated on a warm oat or "
            "taupe linen sofa, a textured throw blanket draped over the back, "
            "warm golden-hour light from a window to camera-right giving the "
            "room soft warm tones, a lamp and a plant softly out of focus "
            "behind her. Pose: mid-shot seated, angled slightly to "
            "camera-right, body relaxed against the sofa, hands resting "
            "naturally. Expression: peaceful and neutral, mouth at rest "
            "closed, a warm soft look at the camera. Framing: vertical "
            "mid-shot from the waist up, eye-level."
        ),
    },
    {
        "label": "mary-ugc-07-desk-warm-lamp",
        "prompt": build(
            "Setting: her own home office — a warm-wood or oak desk, a shelf "
            "of books and a small ceramic mug visible behind her in soft "
            "focus, a desk lamp providing warm interior light, soft daylight "
            "from a window adding fill. Pose: chest-up seated at the desk, "
            "body angled very slightly off-axis, one hand resting on the desk "
            "surface near a notebook, the other relaxed in her lap. "
            "Expression: engaged but neutral, mouth closed or barely parted, "
            "eyebrows at rest, an attentive gaze directly at the camera. "
            "Framing: vertical chest-up seated, eye-level."
        ),
    },
    {
        "label": "mary-ugc-08-desk-window-daylight",
        "prompt": build(
            "Setting: her own home office — a warm-wood desk with a water "
            "glass and a pen holder, a framed photo on the edge, a window "
            "behind her giving soft diffused daylight, a shelf with books and "
            "a plant softly out of focus. Pose: chest-up seated at the desk, "
            "body squared to the camera, one hand resting on the desk, the "
            "other at rest in her lap, head level. Expression: present and "
            "neutral, mouth closed, a calm steady gaze at the camera, "
            "professional but warm. Framing: vertical chest-up seated, "
            "eye-level, slight negative space above the head."
        ),
    },
    {
        "label": "mary-ugc-09-sunroom-plants",
        "prompt": build(
            "Setting: her own bright sunroom — she is seated in a comfortable "
            "upholstered armchair or a cushioned window seat, potted plants "
            "and greenery on shelves and sills behind her, soft diffused "
            "natural light flooding in from several windows, light wood trim "
            "visible. Pose: mid-shot seated, body relaxed into the chair, one "
            "arm resting on the armrest, upper body facing the camera. "
            "Expression: serene and neutral, mouth closed at rest, a soft "
            "warm gaze at the camera. Framing: vertical mid-shot from the "
            "waist up, eye-level, greenery soft in the background."
        ),
    },
    {
        "label": "mary-ugc-10-reading-nook-armchair",
        "prompt": build(
            "Setting: her own cozy reading nook — she is seated in a "
            "warm-colored upholstered armchair, a soft blanket folded over "
            "the armrest beside her, a small side table with a book and a "
            "warm cup, soft warm natural light from a nearby window, neutral "
            "walls with minimal decor. Pose: mid-shot seated deep in the "
            "armchair, body relaxed and comfortable, one hand near the "
            "armrest, shoulders at ease. Expression: contemplative and "
            "neutral, mouth closed, soft eyes looking directly at the "
            "camera. Framing: vertical mid-shot from the waist up, eye-level."
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
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


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
                raise RuntimeError(f"Ready but no sample: {data}")
            return sample
        if s in ("Error", "Failed", "Request Moderated", "Content Moderated"):
            raise RuntimeError(f"status={s}: {data}")
        print(f"  [{label}] status={s} -- polling...")
        time.sleep(2)
    raise RuntimeError("timed out after 300s")


def download(url, out):
    with urllib.request.urlopen(url, timeout=60) as r:
        out.write_bytes(r.read())
    print(f"  -> wrote {out.name} ({out.stat().st_size // 1024} KB)")


def gen(shot):
    """Generate one shot. Returns True on success, False on failure."""
    label = shot["label"]
    out = OUT_DIR / f"{label}.jpg"
    txt = OUT_DIR / f"{label}.prompt.txt"
    print(f"[{label}] {ENDPOINT} {WIDTH}x{HEIGHT}")
    try:
        payload = {
            "prompt": shot["prompt"],
            "input_image": REF_1_B64,
            "input_image_2": REF_2_B64,
            "width": WIDTH,
            "height": HEIGHT,
        }
        resp = post_json(ENDPOINT, payload)
        sample = poll(resp.get("polling_url", ""), resp["id"], label)
        download(sample, out)
        txt.write_text(shot["prompt"])
        print(f"  -> wrote {txt.name}")
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, KeyError) as e:
        detail = e
        if isinstance(e, urllib.error.HTTPError):
            detail = f"{e.code}: {e.read().decode(errors='replace')[:300]}"
        print(f"  [ERROR] {label}: {detail}")
        print(f"  Skipping {label}. Re-run with --only {label} to retry.")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. 'mary-ugc-01-sofa-window-left'")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [s for s in SHOTS if (args.only is None or s["label"] == args.only)]
    if not targets:
        sys.exit(
            f"no match for label '{args.only}'. Available: "
            + ", ".join(s["label"] for s in SHOTS)
        )
    ok = 0
    failed = []
    for s in targets:
        if gen(s):
            ok += 1
        else:
            failed.append(s["label"])
    print(
        f"\nDone. {len(targets)} requested, {ok} succeeded, "
        f"{len(failed)} failed/moderated. Output: {OUT_DIR}"
    )
    if failed:
        print("Failed: " + ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
