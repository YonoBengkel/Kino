"""
chatbot_cli.py - Kino versi terminal.

Ini pemenuhan syarat utama tugas: chatbot berjalan di console. Seluruh otaknya
(persona, memori, penanganan error) diambil dari core.py, jadi versi terminal
dan versi web tidak akan pernah berbeda kelakuan.

Jalankan dengan:  python chatbot_cli.py
"""

import os
import sys
from datetime import datetime

import core

# ---------------------------------------------------------------------------
# Persiapan terminal
# ---------------------------------------------------------------------------
# Console Windows secara bawaan memakai cp1252, yang TIDAK bisa mencetak huruf
# seperti "Jūzō Itami" atau tanda kutip melengkung - programnya akan mati dengan
# UnicodeEncodeError di tengah jawaban. Baris ini memaksa keluaran ke UTF-8.
for aliran in (sys.stdout, sys.stderr):
    try:
        aliran.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Trik untuk mengaktifkan kode warna ANSI di Command Prompt lawas.
if os.name == "nt":
    try:
        os.system("")
    except Exception:
        pass

_PAKAI_WARNA = sys.stdout.isatty() and not os.getenv("NO_COLOR")


def _w(kode, teks):
    return "\033[{}m{}\033[0m".format(kode, teks) if _PAKAI_WARNA else teks


def abu(t):
    return _w("90", t)


def cyan(t):
    return _w("36", t)


def hijau(t):
    return _w("32", t)


def kuning(t):
    return _w("33", t)


def merah(t):
    return _w("31", t)


def tebal(t):
    return _w("1", t)


def hapus_baris():
    """Bersihkan baris status supaya hitung mundur tidak menumpuk."""
    sys.stdout.write("\r" + " " * 78 + "\r")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Keadaan sesi
# ---------------------------------------------------------------------------
class Sesi:
    def __init__(self):
        self.klien = core.buat_klien()
        self.riwayat = core.riwayat_baru("cli")
        self.model = core.MODEL_DEFAULT
        self.suhu = core.SUHU_DEFAULT
        self.maks_token = 600  # lebih pendek dari web, layar terminal sempit
        self.mulai = datetime.now()


BANNER = r"""
  _  _______ _   _  ___
 | |/ /_   _| \ | |/ _ \     Kurator film yang menunjukkan RUTE,
 | ' /  | | |  \| | | | |    bukan sekadar daftar tontonan.
 | . \  | | | |\  | |_| |
 |_|\_\ |_| |_| \_|\___/     Ketik /help untuk daftar perintah.
"""


def cetak_bantuan():
    baris = [
        ("/help", "Tampilkan daftar perintah ini"),
        ("/exit", "Keluar dari program"),
        ("/reset", "Kosongkan ingatan, mulai percakapan dari nol"),
        ("/simpan [nama]", "Simpan percakapan ke berkas JSON"),
        ("/muat [nama]", "Muat kembali percakapan yang pernah disimpan"),
        ("/statistik", "Ringkasan sesi + daftar film yang sudah dibahas"),
        ("/rute", "Minta Kino menyusun jalur tontonan bertahap"),
        ("/model", "Ganti model AI yang dipakai"),
        ("/suhu <angka>", "Atur kreativitas jawaban, 0.0 sampai 2.0"),
    ]
    print()
    print(tebal("  PERINTAH KHUSUS"))
    for perintah, arti in baris:
        print("  {}  {}".format(cyan(perintah.ljust(16)), abu(arti)))
    print()
    print(abu("  Selain perintah di atas, apa pun yang kamu ketik dikirim ke Kino."))
    print()


# ---------------------------------------------------------------------------
# Percakapan
# ---------------------------------------------------------------------------
def minta_jawaban(sesi, pesan_user):
    """Kirim satu pesan dan cetak jawabannya sambil mengalir."""
    print()
    print(cyan(tebal("Kino")))

    sedang_status = False
    ada_isi = False

    for jenis, isi in core.tanya(
        sesi.klien,
        sesi.riwayat,
        pesan_user,
        model=sesi.model,
        suhu=sesi.suhu,
        maks_token=sesi.maks_token,
    ):
        if jenis == "status":
            # Hitung mundur saat kena rate limit. Ditulis di baris yang sama
            # berulang-ulang supaya tidak memenuhi layar.
            sys.stdout.write("\r" + kuning("  " + isi))
            sys.stdout.flush()
            sedang_status = True
        elif jenis == "teks":
            if sedang_status:
                hapus_baris()
                sedang_status = False
            ada_isi = True
            sys.stdout.write(isi)
            sys.stdout.flush()
        elif jenis == "error":
            if sedang_status:
                hapus_baris()
                sedang_status = False
            print(merah("  [gagal] " + isi))

    if ada_isi:
        print()
    print()


