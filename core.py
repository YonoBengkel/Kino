"""
core.py - Otak bersama untuk Kino.

Berkas ini sengaja dipisah supaya versi terminal (chatbot_cli.py) dan versi
web (app.py) memakai persona, logika memori, dan penanganan error yang SAMA
PERSIS. Kalau persona diubah, cukup ubah di sini sekali.
"""

import json
import math
import os
import re
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Groq,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

FOLDER_PROYEK = Path(__file__).parent
FOLDER_RIWAYAT = FOLDER_PROYEK / "Riwayat"

# Ditunjuk langsung ke berkas .env di sebelah core.py. Kalau ditulis
# load_dotenv() polos, pencariannya dimulai dari folder tempat perintah
# dijalankan - sehingga menjalankan program dari folder induk akan gagal
# menemukan API key.
load_dotenv(FOLDER_PROYEK / ".env")

# ---------------------------------------------------------------------------
# 1. MODEL
# ---------------------------------------------------------------------------
# Urutan penting: yang pertama jadi default. Pilihan ini bukan tebakan -
# keempatnya diuji dengan pertanyaan film niche dan jebakan film fiktif.
# gpt-oss-120b satu-satunya yang benar di kedua soal, jadi dia yang di depan.
MODEL_TERSEDIA = {
    "openai/gpt-oss-120b": "Paling luas pengetahuan filmnya. Default.",
    "groq/compound-mini": "Punya pencarian web bawaan, fakta lebih segar.",
    "openai/gpt-oss-20b": "Lebih ringan dan cepat, tapi lebih gampang mengarang.",
    "qwen/qwen3.8-27b": "Alternatif. Pengetahuan film klasiknya paling lemah.",
}
MODEL_DEFAULT = "openai/gpt-oss-120b"

SUHU_DEFAULT = 0.7
# Bahasa Indonesia butuh kira-kira dua token per kata, jadi jawaban 300 kata
# sudah memakan sekitar 600 token. Batas 800 membuat kalimat penutup Kino
# terpotong di tengah, jadi dinaikkan.
MAKS_TOKEN_DEFAULT = 1000

# Batas jumlah pesan yang ikut dikirim ke API. Riwayat yang terus tumbuh
# bikin biaya token membengkak dan akhirnya menabrak context window.
MAKS_PESAN_DIKIRIM = 24


# ---------------------------------------------------------------------------
# 2. PERSONA
# ---------------------------------------------------------------------------
_PERSONA = """Kamu adalah Kino, seorang kurator film yang bertugas menjadi JEMBATAN.

PREMIS
Lawan bicaramu bukan orang yang buta film. Dia sudah menonton judul-judul
populer dan menikmatinya. Masalahnya cuma satu: dia tidak tahu langkah
berikutnya. Tugasmu bukan memamerkan film langka, tapi menunjukkan rute.

PROSEDUR - ikuti berurutan setiap kali merekomendasikan
1. BACA SELERA. Dari judul atau keterangan yang disebut pengguna, tentukan
   ELEMEN apa yang sebenarnya dia nikmati, bukan genrenya. Contoh elemen:
   urutan waktu yang dibolak-balik, tokoh yang tidak jelas benar-salahnya,
   kamera yang berani diam lama, naskah yang pelit bicara, dunia yang
   dibangun lewat detail latar dan bukan lewat penjelasan.
2. SEBUT ELEMENNYA. Katakan dugaanmu itu secara singkat. Ini bagian
   terpenting: pengguna harus merasa dibaca, bukan diberi daftar.
3. JEMBATANI. Rekomendasikan satu sampai tiga judul yang menaikkan level
   elemen tadi, disusun dari yang paling mudah dicerna ke yang paling
   menantang.
4. JELASKAN SAMBUNGANNYA. Untuk tiap judul, tulis satu kalimat berpola:
   "Kalau kamu suka <film asal> karena <elemen>, maka <film baru> adalah
   langkah berikutnya karena <alasan>."
5. TUTUP DENGAN SATU PERTANYAAN yang memancing pengguna mempersempit selera.

ATURAN FAKTA - ini yang paling ketat
- Jangan pernah mengarang judul, tahun, sutradara, atau nama kru.
- Kalau tidak yakin pada sebuah detail, JANGAN sebut detail itu. Membahas
  sebuah film tanpa menyebut tahunnya jauh lebih baik daripada menyebut
  tahun yang salah.
- Kalau pengguna menyebut film yang tidak kamu kenal, katakan terus terang
  dan minta petunjuk tambahan. Jangan berpura-pura tahu.

ATURAN SPOILER
- Boleh: premis lima belas menit pertama, tema, gaya penyutradaraan, alasan
  sebuah film dianggap penting.
- Tidak boleh tanpa diminta: twist, nasib akhir tokoh, isi adegan penutup,
  identitas pelaku.
- Kalau pengguna minta spoiler secara eksplisit, beri peringatan satu baris
  dulu, baru jelaskan.

GAYA
- Bahasa Indonesia yang luwes. Boleh menyapa "Sobat Sinema" sesekali, jangan
  di tiap kalimat.
- Boleh puitis saat bicara sinematografi, tapi maksimal satu kalimat puitis
  per judul. Selebihnya bicara yang jelas.
- Jangan menggurui. Tidak ada film yang "wajib" ditonton."""

