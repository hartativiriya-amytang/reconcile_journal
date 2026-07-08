# Aplikasi Rekonsiliasi Data (Django + DRF)

Aplikasi backend untuk merekonsiliasi dua file Excel berdasarkan field/kriteria
yang ditentukan user secara dinamis (maksimal 12 field). Tidak ada data yang
disimpan ke database — proses murni: **upload -> proses di memory -> download hasil**.

## Alur

1. User mendefinisikan daftar field yang mau direkonsiliasi (maks. 12), misalnya:
   - A = Nomor Jurnal
   - B = Keterangan
   - C = Bulan
   - D = Debit
   - E = Kredit

   Untuk tiap field, user menyebutkan nama kolom sesuai yang ada di **File 1**
   dan **File 2** (nama kolom boleh berbeda antar kedua file).

2. User memilih field mana yang dipakai sebagai **kriteria pencocokan**
   (`match_keys`), misalnya cocokkan berdasarkan Nomor Jurnal DAN Bulan.

3. User upload 2 file Excel (`file1`, `file2`).

4. Sistem melakukan reconcile dan menyediakan pilihan hasil:
   - `matched` — irisan data yang cocok di kedua file
   - `unmatched_file1` — data yang hanya ada di File 1
   - `unmatched_file2` — data yang hanya ada di File 2
   - `all` — mengembalikan ketiganya + ringkasan sekaligus dalam 1 file `.zip`

## Autentikasi (akses khusus staff)

Halaman `/` dan seluruh endpoint `/api/*` sekarang **wajib login** dan
**wajib punya role staff** (flag bawaan Django `is_staff`):

- Belum login → otomatis diarahkan ke `/accounts/login/`, lalu setelah
  login sukses langsung diarahkan kembali ke `/` (halaman recon).
- Login tapi bukan staff → dapat pesan 403 (Forbidden), tidak bisa akses
  form maupun API.
- Login sebagai staff → langsung dapat halaman recon dan bisa memanggil
  API-nya.
- Logout tersedia lewat tombol "Logout" di pojok kanan atas halaman recon.

Untuk membuat akun staff pertama:

```bash
python manage.py createsuperuser
```

(superuser otomatis `is_staff=True`). Untuk staff biasa (bukan superuser),
login dulu ke `/admin/` pakai superuser tadi, lalu buat User baru dan
centang **"Staff status"** di halaman edit user — tanpa perlu akses admin
apa pun selain untuk membuat akun, staff tersebut hanya akan bisa membuka
halaman recon (bukan `/admin/` penuh, kecuali diberi permission tambahan).

## Instalasi

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # buat akun staff pertama
python manage.py runserver
```

Server berjalan di `http://127.0.0.1:8000/`. Halaman yang tersedia:

| URL                     | Isi                                                             |
|-------------------------|------------------------------------------------------------------|
| `/`                     | Halaman web untuk upload & reconcile (perlu login staff)         |
| `/accounts/login/`      | Halaman login                                                    |
| `/accounts/logout/`     | Logout (dipanggil lewat tombol di halaman recon)                 |
| `/docs/`                | Dokumentasi API interaktif (Swagger, juga perlu login staff)      |
| `/api/schema/`          | Raw OpenAPI schema (JSON)                                        |
| `/api/config-info/`     | Info skema config & contoh payload (perlu login staff)           |
| `/api/reconcile/`       | Endpoint utama upload + proses + download hasil (perlu login staff) |
| `/admin/`               | Django admin bawaan, untuk kelola akun staff                      |

> Catatan: `/admin/` butuh `python manage.py migrate` supaya tabel session/auth
> tersedia — fitur reconcile sendiri (`/api/reconcile/`) tidak menyentuh
> database untuk **datanya** (Excel yang diupload tetap diproses murni di
> memory), database hanya dipakai untuk data login/session.

## Endpoint

### `GET /api/config-info/`
Endpoint bantu untuk frontend: mengembalikan skema config yang diharapkan,
batas maksimal field, dan opsi output — supaya frontend tidak perlu hardcode.

### `POST /api/reconcile/`
`multipart/form-data` dengan 3 field:

| Field    | Tipe        | Keterangan                                   |
|----------|-------------|-----------------------------------------------|
| `file1`  | file        | File Excel pertama (.xlsx/.xls)               |
| `file2`  | file        | File Excel kedua (.xlsx/.xls)                 |
| `config` | text (JSON) | Definisi field & kriteria (lihat contoh)      |

Contoh isi `config`:

```json
{
  "fields": [
    {"key": "A", "label": "Nomor Jurnal", "file1_column": "No Jurnal", "file2_column": "NoJurnal"},
    {"key": "B", "label": "Keterangan",   "file1_column": "Keterangan", "file2_column": "Description"},
    {"key": "C", "label": "Bulan",        "file1_column": "Bulan", "file2_column": "Month"},
    {"key": "D", "label": "Debit",        "file1_column": "Debit", "file2_column": "Debit"},
    {"key": "E", "label": "Kredit",       "file1_column": "Kredit", "file2_column": "Kredit"}
  ],
  "match_keys": ["A", "C"],
  "output": "all",
  "case_sensitive": false,
  "trim_whitespace": true
}
```

