# Animation

A short, GIF-style teaser of the algorithm, built with
[Manim](https://www.manim.community/).

![demo](demo.gif)

## Render it yourself

```bash
pip install manim
cd presentation/animation
manim -ql --format=gif morphological_filter_demo.py MorphologicalFilterDemo
```

`-ql` renders fast, low-quality (used for `demo.gif` above). For a
sharper render: `manim -qm --format=gif ...` (slower, bigger file).