_GAYA_TERMINAL = """

FORMAT KHUSUS - kamu sedang tampil di layar terminal yang sempit
- Maksimal 180 kata per jawaban. Ini batas keras.
- Jangan pakai tabel, jangan pakai heading bertingkat, jangan pakai teks tebal
  bertumpuk. Paragraf pendek dan tanda hubung untuk daftar sudah cukup."""

_GAYA_WEB = """

FORMAT KHUSUS - kamu sedang tampil di halaman web
- Maksimal 300 kata per jawaban.
- Boleh memakai heading kecil, daftar berpoin, dan teks tebal secukupnya."""


def bangun_system_prompt(mode="web"):
    """Persona sama, aturan format beda. Terminal jauh lebih sempit dari browser."""
    return _PERSONA + (_GAYA_TERMINAL if mode == "cli" else _GAYA_WEB)


# ---------------------------------------------------------------------------
# 3. KLIEN
# ---------------------------------------------------------------------------
def ambil_api_key():
    """Menerima dua nama variabel supaya berkas .env lama tetap jalan."""
    return os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")


def buat_klien():
    kunci = ambil_api_key()
    if not kunci:
        raise RuntimeError(
            "API key tidak ditemukan. Buat berkas .env di folder ini, isi dengan "
            "API_KEY=gsk_... (contohnya ada di .env.example)."
        )
    return Groq(api_key=kunci)


# ---------------------------------------------------------------------------
# 4. RIWAYAT PERCAKAPAN
# ---------------------------------------------------------------------------
# LLM tidak punya ingatan. Setiap panggilan API adalah amnesia total. Yang
# menciptakan ilusi "ingat" adalah kita mengirim ULANG seluruh transkrip
# setiap kali bertanya. Daftar di bawah inilah transkrip itu.
def riwayat_baru(mode="web"):
    return [{"role": "system", "content": bangun_system_prompt(mode)}]


def pangkas_riwayat(riwayat, maks=MAKS_PESAN_DIKIRIM):
    """
    Ambil system prompt + sejumlah pesan terakhir. System prompt tidak boleh
    ikut terbuang, karena di situlah seluruh persona Kino berada.
    """
    if len(riwayat) <= maks:
        return riwayat
    return [riwayat[0]] + riwayat[-(maks - 1):]


def pesan_terlihat(riwayat):
    """Semua pesan kecuali system prompt - ini yang ditampilkan dan disimpan."""
    return [p for p in riwayat if p["role"] != "system"]


# ---------------------------------------------------------------------------
# 5. PENANGANAN ERROR
# ---------------------------------------------------------------------------
def _durasi_ke_detik(teks):
    """Ubah '1m13.5s' atau '20s' atau '30' menjadi jumlah detik."""
    faktor = {"h": 3600, "m": 60, "s": 1, "ms": 0.001}
    total, ketemu = 0.0, False
    for jumlah, satuan in re.findall(r"(\d+(?:\.\d+)?)\s*(ms|h|m|s)?", teks.strip().lower()):
        if not jumlah:
            continue
        total += float(jumlah) * faktor.get(satuan or "s", 1)
        ketemu = True
    return total if ketemu else None


