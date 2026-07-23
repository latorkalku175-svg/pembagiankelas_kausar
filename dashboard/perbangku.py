"""
Logika "Atur Meja" untuk fitur Math Perbangku: menyusun ulang nomor_meja
siswa di satu kelas supaya tiap meja (2 siswa) berisi kombinasi kategori
cluster yang berbeda -- bukan dua siswa "cerdas" duduk bareng, atau dua
siswa "malas" duduk bareng.

Aturan pemasangan (diulang berurutan selama masih ada siswa tersisa di
kategori yang dibutuhkan):
    1. Cerdas  + Malas
    2. Pintar  + Cerdas
    3. Pintar  + Malas

Kalau salah satu kategori sudah habis duluan, sisanya dipasangkan
seadanya (termasuk sesama kategori) supaya tetap semua siswa kebagian
meja. Setiap kali fungsi ini dipanggil, urutan di dalam tiap kategori
diacak ulang (request "kalau ga sesuai bisa diacak lagi semuanya").
"""
import random

URUTAN_PASANGAN = [("cerdas", "malas"), ("pintar", "cerdas"), ("pintar", "malas")]


def atur_meja_per_kelas(kelas):
    """
    Susun ulang nomor_meja seluruh siswa pada objek Kelas ini berdasarkan
    kombinasi cluster_label (lihat URUTAN_PASANGAN), lalu simpan ke database.

    Siswa yang belum punya cluster_label (belum pernah di-cluster) diperlakukan
    sebagai kategori "belum" dan dipasangkan paling akhir, seadanya.

    Return: jumlah meja yang terbentuk.
    """
    siswa_list = list(kelas.siswa_list.all())
    if not siswa_list:
        return 0

    kategori = {"cerdas": [], "pintar": [], "malas": [], "belum": []}
    for s in siswa_list:
        kategori.get(s.cluster_label, kategori["belum"]).append(s)

    for grup in kategori.values():
        random.shuffle(grup)

    meja_list = []  # list of [siswa] atau [siswa, siswa]

    # 1) Pasangkan sesuai urutan kombinasi yang diinginkan, selama dua kategori
    #    yang relevan masih punya sisa siswa. Diulang (cycle) terus sampai
    #    salah satu pasangan kategori sama-sama habis.
    progres = True
    while progres:
        progres = False
        for a, b in URUTAN_PASANGAN:
            if kategori[a] and kategori[b]:
                meja_list.append([kategori[a].pop(), kategori[b].pop()])
                progres = True

    # 2) Sisa siswa (kategori yang pasangannya sudah habis, atau "belum"
    #    di-cluster) dipasangkan seadanya, dua-dua, dari gabungan sisa.
    sisa = kategori["cerdas"] + kategori["pintar"] + kategori["malas"] + kategori["belum"]
    random.shuffle(sisa)
    for i in range(0, len(sisa), 2):
        pasangan = sisa[i:i + 2]
        meja_list.append(pasangan)

    # 3) Acak urutan meja juga, supaya nomor meja gak ketebak dari urutan kategori.
    random.shuffle(meja_list)

    for nomor, pasangan in enumerate(meja_list, start=1):
        for s in pasangan:
            s.nomor_meja = nomor
            s.save(update_fields=["nomor_meja"])

    return len(meja_list)
