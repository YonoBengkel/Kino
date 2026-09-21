# Kino — Kurator Rute Sinema

Chatbot AI berbasis LLM yang tidak sekadar merekomendasikan film, tapi menunjukkan **rute** dari film yang sudah kamu tonton menuju film yang lebih dalam.

Tersedia dalam dua wujud: **versi terminal** (syarat utama tugas) dan **versi web Next.js + FastAPI** (nilai tambah). Keduanya memakai otak yang sama.

---

## 1. Tema dan Konsepnya

Kebanyakan chatbot rekomendasi film berhenti di "ini daftar film bagus, silakan pilih". Masalahnya, itu bukan masalah yang sebenarnya dialami orang.

Premis Kino berbeda: **lawan bicaranya bukan orang yang buta film.** Dia sudah menonton Interstellar, Parasite, atau The Dark Knight, dan menikmatinya. Yang tidak dia punya adalah **pintu masuk ke langkah berikutnya**. Setelah Interstellar, ke mana? Ke Solaris? Ke 2001? Kenapa ke situ dan bukan ke yang lain?

Maka Kino diposisikan bukan sebagai orang yang tahu film langka, tapi sebagai **orang yang tahu rute**. Prosedur kerjanya, yang ditanamkan lewat system prompt:

1. **Baca selera.** Dari judul yang kamu sebut, tentukan *elemen* apa yang sebenarnya kamu nikmati — bukan genrenya. Urutan waktu yang dibolak-balik? Tokoh yang tidak jelas benar-salahnya? Kamera yang berani diam lama?
2. **Sebut elemennya.** Katakan dugaan itu terus terang. Kamu harus merasa dibaca, bukan diberi daftar.
3. **Jembatani.** Rekomendasikan 1–3 judul yang menaikkan level elemen tadi, disusun dari yang paling mudah dicerna ke yang paling menantang.
4. **Jelaskan sambungannya**, dengan pola tetap: *"Kalau kamu suka X karena Y, maka Z adalah langkah berikutnya karena …"*
5. **Tutup dengan satu pertanyaan** yang memancing kamu mempersempit selera.

Nama "Kino" diambil dari bahasa Jerman dan Rusia untuk bioskop, sekaligus rujukan pada konsep *Kino-Eye* milik sineas Dziga Vertov.

### Kenapa ada aturan fakta yang ketat

LLM sangat gemar mengarang tahun rilis dan nama kru **dengan nada yang sangat meyakinkan**. Pada percobaan awal proyek ini, chatbot pernah menulis bahwa Forrest Gump disutradarai Spielberg (padahal Robert Zemeckis) dan menyebut nama Roderick Jaynes sebagai sinematografer Schindler's List (padahal itu nama samaran Coen bersaudara untuk kredit penyuntingan, dan sinematografer film itu Janusz Kamiński).

Untuk chatbot film, inilah mode kegagalan yang paling berbahaya — terdengar pintar sambil salah total. Karena itu system prompt memuat aturan eksplisit: **lebih baik tidak menyebut tahun sama sekali daripada menyebut tahun yang salah.** Sebagai lapisan kedua, tersedia verifikasi opsional lewat basis data TMDB.

---

## 2. Cara Menjalankan

### Prasyarat

- Python 3.10 atau lebih baru
- API key Groq, gratis di <https://console.groq.com/keys>

### Langkah

**1. Masuk ke folder proyek dan pasang dependensinya**

```bash
pip install -r requirements.txt
```

**2. Siapkan API key**

Salin `.env.example` menjadi `.env`, lalu isi kuncinya:

```bash
cp .env.example .env
```

Isi berkas `.env` tersebut:

