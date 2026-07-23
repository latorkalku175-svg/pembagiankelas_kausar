"""
Import data siswa dari file Excel leger rapor (format yang sama dengan yang
dipakai di notebook `Clustering_kausar8_sekolah.ipynb`), lalu latih K-Means
dan simpan hasilnya ke database -- otomatis terpisah per kelas asalnya
(mis. Kelas 1A, 1B, 2A, 2B, ...).

Pipeline ini sengaja meniru notebook persis:
1. Tiap file = 1 kelas (nama kelas dideteksi dari nama file).
2. Tiap file dirapihkan strukturnya (skiprows=6, nama kolom leger standar).
3. Semua kelas digabung jadi satu dataframe satu sekolah.
4. Skor_Akademik & Skor_Disiplin dihitung pakai z-score di seluruh data
   gabungan (bukan per kelas) -- supaya adil dibanding satu sekolah penuh.
5. K-Means (k=3) dijalankan SEKALI untuk seluruh siswa yang diupload.
6. Cluster diberi label Cerdas/Pintar/Malas berdasarkan skor totalnya.
7. Hasilnya disimpan ke Siswa, dikelompokkan kembali ke Kelas asalnya
   (dibuat otomatis kalau belum ada).
"""
import re

import numpy as np
import pandas as pd
from django.utils import timezone
from sklearn.cluster import KMeans

from .models import Kelas, Siswa, RiwayatUploadXlsx

# ---------------------------------------------------------------------------
# Struktur kolom leger (sama seperti KONFIGURASI_KELAS di notebook)
# ---------------------------------------------------------------------------
KOLOM_AWAL = ["No", "Nama_Siswa", "NISN", "NIS", "PAIDBP"]
KOLOM_NILAI = ["PP", "BI_Indo", "MU", "PJODK", "SR", "BI_Inggris", "PLBJ"]
KOLOM_AKHIR = ["Sakit", "Izin", "Alpa", "Menari", "Pramuka_Siaga", "Melukis"]

# kolom nilai eksakta vs non-eksakta (dipakai utk Skor_Akademik)
EKSAKTA_COLS = ["MU"]
NONEKSAKTA_COLS = ["Nilai_Agama", "PP", "BI_Indo", "PJODK", "BI_Inggris", "SR", "PLBJ"]
ABSEN_COLS = ["Izin", "Sakit", "Alpa"]

# Label kelas yang filenya punya kolom PAKDBP tambahan (selain PAIDBP), sesuai
# KONFIGURASI_KELAS di notebook -- cuma 1A. Dipakai sebagai aturan pasti karena
# nebak dari isi data gak reliable kalau blok nilai & absen nempel tanpa jarak
# (GKS-nya udah kosong total / ke-drop duluan, jadi gak ada "celah" pemisah).
LABEL_ADA_PAKDBP = {"1A"}

class ImportError_(ValueError):
    """Dipakai supaya pesan error gampang dibedakan dari ValueError lain."""


def deteksi_label_kelas(nama_file: str) -> str:
    """'f_leger_Kelas 1 A.xlsx' -> '1A', 'Kelas 2B.xlsx' -> '2B', 'kelas_3.xlsx' -> '3'."""
    nama = re.sub(r"\.(xlsx|xls)$", "", nama_file, flags=re.IGNORECASE)
    m = re.search(r"(\d+)\s*[_\-]?\s*([ABab])\b", nama)
    if m:
        return f"{m.group(1)}{m.group(2).upper()}"
    m = re.search(r"(\d+)", nama)
    if m:
        return m.group(1)
    return nama.strip().upper() or "?"


def _rasio_numerik(s: pd.Series) -> float:
    """Berapa persen sel di kolom ini yang keisi nilai angka (bukan huruf predikat/kosong)."""
    terisi = s.dropna()
    if len(terisi) == 0:
        return 0.0
    angka = pd.to_numeric(terisi, errors="coerce")
    return angka.notna().sum() / len(terisi)


def _cari_blok_numerik(mentah: pd.DataFrame, mulai: int, target: int, maks_lompat: int = 3):
    """
    Mulai dari kolom index `mulai`, cari `target` kolom yang isinya mayoritas angka
    (dipakai utk nilai mapel & absensi), sambil melompati kolom non-angka yang nyasar
    di antaranya (mis. kolom GKS yang nyaris kosong, atau predikat huruf B/SB/C).
    Return: list of column index yang dipilih (urut sesuai posisi aslinya).
    """
    dipilih = []
    lompat = 0
    i = mulai
    while i < mentah.shape[1] and len(dipilih) < target:
        if _rasio_numerik(mentah[i]) >= 0.5:
            dipilih.append(i)
            lompat = 0
        else:
            lompat += 1
            if lompat > maks_lompat:
                break
        i += 1
    return dipilih


