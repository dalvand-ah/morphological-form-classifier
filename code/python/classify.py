"""Classify a scanned page: which key(s) does it match, if any?

See main.py for a runnable walkthrough of loading keys and using this.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from filters import line_profile, read_image_gray, resample_profile
from keys import Key
from peaks import peak_set_mismatch_score
from settings import MATCH_THRESHOLD


@dataclass
class Match:
    key_id: str
    cls: str
    score_h: float | None
    score_v: float | None


@dataclass
class ClassificationResult:
    path: Path
    matches: list[Match]

    @property
    def is_match(self) -> bool:
        return len(self.matches) > 0

    @property
    def best_class(self) -> str | None:
        if not self.matches:
            return None
        best = min(self.matches, key=lambda m: min(s for s in (m.score_h, m.score_v) if s is not None))
        return best.cls


def _orientation_score(profile_a, profile_b, level: float) -> float:
    """Lower = more similar. Checks both the profile and its reversal,
    so a page fed in upside-down still matches."""
    forward = peak_set_mismatch_score(profile_a, profile_b, level)
    reversed_ = peak_set_mismatch_score(profile_a[::-1], profile_b, level)
    return min(forward, reversed_)


def classify_image(
    image_path: str | Path, keys: list[Key], threshold: float = MATCH_THRESHOLD
) -> ClassificationResult:
    """Compare one page image against every key, on whichever
    orientation(s) that key is configured to use (`use_h` / `use_v`).
    A page can match more than one key."""
    image = read_image_gray(image_path)
    profile_h = resample_profile(line_profile(image, "horizontal"))
    profile_v = resample_profile(line_profile(image, "vertical"))

    matches = []
    for key in keys:
        score_h = _orientation_score(profile_h, key.profile_h, key.level_h) if key.use_h else None
        score_v = _orientation_score(profile_v, key.profile_v, key.level_v) if key.use_v else None
        matched = (score_h is not None and score_h < threshold) or (score_v is not None and score_v < threshold)
        if matched:
            matches.append(Match(key_id=key.key_id, cls=key.cls, score_h=score_h, score_v=score_v))

    return ClassificationResult(path=Path(image_path), matches=matches)
