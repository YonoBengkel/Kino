"""
app.py - Kino versi web (Streamlit).

Ini bagian nilai tambah dari tugas. Persona, memori, dan penanganan errornya
diambil dari core.py - berkas ini hanya mengurus tampilan.

Jalankan dengan:  streamlit run app.py
"""

import json
from datetime import datetime

import streamlit as st

import core

st.set_page_config(
    page_title="Kino - Kurator Rute Sinema",
    page_icon="🎬",
    layout="centered",
)

AVATAR_KINO = "🎬"
AVATAR_KAMU = "🍿"


# ---------------------------------------------------------------------------
# Penyiapan awal
# ---------------------------------------------------------------------------
# Streamlit menjalankan ULANG seluruh berkas ini dari baris pertama setiap kali
# ada interaksi - ketik, klik, geser slider. Variabel Python biasa akan lahir
# kembali dalam keadaan kosong setiap kali itu terjadi. st.session_state adalah
# satu-satunya tempat yang selamat dari rerun, jadi di situlah riwayat disimpan.
# Versi terminal tidak butuh ini, karena prosesnya terus hidup.
if "riwayat" not in st.session_state:
    st.session_state.riwayat = core.riwayat_baru("web")
    st.session_state.mulai = datetime.now()
    st.session_state.selesai = False
    st.session_state.catatan = None
    st.session_state.tertunda = None


@st.cache_resource
def ambil_klien():
    """Klien dibuat sekali saja, tidak ikut lahir ulang setiap rerun."""
    return core.buat_klien()


try:
    klien = ambil_klien()
except RuntimeError as e:
    st.error(str(e))
    st.stop()


def catat(pesan, jenis="info"):
    st.session_state.catatan = (jenis, pesan)


# ---------------------------------------------------------------------------
# Perintah khusus - persis seperti versi terminal
# ---------------------------------------------------------------------------
BANTUAN = """
| Perintah | Arti |
|---|---|
| `/help` | Tampilkan daftar ini |
| `/reset` atau `/clear` | Kosongkan ingatan Kino |
| `/statistik` | Ringkasan sesi + film yang sudah dibahas |
| `/rute` | Minta Kino menyusun jalur tontonan bertahap |
| `/simpan` | Siapkan berkas riwayat untuk diunduh |
| `/exit` | Akhiri sesi dan tampilkan ringkasan penutup |

Untuk memuat percakapan lama, pakai tombol unggah di panel kiri.
"""


def tangani_perintah(masukan):
    """
    Pemeriksa yang berjalan SEBELUM pesan dikirim ke API.

    Tanpa fungsi ini, mengetik "exit" di kotak chat cuma dikirim ke Kino dan
    dijawab sebagai pertanyaan biasa tentang film. Inilah yang dulu hilang.
    """
    nama = masukan[1:].split(maxsplit=1)[0].lower() if len(masukan) > 1 else ""

    if nama in ("help", "bantuan", "?"):
        catat(BANTUAN)
    elif nama in ("reset", "clear", "bersih"):
        st.session_state.riwayat = core.riwayat_baru("web")
        st.session_state.mulai = datetime.now()
        catat("Ingatan Kino dikosongkan. Mulai dari nol.", "sukses")
    elif nama in ("statistik", "stats"):
        st.session_state.tampil_statistik = True
    elif nama == "rute":
        if not core.pesan_terlihat(st.session_state.riwayat):
            catat("Sebutkan dulu satu film yang kamu suka, baru Kino bisa menyusun rute.", "peringatan")
        else:
            st.session_state.tertunda = (
                "Berdasarkan seleraku yang sudah kamu baca sejauh ini, susun satu jalur "
                "tontonan bertahap berisi tiga sampai empat judul. Urutkan dari yang paling "
                "mudah dicerna sampai yang paling menantang, dan untuk tiap langkah jelaskan "
                "apa yang sedang dilatih di diriku sebagai penonton."
            )
    elif nama == "simpan":
        if not core.pesan_terlihat(st.session_state.riwayat):
            catat("Belum ada yang bisa disimpan.", "peringatan")
        else:
            catat("Berkas siap diunduh lewat tombol di panel kiri.", "sukses")
    elif nama in ("exit", "keluar", "quit"):
        st.session_state.selesai = True
    else:
        catat("Perintah `/{}` tidak dikenal. Ketik `/help`.".format(nama), "galat")


