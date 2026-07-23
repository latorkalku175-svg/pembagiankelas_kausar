"""
Logika clustering K-Means untuk mengelompokkan siswa menjadi tiga kategori:
Cerdas, Pintar, dan Malas.

Pipeline ini mengikuti versi REVISI pada notebook
`Clustering_kausar8_sekolah.ipynb` (lihat bagian "Feature Engineering &
Clustering"). Versi awal dulu menjalankan KMeans langsung di atas fitur
mentah (nilai akademik + Izin/Sakit/Alpa), tapi karena Izin/Sakit/Alpa
mayoritas bernilai 0, hasilnya melenceng -- KMeans jadi membelah siswa
berdasarkan "pernah absen atau enggak", bukan berdasarkan nilai akademiknya.

Perbaikannya: dihitung dulu dua skor komposit per siswa di ruang z-score,
baru KMeans (k=3) dijalankan di ruang 2 dimensi ini (bukan fitur mentah):

    Skor_Akademik = z(Eksakta) + z(NonEksakta) - z(Rangking)
    Skor_Disiplin = -(z(Izin) + z(Sakit) + 3 * z(Alpa))

(Rangking/Izin/Sakit/Alpa: makin kecil makin bagus, jadi tandanya dibalik.
Alpa diberi bobot x3 karena bolos tanpa keterangan adalah indikator "malas"
paling kuat, beda dari Izin/Sakit yang ada alasannya.)

Cluster lalu dilabel otomatis berdasarkan rata-rata skor total
(Skor_Akademik + Skor_Disiplin) tiap cluster: cluster dengan skor tertinggi
diberi label "Cerdas", menengah "Pintar", terendah "Malas". Logika ini
identik dengan yang dipakai saat import Excel di
`excel_import.py::proses_upload_dan_cluster`, supaya hasil "Jalankan ulang
clustering" manual selalu konsisten dengan hasil import.

PENTING -- digabung per TINGKAT, bukan per rombel (kelas):
Sama seperti saat upload Excel (proses_upload_dan_cluster menggabungkan
semua file/rombel yang diupload bareng jadi satu `df_sekolah` sebelum
dilatih KMeans-nya), run_clustering() di sini JUGA menggabungkan seluruh
siswa dari semua kelas dengan tingkat yang sama milik guru yang sama
(mis. "Kelas 1A" + "Kelas 1B" digabung jadi satu populasi "Tingkat 1")
sebelum dilatih. Kalau tiap rombel di-cluster sendiri-sendiri secara
terpisah, z-score & KMeans-nya jadi dihitung dari populasi yang beda-beda
(dan kalau muridnya sedikit, hasilnya gampang melenceng/tidak sebanding
antar rombel). Hasil cluster tetap disimpan ke masing-masing siswa sesuai
kelasnya sendiri (1A tetap 1A, 1B tetap 1B) -- yang digabung cuma
perhitungannya, bukan datanya.
"""
from django.utils import timezone
import pandas as pd
from sklearn.cluster import KMeans


def _zscore(s):
    """Z-score sebuah pandas Series. Kalau std-nya 0/NaN (semua nilai sama),
    kembalikan 0 di semua baris -- supaya fitur itu tidak ikut membelah
    cluster (bukannya error pembagian dengan nol)."""
    std = s.std(ddof=0)
    if not std or pd.isna(std):
        return s * 0.0
    return (s - s.mean()) / std


def _kumpulkan_kelas_setingkat(kelas):
    """
    Kembalikan daftar semua objek Kelas milik guru yang sama & tingkat yang
    sama dengan `kelas` (termasuk `kelas` itu sendiri) -- mis. dari "Kelas 1A"
    akan ikut ditemukan "Kelas 1B", "Kelas 1C", dst kalau ada.

    Kalau tingkat kelas tidak terdeteksi dari namanya (properti `tingkat`
    mengembalikan None), kembalikan cuma kelas itu sendiri supaya tidak
    sengaja tergabung dengan kelas lain yang sebenarnya tidak berhubungan.
    """
    if kelas.tingkat is None:
        return [kelas]

    # Import di sini (bukan di top-level) untuk menghindari import melingkar
    # antara models.py <-> clustering.py.
    from .models import Kelas

    sekelompok = [
        k for k in Kelas.objects.filter(guru=kelas.guru)
        if k.tingkat == kelas.tingkat
    ]
    # Pastikan `kelas` sendiri selalu ikut walau query di atas entah kenapa
    # tidak menyertakannya (mis. baru saja dibuat & belum ke-refresh).
    if not any(k.id == kelas.id for k in sekelompok):
        sekelompok.append(kelas)
    return sekelompok


