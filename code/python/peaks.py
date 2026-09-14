"""Find the sharp peaks in a line profile, and compare two peak sets.

A profile from filters.py has a handful of sharp spikes where a ruled
line crossed it. Two pages with the same form layout should have spikes
at (roughly) the same positions, even with small scan/scale jitter.
"""
from __future__ import annotations

import numpy as np

from settings import PEAK_GROUP_GAP, PEAK_MATCH_TOLERANCE, PEAK_MAX_WIDTH


def group_adjacent_indices(indices: np.ndarray, gap: int = PEAK_GROUP_GAP) -> list[np.ndarray]:
    """Group indices that are within `gap` samples of their neighbor,
    e.g. [10, 11, 12, 40, 41] with gap=5 -> [[10,11,12], [40,41]]."""
    groups: list[list[int]] = []
    current: list[int] = []
    for idx in indices:
        if not current or idx - current[-1] < gap:
            current.append(idx)
        else:
            groups.append(current)
            current = [idx]
    if current:
        groups.append(current)
    return [np.array(g) for g in groups]


def keep_sharp_peaks(groups: list[np.ndarray], max_width: int = PEAK_MAX_WIDTH) -> list[np.ndarray]:
    """Keep only groups narrower than `max_width` samples. A real ruled
    line gives a narrow spike; wide/blurry regions are noise."""
    return [g for g in groups if g[-1] - g[0] < max_width]


def extract_sharp_peak_positions(
    profile: np.ndarray, level: float, group_gap: int = PEAK_GROUP_GAP, max_width: int = PEAK_MAX_WIDTH
) -> list[int]:
    """Threshold `profile` at `level`, group the crossings into peaks,
    keep the sharp ones, and return each peak's mean position."""
    above = np.where(profile > level)[0]
    groups = group_adjacent_indices(above, gap=group_gap)
    sharp = keep_sharp_peaks(groups, max_width=max_width)
    return [int(g.mean()) for g in sharp]


def peak_set_mismatch_score(
    profile_a: np.ndarray, profile_b: np.ndarray, level: float, match_tolerance: int = PEAK_MATCH_TOLERANCE
) -> float:
    """Compare two profiles by their peak positions: each peak in
    profile_a is greedily matched to the closest unmatched peak in
    profile_b within `match_tolerance` samples. The score is the number
    of peaks left unmatched on both sides — 0 means every peak lined up,
    higher means the pages likely have a different layout."""
    peaks_a = extract_sharp_peak_positions(profile_a, level)
    peaks_b = extract_sharp_peak_positions(profile_b, level)

    matched_a = [False] * len(peaks_a)
    matched_b = [False] * len(peaks_b)
    for i, pa in enumerate(peaks_a):
        for j, pb in enumerate(peaks_b):
            if matched_b[j]:
                continue
            if abs(pa - pb) < match_tolerance:
                matched_a[i] = matched_b[j] = True

    return float(matched_a.count(False) + matched_b.count(False))