def baca_file_leger(file_obj, label: str = None, skiprows: int = 6) -> pd.DataFrame:
    """
    Baca 1 file leger Excel & rapihkan strukturnya (setara rapihkan_struktur di notebook).

    Kolom dikenali dari ISI-nya (angka vs predikat huruf) + posisi dari kiri, bukan dari
    total jumlah kolom -- supaya tahan terhadap kolom "siluman" (kosong total, sisa
    formatting) maupun kolom ekstrakurikuler tambahan di ujung kanan yang formatnya
    macem-macem (angka atau predikat huruf B/SB/C), tergantung sekolahnya. Kolom apa pun
    setelah blok Sakit/Izin/Alpa diabaikan (predikat ekstrakurikuler, gak dipakai utk
    clustering).

    `label` (mis. "1A") dipakai buat nentuin ada/tidaknya kolom PAKDBP secara pasti
    (lihat LABEL_ADA_PAKDBP) -- soalnya kalau ditebak dari isi data doang gak reliable
    ketika blok nilai & absen nempel tanpa kolom kosong pemisah di antaranya.
    """
    nama_file = getattr(file_obj, "name", "file")
    try:
        file_obj.seek(0)
    except Exception:  # noqa: BLE001
        pass
    try:
        mentah = pd.read_excel(file_obj, header=None, skiprows=skiprows)
    except Exception as exc:  # noqa: BLE001
        raise ImportError_(f"Gagal membaca '{nama_file}': bukan file Excel yang valid.") from exc

    # Buang kolom yang isinya kosong total dulu (kolom "siluman" sisa formatting Excel).
    mentah = mentah.dropna(axis=1, how="all")
    mentah.columns = range(mentah.shape[1])

    if mentah.shape[1] < 5 + len(KOLOM_NILAI):
        raise ImportError_(
            f"Struktur kolom '{nama_file}' tidak dikenali (cuma {mentah.shape[1]} kolom "
            f"setelah baris ke-{skiprows} dilewati). Pastikan formatnya sama seperti leger "
            f"rapor sekolah."
        )

    # 5 kolom pertama selalu tetap: No, Nama, NISN, NIS, PAIDBP.
    indeks_awal = list(range(5))

    ada_pakdbp = (label or "").upper() in LABEL_ADA_PAKDBP
    indeks_pakdbp = 5 if ada_pakdbp else None
    mulai_nilai = 6 if ada_pakdbp else 5
    indeks_nilai = list(range(mulai_nilai, mulai_nilai + len(KOLOM_NILAI)))
    if indeks_nilai[-1] >= mentah.shape[1] or _rasio_numerik(mentah[indeks_nilai[-1]]) < 0.5:
        raise ImportError_(
            f"Struktur kolom '{nama_file}' tidak dikenali: blok nilai mapel "
            f"({len(KOLOM_NILAI)} kolom) tidak ditemukan di posisi yang diharapkan "
            f"(kelas '{label}', ada_pakdbp={ada_pakdbp})."
        )

    # Setelah blok nilai: cari 3 kolom angka berikutnya = Sakit, Izin, Alpa.
    # Boleh ada kolom non-angka di antaranya (GKS yang nyaris kosong) -- dilompati.
    setelah_nilai = indeks_nilai[-1] + 1
    indeks_absen = _cari_blok_numerik(mentah, setelah_nilai, 3, maks_lompat=3)
    if len(indeks_absen) < 3:
        raise ImportError_(
            f"Struktur kolom '{nama_file}' tidak dikenali: kolom Sakit/Izin/Alpa "
            f"tidak ditemukan setelah blok nilai mapel."
        )

    # Kolom apa pun setelah blok Sakit/Izin/Alpa dianggap kolom ekstrakurikuler
    # (predikat huruf B/SB/C, mis. Menari/Pramuka_Siaga/Melukis) -- dihitung
    # berapa banyak yang terisi per siswa (bukan dipakai sbg fitur clustering),
    # dipakai untuk kolom "Jumlah Ekstrakurikuler" saat data diunduh/diolah.
    setelah_absen = indeks_absen[-1] + 1
    indeks_ekskul = list(range(setelah_absen, mentah.shape[1]))
    if indeks_ekskul:
        jumlah_ekskul_semua = mentah[indeks_ekskul].notna().sum(axis=1)
    else:
        jumlah_ekskul_semua = pd.Series(0, index=mentah.index)

    kolom_dipakai = indeks_awal + ([indeks_pakdbp] if ada_pakdbp else []) + indeks_nilai + indeks_absen
    nama_kolom = (
        list(KOLOM_AWAL)
        + (["PAKDBP"] if ada_pakdbp else [])
        + list(KOLOM_NILAI)
        + ["Sakit", "Izin", "Alpa"]
    )
    # Kolom apa pun di luar `kolom_dipakai` (GKS, predikat ekstrakurikuler, dst)
    # otomatis diabaikan di sini -- gak pernah ikut ke nama_kolom.
    mentah = mentah[kolom_dipakai]
    mentah.columns = nama_kolom
    mentah["Jumlah_Ekstrakurikuler"] = jumlah_ekskul_semua

    df = mentah.dropna(how="all")
    df["NISN"] = df["NISN"].astype(str)
    df["NIS"] = df["NIS"].astype(str)
    df = df[df["No"].notna()].reset_index(drop=True)

    if ada_pakdbp:
        df["Nilai_Agama"] = pd.to_numeric(df["PAIDBP"], errors="coerce").fillna(
            pd.to_numeric(df["PAKDBP"], errors="coerce")
        )
        df = df.drop(columns=["PAIDBP", "PAKDBP"], errors="ignore")
    else:
        df["Nilai_Agama"] = pd.to_numeric(df["PAIDBP"], errors="coerce")
        df = df.drop(columns=["PAIDBP"], errors="ignore")

    if df.empty:
        raise ImportError_(f"File '{nama_file}' tidak punya baris data siswa yang valid.")

    # Samakan skema output dengan baca_file_rekap(): hitung "Eksakta"/"NonEksakta"
    # di sini juga, supaya proses_upload_dan_cluster() gak perlu tahu file ini
    # tadinya format leger apa rekap -- keduanya berakhir dengan kolom yang sama.
    kolom_numerik = [c for c in (EKSAKTA_COLS + NONEKSAKTA_COLS + ["Sakit", "Izin", "Alpa"]) if c in df.columns]
    for c in kolom_numerik:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if kolom_numerik:
        df[kolom_numerik] = df[kolom_numerik].apply(lambda s: s.fillna(s.median()))
        df[kolom_numerik] = df[kolom_numerik].fillna(0.0)

    df["Eksakta"] = df[EKSAKTA_COLS].mean(axis=1)
    df["NonEksakta"] = df[NONEKSAKTA_COLS].mean(axis=1)
    return df


