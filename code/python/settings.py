"""Tunable numeric constants for the filter/matching pipeline, loaded
from data/settings.json so they can be changed without touching code.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = _REPO_ROOT / "data" / "settings.json"

with open(SETTINGS_PATH, encoding="utf-8") as _f:
    _settings = json.load(_f)

DILATE_KSIZE: int = _settings["dilate_ksize"]
ERODE_KSIZE: int = _settings["erode_ksize"]

LINE_HALF_LEN: int = _settings["line_half_len"]
BOX_KERNEL_VERTICAL: tuple[int, int] = tuple(_settings["box_kernel_vertical"])
BOX_KERNEL_HORIZONTAL: tuple[int, int] = tuple(_settings["box_kernel_horizontal"])
LINE_ITERATIONS: int = _settings["line_iterations"]

RESAMPLE_LENGTH: int = _settings["resample_length"]

PEAK_GROUP_GAP: int = _settings["peak_group_gap"]
PEAK_MAX_WIDTH: int = _settings["peak_max_width"]
PEAK_MATCH_TOLERANCE: int = _settings["peak_match_tolerance"]

MATCH_THRESHOLD: float = _settings["match_threshold"]
