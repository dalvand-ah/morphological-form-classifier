"""FastAPI backend for the docclass demo app.

Doubles as a real, usable API (not just a UI backend) — every endpoint
here works fine called directly with curl/Postman/another script,
independent of the React frontend it also serves.

Run (dev, with auto-reload, from presentation/webapp/):
    uvicorn backend.main:app --reload --port 8000

`frontend/dist` (if built) is served automatically — see _frontend_dist below.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import pipeline, pool

app = FastAPI(
    title="docclass demo API",
    description="Compare scanned form pages by morphological line-profile matching.",
    version="0.2.0",
)

# Permissive CORS so the frontend can be run separately in dev (npm run dev)
# against this backend. Fine for a local demo tool; tighten if ever deployed.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ---------------------------------------------------------------- Pool browsing


class KeyInfo(BaseModel):
    id: str
    thumbnail_png: str
    level_h: float
    level_v: float
    use_h: bool
    use_v: bool
    class_id: str
    version: int
    profile_h: list[float]
    profile_v: list[float]


class PoolInfo(BaseModel):
    keys: list[KeyInfo]


@app.get("/api/pool", response_model=PoolInfo)
def get_pool():
    """The data/templates/key contents, for the "key page" picker: each
    key's default level/orientation config (or the "not configured"
    defaults for a key with no entry), its class/version grouping, and
    both profiles (downsampled, for the small preview charts)."""
    keys = []
    for path in pool.list_key_files():
        image = pipeline.decode_image(path.read_bytes())
        cfg = pool.key_config(path.stem)
        dual = pipeline.compute_dual_profile(image)
        keys.append(
            KeyInfo(
                id=path.stem,
                thumbnail_png=pipeline.to_png_data_url(image, max_width=160),
                profile_h=dual.chart_h,
                profile_v=dual.chart_v,
                level_h=cfg["level_h"],
                level_v=cfg["level_v"],
                use_h=cfg["use_h"],
                use_v=cfg["use_v"],
                class_id=cfg["class"],
                version=cfg["version"],
            )
        )
    return PoolInfo(keys=keys)


class GalleryInfo(BaseModel):
    id: str
    thumbnail_png: str


@app.get("/api/gallery/random", response_model=list[GalleryInfo])
def random_gallery_images(n: int = 20):
    """A random subset of data/templates/funsd, for the "other page"
    picker."""
    files = pool.list_gallery_files()
    chosen = random.sample(files, min(n, len(files)))
    return [
        GalleryInfo(id=p.stem, thumbnail_png=pipeline.to_png_data_url(pipeline.decode_image(p.read_bytes()), max_width=160))
        for p in chosen
    ]


# ---------------------------------------------------------------- Compare


def _resolve_image(upload: Optional[UploadFile], key_id: Optional[str], gallery_id: Optional[str], label: str):
    if upload is not None and upload.filename:
        return pipeline.decode_image(upload.file.read()), upload.filename
    if key_id:
        return pipeline.decode_image(pool.key_path(key_id).read_bytes()), f"{key_id} (key)"
    if gallery_id:
        return pipeline.decode_image(pool.gallery_path(gallery_id).read_bytes()), f"{gallery_id} (gallery)"
    raise HTTPException(422, f"{label}: provide an uploaded file, a key id, or a gallery id")


@app.post("/api/compare")
def compare(
    image_a: Optional[UploadFile] = File(None),
    image_b: Optional[UploadFile] = File(None),
    image_a_key_id: Optional[str] = Form(None),
    image_b_key_id: Optional[str] = Form(None),
    image_a_gallery_id: Optional[str] = Form(None),
    image_b_gallery_id: Optional[str] = Form(None),
    level_h: float = Form(pipeline.DEFAULT_LEVEL),
    level_v: float = Form(pipeline.DEFAULT_LEVEL),
):
    """Run both the horizontal- and vertical-line-profile pipeline on two
    pages and score how well each orientation's profile matches. Each
    image can be an upload, a key id, or a gallery id — either slot can
    be any of the three, independently."""
    arr_a, name_a = _resolve_image(image_a, image_a_key_id, image_a_gallery_id, "image_a")
    arr_b, name_b = _resolve_image(image_b, image_b_key_id, image_b_gallery_id, "image_b")
    try:
        return pipeline.compare_pages(arr_a, name_a, arr_b, name_b, level_h=level_h, level_v=level_v)
    except Exception as exc:  # pragma: no cover - surfaced to the UI as an error toast
        raise HTTPException(400, str(exc)) from exc


# --- Serve the built React frontend, if present (production / single-command mode) ---
_frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
