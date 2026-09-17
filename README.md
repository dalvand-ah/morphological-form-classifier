# Document Classification via Morphological Filtering

![demo](presentation/animation/demo.gif)

This project extracts structural information from scanned image data
— specifically, the horizontal and vertical lines on a page, along
with their size and position relative to one another — using
classical morphological filtering (dilation/erosion) instead of a
trained model. That information is enough to classify a scanned page
as one of a handful of known form layouts: each page is reduced to a
1D line profile, and two line profiles are compared by their peaks.

## Why morphological filtering?

Mathematical morphology began in the 1960s (Matheron and Serra, École
des Mines de Paris) as a non-statistical, set-theoretic way to study
the shape and structure of materials — no training data, no
probability, just how a shape does or doesn't fit inside another. It
grew into a standard toolkit for tasks like image segmentation and
classification. This project uses the grayscale variant — where
operations act on pixel intensity instead of a binary mask —
described here:

> S. R. Sternberg, "Grayscale morphology," *Computer Vision, Graphics,
> and Image Processing*, 35(3), 333–355, 1986.

It's tempting to see a connection to CNNs here — both slide a small
window over an image and combine local values, and *morphological
neural networks* formalize exactly that link — but a standard CNN's
actual lineage traces back to neuroscience-inspired models
(Fukushima's Neocognitron, then LeCun's CNN), not to morphology. The
kinship is conceptual, not historical.

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
  two notebooks: a tour of morphological filtering, and this project's
  algorithm walked through step by step.

## Advantages over a learning-based approach

- **Understandable** — every step is inspectable; a wrong match can be
  diagnosed, not just re-trained around.
- **Works with little data** — no training set, just a handful of
  enrolled keys.
- **No labels needed** — can group similar-looking forms together even
  unlabeled.
- **New classes are free** — add a new key any time, no retraining.

## Why I built it this way

This was a work assignment: I was given a scanned-form classification
project to build. I first looked into newer, learned approaches, but
the number of pages to process was very large, and speed mattered —
those approaches didn't meet the throughput I needed. I'd previously
read up on the theory behind morphological filters, so I decided to
try this classical method instead. It worked far better than I
expected — despite how simple it is, it performed really well for
this project.

## What's next

- [ ] A C implementation, to see the actual speed difference.
- [ ] A formal comparison against newer, ML-based methods.

---

*Organized and documented with help from Claude (Anthropic).*