def _detik_tunggu(e):
    """Cari tahu berapa lama harus menunggu, dari header resmi atau dari teks error."""
    respons = getattr(e, "response", None)
    header = getattr(respons, "headers", None)
    if header is not None:
        for kunci in ("retry-after", "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens"):
            try:
                nilai = header.get(kunci)
            except Exception:
                nilai = None
            if nilai:
                detik = _durasi_ke_detik(str(nilai))
                if detik:
                    return detik
    cocok = re.search(r"try again in ([0-9hms.\s]+)", str(e), re.IGNORECASE)
    return _durasi_ke_detik(cocok.group(1)) if cocok else None


def analisis_error(e):
    """
    Terjemahkan error mentah menjadi (pesan untuk manusia, layak diulang, detik tunggu).

    Inti dari penanganan error: tidak semua kegagalan sama. API key salah tidak
    akan membaik walau diulang seribu kali, sementara server sibuk biasanya
    sembuh sendiri dalam beberapa detik.
    """
    if isinstance(e, AuthenticationError):
        return ("API key ditolak Groq. Periksa isi berkas .env.", False, None)
    if isinstance(e, PermissionDeniedError):
        return ("Akunmu tidak punya izin memakai model ini.", False, None)
    if isinstance(e, NotFoundError):
        return ("Model ini tidak ada di akunmu. Ganti lewat perintah /model.", False, None)
    if isinstance(e, RateLimitError):
        return ("Batas pemakaian Groq tercapai.", True, _detik_tunggu(e))
    if isinstance(e, BadRequestError):
        teks = str(e).lower()
        if "context" in teks or "too large" in teks or "maximum" in teks:
            return (
                "Percakapan sudah terlalu panjang untuk model ini. "
                "Ketik /reset untuk memulai sesi baru.",
                False,
                None,
            )
        return ("Permintaan ditolak Groq: {}".format(e), False, None)
    if isinstance(e, (APITimeoutError, APIConnectionError)):
        return ("Tidak bisa menghubungi server Groq. Periksa koneksi internet.", True, None)
    if isinstance(e, InternalServerError):
        return ("Server Groq sedang bermasalah di pihak mereka.", True, None)
    return ("Gangguan tak terduga ({}): {}".format(type(e).__name__, e), False, None)


# ---------------------------------------------------------------------------
# 6. PENGIRIMAN PESAN
# ---------------------------------------------------------------------------
def _stream_sekali(client, riwayat, model, suhu, maks_token):
    aliran = client.chat.completions.create(
        model=model,
        messages=pangkas_riwayat(riwayat),
        temperature=suhu,
        max_tokens=maks_token,
        stream=True,
    )
    for bagian in aliran:
        if not bagian.choices:
            continue
        isi = bagian.choices[0].delta.content
        if isi:
            yield isi


def kirim_pesan(
    client,
    riwayat,
    model=MODEL_DEFAULT,
    suhu=SUHU_DEFAULT,
    maks_token=MAKS_TOKEN_DEFAULT,
    maks_percobaan=3,
    batas_tunggu=60.0,
):
    """
    Generator yang menghasilkan pasangan (jenis, isi):
        ("status", str) - kabar proses, misal hitung mundur rate limit
        ("teks",   str) - potongan jawaban untuk langsung dicetak
        ("error",  str) - gagal total, jawaban tidak terbentuk

    Bentuk generator dipilih supaya CLI dan Streamlit bisa memakai fungsi yang
    sama persis, cuma beda cara menampilkannya.

    Catatan: SDK groq sendiri sudah mengulang 2 kali secara diam-diam untuk
    sebagian error. Jadi maks_percobaan=3 di sini artinya percobaan berlapis,
    bukan tepat tiga kali panggilan jaringan.
    """
    percobaan = 0
    while True:
        percobaan += 1
        ada_teks = False
        try:
            for potongan in _stream_sekali(client, riwayat, model, suhu, maks_token):
                ada_teks = True
                yield "teks", potongan
            return
        except Exception as e:
            pesan, layak_ulang, tunggu = analisis_error(e)

            # Kalau sebagian jawaban sudah terlanjur tampil, mengulang dari nol
            # akan membuat teks tercetak dua kali. Lebih baik berhenti.
            if ada_teks:
                yield "error", "Koneksi terputus di tengah jawaban. " + pesan
                return

            if not layak_ulang or percobaan >= maks_percobaan:
                yield "error", pesan
                return

            # Jeda menaik kalau server tidak memberi tahu lama tunggunya.
            if tunggu is None:
                tunggu = min(2 ** percobaan, 10)

            # Limit per menit: tunggunya hitungan detik, layak ditunggu.
            # Limit harian: tunggunya berjam-jam, menggantung program itu percuma.
            if tunggu > batas_tunggu:
                menit = int(math.ceil(tunggu / 60))
                yield "error", (
                    "{} Perlu menunggu sekitar {} menit lagi - terlalu lama untuk "
                    "ditunggu otomatis. Riwayatmu aman, simpan dengan /simpan.".format(pesan, menit)
                )
                return

            for sisa in range(int(math.ceil(tunggu)), 0, -1):
                yield "status", "{} Mencoba lagi dalam {} detik...".format(pesan, sisa)
                time.sleep(1)
            yield "status", "Mencoba lagi sekarang..."


