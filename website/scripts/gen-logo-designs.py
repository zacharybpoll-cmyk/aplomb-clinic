#!/usr/bin/env python3
"""
APLOMB. — generate four logo design candidates via Flux 2 Pro.

Outputs to `aplomb.clinic/Logo Designs/`:
  01-pure-wordmark.jpg + .prompt.txt
  02-plumb-line-mark.jpg + .prompt.txt
  03-monogram-cartouche.jpg + .prompt.txt
  04-botanical-crest.jpg + .prompt.txt

Run:
  source ~/.claude/secrets.env
  python3 gen-logo-designs.py                          # all 4
  python3 gen-logo-designs.py --only 02-plumb-line-mark  # one
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

OUT_DIR = Path(__file__).resolve().parent.parent / "Logo Designs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 1024

CANDIDATES = [
    {
        "label": "01-pure-wordmark",
        "prompt": (
            "A clean editorial luxury cosmetics WORDMARK logo. The wordmark "
            "reads exactly \"Aplomb.\" — capital A, lowercase p-l-o-m-b, "
            "followed by a period — rendered in Cormorant Garamond serif "
            "typeface, italic, 500 weight, with tight kerning. The letters "
            "A-p-l-o-m-b are in deep warm ink color #1a1512; the trailing "
            "period is in deep amber #7a3d14. The wordmark sits perfectly "
            "centered on a warm bone (#efe8dc) background, with generous "
            "negative space on all sides. A single fine hairline horizontal "
            "rule in ink #1a1512 sits above and below the wordmark, far "
            "enough away to feel architectural rather than crowded. No other "
            "graphic elements, no decoration, no border, no shadow, no "
            "gradient, no glow, no embossed bevel, no 3D effect, no "
            "photographic texture. Editorial luxury skincare brand identity "
            "in the lineage of Aesop, Le Labo, The Ordinary. Clean flat "
            "vector-style graphic. The wordmark must read exactly Aplomb. "
            "with no extra letters, no missing letters, no other characters "
            "anywhere in the image. Square 1:1 format, 1024x1024."
        ),
    },
    {
        "label": "02-plumb-line-mark",
        "prompt": (
            "A premium luxury cosmetics LOGO with a small geometric mark "
            "above the wordmark. The graphic mark is a single thin vertical "
            "hairline thread in deep amber #7a3d14, exactly vertical, ending "
            "at the bottom in a small inverted-teardrop weight in the same "
            "amber — the silhouette of an architect's or surveyor's "
            "plumb-bob plummet, geometric and exact. Below the mark, "
            "separated by clean negative space, the wordmark reads exactly "
            "\"Aplomb.\" — capital A, lowercase p-l-o-m-b, period — in "
            "Cormorant Garamond serif typeface, italic, 500 weight. Letters "
            "in ink #1a1512, period in deep amber #7a3d14 matching the "
            "plumb-line mark. Background: warm bone #efe8dc. Generous "
            "negative space all around. No other graphic elements, no "
            "border, no shadow, no gradient, no glow, no 3D effect, no "
            "photographic texture, no decorative flourishes. Editorial "
            "scientific-instrument minimalism in the lineage of Le Labo and "
            "Helmut Lang. Clean flat vector-style graphic. The wordmark "
            "must read exactly Aplomb. with no extra letters or characters "
            "anywhere in the image. Square 1:1 format, 1024x1024."
        ),
    },
    {
        "label": "03-monogram-cartouche",
        "prompt": (
            "A premium luxury cosmetics MONOGRAM logo design — an "
            "apothecary-style stamp. A single italic capital letter \"A\" "
            "followed by a period — rendered in Cormorant Garamond serif "
            "typeface, italic, 500 weight — sits centered inside a thin "
            "elliptical oval cartouche border. The capital A is in ink "
            "#1a1512; the period is in deep amber #7a3d14. The oval "
            "cartouche outline is a single 1pt hairline in ink #1a1512, "
            "with no fill. Below the cartouche, separated by negative "
            "space, the full wordmark reads exactly \"Aplomb.\" in IBM Plex "
            "Sans typeface, smaller, slightly letterspaced (tracking +50), "
            "in ink #1a1512 with the period in deep amber #7a3d14. "
            "Background: warm bone #efe8dc. Generous negative space all "
            "around. No other graphic elements, no shadow, no gradient, no "
            "glow, no embossed bevel, no 3D effect, no photographic "
            "texture, no extra decoration. Editorial luxury apothecary "
            "brand mark in the lineage of Augustinus Bader, Maison "
            "Margiela, Le Labo. Clean flat vector-style graphic. The "
            "wordmark below the cartouche must read exactly Aplomb. with "
            "no extra letters or characters anywhere in the image. Square "
            "1:1 format, 1024x1024."
        ),
    },
    {
        "label": "04-botanical-crest",
        "prompt": (
            "A premium luxury cosmetics LOGO with a small botanical crest "
            "motif above the wordmark. The botanical illustration is a "
            "single sprig of olive branch — one slim curving stem with "
            "three small almond-shaped leaves arranged naturally, plus one "
            "small olive at the base — rendered as a fine warm ink linework "
            "drawing in deep ink #1a1512 with subtle deep amber #7a3d14 "
            "highlights on the leaf veins and the olive itself. The "
            "illustration is delicate, restrained, scientific-botanical, in "
            "the lineage of Beatrix Potter botanical studies and Nature "
            "magazine cover illustration. Below the botanical sprig, "
            "separated by negative space, the wordmark reads exactly "
            "\"Aplomb.\" — capital A, lowercase p-l-o-m-b, period — in "
            "Cormorant Garamond serif typeface, italic, 500 weight. Letters "
            "in ink #1a1512, period in deep amber #7a3d14. Background: "
            "warm bone #efe8dc. Generous negative space all around. No "
            "fill colors, no shading, no gradient, no shadow, no glow, no "
            "3D effect, no photographic texture — pure flat hairline ink "
            "linework only for the botanical. Editorial luxury heritage "
            "apothecary in the lineage of Diptyque, La Roche-Posay, "
            "Chantecaille. Clean flat graphic. The wordmark must read "
            "exactly Aplomb. with no extra letters or characters anywhere "
            "in the image. Square 1:1 format, 1024x1024."
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
            sys.exit(f"[{label}] status={s}: {data}")
        print(f"  [{label}] status={s} -- polling...")
        time.sleep(2)
    sys.exit(f"[{label}] timed out")


def download(url, out):
    with urllib.request.urlopen(url, timeout=60) as r:
        out.write_bytes(r.read())
    print(f"  -> wrote {out.name} ({out.stat().st_size // 1024} KB)")


def gen(c):
    img_out = OUT_DIR / f"{c['label']}.jpg"
    prompt_out = OUT_DIR / f"{c['label']}.prompt.txt"
    print(f"[{c['label']}] {ENDPOINT} {SIZE}x{SIZE}")
    prompt_out.write_text(c["prompt"])
    resp = post_json(
        ENDPOINT,
        {
            "prompt": c["prompt"],
            "width": SIZE,
            "height": SIZE,
        },
    )
    sample = poll(resp.get("polling_url", ""), resp["id"], c["label"])
    download(sample, img_out)
    return img_out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="regen one label, e.g. '02-plumb-line-mark'")
    args = ap.parse_args()

    if args.only:
        targets = [c for c in CANDIDATES if c["label"] == args.only]
    else:
        targets = CANDIDATES

    if not targets:
        sys.exit(f"no candidate matches selection. Valid labels: {[c['label'] for c in CANDIDATES]}")

    for c in targets:
        gen(c)
    print(f"\nDone. {len(targets)} image(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
