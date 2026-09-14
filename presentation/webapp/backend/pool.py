"""Reads the two local image pools the web demo lets you browse instead
of always uploading a file:
- data/templates/key    — the enrolled key/template forms
- data/templates/funsd  — a gallery of sample pages (FUNSD dataset) to
  test against the keys
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
KEYS_DIR = _REPO_ROOT / "data" / "templates" / "key"
GALLERY_DIR = _REPO_ROOT / "data" / "templates" / "funsd"
KEYS_CONFIG_PATH = KEYS_DIR / "config.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

DEFAULT_KEY_CONFIG = {"level_h": 0.0, "level_v": 0.0, "use_h": False, "use_v": False}


def _list_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def list_key_files() -> list[Path]:
    return _list_images(KEYS_DIR)


def list_gallery_files() -> list[Path]:
    return _list_images(GALLERY_DIR)


def load_keys_config() -> dict[str, dict]:
    if not KEYS_CONFIG_PATH.exists():
        return {}
    with open(KEYS_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def key_config(key_id: str) -> dict:
    """Per-key defaults (level_h, level_v, use_h, use_v, class, version).
    A key with no entry in config.json gets level 0 and both
    orientations off, so the UI can show that plainly rather than
    silently guessing."""
    cfg = load_keys_config().get(key_id) or {}
    merged = {**DEFAULT_KEY_CONFIG, **cfg}
    merged.setdefault("class", key_id)
    merged.setdefault("version", 1)
    return merged


def key_path(key_id: str) -> Path:
    for path in list_key_files():
        if path.stem == key_id:
            return path
    raise FileNotFoundError(key_id)


def gallery_path(gallery_id: str) -> Path:
    for path in list_gallery_files():
        if path.stem == gallery_id:
            return path
    raise FileNotFoundError(gallery_id)