# ---------------------------------------------------------------------------
# Perintah khusus
# ---------------------------------------------------------------------------
def perintah_simpan(sesi, argumen):
    if not core.pesan_terlihat(sesi.riwayat):
        print(kuning("  Belum ada yang bisa disimpan."))
        return
    try:
        tujuan = core.simpan_riwayat(sesi.riwayat, argumen or None)
        print(hijau("  Tersimpan di {}".format(tujuan)))
    except OSError as e:
        print(merah("  Gagal menyimpan: {}".format(e)))


def perintah_muat(sesi, argumen):
    tersedia = core.daftar_riwayat()
    if not tersedia:
        print(kuning("  Belum ada berkas riwayat di folder Riwayat/."))
        return

    if not argumen:
        print()
        print(tebal("  BERKAS TERSEDIA"))
        for i, berkas in enumerate(tersedia, 1):
            print("  {} {}".format(cyan(str(i).rjust(2) + "."), berkas.name))
        print()
        pilihan = input(hijau("  Nomor berkas (kosongkan untuk batal) > ")).strip()
        if not pilihan:
            return
        try:
            argumen = tersedia[int(pilihan) - 1].name
        except (ValueError, IndexError):
            print(merah("  Nomor tidak dikenali."))
            return

    try:
        sesi.riwayat = core.muat_riwayat(argumen, "cli")
        jumlah = len(core.pesan_terlihat(sesi.riwayat))
        print(hijau("  Berhasil memuat {} pesan. Kino sudah ingat obrolan itu.".format(jumlah)))
    except (OSError, ValueError) as e:
        print(merah("  Gagal memuat: {}".format(e)))


def perintah_statistik(sesi):
    s = core.hitung_statistik(sesi.riwayat, sesi.mulai)
    print()
    print(tebal("  STATISTIK SESI"))
    print("  Pesan kamu        : {}".format(s["pesan_kamu"]))
    print("  Balasan Kino      : {}".format(s["balasan_kino"]))
    print("  Rata-rata panjang : {} kata per balasan".format(s["rata_kata_balasan"]))
    print("  Perkiraan token   : {} {}".format(s["perkiraan_token"], abu("(kasar)")))
    print("  Lama sesi         : {} menit".format(s["durasi_menit"]))

    if not core.pesan_terlihat(sesi.riwayat):
        print()
        return

    print()
    # Ditulis tanpa baris baru supaya hapus_baris() bisa menimpanya nanti.
    sys.stdout.write(abu("  Membaca film apa saja yang sudah dibahas..."))
    sys.stdout.flush()
    judul = core.ekstrak_judul(sesi.klien, sesi.riwayat, sesi.model)
    hapus_baris()

    if not judul:
        print(abu("  Belum ada judul film yang terdeteksi."))
        print()
        return

    print(tebal("  FILM YANG DIBAHAS ({})".format(len(judul))))
    terverifikasi = core.verifikasi_judul(judul) if core.tmdb_aktif() else []
    peta = {f["judul"].lower(): f for f in terverifikasi}

    for j in judul:
        cocok = peta.get(j.lower())
        if cocok:
            print("  - {} {}".format(j, abu("({}, terverifikasi TMDB)".format(cocok["tahun"]))))
        else:
            print("  - {}".format(j))
    print()


def perintah_model(sesi):
    daftar = list(core.MODEL_TERSEDIA.items())
    print()
    print(tebal("  MODEL TERSEDIA"))
    for i, (nama, arti) in enumerate(daftar, 1):
        tanda = hijau(" <- sedang dipakai") if nama == sesi.model else ""
        print("  {} {}{}".format(cyan(str(i) + "."), nama, tanda))
        print("     {}".format(abu(arti)))
    print()
    pilihan = input(hijau("  Nomor model (kosongkan untuk batal) > ")).strip()
    if not pilihan:
        return
    try:
        sesi.model = daftar[int(pilihan) - 1][0]
        print(hijau("  Model diganti ke {}".format(sesi.model)))
    except (ValueError, IndexError):
        print(merah("  Nomor tidak dikenali."))


