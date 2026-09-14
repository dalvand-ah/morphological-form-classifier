// Thin wrapper around the backend's REST API (see backend/main.py).
// Every function here maps 1:1 to one endpoint; no logic lives here.

const BASE = '/api'

async function asJson(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      // ignore, use statusText
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function fetchPool() {
  const res = await fetch(`${BASE}/pool`)
  return asJson(res)
}

export async function fetchRandomGallery(n = 20) {
  const res = await fetch(`${BASE}/gallery/random?n=${n}`)
  return asJson(res)
}

// imageA / imageB: { file } (an uploaded File), { keyId }, or { galleryId }.
export async function comparePages({ imageA, imageB, levelH, levelV }) {
  const form = new FormData()

  if (imageA.file) form.append('image_a', imageA.file)
  else if (imageA.keyId) form.append('image_a_key_id', imageA.keyId)
  else if (imageA.galleryId) form.append('image_a_gallery_id', imageA.galleryId)

  if (imageB.file) form.append('image_b', imageB.file)
  else if (imageB.keyId) form.append('image_b_key_id', imageB.keyId)
  else if (imageB.galleryId) form.append('image_b_gallery_id', imageB.galleryId)

  form.append('level_h', String(levelH))
  form.append('level_v', String(levelV))

  const res = await fetch(`${BASE}/compare`, { method: 'POST', body: form })
  return asJson(res)
}
