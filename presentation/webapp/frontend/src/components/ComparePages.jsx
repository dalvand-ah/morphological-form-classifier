import { useEffect, useMemo, useState } from 'react'
import { comparePages, fetchPool, fetchRandomGallery } from '../api'
import Carousel from './Carousel'
import ProfileChart from './ProfileChart'

const COLOR_A = '#2f5d50'
const COLOR_B = '#b3452f'

// One "pick a page" slot: browse the pool (Carousel) by default, or
// switch to a local file from your own computer instead.
function ImagePicker({ label, items, selectedId, onSelect, onRandom, emptyHint, file, onFileChange }) {
  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl])

  if (file) {
    return (
      <div className="picker">
        <span className="picker-label">{label}</span>
        <img className="preview-thumb" src={previewUrl} alt={file.name} />
        <div className="carousel-caption">{file.name}</div>
        <button type="button" className="link-button" onClick={() => onFileChange(null)}>
          use a pool image instead
        </button>
      </div>
    )
  }

  return (
    <div className="picker">
      <Carousel
        label={label}
        items={items}
        selectedId={selectedId}
        onSelect={onSelect}
        onRandom={onRandom}
        emptyHint={emptyHint}
      />
      <label className="file-input">
        or upload your own:{' '}
        <input type="file" accept="image/*" onChange={(e) => onFileChange(e.target.files?.[0] || null)} />
      </label>
    </div>
  )
}

