"""
Manim (Community Edition) script for a short, GIF-style teaser — meant to
be converted to a looping .gif for a GitHub README / social post.

This file is CODE ONLY — nothing has been rendered here. Run it yourself
with (from this folder, so the code/python import resolves):

    pip install manim
    cd presentation/animation
    manim -ql --format=gif morphological_filter_demo.py MorphologicalFilterDemo
    # or render mp4 and convert: manim -pqh morphological_filter_demo.py MorphologicalFilterDemo

Story (mostly on-screen titles, paced to actually be readable). A single
running title at the top changes as the story moves through four beats:

  "A Scanned Form"            - the real key page appears, centered.
  "Morphological Filter"      - an "image + kernel = filtered result"
                                 equation builds (kernel icon = a square
                                 with only its middle row colored, the
                                 literal shape of the horizontal-line
                                 kernel).
  "Filtered Image to Line Profile" - a highlight bar sweeps down the
                                 filtered image while, in sync, the real
                                 horizontal-profile output draws itself as
                                 a curve: summing each row's (inverted)
                                 gray value left-to-right, so a long
                                 horizontal rule line shows up as a peak.
  "Used for classification"   - the key plus one real, unrelated page each
                                 get their own profile curve, side by
                                 side. Copies of both curves slide down to
                                 a shared chart at the bottom and merge —
                                 the two don't line up, so it ends on
                                 "No match".
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    BLUE,
    DOWN,
    GREEN,
    GREY_B,
    LEFT,
    ORANGE,
    RED,
    RIGHT,
    UP,
    YELLOW,
    Axes,
    Create,
    Cross,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    Line,
    Rectangle,
    Scene,
    Text,
    UpdateFromAlphaFunc,
    VGroup,
    ValueTracker,
    Write,
    linear,
)

# Make code/python's filters importable when this script is run from
# presentation/animation/ (as intended). No confidential data is touched —
# only the bundled, non-confidential images under data/templates/.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "code" / "python"))

from filters import (  # noqa: E402
    background_residual,
    line_filtered,
    profile_from_filtered,
    read_image_gray,
    resample_profile,
)

KEY_IMAGE_PATH = REPO_ROOT / "data" / "templates" / "key" / "92094751.png"  # the "key" / template page
# An unrelated FUNSD page -> should NOT match the key.
NOMATCH_IMAGE_PATH = REPO_ROOT / "data" / "templates" / "funsd" / "0001129658.png"

TITLE_FONT_SIZE = 38


def to_rgb_uint8(gray: np.ndarray) -> np.ndarray:
    """Min-max normalize any real-valued 2D array to a displayable uint8 RGB image."""
    g = gray.astype(np.float64)
    lo, hi = g.min(), g.max()
    g = (g - lo) / (hi - lo + 1e-9)
    g8 = (g * 255).astype(np.uint8)
    return np.stack([g8, g8, g8], axis=-1)


def kernel_icon(size: float = 1.0) -> VGroup:
    """A small square with only its middle row colored — the actual shape
    of the horizontal-line kernel in code/python/filters.py."""
    n = 5
    cell = size / n
    icon = VGroup()
    for r in range(n):
        for c in range(n):
            colored = r == n // 2
            sq = Rectangle(
                width=cell,
                height=cell,
                stroke_color=GREY_B,
                stroke_width=1,
                fill_color=YELLOW if colored else None,
                fill_opacity=0.9 if colored else 0,
            )
            sq.move_to(np.array([c * cell, -r * cell, 0]))
            icon.add(sq)
    icon.move_to(np.zeros(3))
    return icon


def real_profile(path: Path, length: int = 150) -> tuple[np.ndarray, np.ndarray]:
    """Run the real filter pipeline on a real bundled image; return
    (raw_rgb_for_display, resampled_profile) — the raw page image, not
    the filtered one, since the "Used for classification" beat is meant
    to look like real documents, not the filter's intermediate output."""
    gray = read_image_gray(path)
    residual = background_residual(gray)
    filtered = line_filtered(residual, "horizontal")
    profile = profile_from_filtered(filtered, "horizontal")
    return to_rgb_uint8(gray), resample_profile(profile, length=length)


def mini_chart(profile: np.ndarray, color, width: float, height: float) -> VGroup:
    axes = Axes(
        x_range=[0, 1, 1],
        y_range=[
            float(profile.min()),
            float(profile.max()) or 1.0,
            (float(profile.max()) - float(profile.min())) or 1.0,
        ],
        x_length=width,
        y_length=height,
        tips=False,
        axis_config={"stroke_width": 1.5, "include_ticks": False},
    )
    xs = np.linspace(0, 1, len(profile))
    curve = axes.plot_line_graph(x_values=xs, y_values=profile, line_color=color, add_vertex_dots=False)
    return VGroup(axes, curve)


