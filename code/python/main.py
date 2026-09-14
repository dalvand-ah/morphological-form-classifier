"""Start here. Loads the keys, picks a page to test, and reports whether
it matches any key.

Run it:
    python main.py
"""
from __future__ import annotations

import random
from pathlib import Path

from classify import classify_image
from keys import load_keys


def pick_random_test_image() -> Path:
    """A random page from the FUNSD sample pool, just so this script
    always has something to test with."""
    funsd_dir = Path(__file__).resolve().parents[2] / "data" / "templates" / "funsd"
    image_exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
    candidates = [p for p in funsd_dir.iterdir() if p.suffix.lower() in image_exts]
    return random.choice(candidates)



if __name__ == "__main__":
    keys = load_keys()
    print(f"loaded {len(keys)} key(s): {[k.key_id for k in keys]}")

    image_path = pick_random_test_image()
    # A few known examples, found by testing every FUNSD page against the keys:
    # image_path = Path("../../data/templates/funsd/92094746.png")        # matches key 92094751
    # image_path = Path("../../data/templates/key/91856041_6049.png")     # matches itself (trivial)
    # image_path = Path("../../data/templates/funsd/0012529284.png")      # close, but no match
    # image_path = Path("../../data/templates/funsd/82253362_3364.png")   # no match

    print(f"testing: {image_path.name}")
    result = classify_image(image_path, keys)

    if result.is_match:
        print(f"MATCH -> class '{result.best_class}'")
        for m in result.matches:
            print(f"  key={m.key_id}  class={m.cls}  score_h={m.score_h}  score_v={m.score_v}")
    else:
        print("no match")
