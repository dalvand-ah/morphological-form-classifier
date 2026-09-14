"""Single-file API for the form-classification algorithm. Hand this one
file to another system/team — it has no dependency on the rest of this
repo, only numpy + opencv.

Three functions:
- add_key(image_path, ...)   register a new reference key
- remove_key(key_id)          un-register one
- classify(image_path)         check an image against every key added so far

Keys are cached in keystore/ (next to this file) as one profile.npz per
key plus a shared config.json — add_key computes each key's 1D profile
once and saves it, so classify() never has to re-read or re-filter a
key's image again, just load its cached profile and compare.

A "class" can have more than one key (e.g. two different scans of the
same real-world form) — classify() reports every class with at least
one matching key.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

KEYSTORE_DIR = Path(__file__).resolve().parent / "keystore"
CONFIG_PATH = KEYSTORE_DIR / "config.json"

# ---------------------------------------------------------------------
# Image -> 1D profile (same algorithm as code/python/filters.py)
# ---------------------------------------------------------------------


def _read_image_gray(path: str | Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"could not read image: {path}")
    return image


def _background_residual(image: np.ndarray, dilate_ksize: int = 20, erode_ksize: int = 15) -> np.ndarray:
    k_dilate = np.ones((dilate_ksize, dilate_ksize), np.uint8)
    k_erode = np.ones((erode_ksize, erode_ksize), np.uint8)
    background = cv2.erode(cv2.dilate(image, k_dilate), k_erode)
    diff = image.astype(np.uint8) - background.astype(np.uint8)
    return (diff + np.uint8(255)).astype(np.float64) / 2


def _line_filtered(residual: np.ndarray, orientation: str, line_half_len: int = 20, iterations: int = 2) -> np.ndarray:
    m = 2 * line_half_len + 1
    kernel = np.zeros((m, m), np.uint8)
    if orientation == "vertical":
        kernel[:, line_half_len] = 1
        box_kernel = (15, 5)
    else:
        kernel[line_half_len, :] = 1
        box_kernel = (5, 15)
    dilated = cv2.dilate(residual, kernel)
    return cv2.erode(dilated, np.ones(box_kernel), iterations=iterations)


def _profile_from_filtered(filtered: np.ndarray, orientation: str) -> np.ndarray:
    axis = 0 if orientation == "vertical" else 1
    return (255 - filtered).sum(axis=axis) / (255 * filtered.shape[axis])


def _resample_profile(y: np.ndarray, length: int = 3000) -> np.ndarray:
    x_common = np.linspace(0, 1, length)
    x = np.linspace(0, 1, len(y))
    return np.interp(x_common, x, y)


def _compute_profiles(image_path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """image -> (profile_h, profile_v), resampled and ready to compare."""
    image = _read_image_gray(image_path)
    residual = _background_residual(image)
    profile_h = _resample_profile(_profile_from_filtered(_line_filtered(residual, "horizontal"), "horizontal"))
    profile_v = _resample_profile(_profile_from_filtered(_line_filtered(residual, "vertical"), "vertical"))
    return profile_h, profile_v


# ---------------------------------------------------------------------
# Peak extraction + matching (same algorithm as code/python/peaks.py)
# ---------------------------------------------------------------------


def _extract_sharp_peak_positions(profile: np.ndarray, level: float, group_gap: int = 5, max_width: int = 50) -> list[int]:
    above = np.where(profile > level)[0]

    groups: list[list[int]] = []
    current: list[int] = []
    for idx in above:
        if not current or idx - current[-1] < group_gap:
            current.append(idx)
        else:
            groups.append(current)
            current = [idx]
    if current:
        groups.append(current)

    sharp = [g for g in groups if g[-1] - g[0] < max_width]
    return [int(np.mean(g)) for g in sharp]


def _peak_set_mismatch_score(profile_a: np.ndarray, profile_b: np.ndarray, level: float, match_tolerance: int = 50) -> float:
    peaks_a = _extract_sharp_peak_positions(profile_a, level)
    peaks_b = _extract_sharp_peak_positions(profile_b, level)

    matched_a = [False] * len(peaks_a)
    matched_b = [False] * len(peaks_b)
    for i, pa in enumerate(peaks_a):
        for j, pb in enumerate(peaks_b):
            if matched_b[j]:
                continue
            if abs(pa - pb) < match_tolerance:
                matched_a[i] = matched_b[j] = True

    return float(matched_a.count(False) + matched_b.count(False))


def _orientation_score(profile_a: np.ndarray, profile_b: np.ndarray, level: float) -> float:
    """Lower = more similar. Checks both the profile and its reversal,
    so a page fed in upside-down still matches."""
    forward = _peak_set_mismatch_score(profile_a, profile_b, level)
    reversed_ = _peak_set_mismatch_score(profile_a[::-1], profile_b, level)
    return min(forward, reversed_)


# ---------------------------------------------------------------------
# Keystore (add_key / remove_key state, cached on disk)
# ---------------------------------------------------------------------


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_config(config: dict) -> None:
    KEYSTORE_DIR.mkdir(exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def add_key(
    image_path: str | Path,
    key_id: str | None = None,
    cls: str | None = None,
    version: int = 1,
    use_h: bool = True,
    use_v: bool = False,
    level_h: float = 0.6,
    level_v: float = 0.6,
) -> str:
    """Register `image_path` as a new key. Computes its profile once and
    caches it in keystore/, so future classify() calls are instant for
    this key (no re-reading or re-filtering the image).

    `key_id` defaults to the image's filename (without extension).
    `cls` groups keys that are really the same real-world form scanned
    more than once — defaults to `key_id` (its own class) if not given.
    `use_h` / `use_v` choose which orientation(s) to check this key on,
    and `level_h` / `level_v` how strict each one is (see classify()).
    """
    key_id = key_id or Path(image_path).stem
    cls = cls or key_id

    profile_h, profile_v = _compute_profiles(image_path)
    KEYSTORE_DIR.mkdir(exist_ok=True)
    np.savez(KEYSTORE_DIR / f"{key_id}.npz", profile_h=profile_h, profile_v=profile_v)

    config = _load_config()
    config[key_id] = {
        "class": cls,
        "version": version,
        "use_h": use_h,
        "use_v": use_v,
        "level_h": level_h,
        "level_v": level_v,
    }
    _save_config(config)
    return key_id


def remove_key(key_id: str) -> None:
    """Un-register a key added with add_key()."""
    config = _load_config()
    config.pop(key_id, None)
    _save_config(config)

    npz_path = KEYSTORE_DIR / f"{key_id}.npz"
    if npz_path.exists():
        npz_path.unlink()


@dataclass
class Match:
    key_id: str
    cls: str
    score_h: float | None
    score_v: float | None


@dataclass
class ClassificationResult:
    is_match: bool
    classes: list[str]
    matches: list[Match]


def classify(image_path: str | Path, threshold: float = 4.0) -> ClassificationResult:
    """Compare `image_path` against every key added so far. A page can
    match more than one key; `classes` lists every class (see add_key)
    with at least one matching key."""
    profile_h, profile_v = _compute_profiles(image_path)
    config = _load_config()

    matches: list[Match] = []
    for key_id, cfg in config.items():
        with np.load(KEYSTORE_DIR / f"{key_id}.npz") as data:
            score_h = _orientation_score(profile_h, data["profile_h"], cfg["level_h"]) if cfg["use_h"] else None
            score_v = _orientation_score(profile_v, data["profile_v"], cfg["level_v"]) if cfg["use_v"] else None
        matched = (score_h is not None and score_h < threshold) or (score_v is not None and score_v < threshold)
        if matched:
            matches.append(Match(key_id=key_id, cls=cfg["class"], score_h=score_h, score_v=score_v))

    return ClassificationResult(
        is_match=bool(matches),
        classes=sorted({m.cls for m in matches}),
        matches=matches,
    )


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------

# add_key("path/to/form_a.jpg")                        # key_id = "form_a", class = "form_a"
# add_key("path/to/form_a_rescan.jpg", key_id="form_a_v2", cls="form_a")  # same class, another scan
# add_key("path/to/form_b.jpg", use_h=False, use_v=True, level_v=0.55)    # check vertical lines instead

# remove_key("form_a_v2")                               # no longer checked by classify()

# result = classify("path/to/incoming_page.jpg")
# result.is_match      # True/False
# result.classes       # e.g. ["form_a"]
# result.matches       # [Match(key_id="form_a", cls="form_a", score_h=0.0, score_v=None)]
