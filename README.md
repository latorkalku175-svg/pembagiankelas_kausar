# GuruKelas

Aplikasi web untuk membantu guru mengelola kelas, dibangun dengan **Django**. Dibuat berdasarkan desain dashboard "GuruKelas" — sidebar navigasi, header sapaan, kartu cluster siswa (Cerdas / Pintar / Malas), dan menu Fitur Cepat.

## Fitur

- **Login** — autentikasi guru dengan Django Auth.
- **Beranda** — ringkasan jumlah siswa per kategori cluster dan akses cepat ke fitur utama.
- **Kelas** — membuat kelas, menambah/mengedit/menghapus siswa beserta nilai akademiknya.
- **Cluster** — pengelompokan siswa otomatis menjadi **Cerdas / Pintar / Malas** menggunakan algoritma **K-Means** (scikit-learn) berdasarkan nilai matematika, nilai bahasa, kehadiran, dan keaktifan. Tombol "Jalankan Ulang K-Means" untuk menghitung ulang kapan saja.
- **Math Perbangku** — denah tingkat pemahaman matematika siswa dikelompokkan per nomor meja.
- **Upload File** — guru dapat membagikan file materi ke siswa di kelas yang sedang aktif.
- **Riwayat Laporan** — riwayat aktivitas guru: jumlah upload Excel per guru, waktu login terakhir, tanggal bergabung, dan log detail setiap upload Excel.
- **Pengaturan** — edit profil guru dan ubah password.
- Mendukung banyak kelas sekaligus, dipilih lewat dropdown di header.

## Struktur Proyek

```
gurukelas_project/   # Konfigurasi proyek Django (settings, urls)
dashboard/           # App utama: models, views, forms, clustering, admin
  clustering.py      # Logika K-Means untuk pengelompokan siswa
templates/           # Template HTML (base.html + halaman per fitur)
static/css/          # CSS kustom (selain Tailwind via CDN)
```

## Cara Menjalankan

1. **Buat virtual environment & install dependensi**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Jalankan migrasi database**
   ```bash
   python manage.py migrate
   ```
   *(Database `db.sqlite3` yang disertakan sudah berisi data contoh — langkah ini hanya diperlukan jika Anda memulai dari database baru.)*

3. **Jalankan server**
   ```bash
   python manage.py runserver
   ```
   Buka [http://127.0.0.1:8000](http://127.0.0.1:8000) di browser.

### Login

Buat akun guru/admin sendiri dengan `python manage.py createsuperuser`, lalu kelola data lewat halaman admin di `/admin/`.

## Tentang Clustering K-Means

Setiap siswa memiliki 4 atribut: nilai matematika, nilai bahasa, persentase kehadiran, dan skor keaktifan. Saat tombol **"Jalankan K-Means"** ditekan, sistem menjalankan `KMeans(n_clusters=3)` dari scikit-learn terhadap seluruh siswa di kelas aktif. Tiga cluster yang dihasilkan kemudian diberi label **Cerdas**, **Pintar**, dan **Malas** berdasarkan skor komposit (rata-rata terbobot dari keempat atribut) — cluster dengan skor tertinggi menjadi "Cerdas", terendah menjadi "Malas". Logika ini ada di `dashboard/clustering.py` dan dapat disesuaikan bobot maupun jumlah fiturnya.

## Catatan Produksi

Proyek ini dikonfigurasi untuk pengembangan lokal (`DEBUG = True`, `SECRET_KEY` contoh, SQLite). Sebelum deploy ke produksi:
- Set `DEBUG = False` dan isi `ALLOWED_HOSTS`.
- Ganti `SECRET_KEY` dengan nilai rahasia baru (mis. lewat environment variable).
- Gunakan database produksi (PostgreSQL, dll).
- Konfigurasikan penyimpanan file (`MEDIA_ROOT`) dan static files (`collectstatic`) sesuai server Anda.
# pembagiankelas_kausar
# pembagiankelas_kausar