```env
API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

> Nama `GROQ_API_KEY` juga diterima — program mengenali keduanya.
> Berkas `.env` sudah terdaftar di `.gitignore`, jadi tidak akan ikut ter-push.

**3a. Menjalankan versi terminal**

```bash
Buka file `kino_chatbot.ipynb` di VS Code, Jupyter Notebook, atau Google Colab, lalu jalankan semua sel (*Run All*).
```

**3b. Menjalankan versi web**

Jalankan backend:
```bash
python -m uvicorn api:app --reload --port 8000
```
Jalankan frontend:
```bash
cd web
npm install
npm run dev
```

Halaman akan terbuka sendiri di `http://localhost:8501`.

### Daftar perintah khusus

| Perintah | Arti | Terminal | Web |
|---|---|:-:|:-:|
| `/help` | Tampilkan daftar perintah | ✅ | ✅ |
| `/exit` | Keluar (di web: tampilkan layar penutup) | ✅ | ✅ |
| `/reset` atau `/clear` | Kosongkan ingatan, mulai dari nol | ✅ | ✅ |
| `/simpan [nama]` | Simpan percakapan ke JSON | ✅ | ✅ |
| `/muat [nama]` | Muat percakapan lama | ✅ | lewat tombol unggah |
| `/statistik` | Ringkasan sesi + film yang sudah dibahas | ✅ | ✅ |
| `/rute` | Susun jalur tontonan bertahap | ✅ | ✅ |
| `/model` | Ganti model AI | ✅ | lewat panel kiri |
| `/suhu <angka>` | Atur kreativitas jawaban | ✅ | lewat panel kiri |

Apa pun yang diketik tanpa diawali garis miring dikirim ke Kino sebagai pertanyaan biasa.

---

## 3. Cuplikan Percakapan

Contoh sungguhan dari versi terminal:

```
Kamu > aku suka Interstellar

Kino
Kamu tampaknya terpikat pada eksplorasi ruang-waktu yang megah — bagaimana
film menata skala kosmos sekaligus memutar waktu.

- Kalau kamu suka Interstellar karena elemen itu, maka Gravity adalah
  langkah berikutnya karena ia menyorot isolasi di luar angkasa lewat
  satu-shot panjang yang menegangkan.
- Selanjutnya, Arrival mengangkat konsep waktu non-linier lewat bahasa
  alien, menantang cara kita memaknai masa depan.
- Untuk tantangan paling tinggi, 2001: A Space Odyssey menelusuri evolusi
  manusia lewat gambar tanpa dialog.

Sobat Sinema, elemen mana yang paling membuatmu terpesona — visual luar
angkasa atau cara cerita memutar waktu?
```

```
Kamu > /statistik

  STATISTIK SESI
  Pesan kamu        : 1
  Balasan Kino      : 1
  Rata-rata panjang : 115 kata per balasan
  Perkiraan token   : 852 (kasar)
  Lama sesi         : 0.4 menit

  FILM YANG DIBAHAS (4)
  - Interstellar
  - Gravity
  - Arrival
  - 2001: A Space Odyssey
```

> **Catatan:** tambahkan tangkapan layar versi web di sini, misalnya
> `![Tampilan web](tangkapan/web.png)`.

---

## 4. Struktur Kode

```
Chatbot/
├── core.py             ← otak bersama: persona, memori, error, statistik
├── kino_chatbot.ipynb  ← antarmuka Jupyter Notebook (pengganti CLI)
├── api.py              ← backend FastAPI      (nilai tambah)
├── web/                ← antarmuka Next.js    (nilai tambah)
├── .env                ← API key (TIDAK ikut ter-push)
├── .env.example        ← contoh isi .env
├── .gitignore
├── requirements.txt
└── Riwayat/            ← percakapan yang disimpan
```

### Kenapa dipisah jadi tiga berkas

Versi terminal dan versi web butuh persona, cara memanggil API, dan penanganan error yang **sama persis**. Kalau keduanya ditulis terpisah, mengubah persona berarti mengubah dua tempat — dan cepat atau lambat keduanya jadi berbeda kelakuan. `core.py` adalah satu-satunya sumber kebenaran; dua berkas lainnya hanya mengurus tampilan.

### Isi `core.py`

