"""Turn a scanned page into a 1D "line profile".

Idea: a form page is mostly printed text plus a grid of ruled lines.
1. Estimate the background by opening the image (dilate then erode with
   big square kernels) and subtract it — this flattens shading and
   keeps text + lines roughly equally dark.
2. Isolate the ruled lines: dilate with a thin, long line-shaped kernel
   (this "bridges" small gaps so a broken ruled line becomes solid),
   then erode back down with a small box kernel to clean up noise.
3. Collapse the 2D result to 1D by summing along one axis. Wherever a
   ruled line was, you get a spike.

A page has both horizontal and vertical ruled lines, so every step below
takes an `orientation` ("horizontal" or "vertical") instead of being
duplicated per orientation — the two only differ in which way the line
kernel points and which axis gets summed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from settings import BOX_KERNEL_HORIZONTAL, BOX_KERNEL_VERTICAL, DILATE_KSIZE, ERODE_KSIZE, LINE_HALF_LEN, LINE_ITERATIONS, RESAMPLE_LENGTH

Orientation = Literal["horizontal", "vertical"]


def read_image_gray(path: str | Path) -> np.ndarray:
    """Read an image as grayscale. Reads the raw bytes first instead of
    calling cv2.imread directly, since cv2.imread silently fails on some
    platforms when the path has non-ASCII characters."""
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"could not read image: {path}")
    return image


def background_residual(image: np.ndarray, dilate_ksize: int = DILATE_KSIZE, erode_ksize: int = ERODE_KSIZE) -> np.ndarray:
    """Subtract an estimated background from `image`, so both text and
    ruled lines stand out evenly regardless of scan shading."""
    k_dilate = np.ones((dilate_ksize, dilate_ksize), np.uint8)
    k_erode = np.ones((erode_ksize, erode_ksize), np.uint8)
    background = cv2.erode(cv2.dilate(image, k_dilate), k_erode)
    diff = image.astype(np.uint8) - background.astype(np.uint8)
    return (diff + np.uint8(255)).astype(np.float64) / 2


def line_filtered(
    residual: np.ndarray,
    orientation: Orientation,
    line_half_len: int = LINE_HALF_LEN,
    box_kernel: tuple[int, int] | None = None,
    iterations: int = LINE_ITERATIONS,
) -> np.ndarray:
    """Isolate the ruled lines running in `orientation` from a
    background_residual result: dilate with a thin line kernel pointed
    that way, then erode back down with a small box kernel."""
    m = 2 * line_half_len + 1
    kernel = np.zeros((m, m), np.uint8)
    if orientation == "vertical":
        kernel[:, line_half_len] = 1
        box_kernel = box_kernel or BOX_KERNEL_VERTICAL
    else:
        kernel[line_half_len, :] = 1
        box_kernel = box_kernel or BOX_KERNEL_HORIZONTAL
    dilated = cv2.dilate(residual, kernel)
    return cv2.erode(dilated, np.ones(box_kernel), iterations=iterations)


def profile_from_filtered(filtered: np.ndarray, orientation: Orientation) -> np.ndarray:
    """Collapse a line_filtered result to a 1D profile: spikes where a
    ruled line running in `orientation` was found."""
    axis = 0 if orientation == "vertical" else 1
    return (255 - filtered).sum(axis=axis) / (255 * filtered.shape[axis])


def line_profile(image: np.ndarray, orientation: Orientation, **kwargs) -> np.ndarray:
    """image -> background_residual -> line_filtered -> profile, in one call."""
    filtered = line_filtered(background_residual(image), orientation, **kwargs)
    return profile_from_filtered(filtered, orientation)


def resample_profile(y: np.ndarray, length: int = RESAMPLE_LENGTH) -> np.ndarray:
    """Resample a 1D profile to a fixed length, so profiles from
    differently-sized pages can be compared point-for-point."""
    x_common = np.linspace(0, 1, length)
    x = np.linspace(0, 1, len(y))
    return np.interp(x_common, x, y)