def tanya(client, riwayat, pesan_user, **opsi):
    """
    Bungkus kirim_pesan dengan pengelolaan riwayat yang benar.

    Kalau panggilan API gagal, pesan pengguna DICABUT kembali dari riwayat.
    Tanpa ini, riwayat bisa berisi dua pesan 'user' berturut-turut tanpa
    jawaban di antaranya - struktur percakapan jadi cacat dan giliran
    berikutnya ikut kacau.

    Pembersihan diletakkan di blok finally, bukan di akhir fungsi. Alasannya:
    kalau pengguna menekan Ctrl+C di tengah jawaban, generator ini ditinggalkan
    sebelum barisnya habis. Tanpa finally, pembersihan itu tidak akan pernah
    dijalankan dan riwayat tertinggal dalam keadaan cacat.
    """
    riwayat.append({"role": "user", "content": pesan_user})
    kumpulan, gagal = [], False

    try:
        for jenis, isi in kirim_pesan(client, riwayat, **opsi):
            if jenis == "teks":
                kumpulan.append(isi)
            elif jenis == "error":
                gagal = True
            yield jenis, isi
    finally:
        if gagal or not kumpulan:
            riwayat.pop()
        else:
            # Kalau jawaban terpotong di tengah karena dibatalkan, bagian yang
            # sudah tampil tetap disimpan - pengguna sudah terlanjur membacanya.
            riwayat.append({"role": "assistant", "content": "".join(kumpulan)})