def _kolom_ternormalisasi(nama_kolom) -> dict:
    """Peta nama kolom asli -> versi dinormalisasi (huruf kecil, tanpa spasi/underscore/strip),
    supaya pencocokan header gak baper sama variasi penulisan ("Nilai Eksakta" vs "nilai_eksakta")."""
    hasil = {}
    for kol in nama_kolom:
        key = re.sub(r"[\s_\-]+", "", str(kol)).strip().lower()
        hasil.setdefault(key, kol)
    return hasil


def _cocokkan_kolom(peta: dict, *alias):
    for a in alias:
        if a in peta:
            return peta[a]
    return None


def baca_file_rekap(file_obj):
    """
    Baca format 'rekap' yang lebih ringkas -- header langsung di baris pertama
    (tanpa skiprows), sudah berupa ringkasan per siswa (bukan leger nilai mentah
    per mapel), mis.:

        No | Nama Siswa | NISN | Nilai Eksakta | Nilai Non-Eksakta | Peringkat | Absensi | Jumlah Ekstrakurikuler

    Return None kalau file ini BUKAN format rekap (kolom wajibnya gak ketemu),
    supaya caller bisa coba baca_file_leger() sebagai fallback.
    """
    nama_file = getattr(file_obj, "name", "file")
    try:
        file_obj.seek(0)
    except Exception:  # noqa: BLE001
        pass
    try:
        mentah = pd.read_excel(file_obj, header=0)
    except Exception:  # noqa: BLE001
        return None

    peta = _kolom_ternormalisasi(mentah.columns)
    kolom_nama = _cocokkan_kolom(peta, "namasiswa", "nama")
    kolom_eksakta = _cocokkan_kolom(peta, "nilaieksakta", "eksakta")
    kolom_noneksakta = _cocokkan_kolom(peta, "nilainoneksakta", "noneksakta")

    if not (kolom_nama and kolom_eksakta and kolom_noneksakta):
        return None  # bukan format rekap -- biar dicoba format leger di caller

    kolom_nisn = _cocokkan_kolom(peta, "nisn")
    kolom_nis = _cocokkan_kolom(peta, "nis")
    kolom_absensi = _cocokkan_kolom(peta, "absensi", "jumlahabsen", "totalabsen", "absen")
    kolom_ekskul = _cocokkan_kolom(
        peta, "jumlahekstrakurikuler", "ekstrakurikuler", "jumlahekskul", "ekskul"
    )

    df = pd.DataFrame()
    df["Nama_Siswa"] = mentah[kolom_nama].astype(str).str.strip()
    df["NISN"] = mentah[kolom_nisn].astype(str).str.strip() if kolom_nisn else ""
    df["NIS"] = mentah[kolom_nis].astype(str).str.strip() if kolom_nis else ""
    df["Eksakta"] = pd.to_numeric(mentah[kolom_eksakta], errors="coerce")
    df["NonEksakta"] = pd.to_numeric(mentah[kolom_noneksakta], errors="coerce")

    if kolom_absensi:
        absensi = pd.to_numeric(mentah[kolom_absensi], errors="coerce").fillna(0.0)
    else:
        absensi = 0.0
    # Format rekap cuma punya 1 angka "Absensi" total (gak dipisah izin/sakit/alpa).
    # Dimasukkan sebagai "Izin" (bobot x1 di Skor_Disiplin) -- bukan "Alpa" (bobot x3) --
    # supaya gak menghukum siswa 3x lipat berdasarkan angka yang belum tentu alpa semua.
    df["Izin"] = absensi
    df["Sakit"] = 0.0
    df["Alpa"] = 0.0
    if kolom_ekskul:
        df["Jumlah_Ekstrakurikuler"] = pd.to_numeric(mentah[kolom_ekskul], errors="coerce").fillna(0).astype(int)
    else:
        df["Jumlah_Ekstrakurikuler"] = 0

    df = df[df["Nama_Siswa"].str.lower() != "nan"]
    df = df[df["Nama_Siswa"] != ""]
    df = df.reset_index(drop=True)

    if df.empty:
        raise ImportError_(f"File '{nama_file}' (format rekap) tidak punya baris data siswa yang valid.")

    return df


