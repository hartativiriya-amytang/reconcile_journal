# User Roles

Sistem ini memiliki 2 grup pengguna dengan akses berbeda:

---

## 1. Finance

Grup ini mengakses sistem **hanya melalui REST API** (`/api/`).

### Yang bisa dilakukan:
| Aktivitas | Endpoint |
|---|---|
| Upload file Excel & jalankan rekonsiliasi | `POST /api/reconcile/` |
| Buat konfigurasi field rekonsiliasi | `POST /api/bulk-configure/` |
| Kelola konfigurasi rekonsiliasi | `GET/POST/PUT/DELETE /api/configs/` |
| Kelola field, mapping, rules | `GET/POST/PUT/DELETE /api/fields/`, `/api/mappings/`, `/api/rules/` |
| Lihat hasil rekonsiliasi | `GET /api/sessions/`, `/api/sessions/{id}/results/` |
| Download hasil Excel | `GET /api/sessions/{id}/download_matched/`, `download_unmatched/`, `download_summary/` |

### Cara pakai:
1. Buat konfigurasi via `POST /api/bulk-configure/`
2. Upload 2 file Excel & proses via `POST /api/reconcile/`
3. Cek hasil session via `GET /api/sessions/`
4. Download hasil matched/unmatched/summary dalam format Excel

### Persyaratan:
- User harus login (Session atau Basic Auth)
- User harus anggota grup **Finance**

---

## 2. Admin Finance

Grup ini mengakses sistem **hanya melalui Django Admin** (`/admin/`).

### Yang bisa dilakukan:
| Aktivitas | Lokasi di Admin |
|---|---|
| Approve akun user baru | `Admin → Authentication and Authorization → Users` |
| Atur grup & hak akses | `Admin → Authentication and Authorization → Groups` |
| Lihat & kelola semua data konfigurasi | `Admin → Reconcile → Reconciliation Configs` |
| Lihat session rekonsiliasi | `Admin → Reconcile → Reconciliation Sessions` |
| Lihat hasil rekonsiliasi | `Admin → Reconcile → Reconciliation Results` |
| Administrasi sistem secara penuh | Semua model terdaftar di Admin |

### Cara pakai:
1. Login ke `/admin/`
2. Untuk memberikan akses ke user Finance:
   - Buka `Authentication and Authorization → Users`
   - Pilih user, centang `Staff status`, pilih grup **Finance**
   - Save
3. Untuk membuat user Admin Finance baru:
   - Buka `Authentication and Authorization → Users`
   - Buat user baru, centang `Staff status`, pilih grup **Admin Finance**
   - Save

### Persyaratan:
- User harus login
- User harus **Staff status** (is_staff = True)
- User harus anggota grup **Admin Finance**

---

## Ringkasan Akses

| Fitur | Finance | Admin Finance |
|---|---|---|
| Upload Excel & Rekonsiliasi | via API | - |
| Konfigurasi field rekonsiliasi | via API | via Admin |
| Lihat hasil rekonsiliasi | via API | via Admin |
| Download hasil Excel | via API | via Admin |
| Kelola User & Group | - | via Admin |
| Administrasi data | - | via Admin |

Superuser memiliki akses penuh ke kedua area.