| Bagian | Fungsi utama | Tugasnya |
|---|---|---|
| 1. Model | `MODEL_TERSEDIA` | Daftar model, diurutkan berdasarkan hasil uji |
| 2. Persona | `bangun_system_prompt()` | Merakit system prompt; aturan panjang jawaban berbeda antara terminal dan web |
| 3. Klien | `buat_klien()` | Membaca API key dari `.env` |
| 4. Riwayat | `riwayat_baru()`, `pangkas_riwayat()` | Mengelola memori percakapan |
| 5. Error | `analisis_error()` | Menerjemahkan error mentah jadi keputusan: ulangi atau menyerah |
| 6. Kirim | `kirim_pesan()`, `tanya()` | Streaming jawaban + percobaan ulang |
| 7. Berkas | `simpan_riwayat()`, `muat_riwayat()` | Simpan dan muat JSON |
| 8. Statistik | `hitung_statistik()`, `ekstrak_judul()` | Angka sesi dan daftar film yang dibahas |
| 9. TMDB | `cari_film()` | Verifikasi fakta (opsional) |

### Bagaimana conversation history bekerja

Ini bagian yang paling sering disalahpahami, jadi perlu dijelaskan terpisah.

**LLM tidak punya ingatan sama sekali.** Setiap panggilan API adalah amnesia total — model tidak tahu kamu pernah bicara dengannya lima detik lalu. Yang menciptakan ilusi "ingat" adalah program **mengirim ulang seluruh transkrip percakapan setiap kali bertanya.**

```
Giliran 1 — kamu ketik "aku suka Interstellar"
  yang DIKIRIM : [system, user:"aku suka Interstellar"]
  balasan masuk → riwayat jadi [system, user, assistant]

Giliran 2 — kamu ketik "kenapa?"
  yang DIKIRIM : [system, user:"aku suka Interstellar",
                  assistant:"...", user:"kenapa?"]
                  ↑ seluruhnya dikirim ulang dari nol
```

Di giliran kedua, model paham "kenapa?" merujuk ke apa **hanya karena** tiga pesan sebelumnya ikut dikirim.

Tiga konsekuensi yang ditangani di kode ini:

- **Biaya token membengkak.** Giliran ke-10 mengirim ulang sembilan giliran sebelumnya. Karena itu ada `pangkas_riwayat()`, yang hanya mengirim system prompt plus sejumlah pesan terakhir.
- **Struktur bisa cacat.** Kalau API gagal setelah pesan pengguna masuk daftar, riwayat berisi dua pesan `user` berturut-turut tanpa jawaban di antaranya. Karena itu `tanya()` **mencabut kembali** pesan pengguna saat gagal — dan pencabutan itu diletakkan di blok `finally`, supaya tetap jalan meski pengguna menekan Ctrl+C di tengah jawaban.
- **Aplikasi Web butuh perlakuan khusus.** Antarmuka web (Next.js) berkomunikasi via API call yang *stateless* (tiada ingatan), sehingga `api.py` harus meneruskan dan merakit ulang seluruh struktur pesan JSON yang dikirim dari *client* ke `core.py`. Versi terminal tidak butuh ini karena prosesnya terus hidup di memori.

### Bagaimana penanganan error bekerja

Kuncinya: **tidak semua kegagalan sama.** API key salah tidak akan membaik walau diulang seribu kali; server sibuk biasanya sembuh dalam beberapa detik. `analisis_error()` memilah keduanya:

| Yang terjadi | Kelas error | Tindakan |
|---|---|---|
| API key salah | `AuthenticationError` | Berhenti, beri pesan jelas |
| Kena batas pemakaian | `RateLimitError` | Baca lama tunggu, hitung mundur, coba lagi |
| Percakapan terlalu panjang | `BadRequestError` | Sarankan `/reset` |
| Model tidak ada di akun | `NotFoundError` | Sarankan `/model` |
| Internet putus | `APIConnectionError` | Ulangi dengan jeda menaik |
| Server Groq bermasalah | `InternalServerError` | Ulangi dengan jeda menaik |
| Ctrl+C di terminal | `KeyboardInterrupt` | Keluar rapi, tawarkan simpan riwayat |