def _kumpulkan_fitur(siswa_qs):
    """
    Susun DataFrame KelasId/Eksakta/NonEksakta/Rangking/Izin/Sakit/Alpa per
    siswa, sejajar urutannya dengan `siswa_qs`.

    Mengutamakan fitur hasil import leger Excel (siswa.eksakta, siswa.izin,
    dst -- lihat excel_import.py) kalau tersedia, supaya hasilnya identik
    dengan notebook. Untuk siswa yang diinput manual lewat form (belum
    pernah diisi lewat upload Excel, jadi eksakta/nonekstakta/rangking-nya
    masih kosong), dipakai nilai_matematika/nilai_bahasa sebagai gantinya,
    dan Rangking yang masih kosong dihitung dari rata-rata nilai akademik
    DI DALAM KELASNYA SENDIRI (bukan digabung rombel lain) -- persis seperti
    notebook: `df_sekolah.groupby('Kelas')['Nilai_Akademik_Rata2'].rank(...)`.
    """
    df = pd.DataFrame({
        "KelasId": [s.kelas_id for s in siswa_qs],
        "Eksakta": [s.eksakta if s.eksakta is not None else s.nilai_matematika for s in siswa_qs],
        "NonEksakta": [s.nonekstakta if s.nonekstakta is not None else s.nilai_bahasa for s in siswa_qs],
        "Izin": [s.izin or 0.0 for s in siswa_qs],
        "Sakit": [s.sakit or 0.0 for s in siswa_qs],
        "Alpa": [s.alpa or 0.0 for s in siswa_qs],
        "Rangking": [s.rangking for s in siswa_qs],
    })

    if df["Rangking"].isna().any():
        nilai_akademik_rata2 = (df["Eksakta"] + df["NonEksakta"]) / 2
        rangking_per_kelas = nilai_akademik_rata2.groupby(df["KelasId"]).rank(
            method="min", ascending=False
        )
        # fillna: kolom Rangking yang SUDAH ada (mis. dari upload Excel)
        # dipertahankan apa adanya, cuma yang kosong (siswa manual) yang diisi.
        df["Rangking"] = df["Rangking"].fillna(rangking_per_kelas)

    return df