# ---------------------------------------------------------------------------
# Panel samping
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎬 Ruang Proyeksi")

    st.subheader("Mesin")
    daftar_model = list(core.MODEL_TERSEDIA)
    model = st.selectbox(
        "Model AI",
        daftar_model,
        index=0,
        help="Urutan disusun berdasarkan hasil uji pengetahuan film, bukan tebakan.",
    )
    st.caption(core.MODEL_TERSEDIA[model])

    suhu = st.slider("Kreativitas jawaban", 0.0, 2.0, core.SUHU_DEFAULT, 0.1)
    maks_token = st.slider("Panjang maksimal jawaban", 200, 1200, core.MAKS_TOKEN_DEFAULT, 50)

    st.divider()

    st.subheader("Riwayat")
    kolom_kiri, kolom_kanan = st.columns(2)

    with kolom_kiri:
        if st.button("Kosongkan", use_container_width=True):
            st.session_state.riwayat = core.riwayat_baru("web")
            st.session_state.mulai = datetime.now()
            st.rerun()

    terlihat = core.pesan_terlihat(st.session_state.riwayat)
    with kolom_kanan:
        st.download_button(
            "Unduh",
            data=json.dumps(terlihat, indent=2, ensure_ascii=False),
            file_name="chat_kino_{:%Y%m%d_%H%M%S}.json".format(datetime.now()),
            mime="application/json",
            use_container_width=True,
            disabled=not terlihat,
        )

    berkas = st.file_uploader("Muat percakapan lama", type="json")
    if berkas is not None and st.session_state.get("berkas_terakhir") != berkas.name:
        try:
            st.session_state.riwayat = core.muat_riwayat(berkas.getvalue(), "web")
            st.session_state.berkas_terakhir = berkas.name
            st.session_state.selesai = False
            st.rerun()
        except (ValueError, UnicodeDecodeError) as e:
            st.error("Gagal memuat: {}".format(e))

    st.divider()

    st.subheader("Statistik")
    s = core.hitung_statistik(st.session_state.riwayat, st.session_state.mulai)
    a, b = st.columns(2)
    a.metric("Pesanmu", s["pesan_kamu"])
    b.metric("Balasan Kino", s["balasan_kino"])
    st.caption(
        "Perkiraan {} token terpakai · rata-rata {} kata per balasan · {} menit".format(
            s["perkiraan_token"], s["rata_kata_balasan"], s["durasi_menit"]
        )
    )

    # Ekstraksi judul memanggil API lagi, jadi sengaja dipasang di balik tombol
    # dan tidak dijalankan otomatis setiap pesan.
    if st.button("Film apa saja yang sudah dibahas?", use_container_width=True, disabled=not terlihat):
        st.session_state.tampil_statistik = True

    if st.session_state.get("tampil_statistik"):
        with st.spinner("Membaca transkrip..."):
            judul = core.ekstrak_judul(klien, st.session_state.riwayat, model)
            fakta = core.verifikasi_judul(judul) if core.tmdb_aktif() else []
        peta = {f["judul"].lower(): f for f in fakta}
        if judul:
            for j in judul:
                cocok = peta.get(j.lower())
                st.write("• {}{}".format(j, " ({})".format(cocok["tahun"]) if cocok else ""))
        else:
            st.caption("Belum ada judul yang terdeteksi.")
        st.session_state.tampil_statistik = False

    if core.tmdb_aktif():
        st.caption("✅ Verifikasi fakta TMDB aktif")

    st.divider()
    st.caption("Ketik `/help` di kotak chat untuk daftar perintah.")


# ---------------------------------------------------------------------------
# Halaman utama
# ---------------------------------------------------------------------------
st.title("🍿 Kino")
st.caption(
    "Kurator yang menunjukkan **rute**, bukan sekadar daftar. "
    "Sebut satu film yang kamu suka, dan Kino akan menebak apa yang sebenarnya "
    "kamu nikmati dari film itu."
)

if st.session_state.catatan:
    jenis, pesan = st.session_state.catatan
    {"sukses": st.success, "peringatan": st.warning, "galat": st.error}.get(jenis, st.info)(pesan)
    st.session_state.catatan = None

for pesan in core.pesan_terlihat(st.session_state.riwayat):
    with st.chat_message(
        pesan["role"], avatar=AVATAR_KINO if pesan["role"] == "assistant" else AVATAR_KAMU
    ):
        st.markdown(pesan["content"])


# ---------------------------------------------------------------------------
# Layar penutup setelah /exit
# ---------------------------------------------------------------------------
if st.session_state.selesai:
    st.divider()
    st.subheader("Sesi ditutup")
    akhir = core.hitung_statistik(st.session_state.riwayat, st.session_state.mulai)
    x, y, z = st.columns(3)
    x.metric("Pesanmu", akhir["pesan_kamu"])
    y.metric("Balasan Kino", akhir["balasan_kino"])
    z.metric("Lama sesi", "{} menit".format(akhir["durasi_menit"]))
    st.info("Unduh riwayatnya lewat panel kiri sebelum menutup tab ini.")
    if st.button("Mulai sesi baru"):
        st.session_state.riwayat = core.riwayat_baru("web")
        st.session_state.mulai = datetime.now()
        st.session_state.selesai = False
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------------
# Giliran percakapan
# ---------------------------------------------------------------------------
# chat_input selalu dirender lebih dulu supaya kotak ketiknya tidak hilang
# sekejap ketika giliran ini dipicu oleh perintah /rute, bukan oleh ketikan.
ketikan = st.chat_input("Sebut satu film yang kamu suka, atau ketik /help")
masukan = st.session_state.tertunda or ketikan
st.session_state.tertunda = None

if masukan:
    if masukan.startswith("/"):
        tangani_perintah(masukan)
        st.rerun()

    with st.chat_message("user", avatar=AVATAR_KAMU):
        st.markdown(masukan)

    with st.chat_message("assistant", avatar=AVATAR_KINO):
        # Dua kotak terpisah: satu untuk kabar proses dan pesan galat, satu lagi
        # untuk teks jawaban. Kalau digabung, pesan galat akan menimpa jawaban
        # yang sudah terlanjur tampil di layar.
        kotak_kabar = st.empty()
        kotak_teks = st.empty()
        terkumpul = ""

        for jenis, isi in core.tanya(
            klien,
            st.session_state.riwayat,
            masukan,
            model=model,
            suhu=suhu,
            maks_token=maks_token,
        ):
            if jenis == "status":
                kotak_kabar.warning(isi)
            elif jenis == "teks":
                terkumpul += isi
                kotak_teks.markdown(terkumpul + "▌")
            elif jenis == "error":
                kotak_kabar.error(isi)

        if terkumpul:
            kotak_teks.markdown(terkumpul)  # buang kursor kedip di ujung
            # Panel samping sudah terlanjur dirender di awal skrip, jadi angka
            # statistiknya belum memuat giliran ini. Satu rerun membuat sidebar
            # ikut membaca riwayat yang baru saja bertambah.
            st.rerun()
        else:
            kotak_teks.empty()