Untuk rate limit ada satu nuansa penting. Groq punya **dua jenis batas**: per menit dan per hari. Batas per menit cuma perlu ditunggu beberapa detik, jadi program menampilkan hitung mundur lalu melanjutkan sendiri. Batas harian perlu ditunggu berjam-jam — menggantung program di situ percuma, jadi program berhenti dan menyarankan menyimpan riwayat dulu.

> Catatan teknis: SDK `groq` sendiri sudah mengulang 2 kali secara diam-diam untuk sebagian error. Jadi `maks_percobaan=3` di kode ini berarti percobaan berlapis, bukan tepat tiga kali panggilan jaringan.

### Kenapa ada `reasoning_effort` di `opsi_model()`

Ini temuan dari pengujian, bukan salinan dari dokumentasi.

Model keluarga `gpt-oss` melakukan penalaran internal **sebelum** menulis jawaban, dan penalaran itu ikut dihitung sebagai token keluaran. Pada permintaan yang rumit — misalnya `/rute`, yang meminta jalur bertahap lengkap dengan penjelasan — penalarannya bisa menghabiskan seluruh jatah `max_tokens` dan menyisakan jawaban **benar-benar kosong**. Dari sisi API panggilannya sukses, tidak ada error apa pun, jadi program cuma diam.

Diuji sembilan kali pada permintaan yang sama dengan `max_tokens=600`:

| `reasoning_effort` | Panjang penalaran | Panjang jawaban |
|---|---|---|
| `low` | ~150–190 huruf | 1115–1246 huruf, selalu terisi |
| `medium` | 807–2449 huruf | pernah tinggal 115 huruf |
| tidak diisi | sampai 2612 huruf | **pernah 0 huruf** |

Karena itu `reasoning_effort="low"` dipasang otomatis. Parameter ini ditolak oleh `groq/compound`, jadi `opsi_model()` memeriksa nama model dulu sebelum mengirimkannya.

Sebagai lapisan pengaman kedua, `kirim_pesan()` juga memeriksa kasus "aliran selesai tanpa satu pun potongan teks" dan memberi tahu pengguna — supaya kegagalan semacam ini tidak pernah lagi berlalu tanpa suara.

### Bagaimana statistik "film yang dibahas" bekerja

Statistik angka biasa (jumlah pesan, rata-rata panjang) hanya perlu `len()` dan pengurangan waktu — murah, dihitung setiap saat.

Tapi "topik yang sering dibahas" lebih rumit. Mencocokkan kata dengan daftar judul terlalu rapuh, karena akan gagal untuk film di luar daftar. Yang dipakai di sini: **LLM kedua sebagai pengekstrak.** Transkrip dikirim ke model dengan permintaan membalas dalam bentuk JSON berisi daftar judul. Model paham mana yang judul film dan mana yang bukan, jadi jauh lebih andal.

Karena cara ini memakan satu panggilan API tambahan, ekstraksi hanya dijalankan saat statistik dibuka — bukan setiap pesan.

---

## 5. Pemetaan ke Ketentuan Tugas

| Ketentuan | Di mana |
|---|---|
| Berjalan di console/notebook | `kino_chatbot.ipynb` |
| Menggunakan API LLM | Groq, lewat `core.buat_klien()` |
| Punya system prompt sesuai tema | `core._PERSONA` |
| Mengelola conversation history | `core.riwayat_baru()`, `pangkas_riwayat()`, `tanya()` |
| Penanganan error | `core.analisis_error()`, `core.kirim_pesan()` |
| Minimal 2 perintah khusus | 9 perintah, lihat tabel di bagian 2 |
| *Bonus* — tampilan web | `api.py` + folder `web/` (Next.js) |
| *Bonus* — streaming response | `core._stream_sekali()` |
| *Bonus* — simpan & muat riwayat | `simpan_riwayat()`, `muat_riwayat()` |
| *Bonus* — statistik percakapan | `hitung_statistik()`, `ekstrak_judul()` |
| *Bonus* — kontrol parameter | `/model`, `/suhu`, dan panel kiri versi web |
| *Bonus* — fitur relevan tema | `/rute`, verifikasi TMDB |