def _label_berdasarkan_peringkat(skor_total):
    """
    Urutkan siswa berdasarkan skor_total (tertinggi -> terendah), lalu bagi
    rata ke 3 kelompok berdasarkan urutannya: sepertiga teratas -> Cerdas,
    sepertiga tengah -> Pintar, sepertiga bawah -> Malas.

    Dipakai sebagai fallback di dua kondisi:
    1. Siswa kurang dari 3 orang (K-Means butuh minimal sebanyak jumlah cluster).
    2. K-Means "degenerate" -- titik datanya identik/kurang variasi sehingga
       cluster yang terbentuk kurang dari 3 (lihat ConvergenceWarning sklearn:
       "Number of distinct clusters (...) found smaller than n_clusters").
    """
    n = len(skor_total)
    urutan = skor_total.sort_values(ascending=False).index.tolist()
    label_terurut = ["cerdas", "pintar", "malas"]
    return {idx: label_terurut[min(rank * 3 // n, 2)] for rank, idx in enumerate(urutan)}


def run_clustering(kelas):
    """
    Menjalankan K-Means (k=3) terhadap seluruh siswa dari `kelas` DIGABUNG
    dengan siswa dari kelas lain yang setingkat & milik guru yang sama
    (mis. "Kelas 1A" otomatis digabung dengan "Kelas 1B" kalau ada) --
    supaya perhitungan z-score & KMeans-nya konsisten dengan hasil upload
    Excel di excel_import.py, yang juga menggabungkan seluruh rombel
    setingkat dalam satu kali proses.

    Hasil cluster tetap disimpan ke masing-masing siswa sesuai kelas
    aslinya masing-masing (bukan dipindah/dicampur kelasnya).

    Mengembalikan dict ringkasan CUMA untuk siswa di `kelas` yang diminta
    (bukan seluruh gabungan), supaya tampilan "Cluster Siswa – Kelas 1A"
    tetap menunjukkan angka 1A saja walau perhitungannya sudah digabung
    dengan 1B.
    """
    kelompok_kelas = _kumpulkan_kelas_setingkat(kelas)

    siswa_qs = []
    for k in kelompok_kelas:
        siswa_qs.extend(list(k.siswa_list.all()))
    n = len(siswa_qs)

    ringkasan = {"cerdas": 0, "pintar": 0, "malas": 0}
    if n == 0:
        return ringkasan

    fitur = _kumpulkan_fitur(siswa_qs)
    skor_akademik = _zscore(fitur["Eksakta"]) + _zscore(fitur["NonEksakta"]) - _zscore(fitur["Rangking"])
    skor_disiplin = -(_zscore(fitur["Izin"]) + _zscore(fitur["Sakit"]) + 3 * _zscore(fitur["Alpa"]))
    skor_total = skor_akademik + skor_disiplin

    now = timezone.now()

    def _simpan(label_per_idx, cluster_raw_per_idx=None):
        for i in range(n):
            s = siswa_qs[i]
            label = label_per_idx[i]
            s.skor_akademik = round(float(skor_akademik.iloc[i]), 3)
            s.skor_disiplin = round(float(skor_disiplin.iloc[i]), 3)
            s.rangking = float(fitur["Rangking"].iloc[i])
            s.cluster_raw = cluster_raw_per_idx[i] if cluster_raw_per_idx else None
            s.cluster_label = label
            s.cluster_terakhir_diupdate = now
            s.save(update_fields=[
                "skor_akademik", "skor_disiplin", "rangking",
                "cluster_raw", "cluster_label", "cluster_terakhir_diupdate",
            ])
            # Ringkasan yang dikembalikan cuma menghitung siswa dari `kelas`
            # yang diminta, bukan seluruh kelompok setingkat yang digabung.
            if s.kelas_id == kelas.id:
                ringkasan[label] += 1

    if n < 3:
        # Tidak cukup data untuk 3 cluster -- urutkan langsung dari skor total.
        _simpan(_label_berdasarkan_peringkat(skor_total), cluster_raw_per_idx=None)
        return ringkasan

    X_cluster = pd.DataFrame({"Skor_Akademik": skor_akademik, "Skor_Disiplin": skor_disiplin})
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    cluster_idx = kmeans.fit_predict(X_cluster)

    if len(set(cluster_idx)) < 3:
        # K-Means gagal membentuk 3 cluster berbeda (data terlalu seragam/
        # banyak nilai identik, mis. kelas baru yang siswanya belum punya
        # variasi nilai) -- pakai fallback urutan skor_total supaya tetap
        # menghasilkan 3 kategori, bukannya error.
        _simpan(_label_berdasarkan_peringkat(skor_total), cluster_raw_per_idx=None)
        return ringkasan

    # Label tiap cluster berdasarkan rata-rata skor totalnya (tertinggi -> Cerdas).
    skor_total_per_cluster = skor_total.groupby(cluster_idx).mean()
    urutan_cluster = skor_total_per_cluster.sort_values(ascending=False).index.tolist()
    cluster_id_to_label = {
        urutan_cluster[0]: "cerdas",
        urutan_cluster[1]: "pintar",
        urutan_cluster[2]: "malas",
    }
    label_per_idx = {i: cluster_id_to_label[int(cluster_idx[i])] for i in range(n)}
    _simpan(label_per_idx, cluster_raw_per_idx={i: int(cluster_idx[i]) for i in range(n)})

    return ringkasan