def _zscore(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    if not std or pd.isna(std):
        return s * 0.0
    return (s - s.mean()) / std


def proses_upload_dan_cluster(files, guru, diupload_oleh=None):
    """
    files: daftar UploadedFile (1 file = 1 kelas, format leger Excel).
    guru: User pemilik Kelas (kelas akan dibuat/diisi atas nama user ini).
    diupload_oleh: User yang benar-benar melakukan aksi upload -- biasanya sama
        dengan `guru`, tapi bisa beda kalau superuser upload-kan untuk guru lain.
        Dipakai untuk RiwayatUploadXlsx supaya tercatat siapa yang upload.

    Return (ringkasan, peringatan):
      ringkasan: dict {"Kelas 1A": {"jumlah": n, "cerdas": x, "pintar": y, "malas": z}, ...}
      peringatan: list pesan warning (mis. file yang gagal dibaca, dilewati).
    """
    if diupload_oleh is None:
        diupload_oleh = guru

    peringatan = []
    daftar_df = []
    nama_file_per_label = {}  # label_kelas -> nama file asli (buat riwayat upload)
    file_asli_per_label = {}  # label_kelas -> UploadedFile asli (buat disimpan & diunduh lagi)

    for f in files:
        nama_file = getattr(f, "name", "") or "tanpa-nama.xlsx"
        label = deteksi_label_kelas(nama_file)
        try:
            df = baca_file_rekap(f)
            if df is None:
                df = baca_file_leger(f, label=label)
        except ImportError_ as exc:
            peringatan.append(str(exc))
            continue
        df["Kelas"] = label
        m = re.search(r"\d+", label)
        df["Tingkat"] = int(m.group()) if m else 0
        daftar_df.append(df)
        nama_file_per_label[label] = nama_file
        file_asli_per_label[label] = f

    if not daftar_df:
        detail = " ".join(peringatan) if peringatan else ""
        raise ImportError_(
            "Tidak ada file yang berhasil dibaca. Periksa kembali format file Excel-nya."
            + (f" Detail: {detail}" if detail else "")
        )

    df_sekolah = pd.concat(daftar_df, ignore_index=True)

    # "Eksakta", "NonEksakta", "Izin", "Sakit", "Alpa" sudah dihitung masing-masing
    # oleh baca_file_leger()/baca_file_rekap() -- di sini cuma jaga-jaga terakhir
    # supaya gak ada NaN yang nyangkut sampai disimpan ke database (bisa bikin
    # "NOT NULL constraint failed").
    kolom_fitur = ["Eksakta", "NonEksakta", "Izin", "Sakit", "Alpa"]
    for c in kolom_fitur:
        df_sekolah[c] = pd.to_numeric(df_sekolah[c], errors="coerce")
    df_sekolah[kolom_fitur] = df_sekolah[kolom_fitur].apply(lambda s: s.fillna(s.median()))
    df_sekolah[kolom_fitur] = df_sekolah[kolom_fitur].fillna(0.0)
    if "Jumlah_Ekstrakurikuler" not in df_sekolah.columns:
        df_sekolah["Jumlah_Ekstrakurikuler"] = 0
    df_sekolah["Jumlah_Ekstrakurikuler"] = (
        pd.to_numeric(df_sekolah["Jumlah_Ekstrakurikuler"], errors="coerce").fillna(0).astype(int)
    )

    df_sekolah["Nilai_Akademik_Rata2"] = df_sekolah[["Eksakta", "NonEksakta"]].mean(axis=1)
    # rangking tetap per Kelas (per rombel), biar adil dibanding sesama teman sekelas
    df_sekolah["Rangking"] = (
        df_sekolah.groupby("Kelas")["Nilai_Akademik_Rata2"].rank(method="min", ascending=False)
    )

    # Skor_Akademik & Skor_Disiplin berbasis z-score (sama seperti notebook).
    # Rangking/Izin/Sakit/Alpa: makin kecil makin bagus -> dibalik tandanya.
    # Alpa dikasih bobot x3 karena bolos tanpa keterangan = indikator "malas" paling kuat.
    df_sekolah["Skor_Akademik"] = (
        _zscore(df_sekolah["Eksakta"]) + _zscore(df_sekolah["NonEksakta"]) - _zscore(df_sekolah["Rangking"])
    )
    df_sekolah["Skor_Disiplin"] = -(
        _zscore(df_sekolah["Izin"]) + _zscore(df_sekolah["Sakit"]) + 3 * _zscore(df_sekolah["Alpa"])
    )

    n = len(df_sekolah)
    skor_total = df_sekolah["Skor_Akademik"] + df_sekolah["Skor_Disiplin"]

    def _label_berdasarkan_peringkat(skor_total):
        """Urutkan siswa dari skor_total tertinggi->terendah, lalu bagi rata ke
        3 kelompok (sepertiga teratas=Cerdas, tengah=Pintar, bawah=Malas).
        Dipakai utk n<3 ATAU saat K-Means gagal membentuk 3 cluster berbeda
        (data terlalu seragam -- lihat ConvergenceWarning sklearn)."""
        m = len(skor_total)
        urutan = skor_total.sort_values(ascending=False).index
        label3 = ["cerdas", "pintar", "malas"]
        kategori = pd.Series(index=skor_total.index, dtype=object)
        for rank, idx in enumerate(urutan):
            kategori.loc[idx] = label3[min(rank * 3 // m, 2)]
        return kategori

    if n < 3:
        # kurang dari 3 siswa -> tidak cukup buat 3 cluster, urutkan manual
        df_sekolah["Kategori"] = _label_berdasarkan_peringkat(skor_total)
    else:
        X_cluster = df_sekolah[["Skor_Akademik", "Skor_Disiplin"]].fillna(0.0).to_numpy()
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df_sekolah["Cluster_Raw"] = kmeans.fit_predict(X_cluster)

        if len(set(df_sekolah["Cluster_Raw"])) < 3:
            # K-Means gagal membentuk 3 cluster berbeda (data terlalu seragam)
            # -- fallback ke urutan skor_total supaya tetap 3 kategori.
            df_sekolah["Kategori"] = _label_berdasarkan_peringkat(skor_total)
        else:
            skor_total_per_cluster = df_sekolah.groupby("Cluster_Raw").apply(
                lambda g: (g["Skor_Akademik"] + g["Skor_Disiplin"]).mean()
            )
            urutan_cluster = skor_total_per_cluster.sort_values(ascending=False).index.tolist()
            label_map = {
                urutan_cluster[0]: "cerdas",
                urutan_cluster[1]: "pintar",
                urutan_cluster[2]: "malas",
            }
            df_sekolah["Kategori"] = df_sekolah["Cluster_Raw"].map(label_map)

    # ------------------------------------------------------------------
    # Simpan ke database -- dipisah lagi per Kelas asalnya (1A, 1B, 2A, 2B, ...)
    # ------------------------------------------------------------------
    now = timezone.now()
    ringkasan = {}

    for label_kelas, grup in df_sekolah.groupby("Kelas"):
        nama_kelas = f"Kelas {label_kelas}"
        kelas_obj, _ = Kelas.objects.get_or_create(guru=guru, nama=nama_kelas)
        hitung = {"cerdas": 0, "pintar": 0, "malas": 0}
        meja_berikutnya = kelas_obj.siswa_list.count() + 1

        for _, row in grup.iterrows():
            nama_siswa = str(row.get("Nama_Siswa", "")).strip()
            if not nama_siswa or nama_siswa.lower() == "nan":
                continue
            nis = str(row.get("NIS", "")).strip()
            nis = "" if nis.lower() == "nan" else nis
            nisn = str(row.get("NISN", "")).strip()
            nisn = "" if nisn.lower() == "nan" else nisn

            siswa = None
            if nis:
                siswa = Siswa.objects.filter(kelas=kelas_obj, nis=nis).first()
            if siswa is None:
                siswa = Siswa.objects.filter(kelas=kelas_obj, nama=nama_siswa).first()
            if siswa is None:
                siswa = Siswa(kelas=kelas_obj, nama=nama_siswa, nomor_meja=meja_berikutnya)
                meja_berikutnya += 1

            # NB: "x or 0" TIDAK aman buat NaN, karena float('nan') itu truthy di Python
            # (jadi "NaN or 0" hasilnya NaN, bukan 0) -- makanya dicek manual pakai pd.isna.
            def _angka_aman(nilai):
                nilai = pd.to_numeric(nilai, errors="coerce")
                return 0.0 if pd.isna(nilai) else float(nilai)

            izin = _angka_aman(row.get("Izin", 0))
            sakit = _angka_aman(row.get("Sakit", 0))
            alpa = _angka_aman(row.get("Alpa", 0))
            eksakta = round(float(row["Eksakta"]), 1)
            nonekstakta = round(float(row["NonEksakta"]), 1)
            kehadiran_estimasi = max(0.0, min(100.0, 100 - (izin * 1 + sakit * 1 + alpa * 3)))

            siswa.nama = nama_siswa
            siswa.nis = nis
            siswa.nisn = nisn
            siswa.nilai_matematika = eksakta
            siswa.nilai_bahasa = nonekstakta
            siswa.kehadiran_persen = round(kehadiran_estimasi, 1)
            siswa.keaktifan = nonekstakta
            siswa.eksakta = eksakta
            siswa.nonekstakta = nonekstakta
            siswa.izin = izin
            siswa.sakit = sakit
            siswa.alpa = alpa
            siswa.rangking = float(row["Rangking"])
            siswa.skor_akademik = round(float(row["Skor_Akademik"]), 3)
            siswa.skor_disiplin = round(float(row["Skor_Disiplin"]), 3)
            siswa.jumlah_ekstrakurikuler = int(row.get("Jumlah_Ekstrakurikuler", 0) or 0)
            siswa.cluster_label = row["Kategori"]
            siswa.cluster_raw = int(row["Cluster_Raw"]) if "Cluster_Raw" in row and not pd.isna(row["Cluster_Raw"]) else None
            siswa.cluster_terakhir_diupdate = now
            siswa.save()

            hitung[row["Kategori"]] += 1

        ringkasan[nama_kelas] = {"jumlah": int(len(grup)), **hitung}

        riwayat = RiwayatUploadXlsx(
            kelas=kelas_obj,
            diupload_oleh=diupload_oleh,
            nama_file=nama_file_per_label.get(label_kelas, "tanpa-nama.xlsx"),
            jumlah_siswa=int(len(grup)),
        )
        f_asli = file_asli_per_label.get(label_kelas)
        if f_asli is not None:
            try:
                f_asli.seek(0)
            except Exception:  # noqa: BLE001
                pass
            riwayat.file_asli.save(
                nama_file_per_label.get(label_kelas, "tanpa-nama.xlsx"), f_asli, save=False
            )
        riwayat.save()

    return ringkasan, peringatan
