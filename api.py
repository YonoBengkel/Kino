"""
api.py - Backend API untuk Kino versi web (Next.js).

Menyediakan REST API dan streaming SSE agar frontend Next.js bisa
berkomunikasi dengan otak Kino di core.py.

Jalankan dengan:  uvicorn api:app --reload --port 8000
"""

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import core

app = FastAPI(title="Kino API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Klien dibuat sekali saat server menyala.
try:
    _klien = core.buat_klien()
except RuntimeError:
    _klien = None


def _perlu_klien():
    global _klien
    if _klien is None:
        try:
            _klien = core.buat_klien()
        except RuntimeError:
            raise HTTPException(
                status_code=500,
                detail="API key tidak ditemukan. Isi berkas .env terlebih dahulu.",
            )
    return _klien


def _bangun_riwayat(messages: list[dict]) -> list[dict]:
    """Rakit ulang riwayat lengkap dari daftar pesan klien."""
    riwayat = core.riwayat_baru("web")
    for msg in messages:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            riwayat.append({"role": msg["role"], "content": msg["content"]})
    return riwayat


# ---------------------------------------------------------------------------
# Skema permintaan
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    model: str = core.MODEL_DEFAULT
    temperature: float = core.SUHU_DEFAULT
    max_tokens: int = core.MAKS_TOKEN_DEFAULT


class StatsRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    model: str = core.MODEL_DEFAULT
    extract_titles: bool = False


class VerifyRequest(BaseModel):
    titles: list[str]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "api_key": bool(core.ambil_api_key()),
        "tmdb": core.tmdb_aktif(),
    }


@app.get("/api/models")
def get_models():
    return {
        "models": core.MODEL_TERSEDIA,
        "default": core.MODEL_DEFAULT,
        "defaults": {
            "temperature": core.SUHU_DEFAULT,
            "max_tokens": core.MAKS_TOKEN_DEFAULT,
        },
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    klien = _perlu_klien()
    riwayat = _bangun_riwayat(req.messages)

    def generate():
        for jenis, isi in core.kirim_pesan(
            klien,
            riwayat,
            model=req.model,
            suhu=req.temperature,
            maks_token=req.max_tokens,
        ):
            data = json.dumps({"type": jenis, "content": isi}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/stats")
def stats(req: StatsRequest):
    klien = _perlu_klien()
    riwayat = _bangun_riwayat(req.messages)
    s = core.hitung_statistik(riwayat)

    titles = []
    if req.extract_titles and core.pesan_terlihat(riwayat):
        titles = core.ekstrak_judul(klien, riwayat, req.model)

    return {"stats": s, "titles": titles}


@app.post("/api/verify")
def verify(req: VerifyRequest):
    if not core.tmdb_aktif():
        return {"results": [], "active": False}
    results = core.verifikasi_judul(req.titles)
    return {"results": results, "active": True}