def perintah_suhu(sesi, argumen):
    if not argumen:
        print(abu("  Suhu sekarang {}. Contoh pemakaian: /suhu 1.2".format(sesi.suhu)))
        return
    try:
        nilai = float(argumen.replace(",", "."))
    except ValueError:
        print(merah("  Itu bukan angka."))
        return
    if not 0.0 <= nilai <= 2.0:
        print(merah("  Suhu harus di antara 0.0 dan 2.0."))
        return
    sesi.suhu = nilai
    print(hijau("  Suhu diatur ke {}.".format(nilai)))


def perintah_rute(sesi):
    if not core.pesan_terlihat(sesi.riwayat):
        print(kuning("  Sebutkan dulu satu film yang kamu suka, baru Kino bisa menyusun rute."))
        return
    minta_jawaban(
        sesi,
        "Berdasarkan seleraku yang sudah kamu baca sejauh ini, susun satu jalur "
        "tontonan bertahap berisi tiga sampai empat judul. Urutkan dari yang paling "
        "mudah dicerna sampai yang paling menantang, dan untuk tiap langkah jelaskan "
        "apa yang sedang dilatih di diriku sebagai penonton.",
    )


def tawarkan_simpan(sesi):
    """Dipanggil saat keluar - jangan sampai percakapan bagus hilang begitu saja."""
    if not core.pesan_terlihat(sesi.riwayat):
        return
    try:
        jawab = input(hijau("  Simpan percakapan ini dulu? (y/n) > ")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if jawab.startswith("y"):
        perintah_simpan(sesi, None)


def tangani_perintah(sesi, masukan):
    """
    Pemeriksa yang berjalan SEBELUM pesan dikirim ke API.

    Inilah yang hilang di versi lama: tanpa fungsi ini, mengetik "exit" cuma
    dikirim ke Kino dan dijawab sebagai pertanyaan biasa.

    Kembalikan True kalau program harus berhenti.
    """
    bagian = masukan[1:].split(maxsplit=1)
    nama = bagian[0].lower() if bagian else ""
    argumen = bagian[1].strip() if len(bagian) > 1 else ""

    if nama in ("exit", "keluar", "quit"):
        tawarkan_simpan(sesi)
        print(abu("  Sampai jumpa, Sobat Sinema."))
        return True

    if nama in ("reset", "clear", "bersih"):
        sesi.riwayat = core.riwayat_baru("cli")
        sesi.mulai = datetime.now()
        print(hijau("  Ingatan Kino dikosongkan. Mulai dari nol."))
    elif nama in ("help", "bantuan", "?"):
        cetak_bantuan()
    elif nama == "simpan":
        perintah_simpan(sesi, argumen)
    elif nama == "muat":
        perintah_muat(sesi, argumen)
    elif nama in ("statistik", "stats"):
        perintah_statistik(sesi)
    elif nama == "rute":
        perintah_rute(sesi)
    elif nama == "model":
        perintah_model(sesi)
    elif nama == "suhu":
        perintah_suhu(sesi, argumen)
    else:
        print(merah("  Perintah /{} tidak dikenal. Ketik /help.".format(nama)))

    return False


# ---------------------------------------------------------------------------
# Program utama
# ---------------------------------------------------------------------------
def main():
    print(cyan(BANNER))

    try:
        sesi = Sesi()
    except RuntimeError as e:
        print(merah("  {}".format(e)))
        return 1

    print(abu("  Model: {}  |  Suhu: {}".format(sesi.model, sesi.suhu)))
    if core.tmdb_aktif():
        print(abu("  Verifikasi TMDB: aktif"))
    print()

    while True:
        try:
            masukan = input(hijau(tebal("Kamu > "))).strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C atau Ctrl+D. Tanpa penanganan ini, program mati dengan
            # tumpukan traceback yang jelek dan percakapan langsung hilang.
            print()
            tawarkan_simpan(sesi)
            print(abu("  Sampai jumpa."))
            return 0

        if not masukan:
            continue

        if masukan.startswith("/"):
            if tangani_perintah(sesi, masukan):
                return 0
            continue

        try:
            minta_jawaban(sesi, masukan)
        except KeyboardInterrupt:
            # Ctrl+C di tengah jawaban: batalkan balasan ini saja, jangan tutup
            # program. Riwayat sudah dirapikan sendiri oleh core.tanya().
            print()
            print(kuning("  Jawaban dibatalkan."))
            print()


if __name__ == "__main__":
    sys.exit(main())
