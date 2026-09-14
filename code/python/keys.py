"""Load the reference "keys" (data/templates/key) that pages get compared
against.

Each key is one reference form image plus a config.json entry:
- level_h / level_v: peak-detection sensitivity for each orientation
- use_h / use_v: whether that orientation is even checked for this key
- class / version: keys with the same class are just different scans of
  the same real-world form
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from filters import line_profile, read_image_gray, resample_profile

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEYS_DIR = _REPO_ROOT / "data" / "templates" / "key"

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


@dataclass
class Key:
    key_id: str
    cls: str
    version: int
    use_h: bool
    use_v: bool
    level_h: float
    level_v: float
    profile_h: np.ndarray
    profile_v: np.ndarray


def _find_image(keys_dir: Path, key_id: str) -> Path:
    for ext in IMAGE_EXTS:
        candidate = keys_dir / f"{key_id}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"no image for key '{key_id}' in {keys_dir}")


def load_keys(keys_dir: str | Path = DEFAULT_KEYS_DIR) -> list[Key]:
    """Read config.json and build a Key (with both profiles already
    computed from its image) for every entry."""
    keys_dir = Path(keys_dir)
    with open(keys_dir / "config.json", encoding="utf-8") as f:
        config = json.load(f)

    keys = []
    for key_id, cfg in config.items():
        image = read_image_gray(_find_image(keys_dir, key_id))
        keys.append(
            Key(
                key_id=key_id,
                cls=cfg.get("class", key_id),
                version=cfg.get("version", 1),
                use_h=cfg.get("use_h", False),
                use_v=cfg.get("use_v", False),
                level_h=cfg.get("level_h", 0.0),
                level_v=cfg.get("level_v", 0.0),
                profile_h=resample_profile(line_profile(image, "horizontal")),
                profile_v=resample_profile(line_profile(image, "vertical")),
            )
        )
    return keys
