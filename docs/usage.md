# Recon System — Dokumentasi Penggunaan

## Tentang Sistem

Recon System adalah aplikasi **rekonsiliasi data** berbasis Django yang membandingkan dua file Excel (File A dan File B) untuk menemukan data yang cocok (*matched*) dan yang tidak cocok (*unmatched*). Berguna untuk keperluan audit, akuntansi, pencocokan bank statement, PPN vs Pembukuan, dan sejenisnya.

---

## Cara Kerja

### Alur Rekonsiliasi

```
Upload File A & File B
       ↓
     Parsing Excel (pandas)
       ↓
  Mapping Kolom → Field Sistem
       ↓
  Generate Match Key (MD5 hash)
       ↓
  Set Intersection & Difference
       ↓
  Simpan Hasil (MATCH / ONLY_A / ONLY_B)
       ↓
  Tampilkan Statistik + Download Excel
```

### Proses Detail

1. **Upload** — Dua file `.xlsx` / `.xls` diunggah.
2. **Parsing** — `ExcelParser` membaca file menggunakan pandas (`dtype=str` untuk konsistensi).
3. **Mapping** — Nama kolom Excel dipetakan ke *field* sistem yang sudah dikonfigurasi.
4. **Match Key** — `RuleEngine` menggabungkan nilai dari semua *field matching* (lowercase, stripped) lalu menghasilkan MD5 hash sebagai sidik jari unik tiap record.
5. **Perbandingan** — Kedua dataset diubah ke dictionary dengan key = MD5 hash. Operasi *set intersection* menghasilkan data MATCH, *set difference* menghasilkan ONLY_A (data hanya di File A) dan ONLY_B (data hanya di File B).
6. **Penyimpanan** — Hasil disimpan sebagai row `ReconciliationResult` yang terikat ke `ReconciliationSession`.
7. **Output** — User melihat statistik + bisa mendownload file Excel hasil rekonsiliasi.

---

## User dan Group — Untuk Apa?

### Django Auth bawaan

Sistem menggunakan model **`auth.User`** dan **`auth.Group`** bawaan Django (bukan custom user model). Fungsinya:

