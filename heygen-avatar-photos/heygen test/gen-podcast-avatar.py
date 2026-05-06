#!/usr/bin/env python3
"""
Generate 10 identity-locked portraits of the same woman (late-20s brunette
podcast host) for HeyGen Photo Avatar training.

Uses Flux 2 Pro with `input_image` (the MHIH hoodie reference) for identity
preservation, varying head pose and expression across the set.

Run:
  source ~/.claude/secrets.env
  python3 "/Users/zacharypoll/Desktop/heygen test/gen-podcast-avatar.py"
  python3 "/Users/zacharypoll/Desktop/heygen test/gen-podcast-avatar.py" --only 03-frontal-open-smile
  python3 "/Users/zacharypoll/Desktop/heygen test/gen-podcast-avatar.py" --only 09-laughing --wardrobe softer
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
OUT_DIR = Path("/Users/zacharypoll/Desktop/heygen test")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1024, 1024

# --- Reference image (identity lock) ---------------------------------------
REF = Path(
    "/Users/zacharypoll/Desktop/Documents/Claude Code/MHIH/"
    "Photos of people wearing them/cleaned/"
    "5cd29e3c-8595-4d8d-abc3-cf625b6fc740.png"
)
if not REF.exists():
    sys.exit(f"reference image missing: {REF}")
REF_B64 = base64.b64encode(REF.read_bytes()).decode("ascii")

# --- Prompt building blocks ------------------------------------------------
SUBJECT = (
    "the exact same woman shown in the reference image: late 20s, "
    "approximately 27. Long shoulder-length wavy brunette hair, sun-warmed "
    "mid-brown with subtle natural lighter strands and a slight tousle, "
    "parted to one side, a few flyaways. Light hazel-green eyes with thick "
    "dark lashes. Defined high cheekbones, a slim straight nose, full "
    "natural lips, a strong but feminine jaw. Healthy lightly tanned skin "
    "with visible pores and faint freckles across the bridge of her nose — "
    "real, not retouched. Naturally full dark eyebrows. Minimal makeup — a "
    "wash of mascara and balm, nothing more. Match the identity, face shape, "
    "hair color, and eye color of the reference photograph exactly."
)

# Three wardrobe variants, escalating from soft → bold. Default is the bold
# one; if BFL moderates a shot, re-run with --wardrobe softer or softest.
WARDROBE_BOLD = (
    "Wearing a fitted low-cut black bodysuit with a deep sweetheart "
    "neckline that sits well below the collarbone, framing visible "
    "décolletage. Form-fitting through the bust and torso. Small gold hoop "
    "earrings. A delicate gold chain necklace resting at the décolletage."
)
WARDROBE_SOFTER = (
    "Wearing a fitted black silk wrap blouse with a deep V neckline, "
    "showing the collarbones and a hint of décolletage — editorial fashion "
    "magazine cut, tasteful. Small gold hoop earrings. A delicate gold "
    "chain necklace."
)
WARDROBE_SOFTEST = (
    "Wearing a fitted black scoop-neck ribbed top, neckline sitting just "
    "below the collarbone. Small gold hoop earrings. A delicate gold "
    "chain necklace."
)
WARDROBES = {
    "bold": WARDROBE_BOLD,
    "softer": WARDROBE_SOFTER,
    "softest": WARDROBE_SOFTEST,
}

SETTING = (
    "Seated in a modern podcast studio. Behind her: a warm dark walnut "
    "acoustic-panel wall with subtle vertical slat texture, a soft warm "
    "tungsten edge light catching her hair from behind, a hint of a "
    "bokeh-blurred amber LED accent strip, and the out-of-focus arm of a "
    "Shure SM7B microphone on a boom intruding softly into the frame. "
    "Tight head-and-shoulders portrait crop, eyes roughly on the upper "
    "third of the frame. Shallow depth of field — the panel wall is creamy "
    "out-of-focus. Square 1024x1024 composition."
)

CAMERA = (
    "Shot on a Phase One IQ4 medium format with a Schneider 80mm "
    "leaf-shutter lens, available tungsten light, no flash, no fill. Real "
    "medium-format depth of field. Desaturated editorial color grade — "
    "warm cream highlights, soft amber midtones, deep umber shadows."
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


def build(pose_and_expression: str, wardrobe_key: str) -> str:
    return (
        "A documentary editorial portrait of "
        + SUBJECT
        + " "
        + WARDROBES[wardrobe_key]
        + " "
        + pose_and_expression
        + " "
        + SETTING
        + " "
        + CAMERA
        + ANTI_AI_TAIL
    )


# --- The 10 shots (pose/expression matrix) ---------------------------------
POSES = [
    ("01-frontal-neutral",
     "Pose: head straight on to the camera, eyes looking directly at the "
     "lens, shoulders square. Expression: closed mouth, completely relaxed, "
     "no smile, calm and direct — the canonical reference frame."),
    ("02-frontal-soft-smile",
     "Pose: head straight on to the camera, eyes looking directly at the "
     "lens, shoulders square. Expression: a soft closed-mouth warm smile, "
     "eyes slightly crinkled at the corners, genuine warmth, not posed."),
    ("03-frontal-open-smile",
     "Pose: head straight on to the camera, eyes looking directly at the "
     "lens, shoulders square. Expression: an open smile with the upper "
     "teeth clearly but naturally visible, eyes crinkled with real warmth — "
     "the kind of smile that happens mid-conversation."),
    ("04-three-quarter-left",
     "Pose: head and shoulders turned approximately 30 degrees to her own "
     "left (camera sees more of the right side of her face), eyes looking "
     "back to the camera lens. Expression: a subtle closed-mouth smile, "
     "calm and engaged."),
    ("05-three-quarter-right",
     "Pose: head and shoulders turned approximately 30 degrees to her own "
     "right (camera sees more of the left side of her face), eyes looking "
     "back to the camera lens. Expression: a subtle closed-mouth smile, "
     "calm and engaged."),
    ("06-tilt-right-neutral",
     "Pose: head facing the camera, with a subtle tilt toward her own right "
     "shoulder (about 8 degrees), eyes on the lens. Expression: neutral and "
     "contemplative, closed mouth, no smile."),
    ("07-tilt-left-soft-smile",
     "Pose: head facing the camera, with a subtle tilt toward her own left "
     "shoulder (about 8 degrees), eyes on the lens. Expression: a soft "
     "closed-mouth smile, gentle and approachable."),
    ("08-speaking-mid-vowel",
     "Pose: head straight on, eyes on the lens. Expression: caught mid-word "
     "in natural speech — lips parted in an open 'ah' or 'oh' viseme, lower "
     "jaw slightly dropped, the relaxed mouth shape of someone speaking a "
     "vowel mid-sentence. Subtle and natural, NOT exaggerated, NOT a yawn, "
     "NOT a kissy face. The rest of her face is alert and engaged, eyebrows "
     "in a normal neutral position."),
    ("09-laughing",
     "Pose: head tilted very slightly back, eyes mostly to the camera but "
     "partly crinkled shut from genuine laughter, shoulders relaxed. "
     "Expression: a real, joyful laugh — open mouth, upper teeth showing "
     "naturally, deep eye crinkles. Caught at the peak of a real laugh, "
     "NOT posed, NOT a forced smile."),
    ("10-contemplative-serious",
     "Pose: head straight on, eyes drifting slightly off-camera (just past "
     "the lens, as if listening to something off to her right), shoulders "
     "square. Expression: closed mouth, thoughtful, calm, no smile, brows "
     "softly relaxed — the contemplative listening face of someone "
     "considering an idea. Serious but not stern, warm but not smiling."),
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
        return {"_http_error": e.code, "_body": body}


def poll(polling_url, request_id, label):
    """Returns sample URL on Ready, or None on Moderated. Raises on other errors."""
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


def gen(label, pose_text, wardrobe_key):
    out = OUT_DIR / f"{label}.jpg"
    print(f"[{label}] {ENDPOINT} {WIDTH}x{HEIGHT} wardrobe={wardrobe_key}")
    payload = {
        "prompt": build(pose_text, wardrobe_key),
        "input_image": REF_B64,
        "width": WIDTH,
        "height": HEIGHT,
    }
    resp = post_json(ENDPOINT, payload)
    if "_http_error" in resp:
        print(f"  [{label}] HTTP {resp['_http_error']}: {resp['_body'][:300]}")
        return False
    sample = poll(resp.get("polling_url", ""), resp["id"], label)
    if sample is None:
        return False
    download(sample, out)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. '03-frontal-open-smile'")
    ap.add_argument("--wardrobe", choices=list(WARDROBES.keys()), default="bold",
                    help="bold (default), softer, or softest. Use softer/softest "
                    "to retry shots that came back Content Moderated.")
    args = ap.parse_args()

    targets = [(l, p) for (l, p) in POSES if (args.only is None or l == args.only)]
    if not targets:
        sys.exit(f"no match for label '{args.only}'. Available: " +
                 ", ".join(l for l, _ in POSES))

    rejected = []
    for label, pose in targets:
        ok = gen(label, pose, args.wardrobe)
        if not ok:
            rejected.append(label)

    print(f"\nDone. {len(targets) - len(rejected)} / {len(targets)} succeeded.")
    if rejected:
        print(f"Moderated/failed labels: {', '.join(rejected)}")
        print("Re-run softer with, e.g.:")
        for r in rejected:
            print(f"  python3 \"{Path(__file__)}\" --only {r} --wardrobe softer")


if __name__ == "__main__":
    main()