export default function ComparePages() {
  const [keys, setKeys] = useState([])
  const [gallery, setGallery] = useState([])
  const [keyId, setKeyId] = useState(null)
  const [galleryId, setGalleryId] = useState(null)
  const [keyFile, setKeyFile] = useState(null)
  const [galleryFile, setGalleryFile] = useState(null)

  // Purely visual sliders — moving these only shifts the dashed reference
  // line already drawn on the charts. The peaks/score shown only update
  // when "Compare" is clicked again with the slider's current value.
  const [levelH, setLevelH] = useState(0.6)
  const [levelV, setLevelV] = useState(0.6)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [poolLoading, setPoolLoading] = useState(true)
  const [galleryLoading, setGalleryLoading] = useState(true)

  useEffect(() => {
    fetchPool()
      .then((pool) => {
        setKeys(pool.keys)
        if (pool.keys.length > 0) setKeyId(pool.keys[0].id)
      })
      .catch((e) => setError(String(e)))
      .finally(() => setPoolLoading(false))
    reshuffleGallery()
  }, [])

  function reshuffleGallery() {
    setGalleryLoading(true)
    fetchRandomGallery(20)
      .then((list) => {
        setGallery(list)
        if (list.length > 0) setGalleryId(list[0].id)
      })
      .catch((e) => setError(String(e)))
      .finally(() => setGalleryLoading(false))
  }

  function randomGalleryImage() {
    if (gallery.length < 2) return
    let next
    do {
      next = gallery[Math.floor(Math.random() * gallery.length)].id
    } while (next === galleryId)
    setGalleryId(next)
  }

  async function handleCompare() {
    setLoading(true)
    setError(null)
    try {
      const imageA = keyFile ? { file: keyFile } : { keyId }
      const imageB = galleryFile ? { file: galleryFile } : { galleryId }
      const res = await comparePages({ imageA, imageB, levelH, levelV })
      setResult(res)
    } catch (e) {
      setError(String(e))
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const canRun = !!(keyFile || keyId) && !!(galleryFile || galleryId)

  return (
    <div>
      <div className="card">
        <h2>Pick two pages</h2>
        <p className="card-hint">
          One side browses the key (template) forms, the other a random pull from the FUNSD gallery. Use the arrows
          to flip through each, or upload your own image instead.
        </p>
        {poolLoading || galleryLoading ? (
          <div className="loading-block">
            <span className="spinner" /> Loading pages…
          </div>
        ) : (
          <div className="picker-row">
            <ImagePicker
              label="Key page"
              items={keys}
              selectedId={keyId}
              onSelect={setKeyId}
              emptyHint="no key images in data/templates/key"
              file={keyFile}
              onFileChange={setKeyFile}
            />
            <ImagePicker
              label="Gallery page"
              items={gallery}
              selectedId={galleryId}
              onSelect={setGalleryId}
              onRandom={randomGalleryImage}
              emptyHint="no gallery images in data/templates/funsd"
              file={galleryFile}
              onFileChange={setGalleryFile}
            />
          </div>
        )}

        <div className="controls-row">
          <button className="primary-button" onClick={handleCompare} disabled={!canRun || loading}>
            {loading ? 'Comparing…' : 'Compare'}
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div className="compare-grid">
            {[result.image_a, result.image_b].map((img, idx) => (
              <div className="page-analysis" key={idx}>
                <h3>{img.filename}</h3>
                <figure className="background-figure">
                  <img src={img.background_png} alt="estimated background" />
                  <figcaption>estimated background</figcaption>
                </figure>
                <div className="step-strip step-strip-2">
                  <figure>
                    <img src={img.filtered_h_png} alt="horizontal-line filter" />
                    <figcaption>horizontal-line filter</figcaption>
                  </figure>
                  <figure>
                    <img src={img.filtered_v_png} alt="vertical-line filter" />
                    <figcaption>vertical-line filter</figcaption>
                  </figure>
                </div>
              </div>
            ))}
          </div>

          <div className="orientation-grid">
            <div className="orientation-block">
              <h3>Horizontal-line profile</h3>
              <div className="chart-aspect">
                <ProfileChart
                  series={[
                    { data: result.image_a.profile_h, color: COLOR_A, name: result.image_a.filename },
                    { data: result.image_b.profile_h, color: COLOR_B, name: result.image_b.filename },
                  ]}
                  levelLine={levelH}
                  levelLineColor="#2f9e44"
                  height="100%"
                />
              </div>
              <div className="orientation-footer">
                <label className="slider-control">
                  Peak sensitivity (level)
                  <input
                    type="range"
                    min="0"
                    max="0.95"
                    step="0.05"
                    value={levelH}
                    onChange={(e) => setLevelH(Number(e.target.value))}
                  />
                  <span>{levelH.toFixed(2)}</span>
                </label>
                <span className="score-readout">
                  score_h: {result.score_h == null ? '—' : result.score_h.toFixed(1)}
                  {result.score_h != null && ` (threshold ${result.threshold})`}
                </span>
              </div>
            </div>

            <div className="orientation-block">
              <h3>Vertical-line profile</h3>
              <div className="chart-aspect">
                <ProfileChart
                  series={[
                    { data: result.image_a.profile_v, color: COLOR_A, name: result.image_a.filename },
                    { data: result.image_b.profile_v, color: COLOR_B, name: result.image_b.filename },
                  ]}
                  levelLine={levelV}
                  levelLineColor="#2f9e44"
                  height="100%"
                />
              </div>
              <div className="orientation-footer">
                <label className="slider-control">
                  Peak sensitivity (level)
                  <input
                    type="range"
                    min="0"
                    max="0.95"
                    step="0.05"
                    value={levelV}
                    onChange={(e) => setLevelV(Number(e.target.value))}
                  />
                  <span>{levelV.toFixed(2)}</span>
                </label>
                <span className="score-readout">
                  score_v: {result.score_v == null ? '—' : result.score_v.toFixed(1)}
                  {result.score_v != null && ` (threshold ${result.threshold})`}
                </span>
              </div>
            </div>
          </div>

          <p className="small-note">
            Moving a sensitivity slider only shifts the dashed reference line — it doesn't recompute the peaks or
            score shown above. Click Compare again to re-run with the current slider values.
          </p>
        </div>
      )}
    </div>
  )
}
