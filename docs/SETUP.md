# 📖 Panduan Lengkap Deployment: GitHub Profile Dashboard

Dokumen ini berisi panduan langkah demi langkah yang ramah pemula untuk menerapkan (*deploy*), mengonfigurasi, dan mengotomatiskan **GitHub Profile Dashboard** agar muncul langsung di halaman profil GitHub Anda (**https://github.com/Zakkyaulia**).

---

## 1. Memahami Perbedaan Penting

Sebelum memulai, pahami perbedaan antara ketiga hal ini:

| Tipe | Lokasi Tampil | Fungsi |
|---|---|---|
| **GitHub Profile README** *(Target Kita)* | `https://github.com/Zakkyaulia` | Tampil di beranda profil pribadi saat siapa pun membuka profil GitHub Anda. Harus berada di repositori khusus bernama identik dengan username (`Zakkyaulia/Zakkyaulia`) dan bersifat **Public**. |
| **Repository README** | `https://github.com/user/nama-repo` | Dokumentasi khusus untuk repositori proyek tertentu. |
| **GitHub Pages** | `https://user.github.io/nama-repo` | Situs web statis yang di-hosting di domain terpisah (bukan di profil utama). |

---

## 2. Langkah 1: Buat Repositori Khusus di GitHub

1. Buka browser dan login ke akun GitHub Anda (**Zakkyaulia**).
2. Buat repositori baru di [https://github.com/new](https://github.com/new).
3. Pada kolom **Repository name**, ketik persis sama dengan username Anda:
   ```text
   Zakkyaulia
   ```
4. GitHub akan menampilkan kotak hijau bertuliskan:  
   *“You found a secret! Zakkyaulia/Zakkyaulia is a special repository that you can use to add a README.md to your GitHub profile.”*
5. Pastikan repositori diset ke **Public**.
6. **Jangan** centang *Add a README file*, *Add .gitignore*, atau *Choose a license* (karena kita akan mengunggah file lokal yang sudah siap).
7. Klik tombol **Create repository**.

---

## 3. Langkah 2: Hubungkan & Push File Proyek ke GitHub

Buka terminal (PowerShell atau Command Prompt) di folder proyek ini (`c:\Users\zakky\Documents\Kuliah\Semester 7\github profile`), lalu jalankan perintah berikut secara berurutan:

```powershell
# 1. Inisialisasi git repository lokal (jika belum)
git init

# 2. Tambahkan branch utama 'main'
git branch -M main

# 3. Hubungkan repositori lokal dengan repositori GitHub Anda
git remote add origin https://github.com/Zakkyaulia/Zakkyaulia.git

# 4. Tambahkan seluruh file ke staging
git add .

# 5. Buat commit pertama
git commit -m "feat: initial commit for automated github profile dashboard"

# 6. Push ke GitHub
git push -u origin main
```

*(Catatan: Jika diminta login GitHub, lakukan autentikasi via browser atau token).*

---

## 4. Langkah 3: Konfigurasi Permissions GitHub Actions

Agar GitHub Actions memiliki izin untuk memperbarui file SVG dan data secara otomatis setiap jam, berikan izin *Read and write*:

1. Buka repositori **Zakkyaulia/Zakkyaulia** di browser.
2. Klik tab **Settings** (di menu atas repositori).
3. Di panel sebelah kiri, pilih **Actions** > **General**.
4. Gulir ke bawah hingga bagian **Workflow permissions**.
5. Pilih opsi:  
   🔘 **Read and write permissions**
6. Centang opsi:  
   ☑️ **Allow GitHub Actions to create and approve pull requests** *(opsional tapi disarankan)*.
7. Klik tombol **Save**.

---

## 5. Langkah 4: Uji Coba Manual Workflow (Pertama Kali)

Untuk memastikan otomatisasi berfungsi dengan sempurna tanpa perlu menunggu giliran jadwal jam berikutnya:

1. Klik tab **Actions** di repositori GitHub Anda.
2. Di sebelah kiri, pilih workflow **Update GitHub Profile Dashboard**.
3. Di sebelah kanan akan muncul tombol dropdown **Run workflow**.
4. Klik tombol **Run workflow** (branch: `main`), lalu klik tombol hijau **Run workflow**.
5. Tunggu sekitar 20–40 detik hingga muncul tanda centang hijau (✅ *Success*).
6. Anda dapat mengklik proses tersebut untuk melihat log lengkap dari:
   - Data fetching (REST & GraphQL API)
   - Statistics processing (Kalkulasi commit, bahasa, heatmap)
   - SVG generator (Merender dashboard)
   - Git commit & push

---

## 6. Langkah 5: Verifikasi Dashboard di Profil GitHub

1. Buka halaman profil GitHub utama Anda:  
   👉 **https://github.com/Zakkyaulia**
2. Dashboard SVG bergaya dark-theme yang modern akan langsung muncul di bagian atas profil Anda!
3. Cek komponen berikut:
   - **Header**: Avatar, nama Zakky Aulia Aldrin, subtitle jurusan/kampus, badge kolaborasi.
   - **4 Stat Cards**: Terakhir aktif, Kontribusi bulan ini, Kontribusi tahun ini (dengan donat progress), dan Repo terakhir diperbarui.
   - **Stacked Bar Bahasa**: Distribusi bahasa 3 bulan terakhir dengan legend di bawahnya.
   - **Heatmap 12 Minggu**: Menampilkan 84 kotak kontribusi kalender asli.
   - **Aktivitas Terbaru**: 3 aksi qualifying terbaru.
   - **Social Badges**: Tombol klik ke LinkedIn, Email, Instagram, dan GitHub.

---

## 7. Cara Kerja Pembaruan Otomatis (Setiap Jam)

File `.github/workflows/update-dashboard.yml` telah diprogram dengan cron:
```yaml
schedule:
  - cron: '0 * * * *'
```
- Setiap jam pada menit ke-0 (UTC), GitHub Actions akan bangun secara otomatis di cloud server GitHub.
- Script Python akan mengambil data aktivitas terbaru Anda.
- Jika ada commit baru atau perubahan waktu, SVG dashboard akan diperbarui.
- Commit otomatis dari bot (`github-actions[bot]`) diberi tag `[skip ci]` dan secara eksplisit **dikecualikan** dari statistik kontribusi pribadi sehingga tidak mengotori grafik aktivitas coding Anda sendiri.
- Jika tidak ada perubahan data, workflow akan melewatinya (*skip commit*) tanpa membuat commit sia-sia.

---

## 8. Panduan Mengubah Konfigurasi Pribadi

Semua informasi profil dapat diatur dengan mudah melalui file [`config/profile.json`](../config/profile.json) tanpa perlu menyentuh kode program:

- `display_name`: Nama tampilan Anda.
- `subtitle`: Keterangan status atau kampus.
- `collaboration_status`: Teks pada pill badge hijau.
- `collaboration_available`: `true` untuk menampilkan badge, `false` untuk menyembunyikan.
- `locale`: `"id"` untuk Bahasa Indonesia (sesuai gambar referensi) atau `"en"` untuk Bahasa Inggris.
- `timezone`: Zona waktu (default: `"Asia/Jakarta"`).
- `social_links`: Tautan ke akun LinkedIn, Instagram, Email, dan GitHub Anda.

Setelah mengubah file tersebut, cukup `git commit` dan `git push`, maka GitHub Actions akan langsung memperbarui tampilan dashboard Anda.

---

## 9. Troubleshooting & FAQ

### Q1: Workflow gagal dengan error "Permission to user/repo denied to github-actions[bot]"
**Solusi**: Pastikan Anda telah menyelesaikan **Langkah 3** di atas (Ubah *Workflow permissions* di Settings > Actions > General menjadi *Read and write permissions*).

### Q2: Gambar di profil belum berubah setelah commit baru
**Solusi**: GitHub menggunakan sistem caching gambar proxy bernama *Camo*. Untuk memicu refresh gambar di browser Anda, tekan `Ctrl + F5` (Hard Refresh) atau tunggu beberapa menit hingga cache Camo ter-refresh.

### Q3: Apakah saya perlu membuat Personal Access Token (PAT)?
**Solusi**: **Tidak wajib!** Repositori ini telah dikonfigurasi menggunakan `secrets.GITHUB_TOKEN` bawaan GitHub Actions yang otomatis tersedia secara gratis dan aman. Jika di masa mendatang Anda ingin memasukkan kontribusi dari repositori *Private*, Anda cukup membuat fine-grained PAT dengan scope *read repository & contributions* dan menambahkannya ke *Repository Secrets*.

---
*Dibuat khusus untuk profil GitHub **@Zakkyaulia**.*
