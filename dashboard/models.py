from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Kelas(models.Model):
    """Sebuah kelas yang dikelola oleh seorang guru, mis. 'Kelas 1A'."""
    nama = models.CharField(max_length=50)
    guru = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kelas_list")
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Kelas"
        ordering = ["nama"]

    def __str__(self):
        return self.nama

    @property
    def jumlah_siswa(self):
        return self.siswa_list.count()

    @property
    def tingkat(self):
        """Angka tingkat yang terdeteksi dari nama kelas, mis. 'Kelas 1A' → 1. None kalau tidak ada angka."""
        import re
        m = re.search(r"\d+", self.nama or "")
        return int(m.group()) if m else None


class Siswa(models.Model):
    """Seorang siswa di dalam kelas, dengan data yang dipakai untuk clustering K-Means."""

    CLUSTER_CHOICES = [
        ("cerdas", "Cerdas"),
        ("pintar", "Pintar"),
        ("malas", "Malas"),
    ]

    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name="siswa_list")
    nama = models.CharField(max_length=100)

    # Identitas siswa dari leger rapor (diisi otomatis saat import Excel)
    nis = models.CharField(max_length=30, blank=True, default="")
    nisn = models.CharField(max_length=30, blank=True, default="")

    # Data mentah yang dipakai sebagai fitur K-Means
    nilai_matematika = models.FloatField(
        default=70, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    nilai_bahasa = models.FloatField(
        default=70, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    kehadiran_persen = models.FloatField(
        default=90, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Persentase kehadiran siswa"
    )
    keaktifan = models.FloatField(
        default=70, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Skor keaktifan di kelas (0-100)"
    )

    # Fitur tambahan hasil import leger Excel (lihat dashboard/excel_import.py),
    # dipakai oleh run_clustering() di dashboard/clustering.py supaya hasilnya
    # sama persis seperti pipeline di notebook (Skor_Akademik & Skor_Disiplin
    # berbasis z-score).
    eksakta = models.FloatField(null=True, blank=True, help_text="Rata-rata nilai eksakta (Matematika)")
    nonekstakta = models.FloatField(null=True, blank=True, help_text="Rata-rata nilai non-eksakta")
    izin = models.FloatField(default=0)
    sakit = models.FloatField(default=0)
    alpa = models.FloatField(default=0)
    rangking = models.FloatField(null=True, blank=True, help_text="Rangking di dalam kelasnya")
    skor_akademik = models.FloatField(null=True, blank=True)
    skor_disiplin = models.FloatField(null=True, blank=True)
    jumlah_ekstrakurikuler = models.PositiveIntegerField(
        default=0, help_text="Jumlah kegiatan ekstrakurikuler yang diikuti siswa"
    )

    # Posisi meja, dipakai oleh fitur Math Perbangku (denah tempat duduk)
    nomor_meja = models.PositiveIntegerField(default=1)

    # Hasil clustering K-Means, diisi otomatis oleh fungsi run_clustering()
    cluster_label = models.CharField(
        max_length=10, choices=CLUSTER_CHOICES, blank=True, null=True
    )
    cluster_raw = models.IntegerField(
        null=True, blank=True,
        help_text="ID cluster mentah dari KMeans (0/1/2) sebelum dilabeli"
    )
    cluster_terakhir_diupdate = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Siswa"
        ordering = ["nomor_meja", "nama"]

    def __str__(self):
        return f"{self.nama} ({self.kelas.nama})"

    @property
    def pemahaman_matematika(self):
        """Kategori pemahaman matematika per siswa, dipakai di Math Perbangku."""
        if self.nilai_matematika >= 80:
            return "paham"
        elif self.nilai_matematika >= 60:
            return "cukup"
        return "kurang"


class MateriUpload(models.Model):
    """File materi yang dibagikan guru ke siswa di suatu kelas."""
    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name="materi_list")
    judul = models.CharField(max_length=150)
    deskripsi = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="materi/%Y/%m/")
    diupload_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-diupload_pada"]
        verbose_name_plural = "Materi Upload"

    def __str__(self):
        return self.judul

    @property
    def nama_file(self):
        return self.file.name.split("/")[-1]


