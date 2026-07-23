"""
Logika "Naik Kelas": menggabungkan siswa dari kelas-kelas satu tingkat yang
sudah di-cluster (mis. Kelas 1A + Kelas 1B), lalu menyebar mereka secara rata
ke kelas-kelas baru di tingkat berikutnya (mis. Kelas 2A & Kelas 2B) supaya
tiap kelas baru mendapat campuran kategori cluster (Cerdas/Pintar/Malas) yang
seimbang -- bukan menjalankan K-Means ulang, cukup membagi rata hasil cluster
yang sudah ada.

Siswa DIPINDAH (bukan disalin): riwayat nilai/skor siswa tetap melekat di
data siswa itu sendiri (ikut pindah ke kelas barunya). Kelas-kelas tingkat
lama otomatis DIHAPUS begitu seluruh siswanya selesai dipindah, supaya tidak
ada lagi "riwayat" kelas kosong yang nyangkut di daftar kelas guru.
"""
import random
import re
import string

from .models import Kelas, Siswa

URUTAN_LABEL = ["cerdas", "pintar", "malas", None]  # None = belum sempat di-cluster


def ekstrak_tingkat(nama_kelas: str):
    """'Kelas 1A' -> 1, 'Kelas 2 B' -> 2, 'Kelas Unggulan' -> None."""
    m = re.search(r"\d+", nama_kelas or "")
    return int(m.group()) if m else None


def get_kelas_per_tingkat(guru):
    """
    Mengelompokkan semua Kelas milik `guru` berdasarkan tingkat (angka) yang
    terdeteksi dari namanya. Kelas yang namanya tidak mengandung angka
    (tidak bisa ditentukan tingkatnya) tidak diikutsertakan.

    Return: dict {tingkat: [Kelas, ...]}, terurut dari tingkat terkecil.
    """
    kelompok = {}
    for k in Kelas.objects.filter(guru=guru).order_by("nama"):
        t = ekstrak_tingkat(k.nama)
        if t is None:
            continue
        kelompok.setdefault(t, []).append(k)
    return dict(sorted(kelompok.items()))


def bagi_rata_berdasarkan_cluster(siswa_list, jumlah_kelas_baru):
    """
    Membagi `siswa_list` ke `jumlah_kelas_baru` kelompok secara round-robin
    PER label cluster, supaya tiap kelompok hasil akhirnya dapat proporsi
    Cerdas/Pintar/Malas yang seimbang satu sama lain.

    Return: list berisi `jumlah_kelas_baru` list Siswa.
    """
    kelompok = [[] for _ in range(jumlah_kelas_baru)]

    offset = 0
    for label in URUTAN_LABEL:
        anggota = [s for s in siswa_list if s.cluster_label == label]
        random.shuffle(anggota)
        for i, s in enumerate(anggota):
            kelompok[(i + offset) % jumlah_kelas_baru].append(s)
        # geser offset supaya "sisa" pembagian (kalau jumlahnya tidak habis
        # dibagi rata) tidak selalu numpuk di kelas yang sama untuk tiap label
        offset += len(anggota) % jumlah_kelas_baru

    return kelompok


def proses_naik_kelas(guru, tingkat_asal: int):
    """
    Menjalankan proses naik kelas untuk seluruh siswa di kelas-kelas
    bertingkat `tingkat_asal` milik `guru`.

    Return: dict ringkasan hasil. Raise ValueError kalau tidak ada kelas/siswa.
    """
    kelompok_tingkat = get_kelas_per_tingkat(guru)
    kelas_asal_list = kelompok_tingkat.get(tingkat_asal, [])
    if not kelas_asal_list:
        raise ValueError(f"Tidak ada kelas tingkat {tingkat_asal} yang ditemukan.")

    siswa_list = list(Siswa.objects.filter(kelas__in=kelas_asal_list))
    if not siswa_list:
        raise ValueError("Tidak ada siswa di kelas-kelas tingkat tersebut untuk dinaikkan.")

    jumlah_belum_cluster = sum(1 for s in siswa_list if not s.cluster_label)

    jumlah_kelas_baru = len(kelas_asal_list)
    tingkat_baru = tingkat_asal + 1
    kelompok_siswa = bagi_rata_berdasarkan_cluster(siswa_list, jumlah_kelas_baru)

    huruf = string.ascii_uppercase
    ringkasan_kelas_baru = []

    for i, anggota in enumerate(kelompok_siswa):
        nama_kelas_baru = f"Kelas {tingkat_baru}{huruf[i % len(huruf)]}"
        kelas_baru, _ = Kelas.objects.get_or_create(guru=guru, nama=nama_kelas_baru)

        meja = kelas_baru.siswa_list.count() + 1
        for s in anggota:
            s.kelas = kelas_baru
            s.nomor_meja = meja
            s.save(update_fields=["kelas", "nomor_meja"])
            meja += 1

        hitung = {"cerdas": 0, "pintar": 0, "malas": 0, "belum": 0}
        for s in anggota:
            if s.cluster_label in ("cerdas", "pintar", "malas"):
                hitung[s.cluster_label] += 1
            else:
                hitung["belum"] += 1

        ringkasan_kelas_baru.append({
            "kelas": kelas_baru,
            "jumlah": len(anggota),
            **hitung,
        })

    # Kelas asal sudah kosong (semua siswanya barusan dipindah ke kelas baru
    # di atas) -- hapus otomatis supaya tidak menyisakan "riwayat" kelas
    # tingkat lama yang sudah tidak terpakai lagi di daftar kelas guru.
    # Nama-namanya disimpan dulu sebelum dihapus, dipakai buat pesan sukses
    # di view (setelah .delete() objeknya tidak bisa dipakai lagi).
    nama_kelas_asal = [k.nama for k in kelas_asal_list]
    Kelas.objects.filter(id__in=[k.id for k in kelas_asal_list]).delete()

    return {
        "tingkat_asal": tingkat_asal,
        "tingkat_baru": tingkat_baru,
        "nama_kelas_asal": nama_kelas_asal,
        "ringkasan_kelas_baru": ringkasan_kelas_baru,
        "jumlah_siswa": len(siswa_list),
        "jumlah_belum_cluster": jumlah_belum_cluster,
    }
