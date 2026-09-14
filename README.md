# Document Classification via Morphological Filtering

![demo](presentation/animation/demo.gif)

Classifies scanned form pages by layout — "is this page one of a
handful of known forms?" — using classical morphological filtering
(dilation/erosion) instead of a trained model. A page is reduced to a
1D "line profile," and two profiles are compared by their peaks.

## Why morphological filtering?

Mathematical morphology started in the 1960s (Matheron and Serra,
École des Mines de Paris) as a way to study the shape and structure of
materials using set theory, not statistics. It began as *binary*
morphology (foreground/background) and was later extended to
*grayscale* images — the "gray-style" used in this project, where
operations act directly on pixel intensity instead of a thresholded
mask. The core idea — probe an image with a small shape (a
"structuring element") and record how it fits, or doesn't — turns out
to be a direct way to isolate structure like lines and edges, with no
training involved. A short, classic reference for the grayscale
extension:

> S. R. Sternberg, "Grayscale morphology," *Computer Vision, Graphics,
> and Image Processing*, 35(3), 333–355, 1986.

It's tempting to see a connection to CNNs here — both slide a small
shape/window over an image and combine local values — and there is
real research on *morphological neural networks* that formalizes
exactly that. But a standard CNN's actual lineage is different: it
traces back to neuroscience-inspired models (Fukushima's Neocognitron,
then LeCun's CNN), not to morphology. The kinship is conceptual, not
historical.

## Project structure

- **[`code/python/`](code/python/README.md)** — the core algorithm,
  plus a standalone API for integrating it elsewhere.
- **`data/`** — the enrolled keys (`data/templates/key/`) and a gallery
  of real scanned pages (`data/templates/funsd/`) to test against, from
  the FUNSD dataset:

  > G. Jaume, H. K. Ekenel, J.-P. Thiran, "FUNSD: A Dataset for Form
  > Understanding in Noisy Scanned Documents," *ICDAR-OST*, 2019.
- **[`presentation/webapp/`](presentation/webapp/README.md)** — an
  interactive web demo.
- **[`presentation/animation/`](presentation/animation/README.md)** —
  the GIF above, and the code that made it.
- **[`presentation/notebook/`](presentation/notebook/README.md)** —
  two notebooks: the general filter theory, and this project's
  algorithm walked through step by step.

## Advantages over a learned (CNN) approach

- **Understandable** — every step is inspectable; a wrong match can be
  diagnosed, not just re-trained around.
- **Works with little data** — no training set, just a handful of
  enrolled keys.
- **No labels needed** — can group similar-looking forms together even
  unlabeled.
- **New classes are free** — add a new key any time, no retraining.

## Why I built it this way

This started as a scanned-form classification project. I first looked
at newer, learned approaches, but the number of pages was very large,
which pushed me back toward classical methods. Morphological filtering
ended up working really well — and it was a genuinely fun problem to
dig into.

## What's next

- [ ] A C implementation, to see the actual speed difference.
- [ ] A formal comparison against newer, ML-based methods.

---

*Organized and documented with help from Claude (Anthropic).*