| Konsep | Kegunaan |
|---|---|
| **User** | Login ke antarmuka admin (`/admin/`). Hanya user dengan status *staff*/*superuser* yang bisa mengakses admin. |
| **Group** | Mengelompokkan user dan memberikan *permissions* secara kolektif. Misal: grup "Auditor" diberi permission *view* dan *change* pada semua model rekonsiliasi. |

### Implementasi di Sistem Ini

- **Tidak ada custom user model** — menggunakan tabel `auth_user` standar Django.
- **Tidak ada isolasi data per-user** — semua user yang login bisa melihat semua konfigurasi dan session.
- **Ikon di admin**: User → `fas fa-users`, Group → `fas fa-users-cog`.
- **Permission standar**: Setiap model (`Config`, `Field`, `Mapping`, `Rule`, `Session`, `Result`) memiliki permission `view`, `add`, `change`, `delete` yang bisa diatur via Group.

### Contoh Penggunaan Group

1. Buat Group "Auditor" di `/admin/auth/group/`.
2. Beri permission: dapat melihat hasil rekonsiliasi tetapi tidak bisa menghapus konfigurasi.
3. Masukkan user ke group tersebut.
4. User hanya bisa melakukan aksi sesuai permission yang diberikan.

> **Catatan**: Saat ini permission bersifat global. Jika perlu isolasi per-konfigurasi (misal: User A hanya bisa melihat Config miliknya), perlu dikembangkan RBAC khusus.

---

## Cara Menggunakan

### 1. Instalasi & Setup

```bash
# Clone repo
git clone <repo-url> recon_system
cd recon_system

# Buat virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Migrasi database
python manage.py migrate

# Buat superuser (pertama kali)
python manage.py createsuperuser

# Jalankan server
python manage.py runserver
```

### 2. Akses

| Halaman | URL |
|---|---|
| Admin (default home) | http://127.0.0.1:8000/admin/ |
| Web UI (wizard 3 langkah) | http://127.0.0.1:8000/reconcile/ |
| API Docs (Swagger) | http://127.0.0.1:8000/api/docs/ |
| API Root | http://127.0.0.1:8000/api/ |

### 3. Web UI — 3 Langkah

#### Langkah 1: Configure Fields
- Tentukan nama field (misal: "No Faktur", "DPP", "PPN").
- Pilih tipe data (String / Number / Date).
- Masukkan nama kolom Excel untuk File A dan File B.
- Centang field yang menjadi **kriteria pencocokan** (minimal 1).
- Maksimal 12 field.

#### Langkah 2: Upload Files
- Upload file Excel A dan file Excel B.
- Review ringkasan konfigurasi.
- Klik "Run Reconciliation" untuk menjalankan.

#### Langkah 3: View Results
- Lihat statistik: total A, total B, matched, only A, only B, match rate.
- Download hasil:
  - **Matched Records** — data yang cocok.
  - **Unmatched Records** — multi-sheet (Only A, Only B, Summary).
  - **Summary Report** — ringkasan rekonsiliasi.

### 4. REST API

#### Endpoint Utama

| Method | Endpoint | Fungsi |
|---|---|---|
| GET/POST | `/api/configs/` | Daftar / buat konfigurasi |
| GET/PUT/PATCH/DELETE | `/api/configs/{id}/` | CRUD konfigurasi |
| GET/POST | `/api/fields/` | Daftar / buat field |
| GET/POST | `/api/mappings/` | Daftar / buat mapping |
| GET/POST | `/api/rules/` | Daftar / buat rule |
| GET/POST | `/api/sessions/` | Daftar / buat session |
| GET | `/api/sessions/{id}/results/` | Lihat hasil session (filter `?status=MATCH`) |
| GET | `/api/sessions/{id}/download_matched/` | Download matched Excel |
| GET | `/api/sessions/{id}/download_unmatched/` | Download unmatched Excel |
| GET | `/api/sessions/{id}/download_summary/` | Download summary Excel |

#### Bulk Configure (POST `/api/bulk-configure/`)

Buat konfigurasi + field + mapping + rules dalam satu panggilan:

```json
{
  "config_name": "Rekonsiliasi Bulanan",
  "description": "PPN vs Pembukuan",
  "fields": [
    {
      "field_name": "No Faktur",
      "data_type": "string",
      "excel_column_a": "No Faktur Pajak",
      "excel_column_b": "Invoice Number"
    },
    {
      "field_name": "DPP",
      "data_type": "number",
      "excel_column_a": "DPP",
      "excel_column_b": "Dasar Pengenaan Pajak"
    }
  ],
  "matching_fields": ["No Faktur"]
}
```

#### Reconcile (POST `/api/reconcile/`)

Kirim multipart form-data:
- `config_id` — ID konfigurasi (integer)
- `file_a` — File Excel A
- `file_b` — File Excel B

### 5. Admin Interface

Dashboard admin (Jazzmin dark theme) menampilkan:
- **Stat Cards** — jumlah Config, Session, Rules, Results.
- **Recent Sessions** — tabel session terbaru dengan status badge warna.
- **Quick Actions** — tombol ke New Config, Upload Files, API Docs, dll.

Dari admin Anda bisa:
- CRUD semua data (Config, Field, Mapping, Rule, Session, Result).
- Melihat error session yang gagal (collapsible fieldset).
- Mendownload hasil langsung dari tabel session.

---

## Teknologi

| Komponen | Teknologi |
|---|---|
| Backend | Django 5.2, Python 3.10+ |
| API | Django REST Framework 3.15+ |
| Excel | pandas 2.0+, openpyxl 3.1+ |
| Admin Theme | django-jazzmin 3.0+ (dark) |
| API Docs | drf-spectacular 0.27+ (Swagger) |
| Database | SQLite (default) |
| Matching | MD5 hash-based set comparison |

---

## Catatan Penting

- **File maksimal 10 MB**, format `.xlsx` / `.xls`.
- **Maksimal 12 field** per konfigurasi.
- **Minimal 1 matching field** harus dipilih.
- Rekonsiliasi berjalan **synchronous** (tunggu sampai selesai).
- Semua data dibaca sebagai **string** (`dtype=str`) untuk konsistensi perbandingan.
- API menggunakan permission **AllowAny** (tanpa autentikasi) secara default.

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| Upload gagal "File too large" | File > 10 MB. Perkecil ukuran file atau ubah `DATA_UPLOAD_MAX_MEMORY_SIZE` di settings. |
| Session status "Failed" | Buka session di admin, lihat kolom `error_message` untuk detail error. |
| Data tidak cocok padahal seharusnya cocok | Pastikan tipe data field sesuai (Number vs String). Perbedaan spasi/format tanggal bisa menyebabkan mismatch. |
| Lupa password admin | `python manage.py changepassword <username>` |
