"""Turns code/python's array-in/array-out filter functions into
API-friendly, JSON/PNG-serializable results. No classification math
lives here — it's a thin adapter, same principle as code/python itself:
one place that knows the math, everything else just calls it.

Computes **both** the horizontal-line and vertical-line profiles for
every page, always — unlike code/python/classify.py's single-image CLI,
which only computes whichever orientation each key has enabled. Here
both are always shown, and the level/orientation is chosen explicitly
per key instead of guessed.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

import sys

# The math (filters.py, peaks.py) lives in code/python/ — one copy, shared
# between the command-line classify.py and this web demo.
_CODE_PYTHON = Path(__file__).resolve().parents[3] / "code" / "python"
if str(_CODE_PYTHON) not in sys.path:
    sys.path.insert(0, str(_CODE_PYTHON))

from filters import background_residual, line_filtered, profile_from_filtered, resample_profile  # noqa: E402
from peaks import extract_sharp_peak_positions, peak_set_mismatch_score  # noqa: E402

DEFAULT_LEVEL = 0.6
DEFAULT_MATCH_THRESHOLD = 4.0
CHART_DOWNSAMPLE = 300  # points sent to the frontend for the profile chart


def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Could not decode image — is this a valid image file?")
    return image


def to_png_data_url(image: np.ndarray, max_width: int = 420) -> str:
    """Normalize an array to uint8 grayscale, downscale for the browser,
    and return it as a data: URL the frontend can drop straight into
    an <img src=...>."""
    arr = image.astype(np.float64)
    lo, hi = arr.min(), arr.max()
    normed = np.zeros_like(arr) if hi <= lo else (arr - lo) / (hi - lo) * 255
    normed = normed.astype(np.uint8)

    h, w = normed.shape
    if w > max_width:
        scale = max_width / w
        normed = cv2.resize(normed, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)

    ok, buf = cv2.imencode(".png", normed)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _downsample(values: np.ndarray, n: int = CHART_DOWNSAMPLE) -> list[float]:
    if len(values) <= n:
        return [round(float(v), 4) for v in values]
    idx = np.linspace(0, len(values) - 1, n).astype(int)
    return [round(float(values[i]), 4) for i in idx]


@dataclass
class DualProfile:
    """Both orientations' 1D profile for one page, resampled to a fixed
    length so different pages are directly comparable, plus the
    downsampled arrays used for charting."""

    resampled_h: np.ndarray = field(repr=False, compare=False)
    resampled_v: np.ndarray = field(repr=False, compare=False)
    chart_h: list[float]
    chart_v: list[float]


def compute_dual_profile(image: np.ndarray, resample_length: int = 3000) -> DualProfile:
    residual = background_residual(image)
    profile_h = resample_profile(profile_from_filtered(line_filtered(residual, "horizontal"), "horizontal"), resample_length)
    profile_v = resample_profile(profile_from_filtered(line_filtered(residual, "vertical"), "vertical"), resample_length)
    return DualProfile(
        resampled_h=profile_h,
        resampled_v=profile_v,
        chart_h=_downsample(profile_h),
        chart_v=_downsample(profile_v),
    )


def _peak_chart_positions(resampled: np.ndarray, chart_len: int, level: float) -> list[int]:
    if level <= 0:
        return []
    peaks_full = extract_sharp_peak_positions(resampled, level)
    scale = (chart_len - 1) / (len(resampled) - 1) if len(resampled) > 1 else 0
    return sorted({round(p * scale) for p in peaks_full})


@dataclass
class PageAnalysis:
    filename: str
    background_png: str
    filtered_h_png: str
    filtered_v_png: str
    profile: DualProfile = field(repr=False, compare=False)
    peaks_h: list[int]
    peaks_v: list[int]


def analyze_page(image: np.ndarray, filename: str, level_h: float = DEFAULT_LEVEL, level_v: float = DEFAULT_LEVEL) -> PageAnalysis:
    """Run the full dual-orientation pipeline on one page: background
    estimate (shared), horizontal- and vertical-line-isolated residuals,
    both 1D profiles, and detected peaks for each (using the given
    per-orientation sensitivity levels)."""
    residual = background_residual(image)
    filtered_h = line_filtered(residual, "horizontal")
    filtered_v = line_filtered(residual, "vertical")

    profile_h = resample_profile(profile_from_filtered(filtered_h, "horizontal"))
    profile_v = resample_profile(profile_from_filtered(filtered_v, "vertical"))
    chart_h = _downsample(profile_h)
    chart_v = _downsample(profile_v)

    return PageAnalysis(
        filename=filename,
        background_png=to_png_data_url(residual),
        filtered_h_png=to_png_data_url(filtered_h),
        filtered_v_png=to_png_data_url(filtered_v),
        profile=DualProfile(resampled_h=profile_h, resampled_v=profile_v, chart_h=chart_h, chart_v=chart_v),
        peaks_h=_peak_chart_positions(profile_h, len(chart_h), level_h),
        peaks_v=_peak_chart_positions(profile_v, len(chart_v), level_v),
    )


def _orientation_score(profile_a: np.ndarray, profile_b: np.ndarray, level: float) -> float | None:
    if level <= 0:
        return None
    score_forward = peak_set_mismatch_score(profile_a, profile_b, level)
    score_reversed = peak_set_mismatch_score(profile_a[::-1], profile_b, level)
    return float(min(score_forward, score_reversed))


def compare_pages(
    image_a: np.ndarray,
    name_a: str,
    image_b: np.ndarray,
    name_b: str,
    level_h: float = DEFAULT_LEVEL,
    level_v: float = DEFAULT_LEVEL,
) -> dict:
    analysis_a = analyze_page(image_a, name_a, level_h, level_v)
    analysis_b = analyze_page(image_b, name_b, level_h, level_v)

    score_h = _orientation_score(analysis_a.profile.resampled_h, analysis_b.profile.resampled_h, level_h)
    score_v = _orientation_score(analysis_a.profile.resampled_v, analysis_b.profile.resampled_v, level_v)

    return {
        "image_a": _drop_internal(analysis_a),
        "image_b": _drop_internal(analysis_b),
        "level_h": level_h,
        "level_v": level_v,
        "score_h": score_h,
        "score_v": score_v,
        "threshold": DEFAULT_MATCH_THRESHOLD,
    }


def _drop_internal(analysis: PageAnalysis) -> dict:
    return {
        "filename": analysis.filename,
        "background_png": analysis.background_png,
        "filtered_h_png": analysis.filtered_h_png,
        "filtered_v_png": analysis.filtered_v_png,
        "profile_h": analysis.profile.chart_h,
        "profile_v": analysis.profile.chart_v,
        "peaks_h": analysis.peaks_h,
        "peaks_v": analysis.peaks_v,
    }