### Soal pemilihan model

Daftar model di `core.MODEL_TERSEDIA` tidak disusun asal. Empat model yang tersedia di akun diuji dengan dua pertanyaan: satu menguji pengetahuan film niche (sutradara *Tampopo*, 1985), satu lagi jebakan halusinasi (diminta menceritakan sinopsis film yang tidak pernah ada).

| Model | Pengetahuan niche | Jebakan halusinasi |
|---|---|---|
| `openai/gpt-oss-120b` | ✅ benar | ✅ menolak, sebut alasannya |
| `groq/compound-mini` | ✅ benar | ✅ menolak |
| `openai/gpt-oss-20b` | ⚠️ sutradara benar, tahun salah | ❌ mengarang sinopsis lengkap |
| `qwen/qwen3.8-27b` | ❌ salah sutradara | ✅ menolak |

Karena itu `openai/gpt-oss-120b` dipasang sebagai default.

> Dua pertanyaan tentu bukan tolok ukur ilmiah — anggap ini sinyal, bukan bukti.

---

## 6. Catatan Penggunaan AI

Sesuai ketentuan tugas, berikut pembagian yang sejujurnya:

**Dikerjakan mandiri:**
- Pemilihan tema dan keputusan bahwa konsepnya harus di-*reframe* dari "kurator film niche" menjadi "kurator rute" — karena versi pertama kontradiktif: menyebut The Godfather dan Forrest Gump sebagai film niche jelas tidak jujur.
- Identifikasi bahwa versi awal proyek ini melewatkan syarat utama (hanya ada Web UI, tidak ada versi terminal) dan bahwa perintah `exit`/`clear` yang diketik tidak pernah bekerja.
- Keputusan desain: memakai satu `core.py` bersama, cakupan perintah khusus, dan urutan prioritas pengerjaan.

**Dibantu AI assistant:**
- Penulisan kode `core.py`, `kino_chatbot.ipynb`, dan `app.py`.
- Perancangan taksonomi error dan logika percobaan ulang untuk rate limit.
- Penyusunan ulang teks system prompt.
- Penyusunan README ini.

**Diverifikasi lewat pengujian langsung, bukan diterima begitu saja:**
- Daftar model yang benar-benar tersedia di akun, lewat `client.models.list()` — ternyata `llama-3.3-70b-versatile` yang dipakai di contoh kelas tidak ada di akun ini.
- Perbandingan pengetahuan film keempat model (tabel di bagian 5).
- Kesalahan fakta pada percakapan percobaan pertama (Forrest Gump dan Schindler's List), yang kemudian jadi alasan aturan fakta diperketat.

---

## 7. Batasan yang Diketahui

Disebut terus terang supaya tidak ada klaim berlebihan:

- **Verifikasi TMDB belum diuji dengan kunci sungguhan.** Kode sudah ditulis dan jalur "kunci tidak ada" sudah diuji (program berjalan normal dengan verifikasi nonaktif), tapi jalur "kunci ada" belum pernah dijalankan. Isi `TMDB_API_KEY` di `.env` untuk mengaktifkannya.
- **Perkiraan token bersifat kasar**, dihitung dengan asumsi satu token ≈ empat huruf. Ini bukan angka resmi dari API.
- **`pangkas_riwayat()` memotong begitu saja**, tidak meringkas. Percakapan yang sangat panjang akan kehilangan bagian paling awal.
- **Kino tetap bisa salah fakta** meski aturannya sudah diperketat. Untuk klaim penting, verifikasi sendiri.