class RiwayatUploadXlsx(models.Model):
    """
    Catatan setiap kali file Excel leger diupload untuk melatih K-Means --
    siapa yang upload (guru pemilik kelas, atau superuser yang upload-kan
    untuk guru lain) dan untuk kelas mana.
    """
    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name="riwayat_upload")
    diupload_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="riwayat_upload_xlsx",
        help_text="User yang melakukan upload (bisa guru pemilik kelas atau superuser).",
    )
    nama_file = models.CharField(max_length=255)
    jumlah_siswa = models.PositiveIntegerField(default=0)
    diupload_pada = models.DateTimeField(auto_now_add=True)
    file_asli = models.FileField(
        upload_to="riwayat_upload_xlsx/%Y/%m/",
        null=True,
        blank=True,
        help_text="Salinan file Excel asli yang diupload, dipakai untuk diunduh kembali.",
    )

    class Meta:
        ordering = ["-diupload_pada"]
        verbose_name = "Riwayat Upload Xlsx"
        verbose_name_plural = "Riwayat Upload Xlsx"

    def __str__(self):
        return f"{self.nama_file} → {self.kelas.nama}"


class RiwayatPerbangku(models.Model):
    """
    Catatan setiap kali posisi meja (Math Perbangku) sebuah kelas diatur /
    diacak ulang -- kelas mana, siapa yang mengatur, dan berapa meja
    yang dihasilkan.
    """
    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name="riwayat_perbangku")
    diatur_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="riwayat_perbangku",
        help_text="User yang menjalankan pengaturan ulang posisi meja.",
    )
    jumlah_meja = models.PositiveIntegerField(default=0)
    jumlah_siswa = models.PositiveIntegerField(default=0)
    diatur_pada = models.DateTimeField(auto_now_add=True)
    snapshot = models.JSONField(
        default=dict, blank=True,
        help_text="Salinan susunan meja & data siswa saat itu, dipakai untuk preview/unduh riwayat.",
    )

    class Meta:
        ordering = ["-diatur_pada"]
        verbose_name = "Riwayat Perbangku"
        verbose_name_plural = "Riwayat Perbangku"

    def __str__(self):
        return f"{self.kelas.nama} — {self.jumlah_meja} meja"


class RiwayatClusterKmeans(models.Model):
    """
    Catatan setiap kali clustering K-Means dijalankan -- baik lewat tombol
    'Jalankan Ulang K-Means' di halaman Cluster, maupun otomatis saat guru
    upload Excel leger (proses_upload_dan_cluster). Menyimpan kelas/tingkat
    mana, siapa yang menjalankan, ringkasan jumlah Cerdas/Pintar/Malas, dan
    snapshot lengkap hasil per siswa supaya preview/unduh PDF riwayat lama
    tetap menampilkan hasil persis seperti saat itu, walau data siswa
    berubah/di-cluster ulang belakangan.
    """
    SUMBER_CHOICES = [
        ("manual", "Jalankan Ulang Manual"),
        ("upload_excel", "Upload Excel"),
    ]

    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name="riwayat_cluster")
    dijalankan_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="riwayat_cluster_kmeans",
        help_text="User yang menjalankan clustering (guru pemilik kelas atau superuser).",
    )
    judul_kelas = models.CharField(
        max_length=150, blank=True, default="",
        help_text="Judul gabungan kelas setingkat saat itu, mis. 'Kelas 1A dan 1B'.",
    )
    jumlah_siswa = models.PositiveIntegerField(default=0)
    jumlah_cerdas = models.PositiveIntegerField(default=0)
    jumlah_pintar = models.PositiveIntegerField(default=0)
    jumlah_malas = models.PositiveIntegerField(default=0)
    sumber = models.CharField(max_length=20, choices=SUMBER_CHOICES, default="manual")
    dijalankan_pada = models.DateTimeField(auto_now_add=True)
    snapshot = models.JSONField(
        default=dict, blank=True,
        help_text="Salinan hasil clustering per siswa saat itu, dipakai untuk preview/unduh riwayat.",
    )

    class Meta:
        ordering = ["-dijalankan_pada"]
        verbose_name = "Riwayat Cluster K-Means"
        verbose_name_plural = "Riwayat Cluster K-Means"

    def __str__(self):
        return f"{self.judul_kelas or self.kelas.nama} — {self.jumlah_siswa} siswa"


class ProfilGuru(models.Model):
    """Pengaturan tambahan untuk akun guru, dipakai di halaman Pengaturan."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil")
    sapaan = models.CharField(max_length=50, default="Bu")
    gelar = models.CharField(max_length=100, blank=True, help_text="Contoh: S.Pd., M.Pd.")
    sekolah = models.CharField(max_length=150, blank=True)
    wali_kelas = models.CharField(max_length=50, blank=True, help_text="Contoh: 1B, 2A")
    notifikasi_email = models.BooleanField(default=True)
    foto = models.ImageField(upload_to="foto_guru/", blank=True, null=True)

    def __str__(self):
        return f"Profil {self.user.username}"
