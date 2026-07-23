import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import Kelas, Siswa, ProfilGuru
from dashboard.clustering import run_clustering

NAMA_DEPAN = [
    "Aditya", "Bunga", "Citra", "Dewi", "Eka", "Farhan", "Gita", "Hadi",
    "Indah", "Joko", "Kirana", "Lukman", "Mawar", "Nadia", "Oka", "Putri",
    "Qory", "Rama", "Sinta", "Tegar", "Umi", "Vino", "Wulan", "Xena",
    "Yusuf", "Zahra", "Arka", "Bella", "Caca", "Dimas",
]


class Command(BaseCommand):
    help = "Mengisi data contoh: akun guru Bu Rina, Kelas 1A, dan 30 siswa, lalu menjalankan K-Means."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Hapus data lama sebelum mengisi ulang.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Kelas.objects.filter(guru__username="rina").delete()

        user, created = User.objects.get_or_create(
            username="rina",
            defaults={"first_name": "Rina", "email": "rina@gurukelas.test"},
        )
        if created:
            user.set_password("gurukelas123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Akun guru 'rina' dibuat (password: gurukelas123)"))

        ProfilGuru.objects.get_or_create(user=user, defaults={"sapaan": "Bu", "sekolah": "SD Harapan Bangsa"})

        kelas, _ = Kelas.objects.get_or_create(nama="Kelas 1A", guru=user)

        if kelas.siswa_list.exists():
            self.stdout.write("Kelas 1A sudah memiliki siswa, lewati seeding siswa.")
        else:
            random.seed(7)
            nama_pool = random.sample(NAMA_DEPAN, 30)
            profil_siswa = (
                [self._buat_profil("cerdas") for _ in range(10)]
                + [self._buat_profil("pintar") for _ in range(12)]
                + [self._buat_profil("malas") for _ in range(8)]
            )
            random.shuffle(profil_siswa)

            for i, (nama, profil) in enumerate(zip(nama_pool, profil_siswa), start=1):
                Siswa.objects.create(
                    kelas=kelas,
                    nama=nama,
                    nomor_meja=((i - 1) // 2) + 1,  # 2 siswa per meja
                    nilai_matematika=profil["matematika"],
                    nilai_bahasa=profil["bahasa"],
                    kehadiran_persen=profil["kehadiran"],
                    keaktifan=profil["keaktifan"],
                )
            self.stdout.write(self.style.SUCCESS("30 siswa contoh berhasil dibuat di Kelas 1A."))

        ringkasan = run_clustering(kelas)
        self.stdout.write(self.style.SUCCESS(f"Clustering K-Means selesai: {ringkasan}"))

    @staticmethod
    def _buat_profil(kategori):
        if kategori == "cerdas":
            return {
                "matematika": round(random.uniform(85, 98), 1),
                "bahasa": round(random.uniform(82, 96), 1),
                "kehadiran": round(random.uniform(92, 100), 1),
                "keaktifan": round(random.uniform(80, 97), 1),
            }
        if kategori == "pintar":
            return {
                "matematika": round(random.uniform(65, 82), 1),
                "bahasa": round(random.uniform(62, 80), 1),
                "kehadiran": round(random.uniform(78, 92), 1),
                "keaktifan": round(random.uniform(55, 75), 1),
            }
        return {  # malas
            "matematika": round(random.uniform(35, 58), 1),
            "bahasa": round(random.uniform(32, 56), 1),
            "kehadiran": round(random.uniform(50, 72), 1),
            "keaktifan": round(random.uniform(25, 48), 1),
        }