# ---------------------------------------------------------------------------
# 7. SIMPAN DAN MUAT
# ---------------------------------------------------------------------------
def simpan_riwayat(riwayat, nama=None):
    FOLDER_RIWAYAT.mkdir(exist_ok=True)
    if not nama:
        nama = "chat_kino_{:%Y%m%d_%H%M%S}.json".format(datetime.now())
    if not nama.endswith(".json"):
        nama += ".json"
    tujuan = FOLDER_RIWAYAT / nama
    tujuan.write_text(
        json.dumps(pesan_terlihat(riwayat), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return tujuan


def muat_riwayat(sumber, mode="web"):
    """
    Terima path berkas atau isi JSON langsung. System prompt SELALU dibuat ulang
    dari kode, tidak diambil dari berkas - supaya persona terbaru yang dipakai,
    bukan persona lama yang ikut tersimpan.
    """
    if isinstance(sumber, (str, Path)):
        berkas = Path(sumber)
        if not berkas.exists():
            berkas = FOLDER_RIWAYAT / Path(sumber).name
        isi = json.loads(berkas.read_text(encoding="utf-8"))
    elif isinstance(sumber, bytes):
        isi = json.loads(sumber.decode("utf-8"))
    elif isinstance(sumber, list):
        isi = sumber
    else:
        isi = json.loads(sumber)

    if not isinstance(isi, list):
        raise ValueError("Isi berkas bukan daftar pesan.")

    bersih = [
        {"role": p["role"], "content": p["content"]}
        for p in isi
        if isinstance(p, dict)
        and p.get("role") in ("user", "assistant")
        and p.get("content")
    ]
    if not bersih:
        raise ValueError("Tidak ada pesan yang bisa dipulihkan dari berkas ini.")
    return riwayat_baru(mode) + bersih


def daftar_riwayat():
    if not FOLDER_RIWAYAT.exists():
        return []
    return sorted(FOLDER_RIWAYAT.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# ---------------------------------------------------------------------------
# 8. STATISTIK
# ---------------------------------------------------------------------------
def hitung_statistik(riwayat, mulai=None):
    """Bagian yang murah: semuanya cuma hitung-hitungan, tanpa panggil API."""
    terlihat = pesan_terlihat(riwayat)
    dari_user = [p for p in terlihat if p["role"] == "user"]
    dari_kino = [p for p in terlihat if p["role"] == "assistant"]
    kata_kino = sum(len(p["content"].split()) for p in dari_kino)
    huruf = sum(len(p["content"]) for p in riwayat)

    return {
        "pesan_kamu": len(dari_user),
        "balasan_kino": len(dari_kino),
        "kata_kino": kata_kino,
        "rata_kata_balasan": round(kata_kino / len(dari_kino)) if dari_kino else 0,
        # Perkiraan kasar: satu token kira-kira empat huruf. Bukan angka resmi,
        # tapi cukup untuk merasakan kenapa percakapan panjang cepat kena limit.
        "perkiraan_token": huruf // 4,
        "durasi_menit": round((datetime.now() - mulai).total_seconds() / 60, 1) if mulai else None,
    }


_PROMPT_EKSTRAK = (
    "Berikut transkrip obrolan tentang film. Daftarkan SEMUA judul film atau "
    "serial yang disebut di dalamnya. Balas HANYA dengan JSON berbentuk "
    '{"judul": ["Judul A", "Judul B"]}. Jangan tambahkan penjelasan apa pun. '
    "Jangan mengarang judul yang tidak ada di transkrip.\n\nTRANSKRIP:\n"
)


def ekstrak_judul(client, riwayat, model=MODEL_DEFAULT):
    """
    Bagian yang mahal: "topik yang sering dibahas".

    Caranya memakai LLM kedua sebagai pengekstrak. Transkrip dikirim, balasannya
    diminta berupa JSON. Ini lebih andal daripada mencocokkan kata satu per satu,
    karena model paham mana yang judul film dan mana yang bukan.

    Dipanggil hanya saat statistik dibuka, bukan tiap pesan - supaya tidak boros.
    """
    terlihat = pesan_terlihat(riwayat)
    if not terlihat:
        return []

    transkrip = "\n".join(
        "{}: {}".format(p["role"], p["content"][:1500]) for p in terlihat[-12:]
    )
    try:
        balasan = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _PROMPT_EKSTRAK + transkrip}],
            temperature=0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        isi = json.loads(balasan.choices[0].message.content)
        judul = isi.get("judul", []) if isinstance(isi, dict) else []
    except Exception:
        # Kalau model tidak mendukung mode JSON atau jawabannya berantakan,
        # statistik dasar tetap harus bisa tampil. Gagal di sini tidak fatal.
        return []

    # Buang duplikat tanpa mengubah urutan kemunculan.
    hasil, sudah = [], set()
    for j in judul:
        j = str(j).strip()
        if j and j.lower() not in sudah:
            sudah.add(j.lower())
            hasil.append(j)
    return hasil


# ---------------------------------------------------------------------------
# 9. VERIFIKASI FAKTA LEWAT TMDB (opsional)
# ---------------------------------------------------------------------------
# LLM gemar mengarang tahun rilis dan nama sutradara dengan nada sangat yakin.
# TMDB dipakai untuk mengecek ulang fakta itu ke basis data film sungguhan.
# Kalau TMDB_API_KEY tidak diisi, seluruh fitur ini diam dan program tetap jalan.
_TMDB_URL = "https://api.themoviedb.org/3/search/movie"


def tmdb_aktif():
    return bool(os.getenv("TMDB_API_KEY"))


def cari_film(judul):
    """Kembalikan {judul, tahun, ringkasan} dari TMDB, atau None kalau tidak ketemu."""
    if not tmdb_aktif():
        return None
    try:
        import requests

        balasan = requests.get(
            _TMDB_URL,
            params={
                "api_key": os.getenv("TMDB_API_KEY"),
                "query": judul,
                "language": "id-ID",
            },
            timeout=8,
        )
        balasan.raise_for_status()
        hasil = balasan.json().get("results") or []
        if not hasil:
            return None
        film = hasil[0]
        return {
            "judul": film.get("title") or judul,
            "tahun": (film.get("release_date") or "----")[:4],
            "ringkasan": film.get("overview") or "",
        }
    except Exception:
        # Verifikasi adalah nilai tambah, bukan syarat. Gagal di sini tidak boleh
        # menjatuhkan percakapan.
        return None


def verifikasi_judul(judul_judul):
    return [f for f in (cari_film(j) for j in judul_judul) if f]
