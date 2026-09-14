// A "pick one image by clicking left/right" carousel over a list of
// { id, thumbnail_png }. An optional random button (bottom-right, over
// the image) jumps to a random item — e.g. re-rolling the sample side
// without stepping through the whole list.
export default function Carousel({ label, items, selectedId, onSelect, onRandom, emptyHint }) {
  const idx = Math.max(
    0,
    items.findIndex((it) => it.id === selectedId),
  )
  const current = items[idx]

  function step(delta) {
    if (items.length === 0) return
    const next = (idx + delta + items.length) % items.length
    onSelect(items[next].id)
  }

  return (
    <div className="carousel">
      <span className="picker-label">{label}</span>

      {items.length === 0 ? (
        <div className="carousel-empty">{emptyHint || 'no images available'}</div>
      ) : (
        <div className="carousel-frame">
          <button
            type="button"
            className="carousel-arrow"
            onClick={() => step(-1)}
            disabled={items.length < 2}
            aria-label="previous"
          >
            ‹
          </button>
          <div className="carousel-image-wrap">
            {current && <img className="carousel-image" src={current.thumbnail_png} alt={current.id} />}
            {onRandom && items.length > 1 && (
              <button type="button" className="carousel-random" onClick={onRandom} title="random" aria-label="random">
                🎲
              </button>
            )}
          </div>
          <button
            type="button"
            className="carousel-arrow"
            onClick={() => step(1)}
            disabled={items.length < 2}
            aria-label="next"
          >
            ›
          </button>
        </div>
      )}

      <div className="carousel-caption">{current ? `${idx + 1} / ${items.length} — ${current.id}` : ''}</div>
    </div>
  )
}