def overlay_chart(p_a: np.ndarray, p_b: np.ndarray, color_a, color_b, width: float, height: float) -> VGroup:
    lo = min(p_a.min(), p_b.min())
    hi = max(p_a.max(), p_b.max())
    axes = Axes(
        x_range=[0, 1, 0.5],
        y_range=[float(lo), float(hi) or 1.0, ((float(hi) - float(lo)) / 2) or 0.5],
        x_length=width,
        y_length=height,
        tips=False,
    )
    xs = np.linspace(0, 1, len(p_a))
    curve_a = axes.plot_line_graph(x_values=xs, y_values=p_a, line_color=color_a, add_vertex_dots=False)
    curve_b = axes.plot_line_graph(x_values=xs, y_values=p_b, line_color=color_b, add_vertex_dots=False)
    return VGroup(axes, curve_a, curve_b)


class MorphologicalFilterDemo(Scene):
    def construct(self):
        # ---- Real data, computed once from the actual project code -----
        gray = read_image_gray(KEY_IMAGE_PATH)
        residual = background_residual(gray)
        filtered_h = line_filtered(residual, "horizontal")
        profile_h = profile_from_filtered(filtered_h, "horizontal")

        img_rgb = to_rgb_uint8(gray)
        filtered_rgb = to_rgb_uint8(filtered_h)

        key_profile = resample_profile(profile_h, length=150)
        nomatch_img_rgb, nomatch_profile = real_profile(NOMATCH_IMAGE_PATH, length=150)

        def swap_title(old_title, text, run_time=0.7):
            new_title = Text(text, font_size=TITLE_FONT_SIZE).to_edge(UP)
            if old_title is None:
                self.play(Write(new_title), run_time=run_time)
            else:
                self.play(FadeOut(old_title), Write(new_title), run_time=run_time)
            return new_title

        # =====================================================================
        # 1. Real key page appears centered ("A Scanned Form"), slides left,
        #    then an "image + kernel = filtered result" equation builds next
        #    to it (title switches to "Morphological Filter" as the "+"
        #    appears).
        # =====================================================================
        form_img = ImageMobject(img_rgb).scale_to_fit_height(5.2)
        self.play(FadeIn(form_img), run_time=1.0)
        title = swap_title(None, "A Scanned Form")
        self.wait(0.8)

        self.play(form_img.animate.shift(LEFT * 4.8), run_time=1.0)
        self.wait(0.2)

        plus = Text("+", font_size=46).next_to(form_img, RIGHT, buff=0.5)
        title = swap_title(title, "Morphological Filter")
        self.play(Write(plus), run_time=0.6)

        kernel = kernel_icon(size=1.4).next_to(plus, RIGHT, buff=0.5)
        kernel_label = Text("horizontal-line kernel", font_size=18, color=YELLOW)
        kernel_label.next_to(kernel, UP, buff=0.18)
        self.play(FadeIn(kernel), FadeIn(kernel_label), run_time=0.9)
        self.wait(0.5)

        equals = Text("=", font_size=46).next_to(kernel, RIGHT, buff=0.55)
        self.play(Write(equals), run_time=0.6)

        filtered_img = ImageMobject(filtered_rgb).scale_to_fit_height(5.2).next_to(equals, RIGHT, buff=0.55)
        self.play(FadeIn(filtered_img), run_time=1.0)
        self.wait(1.0)

        self.play(
            FadeOut(form_img, shift=LEFT * 1.0),
            FadeOut(plus),
            FadeOut(kernel),
            FadeOut(kernel_label),
            FadeOut(equals),
            run_time=0.8,
        )
        self.play(filtered_img.animate.move_to(LEFT * 3.9), run_time=1.0)
        self.wait(0.3)

        # =====================================================================
        # 2. Sweep the image top-to-bottom while the horizontal profile
        #    (real profile_from_filtered output) draws itself in sync —
        #    "sum the gray pixels along each row; a long horizontal rule
        #    line shows up as a peak."
        # =====================================================================
        title = swap_title(title, "Filtered Image to Line Profile")

        caption = Text("sum each row → a peak marks a horizontal line", font_size=22, color=GREY_B)
        caption.to_edge(DOWN)
        self.play(FadeIn(caption), run_time=0.6)

        axes = Axes(
            x_range=[0, 1, 0.5],
            y_range=[
                float(profile_h.min()),
                float(profile_h.max()),
                (profile_h.max() - profile_h.min()) / 2 or 0.1,
            ],
            x_length=5.0,
            y_length=5.4,
            tips=False,
        ).shift(RIGHT * 3.6 + DOWN * 0.1)
        xs = np.linspace(0, 1, len(profile_h))
        curve = axes.plot_line_graph(x_values=xs, y_values=profile_h, line_color=GREEN, add_vertex_dots=False)

        img_top = filtered_img.get_top()[1]
        img_bottom = filtered_img.get_bottom()[1]
        img_left = filtered_img.get_left()[0]
        img_right = filtered_img.get_right()[0]

        sweep = Line(
            np.array([img_left, img_top, 0]),
            np.array([img_right, img_top, 0]),
            color=BLUE,
            stroke_width=3,
        )

        t = ValueTracker(0.0)

        def update_sweep(mob, alpha):
            # alpha isn't used directly; position comes from the shared
            # ValueTracker so the sweep line and the curve stay in lockstep.
            y = img_top + t.get_value() * (img_bottom - img_top)
            mob.put_start_and_end_on(
                np.array([img_left, y, 0]),
                np.array([img_right, y, 0]),
            )

        self.play(Create(axes), run_time=0.6)
        self.add(sweep)
        self.play(
            UpdateFromAlphaFunc(sweep, update_sweep),
            t.animate.set_value(1.0),
            Create(curve["line_graph"], rate_func=linear),
            run_time=4.0,
            rate_func=linear,
        )
        self.wait(0.9)

        # Group (not VGroup): mixes ImageMobject with VMobjects.
        self.play(FadeOut(Group(filtered_img, axes, curve, caption, sweep)), run_time=0.6)

        # =====================================================================
        # 3. "Used for classification": key + one unrelated real page, each
        #    with its own profile curve, side by side. Copies of both curves
        #    slide down to a shared chart at the bottom and merge there —
        #    they don't line up, so it ends on "No match".
        # =====================================================================
        title = swap_title(title, "Used for classification")

        cols = [
            (img_rgb, key_profile, GREEN, "Document 1"),
            (nomatch_img_rgb, nomatch_profile, ORANGE, "Document 2"),
        ]
        x_positions = [-2.4, 2.4]
        chart_mobs = []
        row = VGroup()
        images = Group()
        for (img, prof, color, label), x in zip(cols, x_positions):
            # Thumbnails sit lower than a naive centered layout would put
            # them, so there's clear space between the running title
            # (top edge) and the image below it.
            thumb = ImageMobject(img).scale_to_fit_height(2.3).move_to(np.array([x, 1.5, 0]))
            chart = mini_chart(prof, color, width=3.8, height=1.6).move_to(np.array([x, -0.7, 0]))
            cap = Text(label, font_size=18, color=GREY_B).move_to(np.array([x, -1.8, 0]))
            images.add(thumb)
            row.add(chart, cap)
            chart_mobs.append(chart)

        self.play(FadeIn(images), FadeIn(row), run_time=1.2)
        self.wait(1.0)

        key_chart, nomatch_chart = chart_mobs
        target_center = np.array([0, -3.0, 0])
        combo_width, combo_height = 5.2, 1.4

        copy_a = key_chart.copy()
        copy_b = nomatch_chart.copy()
        self.play(
            copy_a.animate.move_to(target_center).stretch_to_fit_width(combo_width).stretch_to_fit_height(
                combo_height
            ),
            copy_b.animate.move_to(target_center).stretch_to_fit_width(combo_width).stretch_to_fit_height(
                combo_height
            ),
            run_time=1.3,
        )
        combined = overlay_chart(key_profile, nomatch_profile, GREEN, ORANGE, width=combo_width, height=combo_height)
        combined.move_to(target_center)
        self.play(FadeOut(copy_a), FadeOut(copy_b), FadeIn(combined), run_time=0.4)

        label = VGroup(Text("No match", font_size=26, color=RED), Cross(scale_factor=0.22, color=RED))
        label.arrange(RIGHT, buff=0.25)
        label.next_to(combined, RIGHT, buff=0.7)
        self.play(FadeIn(label), run_time=0.6)
        self.wait(1.1)
        self.play(FadeOut(combined), FadeOut(label), run_time=0.5)

        self.play(FadeOut(images), FadeOut(row), FadeOut(title), run_time=0.6)