Keterangan opsi tambahan:
- `output`: `"matched"` | `"unmatched_file1"` | `"unmatched_file2"` | `"all"` (default `"all"`)
- `case_sensitive`: apakah pencocokan teks memperhatikan huruf besar/kecil (default `false`)
- `trim_whitespace`: apakah spasi di awal/akhir nilai diabaikan saat pencocokan (default `true`)

Setiap field juga punya opsi (relevan untuk field yang dipakai di `match_keys`):
- `match_type`: `"text"` (default) | `"number"` | `"date"`. Gunakan `"number"`
  untuk kolom jumlah (Debit/Kredit/Bruto/DPP dst.) supaya `1000`, `1000.0`,
  dan `"1000"` dianggap sama. Gunakan `"date"` kalau kolom di kedua file
  berupa tanggal tapi formatnya berbeda (misal satu file kolom tanggal asli
  Excel, file lain teks `"05/01/2024"`) — keduanya akan dinormalisasi ke
  format yang sama sebelum dibandingkan.
- `date_format`: opsional, pola `strptime` (misal `"%m/%d/%Y"` atau
  `"%d/%m/%Y"`) untuk menghilangkan ambiguitas kalau kolom tanggal berupa
  teks. Kalau dikosongkan, sistem mencoba menebak formatnya otomatis.

> **Penting soal keunikan kriteria pencocokan:** proses ini melakukan
> equi-join standar (mirip VLOOKUP/JOIN SQL). Kalau kriteria yang dipilih
> tidak cukup unik (misal cuma "jumlah" saja, dan ada beberapa baris dengan
> jumlah yang sama persis di kedua file), satu baris bisa cocok dengan lebih
> dari satu baris di file lain, sehingga jumlah baris "matched" bisa lebih
> banyak dari jumlah baris asli. Pilih kombinasi field yang benar-benar unik
> per transaksi (misal nomor dokumen + tanggal + jumlah) untuk hasil yang akurat.

Contoh `curl`:

> Karena endpoint ini sekarang butuh login staff, contoh `curl` di bawah
> hanya akan berhasil kalau kamu sudah punya cookie sesi yang valid (login
> dulu lewat browser, atau lakukan login+ambil CSRF token secara manual).
> Untuk mencoba paling gampang, pakai halaman `/` di browser saja setelah
> login — itu sudah otomatis mengurus session & CSRF token untukmu.

```bash
curl -X POST http://127.0.0.1:8000/api/reconcile/ \
  -F "file1=@data_file1.xlsx" \
  -F "file2=@data_file2.xlsx" \
  -F 'config={
        "fields": [
          {"key":"A","label":"Nomor Jurnal","file1_column":"No Jurnal","file2_column":"NoJurnal"},
          {"key":"C","label":"Bulan","file1_column":"Bulan","file2_column":"Month"}
        ],
        "match_keys": ["A","C"],
        "output": "all"
      }' \
  -o hasil_rekonsiliasi.zip
```

Jika `output` = `"all"`, respons berupa file `.zip` berisi:
- `ringkasan.xlsx` — rekap jumlah baris cocok / tidak cocok
- `matched.xlsx`
- `unmatched_file1.xlsx`
- `unmatched_file2.xlsx`

Jika `output` diisi salah satu dari `matched` / `unmatched_file1` / `unmatched_file2`,
respons langsung berupa 1 file `.xlsx` sesuai pilihan tersebut.

## Catatan implementasi

- **Tidak ada penyimpanan ke database.** Kedua file Excel dibaca langsung ke
  `pandas.DataFrame` di memory (`reconciliation/services.py`), diproses, lalu
  hasilnya di-stream langsung sebagai response (`FileResponse`) — tidak pernah
  ditulis ke disk server maupun ke DB.
- Validasi jumlah field (maks. 12), keunikan `key`, dan konsistensi `match_keys`
  ada di `reconciliation/serializers.py`.
- Pencocokan dilakukan dengan `pandas.merge(..., how="outer", indicator=True)`
  sehingga bisa langsung diklasifikasi jadi `both` (matched), `left_only`
  (hanya file1), `right_only` (hanya file2).
- Nilai yang dipakai sebagai kriteria pencocokan dinormalisasi dulu (trim
  spasi + lowercase, bisa dimatikan lewat `case_sensitive`/`trim_whitespace`)
  supaya perbedaan spasi/huruf besar-kecil tidak dianggap tidak cocok.

## Struktur proyek

```
rekonsiliasi_project/
├── manage.py
├── requirements.txt
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── reconciliation/          # App utama
    ├── serializers.py       # Validasi config (fields, match_keys, output)
    ├── services.py          # Logika reconcile pakai pandas (stateless)
    ├── views.py              # Endpoint /api/reconcile/ dan /api/config-info/
    └── urls.py
```
